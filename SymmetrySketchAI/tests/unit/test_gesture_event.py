"""Unit tests for domain.entities.gesture_event.GestureEvent."""
from __future__ import annotations

import pytest

from core.constants import HAND_LANDMARK_COUNT
from core.enums import GestureType, HandLabel
from core.exceptions import VisionError
from domain.entities.gesture_event import GestureEvent, GestureEventValidationError


def make_landmarks(count: int = HAND_LANDMARK_COUNT) -> tuple[tuple[float, float, float], ...]:
    return tuple((0.1 * i, 0.2 * i, 0.0) for i in range(count))


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_construction(self):
        event = GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
        )
        assert event.confidence == 1.0
        assert event.landmarks == ()
        assert event.velocity == 0.0
        assert event.pressure_estimate == 1.0
        assert event.previous_gesture_type is None

    def test_custom_construction_with_landmarks(self):
        landmarks = make_landmarks()
        event = GestureEvent(
            gesture_type=GestureType.PINCH,
            hand_label=HandLabel.LEFT,
            timestamp=1.5,
            confidence=0.87,
            landmarks=landmarks,
            velocity=42.0,
            pressure_estimate=0.6,
            previous_gesture_type=GestureType.POINT,
        )
        assert event.gesture_type is GestureType.PINCH
        assert event.hand_label is HandLabel.LEFT
        assert event.landmarks == landmarks
        assert event.previous_gesture_type is GestureType.POINT

    def test_is_immutable(self):
        event = GestureEvent(
            gesture_type=GestureType.POINT, hand_label=HandLabel.RIGHT, timestamp=0.0
        )
        with pytest.raises(Exception):
            event.timestamp = 5.0  # type: ignore[misc]

    def test_gesture_event_validation_error_is_a_vision_error(self):
        assert issubclass(GestureEventValidationError, VisionError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    def test_rejects_non_gesture_type(self):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(gesture_type="point", hand_label=HandLabel.RIGHT, timestamp=0.0)  # type: ignore[arg-type]

    def test_rejects_non_hand_label(self):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(gesture_type=GestureType.POINT, hand_label="right", timestamp=0.0)  # type: ignore[arg-type]

    def test_rejects_negative_timestamp(self):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(gesture_type=GestureType.POINT, hand_label=HandLabel.RIGHT, timestamp=-1.0)

    @pytest.mark.parametrize("bad_confidence", [-0.1, 1.1])
    def test_rejects_invalid_confidence(self, bad_confidence):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(
                gesture_type=GestureType.POINT,
                hand_label=HandLabel.RIGHT,
                timestamp=0.0,
                confidence=bad_confidence,
            )

    @pytest.mark.parametrize("bad_pressure", [-0.1, 1.1])
    def test_rejects_invalid_pressure_estimate(self, bad_pressure):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(
                gesture_type=GestureType.POINT,
                hand_label=HandLabel.RIGHT,
                timestamp=0.0,
                pressure_estimate=bad_pressure,
            )

    def test_rejects_wrong_landmark_count(self):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(
                gesture_type=GestureType.POINT,
                hand_label=HandLabel.RIGHT,
                timestamp=0.0,
                landmarks=make_landmarks(HAND_LANDMARK_COUNT - 1),
            )

    def test_accepts_empty_landmarks(self):
        GestureEvent(
            gesture_type=GestureType.NONE,
            hand_label=HandLabel.UNKNOWN,
            timestamp=0.0,
            landmarks=(),
        )

    def test_accepts_full_landmark_set(self):
        GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            landmarks=make_landmarks(),
        )

    def test_rejects_invalid_previous_gesture_type(self):
        with pytest.raises(GestureEventValidationError):
            GestureEvent(
                gesture_type=GestureType.POINT,
                hand_label=HandLabel.RIGHT,
                timestamp=0.0,
                previous_gesture_type="fist",  # type: ignore[arg-type]
            )

    def test_boundary_confidence_and_pressure_are_valid(self):
        GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            confidence=0.0,
            pressure_estimate=0.0,
        )
        GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            confidence=1.0,
            pressure_estimate=1.0,
        )


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

class TestStateTransitions:
    def test_no_previous_gesture_is_not_a_transition(self):
        event = GestureEvent(
            gesture_type=GestureType.POINT, hand_label=HandLabel.RIGHT, timestamp=0.0
        )
        assert event.is_transition is False

    def test_same_previous_gesture_is_not_a_transition(self):
        event = GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            previous_gesture_type=GestureType.POINT,
        )
        assert event.is_transition is False

    def test_different_previous_gesture_is_a_transition(self):
        event = GestureEvent(
            gesture_type=GestureType.FIST,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            previous_gesture_type=GestureType.POINT,
        )
        assert event.is_transition is True

    def test_transitioned_to_matches_target_gesture(self):
        event = GestureEvent(
            gesture_type=GestureType.FIST,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            previous_gesture_type=GestureType.POINT,
        )
        assert event.transitioned_to(GestureType.FIST) is True
        assert event.transitioned_to(GestureType.PINCH) is False

    def test_transitioned_to_false_when_no_transition_occurred(self):
        event = GestureEvent(
            gesture_type=GestureType.POINT,
            hand_label=HandLabel.RIGHT,
            timestamp=0.0,
            previous_gesture_type=GestureType.POINT,
        )
        assert event.transitioned_to(GestureType.POINT) is False
