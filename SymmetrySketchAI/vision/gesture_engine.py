"""The stateful Gesture Engine -- turns tracked hands into GestureEvents.

Design rationale:
    Per the project data flow (Camera -> Tracker -> Gesture Engine ->
    Stroke Engine), the engine is the temporal brain of the vision
    layer. Where :class:`~vision.gesture_classifier.GestureClassifier`
    answers "what pose is this single frame?", the engine answers "what
    is the user actually *doing* over time?" It owns everything the
    stateless classifier cannot:

      * Smoothing raw landmarks (via
        :class:`~vision.smoothing.LandmarkSmoother`) before classifying.
      * Debouncing: a candidate pose must persist for
        ``gesture_hold_frames_to_confirm`` frames before it is emitted,
        killing single-frame flicker.
      * Motion gestures: SWIPE_LEFT / SWIPE_RIGHT from fingertip travel.
      * Per-hand velocity and a pinch-derived pressure estimate.
      * Tracking each hand's previous gesture so downstream consumers
        get transition information "for free" on the emitted
        :class:`~domain.entities.gesture_event.GestureEvent`.

    It emits the project's existing ``GestureEvent`` value object and,
    optionally, publishes a :class:`GestureRecognizedEvent` on the
    shared :class:`~core.events.EventBus`, so the future Stroke Engine
    can subscribe without importing the vision layer directly.

    The engine holds no OpenCV/MediaPipe references; it consumes only
    project-owned value objects (:class:`~vision.tracker_result.TrackerResult`,
    :class:`~vision.hand.Hand`).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Final

from config.tracker_config import TrackerConfig
from core.constants import MAX_PRESSURE
from core.dependency_container import DependencyContainer
from core.enums import GestureType, HandLabel
from core.events import Event, EventBus
from core.exceptions import GestureRecognitionError
from core.logger import get_logger
from domain.entities.gesture_event import GestureEvent
from vision.gesture_classifier import GestureClassifier
from vision.hand import Hand
from vision.landmarks import Landmarks
from vision.smoothing import LandmarkSmoother
from vision.tracker_result import TrackerResult

_logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Tuning constants (no magic numbers). Distances in normalized [0, 1] space.
# ---------------------------------------------------------------------------

POSITION_HISTORY_MAXLEN: Final[int] = 16
"""How many recent fingertip samples to retain per hand for motion."""

SWIPE_MAX_TIME_SECONDS: Final[float] = 0.4
"""Longest time window over which a swipe displacement may accumulate."""

SWIPE_MIN_DISPLACEMENT: Final[float] = 0.20
"""Minimum horizontal fingertip travel (fraction of frame) for a swipe."""

SWIPE_MIN_SPEED: Final[float] = 0.6
"""Minimum horizontal speed (normalized units / second) for a swipe."""

PINCH_PRESSURE_RANGE: Final[float] = 0.08
"""Thumb/index distance mapped to the [0, 1] pinch pressure estimate."""


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True, slots=True)
class GestureRecognizedEvent(Event):
    """Published on the :class:`EventBus` whenever the engine emits a
    :class:`GestureEvent`.

    Carrying the value object (rather than loose fields) keeps the event
    self-describing and lets subscribers act without touching the
    vision layer.
    """

    gesture_event: GestureEvent


@dataclass(slots=True)
class _HandState:
    """Mutable per-hand tracking state, keyed by :class:`HandLabel`."""

    smoother: LandmarkSmoother
    candidate: GestureType | None = None
    streak: int = 0
    confirmed: GestureType = GestureType.NONE
    confirmed_confidence: float = 1.0
    last_emitted: GestureType = GestureType.NONE
    last_timestamp: float | None = None
    history: Deque[tuple[float, float, float]] = field(
        default_factory=lambda: deque(maxlen=POSITION_HISTORY_MAXLEN)
    )


class GestureEngine:
    """Converts a stream of :class:`TrackerResult` frames into
    :class:`GestureEvent` objects, one per tracked hand per frame.

    Usage:
        >>> engine = GestureEngine(config=TrackerConfig())
        >>> for frame in tracker_frames:
        ...     for event in engine.process(frame):
        ...         handle(event)
    """

    def __init__(
        self,
        config: TrackerConfig | None = None,
        classifier: GestureClassifier | None = None,
        event_bus: EventBus | None = None,
        container: DependencyContainer | None = None,
    ) -> None:
        """Construct a :class:`GestureEngine`.

        Args:
            config: Tuning parameters. ``smoothing_window_size`` and
                ``gesture_hold_frames_to_confirm`` are read from here,
                so there is a single source of truth shared with the
                tracker. Defaults to :class:`TrackerConfig`.
            classifier: Static-pose classifier. Injectable for testing
                or future ML replacement. Defaults to
                :class:`GestureClassifier`.
            event_bus: If provided, a :class:`GestureRecognizedEvent` is
                published for every emitted gesture.
            container: Optional shared DI container; reserved for
                bootstrap wiring, not required for standalone use.
        """
        self._config = config or TrackerConfig()
        self._classifier = classifier or GestureClassifier()
        self._event_bus = event_bus
        self._container = container
        self._states: dict[HandLabel, _HandState] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def process(self, result: TrackerResult) -> tuple[GestureEvent, ...]:
        """Process one tracker frame, returning one event per hand.

        Hands that were tracked previously but are absent this frame have
        their per-hand state discarded, so stale velocity/history never
        leaks across a detection gap.
        """
        events: list[GestureEvent] = []
        seen: set[HandLabel] = set()
        for hand in result.hands:
            seen.add(hand.label)
            events.append(self.process_hand(hand, result.timestamp))

        for label in list(self._states):
            if label not in seen:
                del self._states[label]

        return tuple(events)

    def process_hand(self, hand: Hand, timestamp: float) -> GestureEvent:
        """Process a single hand and return its :class:`GestureEvent`.

        Raises:
            GestureRecognitionError: If recognition fails on valid input.
        """
        state = self._states.get(hand.label)
        if state is None:
            state = _HandState(
                smoother=LandmarkSmoother(self._config.smoothing_window_size)
            )
            self._states[hand.label] = state

        try:
            smoothed = state.smoother.smooth(hand.landmarks)
            tip = smoothed.index_finger_tip

            velocity = self._compute_velocity(state, timestamp, tip.x, tip.y)
            state.history.append((timestamp, tip.x, tip.y))

            previous = state.last_emitted
            swipe = self._detect_swipe(state)
            if swipe is not None:
                gesture, confidence = swipe
                state.candidate = None
                state.streak = 0
                state.confirmed = gesture
                state.confirmed_confidence = confidence
                state.history.clear()
                pressure = MAX_PRESSURE
            else:
                smoothed_hand = Hand(
                    label=hand.label,
                    handedness_confidence=hand.handedness_confidence,
                    landmarks=smoothed,
                )
                classification = self._classifier.classify(smoothed_hand)
                gesture, confidence = self._confirm(
                    state, classification.gesture_type, classification.confidence
                )
                pressure = self._estimate_pressure(gesture, smoothed)

            state.last_timestamp = timestamp

            event = GestureEvent(
                gesture_type=gesture,
                hand_label=hand.label,
                timestamp=timestamp,
                confidence=confidence,
                landmarks=tuple(point.as_tuple() for point in smoothed.points),
                velocity=velocity,
                pressure_estimate=pressure,
                previous_gesture_type=previous,
            )
            state.last_emitted = gesture

            if self._event_bus is not None:
                self._event_bus.publish(GestureRecognizedEvent(gesture_event=event))
            return event
        except GestureRecognitionError:
            raise
        except Exception as error:  # noqa: BLE001 - re-raised as domain error
            raise GestureRecognitionError(
                f"Failed to recognize gesture for {hand.label!r}: {error}"
            ) from error

    def reset(self) -> None:
        """Discard all per-hand state (e.g. between drawing sessions)."""
        self._states.clear()

    # ------------------------------------------------------------------
    # Internal: temporal confirmation (debounce)
    # ------------------------------------------------------------------
    def _confirm(
        self, state: _HandState, raw: GestureType, raw_confidence: float
    ) -> tuple[GestureType, float]:
        """Debounce ``raw`` and return the currently confirmed gesture.

        A candidate must persist for ``gesture_hold_frames_to_confirm``
        consecutive frames before it replaces the confirmed gesture.
        Until then, the last confirmed gesture keeps being emitted.
        """
        if raw == state.candidate:
            state.streak += 1
        else:
            state.candidate = raw
            state.streak = 1

        if state.streak >= self._config.gesture_hold_frames_to_confirm:
            state.confirmed = raw
            state.confirmed_confidence = raw_confidence

        return state.confirmed, state.confirmed_confidence

    # ------------------------------------------------------------------
    # Internal: motion
    # ------------------------------------------------------------------
    def _compute_velocity(
        self, state: _HandState, timestamp: float, x: float, y: float
    ) -> float:
        """Return fingertip speed in normalized units/second, or 0.

        Note: this is normalized-image-space speed. A canvas mapping (in
        the future drawing layer) can rescale it to canvas units.
        """
        if state.last_timestamp is None or not state.history:
            return 0.0
        dt = timestamp - state.last_timestamp
        if dt <= 0.0:
            return 0.0
        _, prev_x, prev_y = state.history[-1]
        return math.hypot(x - prev_x, y - prev_y) / dt

    def _detect_swipe(
        self, state: _HandState
    ) -> tuple[GestureType, float] | None:
        """Detect a horizontal swipe from recent fingertip history.

        Returns ``(gesture, confidence)`` for a qualifying swipe, else
        ``None``. A swipe must (a) accumulate enough horizontal travel
        (b) within the time window, (c) be horizontal-dominant, and
        (d) exceed the minimum speed.
        """
        if len(state.history) < 2:
            return None

        t_now, x_now, y_now = state.history[-1]
        start: tuple[float, float, float] | None = None
        for sample in state.history:
            if t_now - sample[0] <= SWIPE_MAX_TIME_SECONDS:
                start = sample
                break
        if start is None:
            return None

        t0, x0, y0 = start
        dt = t_now - t0
        if dt <= 0.0:
            return None

        dx = x_now - x0
        dy = y_now - y0
        if abs(dx) < SWIPE_MIN_DISPLACEMENT:
            return None
        if abs(dx) <= abs(dy):  # must be horizontal-dominant
            return None
        if abs(dx) / dt < SWIPE_MIN_SPEED:
            return None

        confidence = _clamp01(abs(dx) / (2.0 * SWIPE_MIN_DISPLACEMENT))
        gesture = GestureType.SWIPE_LEFT if dx < 0 else GestureType.SWIPE_RIGHT
        return gesture, confidence

    def _estimate_pressure(
        self, gesture: GestureType, landmarks: Landmarks
    ) -> float:
        """Estimate simulated pressure in ``[0, 1]``.

        For a pinch, closer thumb/index tips mean higher pressure. All
        other gestures default to full pressure, matching the
        :class:`GestureEvent` / :class:`Point` default.
        """
        if gesture is GestureType.PINCH:
            distance = landmarks.thumb_tip.distance_to_2d(
                landmarks.index_finger_tip
            )
            return _clamp01(1.0 - distance / PINCH_PRESSURE_RANGE)
        return MAX_PRESSURE