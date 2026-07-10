"""Milestone 4C -- Vision Integration Demo.

Purpose:
    Prove that the completed Vision Foundation and Gesture Recognition layers
    work together end-to-end: Camera -> HandTracker -> TrackerResult ->
    GestureEngine -> GestureEvent, visualized in real time.

Scope (intentionally narrow):
    This module implements NO new business logic. It only *integrates* existing
    modules -- ``HandTracker``, ``GestureEngine``, ``TrackerConfig``,
    ``AppConfig``, ``EventBus`` and ``DependencyContainer`` -- and renders their
    output. It never creates strokes, draws artwork, renders symmetry, touches
    layers, or saves/loads/exports anything.

Rendering note:
    ``HandTracker`` is the single sanctioned camera boundary and does not expose
    the raw camera frame (and ``vision/`` must not be modified). The demo
    therefore draws the tracking overlay (skeleton, landmarks, bounding boxes,
    gesture, confidence, FPS, frame time) onto a synthesized canvas sized from
    each ``TrackerResult`` rather than compositing over the BGR frame.

Run:
    python -m examples.vision_demo      # from the package root; ESC to exit
"""

from __future__ import annotations

import logging
import time
from collections import deque
from typing import Final

from config.app_config import AppConfig
from config.tracker_config import TrackerConfig
from core.dependency_container import DependencyContainer
from core.enums import GestureType, HandLabel  # noqa: F401  (HandLabel: HUD labels)
from core.events import EventBus
from core.exceptions import (
    CameraNotAvailableError,
    HandLandmarkerInitializationError,
    VisionError,
)
from core.logger import get_logger
from domain.entities.gesture_event import GestureEvent
from vision.gesture_engine import GestureEngine
from vision.hand import Hand
from vision.landmarks import HandLandmarkIndex
from vision.tracker_result import TrackerResult
from vision.utils.coordinate_utils import normalized_to_pixel

print("VISION_DEMO STARTED")

_logger = get_logger(__name__)

WINDOW_NAME: Final[str] = "SymmetrySketch AI -- Vision Demo (Milestone 4C)"
_ESC_KEY: Final[int] = 27
_FPS_SAMPLE_WINDOW: Final[int] = 30

# BGR colors (OpenCV convention).
_COLOR_LANDMARK: Final[tuple[int, int, int]] = (0, 255, 120)
_COLOR_CONNECTION: Final[tuple[int, int, int]] = (0, 180, 90)
_COLOR_BBOX: Final[tuple[int, int, int]] = (255, 180, 0)
_COLOR_TEXT: Final[tuple[int, int, int]] = (240, 240, 240)
_COLOR_ACCENT: Final[tuple[int, int, int]] = (0, 220, 255)

# Standard MediaPipe 21-point hand skeleton, expressed with the project's own
# HandLandmarkIndex enum so no landmark-index constants are duplicated here.
_HAND_CONNECTIONS: Final[
    tuple[tuple[HandLandmarkIndex, HandLandmarkIndex], ...]
] = (
    (HandLandmarkIndex.WRIST, HandLandmarkIndex.THUMB_CMC),
    (HandLandmarkIndex.THUMB_CMC, HandLandmarkIndex.THUMB_MCP),
    (HandLandmarkIndex.THUMB_MCP, HandLandmarkIndex.THUMB_IP),
    (HandLandmarkIndex.THUMB_IP, HandLandmarkIndex.THUMB_TIP),
    (HandLandmarkIndex.WRIST, HandLandmarkIndex.INDEX_FINGER_MCP),
    (HandLandmarkIndex.INDEX_FINGER_MCP, HandLandmarkIndex.INDEX_FINGER_PIP),
    (HandLandmarkIndex.INDEX_FINGER_PIP, HandLandmarkIndex.INDEX_FINGER_DIP),
    (HandLandmarkIndex.INDEX_FINGER_DIP, HandLandmarkIndex.INDEX_FINGER_TIP),
    (HandLandmarkIndex.INDEX_FINGER_MCP, HandLandmarkIndex.MIDDLE_FINGER_MCP),
    (HandLandmarkIndex.MIDDLE_FINGER_MCP, HandLandmarkIndex.MIDDLE_FINGER_PIP),
    (HandLandmarkIndex.MIDDLE_FINGER_PIP, HandLandmarkIndex.MIDDLE_FINGER_DIP),
    (HandLandmarkIndex.MIDDLE_FINGER_DIP, HandLandmarkIndex.MIDDLE_FINGER_TIP),
    (HandLandmarkIndex.MIDDLE_FINGER_MCP, HandLandmarkIndex.RING_FINGER_MCP),
    (HandLandmarkIndex.RING_FINGER_MCP, HandLandmarkIndex.RING_FINGER_PIP),
    (HandLandmarkIndex.RING_FINGER_PIP, HandLandmarkIndex.RING_FINGER_DIP),
    (HandLandmarkIndex.RING_FINGER_DIP, HandLandmarkIndex.RING_FINGER_TIP),
    (HandLandmarkIndex.RING_FINGER_MCP, HandLandmarkIndex.PINKY_MCP),
    (HandLandmarkIndex.WRIST, HandLandmarkIndex.PINKY_MCP),
    (HandLandmarkIndex.PINKY_MCP, HandLandmarkIndex.PINKY_PIP),
    (HandLandmarkIndex.PINKY_PIP, HandLandmarkIndex.PINKY_DIP),
    (HandLandmarkIndex.PINKY_DIP, HandLandmarkIndex.PINKY_TIP),
)


def build_container(
    app_config: AppConfig | None = None,
    *,
    include_tracker: bool = True,
) -> DependencyContainer:
    """Wire the Vision subsystem into a fresh :class:`DependencyContainer`.

    Registers ``AppConfig`` and ``TrackerConfig`` instances, a shared
    ``EventBus`` singleton, and a ``GestureEngine`` singleton. When
    ``include_tracker`` is True (the default, used by the live demo) a
    ``HandTracker`` singleton is also registered.

    Args:
        app_config: Application config to register. Defaults to ``AppConfig()``.
        include_tracker: Register ``HandTracker`` too. Set False to build a
            fully headless container (no OpenCV/MediaPipe import), which is
            what the integration tests use.

    Returns:
        A configured container. All registrations are lazy: nothing that needs
        a camera or a model is constructed until it is resolved.
    """
    container = DependencyContainer()
    container.register_instance(AppConfig, app_config or AppConfig())
    container.register_instance(TrackerConfig, TrackerConfig())
    container.register_singleton(EventBus, EventBus)
    container.register_singleton(
        GestureEngine,
        lambda: GestureEngine(
            config=container.resolve(TrackerConfig),
            event_bus=container.resolve(EventBus),
            container=container,
        ),
    )

    if include_tracker:
        # Imported lazily: HandTracker pulls in OpenCV + MediaPipe at import
        # time. Deferring the import keeps headless environments (and the
        # integration test) free of those dependencies unless the tracker is
        # actually requested.
        from vision.tracker import HandTracker

        container.register_singleton(
            HandTracker,
            lambda: HandTracker(
                config=container.resolve(TrackerConfig),
                event_bus=container.resolve(EventBus),
                container=container,
            ),
        )

    return container


class _FpsMeter:
    """Rolling FPS / frame-time estimate over the most recent frames."""

    __slots__ = ("_durations",)

    def __init__(self, window: int = _FPS_SAMPLE_WINDOW) -> None:
        self._durations: deque[float] = deque(maxlen=window)

    def record(self, seconds: float) -> None:
        """Record one loop iteration's wall-clock duration (seconds)."""
        if seconds > 0.0:
            self._durations.append(seconds)

    @property
    def frame_time_ms(self) -> float:
        if not self._durations:
            return 0.0
        return 1000.0 * sum(self._durations) / len(self._durations)

    @property
    def fps(self) -> float:
        average = self.frame_time_ms
        return 1000.0 / average if average > 0.0 else 0.0


class VisionDemo:
    """Runs the real-time Camera -> Tracker -> GestureEngine visualization.

    The demo resolves its collaborators from the injected container; it does
    not construct them itself, keeping wiring in one place (``build_container``).
    """

    def __init__(self, container: DependencyContainer) -> None:
        self._container = container
        self._engine: GestureEngine = container.resolve(GestureEngine)
        self._fps = _FpsMeter()
        self._cv2 = None  # bound lazily in run()
        self._np = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def run(self) -> None:
        """Open the tracker, run the processing loop, release everything."""
        import cv2
        import numpy as np
        from vision.tracker import HandTracker

        self._cv2 = cv2
        self._np = np

        tracker = self._container.resolve(HandTracker)
        _logger.info("Starting vision demo. Press ESC to exit.")
        try:
            with tracker:  # start() on enter, stop() (release) on exit
                self._loop(tracker)
        finally:
            cv2.destroyAllWindows()
            _logger.info("Vision demo stopped; all windows closed.")

    def _loop(self, tracker) -> None:
        cv2 = self._cv2
        while True:
            started = time.perf_counter()
            try:
                result = tracker.read_frame()
            except CameraNotAvailableError as error:
                _logger.error("Camera stopped delivering frames: %s", error)
                break

            events = self._engine.process(result)
            canvas = self._render(result, events)
            cv2.imshow(WINDOW_NAME, canvas)

            self._fps.record(time.perf_counter() - started)
            if (cv2.waitKey(1) & 0xFF) == _ESC_KEY:
                _logger.info("ESC pressed; exiting demo loop.")
                break

    # ------------------------------------------------------------------
    # Rendering (presentation only -- no business logic)
    # ------------------------------------------------------------------
    def _render(self, result: TrackerResult, events: tuple[GestureEvent, ...]):
        canvas = self._blank_canvas(result.frame_width, result.frame_height)
        for hand in result.hands:
            self._draw_hand(canvas, hand, result.frame_width, result.frame_height)
        self._draw_hud(canvas, result, events)
        return canvas

    def _blank_canvas(self, width: int, height: int):
        return self._np.zeros((height, width, 3), dtype=self._np.uint8)

    def _draw_hand(self, canvas, hand: Hand, width: int, height: int) -> None:
        cv2 = self._cv2
        landmarks = hand.landmarks

        for start_index, end_index in _HAND_CONNECTIONS:
            start = self._to_pixel(landmarks.by_index(start_index), width, height)
            end = self._to_pixel(landmarks.by_index(end_index), width, height)
            cv2.line(canvas, start, end, _COLOR_CONNECTION, 2)

        for point in landmarks.points:
            cv2.circle(canvas, self._to_pixel(point, width, height), 4,
                       _COLOR_LANDMARK, -1)

        min_x, min_y, max_x, max_y = hand.bounding_box()
        top_left = (int(min_x * width), int(min_y * height))
        bottom_right = (int(max_x * width), int(max_y * height))
        cv2.rectangle(canvas, top_left, bottom_right, _COLOR_BBOX, 2)
        cv2.putText(canvas, hand.label.name,
                    (top_left[0], max(top_left[1] - 8, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, _COLOR_BBOX, 1, cv2.LINE_AA)

    def _to_pixel(self, point, width: int, height: int) -> tuple[int, int]:
        pixel_x, pixel_y = normalized_to_pixel(point.x, point.y, width, height)
        return (int(pixel_x), int(pixel_y))

    def _draw_hud(
        self, canvas, result: TrackerResult, events: tuple[GestureEvent, ...]
    ) -> None:
        cv2 = self._cv2
        lines = [
            WINDOW_NAME,
            f"FPS: {self._fps.fps:5.1f}   Frame: {self._fps.frame_time_ms:5.1f} ms"
            f"   Inference: {result.inference_time_ms:5.1f} ms",
            f"Hands: {result.hand_count}",
        ]
        primary = self._primary_event(result, events)
        if primary is not None:
            lines.append(
                f"Gesture: {primary.gesture_type.name} "
                f"({primary.confidence * 100:4.0f}%)  [{primary.hand_label.name}]"
            )
        else:
            lines.append("Gesture: --")

        y = 24
        for i, text in enumerate(lines):
            color = _COLOR_ACCENT if i == 0 else _COLOR_TEXT
            cv2.putText(canvas, text, (12, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, color, 1, cv2.LINE_AA)
            y += 26

        cv2.putText(canvas, "Press ESC to exit",
                    (12, result.frame_height - 16),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, _COLOR_TEXT, 1, cv2.LINE_AA)

    @staticmethod
    def _primary_event(
        result: TrackerResult, events: tuple[GestureEvent, ...]
    ) -> GestureEvent | None:
        if not events:
            return None
        primary_hand = result.primary_hand()
        if primary_hand is not None:
            for event in events:
                if event.hand_label is primary_hand.label:
                    return event
        return events[0]


def main() -> int:
    """Entry point. Returns a process exit code; never raises on a handled
    vision error.
    """
    app_config = AppConfig()
    logging.basicConfig(
        level=app_config.log_level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )

    try:
        container = build_container(app_config)
        VisionDemo(container).run()
    except ImportError as error:
        _logger.error(
            "A required vision dependency is missing (OpenCV/MediaPipe): %s. "
            "Install with: pip install opencv-python mediapipe",
            error,
        )
        return 1
    except HandLandmarkerInitializationError as error:
        _logger.error(
            "Could not initialize the hand landmarker model: %s. "
            "Verify the model file exists at its configured path.",
            error,
        )
        return 1
    except CameraNotAvailableError as error:
        _logger.error(
            "No usable camera was found (missing, in use, or permission "
            "denied): %s",
            error,
        )
        return 1
    except VisionError as error:
        _logger.error("Vision subsystem error: %s", error)
        return 1
    except KeyboardInterrupt:
        _logger.info("Interrupted by user; shutting down.")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())