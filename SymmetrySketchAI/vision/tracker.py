"""Camera capture and MediaPipe Tasks hand-landmark inference.

Design rationale:
    ``HandTracker`` is the single sanctioned boundary between the
    project's domain-clean vision objects (:class:`~vision.hand.Hand`,
    :class:`~vision.landmarks.Landmarks`,
    :class:`~vision.tracker_result.TrackerResult`) and the two external
    libraries involved in acquiring them: OpenCV (camera capture) and
    MediaPipe Tasks (hand landmark inference). No MediaPipe or OpenCV
    type is ever returned from this class -- every public method returns
    either a project domain object or a plain Python type.

    Responsibilities are intentionally narrow, per the Vision Foundation
    scope: initialize the camera, initialize the MediaPipe Tasks
    ``HandLandmarker``, run inference, and convert results. This class
    does not classify gestures, does not create strokes, and does not
    know anything about rendering -- those belong to later phases.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from types import TracebackType

from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    HandLandmarkerResult,
    RunningMode,
)
from mediapipe import Image, ImageFormat

from config.tracker_config import TrackerConfig
from core.dependency_container import DependencyContainer
from core.enums import HandLabel
from core.events import Event, EventBus
from core.exceptions import (
    CameraNotAvailableError,
    HandLandmarkerInitializationError,
)
from core.logger import get_logger
from core.paths import HAND_LANDMARKER_MODEL_PATH
from vision.hand import Hand
from vision.landmarks import Landmarks
from vision.tracker_result import TrackerResult

_logger = get_logger(__name__)

# MediaPipe reports handedness with these exact category names.
_HANDEDNESS_LABEL_MAP: dict[str, HandLabel] = {
    "Left": HandLabel.LEFT,
    "Right": HandLabel.RIGHT,
}


def _resolve_hand_label(category_name: str | None) -> HandLabel:
    """Map a MediaPipe handedness category name onto :class:`HandLabel`."""
    if category_name is None:
        return HandLabel.UNKNOWN
    return _HANDEDNESS_LABEL_MAP.get(category_name, HandLabel.UNKNOWN)


@dataclass(frozen=True, slots=True)
class TrackerStartedEvent(Event):
    """Published when the tracker successfully opens the camera and
    initializes the hand landmarker.
    """


@dataclass(frozen=True, slots=True)
class TrackerStoppedEvent(Event):
    """Published when the tracker releases the camera and shuts down."""


class HandTracker:
    """Acquires camera frames and runs MediaPipe hand-landmark inference.

    Usage:
        >>> tracker = HandTracker(config=TrackerConfig())
        >>> tracker.start()
        >>> result = tracker.read_frame()
        >>> tracker.stop()

    Or as a context manager::

        >>> with HandTracker(config=TrackerConfig()) as tracker:
        ...     result = tracker.read_frame()
    """

    def __init__(
        self,
        config: TrackerConfig,
        container: DependencyContainer | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Construct a :class:`HandTracker`.

        Args:
            config: Camera and MediaPipe tuning parameters. Nothing in
                this class hardcodes a value that belongs here.
            container: Optional shared :class:`DependencyContainer`.
                Reserved for resolving collaborating services during
                application bootstrap; not required for standalone use.
            event_bus: Optional :class:`EventBus` used to publish
                lifecycle events (:class:`TrackerStartedEvent`,
                :class:`TrackerStoppedEvent`). If omitted, no events are
                published.
        """
        self._config = config
        self._container = container
        self._event_bus = event_bus

        self._capture = None
        self._landmarker: HandLandmarker | None = None
        self._session_start_time: float | None = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Return whether the tracker has an active camera + landmarker
        session.
        """
        return self._is_running

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Open the camera and initialize the MediaPipe hand landmarker.

        Raises:
            CameraNotAvailableError: If the configured camera device
                cannot be opened.
            HandLandmarkerInitializationError: If the model file is
                missing or MediaPipe fails to initialize the landmarker.
        """
        if self._is_running:
            return

        self._capture = self._open_camera()
        self._landmarker = self._create_landmarker()
        self._session_start_time = time.monotonic()
        self._is_running = True

        _logger.info(
            "HandTracker started (camera_index=%s, %sx%s@%sfps).",
            self._config.camera_index,
            self._config.camera_width,
            self._config.camera_height,
            self._config.camera_fps,
        )
        if self._event_bus is not None:
            self._event_bus.publish(TrackerStartedEvent())

    def stop(self) -> None:
        """Release the camera and close the hand landmarker.

        Safe to call even if :meth:`start` was never called, or if the
        tracker is already stopped.
        """
        if self._capture is not None:
            self._capture.release()
            self._capture = None

        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

        was_running = self._is_running
        self._is_running = False
        self._session_start_time = None

        if was_running:
            _logger.info("HandTracker stopped.")
            if self._event_bus is not None:
                self._event_bus.publish(TrackerStoppedEvent())

    def __enter__(self) -> "HandTracker":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop()

    # ------------------------------------------------------------------
    # Frame acquisition
    # ------------------------------------------------------------------
    def read_frame(self) -> TrackerResult:
        """Capture one camera frame and run hand-landmark inference on it.

        Returns:
            A :class:`TrackerResult` describing every hand detected in
            the frame. If the frame could not be captured or no hands
            were detected, an empty result is returned rather than
            raising -- a frame with zero hands is a normal, expected
            outcome, not an error.

        Raises:
            CameraNotAvailableError: If the tracker has not been started,
                or the camera stops returning frames.
        """
        if not self._is_running or self._capture is None or self._landmarker is None:
            raise CameraNotAvailableError(
                "HandTracker.read_frame() called before start() (or "
                "after stop())."
            )

        success, frame = self._capture.read()
        if not success or frame is None:
            raise CameraNotAvailableError(
                "Failed to read a frame from the camera; the device may "
                "have been disconnected."
            )

        frame_height, frame_width = frame.shape[0], frame.shape[1]

        if self._config.mirror_camera_feed:
            frame = self._mirror_frame(frame)

        mp_image = self._to_mediapipe_image(frame)

        elapsed_ms_start = time.perf_counter()
        raw_result = self._landmarker.detect(mp_image)
        inference_time_ms = (time.perf_counter() - elapsed_ms_start) * 1000.0

        timestamp = time.monotonic() - (self._session_start_time or 0.0)

        return self._to_tracker_result(
            raw_result=raw_result,
            timestamp=timestamp,
            frame_width=frame_width,
            frame_height=frame_height,
            inference_time_ms=inference_time_ms,
        )

    # ------------------------------------------------------------------
    # Internal helpers -- camera
    # ------------------------------------------------------------------
    def _open_camera(self):
        # Imported lazily so importing this module never requires a
        # working OpenCV/camera backend (e.g. in headless test/CI
        # environments that only exercise the other vision modules).
        import cv2

        capture = cv2.VideoCapture(self._config.camera_index)
        if not capture.isOpened():
            raise CameraNotAvailableError(
                f"Could not open camera at index {self._config.camera_index!r}."
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.camera_width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.camera_height)
        capture.set(cv2.CAP_PROP_FPS, self._config.camera_fps)

        return capture

    def _mirror_frame(self, frame):
        import cv2

        return cv2.flip(frame, 1)

    def _to_mediapipe_image(self, frame) -> Image:
        import cv2

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image(image_format=ImageFormat.SRGB, data=rgb_frame)

    # ------------------------------------------------------------------
    # Internal helpers -- MediaPipe Tasks
    # ------------------------------------------------------------------
    def _create_landmarker(self) -> HandLandmarker:
        model_path = HAND_LANDMARKER_MODEL_PATH
        if not model_path.exists():
            raise HandLandmarkerInitializationError(
                f"Hand landmarker model not found at {model_path}. "
                "Verify the model file was installed correctly."
            )

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=RunningMode.IMAGE,
            num_hands=self._config.max_tracked_hands,
            min_hand_detection_confidence=self._config.min_hand_detection_confidence,
            min_hand_presence_confidence=self._config.min_hand_presence_confidence,
            min_tracking_confidence=self._config.min_tracking_confidence,
        )

        try:
            return HandLandmarker.create_from_options(options)
        except Exception as error:  # noqa: BLE001 - re-raised as domain error
            raise HandLandmarkerInitializationError(
                f"Failed to initialize MediaPipe HandLandmarker: {error}"
            ) from error

    # ------------------------------------------------------------------
    # Internal helpers -- result conversion (the ONLY place MediaPipe
    # result types are read from)
    # ------------------------------------------------------------------
    def _to_tracker_result(
        self,
        raw_result: HandLandmarkerResult,
        timestamp: float,
        frame_width: int,
        frame_height: int,
        inference_time_ms: float,
    ) -> TrackerResult:
        hands: list[Hand] = []

        hand_landmarks_list = raw_result.hand_landmarks or []
        handedness_list = raw_result.handedness or []

        for index, raw_landmarks in enumerate(hand_landmarks_list):
            landmarks = Landmarks.from_coordinates(
                [(lm.x, lm.y, lm.z) for lm in raw_landmarks]
            )

            label = HandLabel.UNKNOWN
            confidence = 0.0
            if index < len(handedness_list) and handedness_list[index]:
                top_category = handedness_list[index][0]
                label = _resolve_hand_label(top_category.category_name)
                confidence = top_category.score

            hands.append(
                Hand(
                    label=label,
                    handedness_confidence=confidence,
                    landmarks=landmarks,
                )
            )

        return TrackerResult(
            hands=tuple(hands),
            timestamp=timestamp,
            frame_width=frame_width,
            frame_height=frame_height,
            inference_time_ms=inference_time_ms,
        )
