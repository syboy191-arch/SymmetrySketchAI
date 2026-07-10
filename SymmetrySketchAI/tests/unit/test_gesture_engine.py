"""Unit tests for vision.gesture_engine.GestureEngine."""
from __future__ import annotations

import pytest

from config.tracker_config import TrackerConfig
from core.enums import GestureType, HandLabel
from core.events import EventBus
from vision.gesture_classifier import GestureClassification, GestureClassifier
from vision.gesture_engine import GestureEngine, GestureRecognizedEvent
from vision.hand import Hand
from vision.landmarks import HandLandmarkIndex, Landmarks
from vision.tracker_result import TrackerResult


def make_landmarks(index_tip_x: float = 0.46) -> Landmarks:
    """Valid 21-point set; the index fingertip x is adjustable for motion."""
    coords = [(0.01 * i + 0.3, 0.02 * i + 0.3, 0.0) for i in range(21)]
    coords[int(HandLandmarkIndex.INDEX_FINGER_TIP)] = (index_tip_x, 0.40, 0.0)
    return Landmarks.from_coordinates(coords)


def make_hand(index_tip_x: float = 0.46, label: HandLabel = HandLabel.RIGHT) -> Hand:
    return Hand(
        label=label,
        handedness_confidence=0.99,
        landmarks=make_landmarks(index_tip_x),
    )


class StubClassifier(GestureClassifier):
    """Classifier that always returns a fixed gesture, for deterministic
    engine tests decoupled from pose geometry.
    """

    def __init__(self, gesture: GestureType, confidence: float = 0.9) -> None:
        super().__init__()
        self._gesture = gesture
        self._confidence = confidence

    def classify(self, hand: Hand) -> GestureClassification:  # type: ignore[override]
        return GestureClassification(self._gesture, self._confidence)


def fast_config() -> TrackerConfig:
    """No smoothing lag, single-frame confirmation -- isolates engine logic."""
    return TrackerConfig(smoothing_window_size=1, gesture_hold_frames_to_confirm=1)


class TestConfirmation:
    def test_gesture_confirmed_only_after_hold_frames(self):
        config = TrackerConfig(
            smoothing_window_size=1, gesture_hold_frames_to_confirm=3
        )
        engine = GestureEngine(config=config, classifier=StubClassifier(GestureType.POINT))
        # Frames 1 and 2 keep emitting the default NONE (not yet confirmed).
        assert engine.process_hand(make_hand(), 0.0).gesture_type is GestureType.NONE
        assert engine.process_hand(make_hand(), 0.1).gesture_type is GestureType.NONE
        # Third consecutive POINT flips the confirmed gesture.
        assert engine.process_hand(make_hand(), 0.2).gesture_type is GestureType.POINT

    def test_single_frame_config_confirms_immediately(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.FIST)
        )
        assert engine.process_hand(make_hand(), 0.0).gesture_type is GestureType.FIST


class TestTransitions:
    def test_previous_gesture_type_tracks_last_emitted(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        first = engine.process_hand(make_hand(), 0.0)
        assert first.previous_gesture_type is GestureType.NONE
        second = engine.process_hand(make_hand(), 0.1)
        assert second.previous_gesture_type is GestureType.POINT
        assert second.is_transition is False  # POINT -> POINT


class TestVelocity:
    def test_velocity_zero_on_first_frame(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        assert engine.process_hand(make_hand(0.4), 0.0).velocity == 0.0

    def test_velocity_positive_after_movement(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(0.40), 0.0)
        event = engine.process_hand(make_hand(0.50), 0.1)
        assert event.velocity > 0.0


class TestSwipe:
    def test_fast_leftward_motion_is_swipe_left(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(0.80), 0.0)
        event = engine.process_hand(make_hand(0.30), 0.1)
        assert event.gesture_type is GestureType.SWIPE_LEFT

    def test_fast_rightward_motion_is_swipe_right(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(0.20), 0.0)
        event = engine.process_hand(make_hand(0.70), 0.1)
        assert event.gesture_type is GestureType.SWIPE_RIGHT

    def test_slow_motion_is_not_a_swipe(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(0.45), 0.0)
        event = engine.process_hand(make_hand(0.50), 1.0)  # tiny, slow move
        assert event.gesture_type is GestureType.POINT


class TestPressure:
    def test_non_pinch_defaults_to_full_pressure(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        assert engine.process_hand(make_hand(), 0.0).pressure_estimate == 1.0


class TestProcessFrame:
    def test_process_returns_event_per_hand(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.OPEN_PALM)
        )
        result = TrackerResult(
            hands=(make_hand(label=HandLabel.RIGHT),),
            timestamp=0.0,
            frame_width=1280,
            frame_height=720,
            inference_time_ms=5.0,
        )
        events = engine.process(result)
        assert len(events) == 1
        assert events[0].gesture_type is GestureType.OPEN_PALM

    def test_empty_frame_returns_no_events_and_clears_state(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(), 0.0)
        empty = TrackerResult.empty(timestamp=0.1, frame_width=1280, frame_height=720)
        assert engine.process(empty) == ()

    def test_reset_clears_state(self):
        engine = GestureEngine(
            config=fast_config(), classifier=StubClassifier(GestureType.POINT)
        )
        engine.process_hand(make_hand(), 0.0)
        engine.reset()
        # After reset the next frame starts from NONE previous again.
        event = engine.process_hand(make_hand(), 0.1)
        assert event.previous_gesture_type is GestureType.NONE


class TestEventBus:
    def test_publishes_gesture_recognized_event(self):
        bus = EventBus()
        received: list[GestureRecognizedEvent] = []
        bus.subscribe(GestureRecognizedEvent, received.append)
        engine = GestureEngine(
            config=fast_config(),
            classifier=StubClassifier(GestureType.POINT),
            event_bus=bus,
        )
        engine.process_hand(make_hand(), 0.0)
        assert len(received) == 1
        assert received[0].gesture_event.gesture_type is GestureType.POINT