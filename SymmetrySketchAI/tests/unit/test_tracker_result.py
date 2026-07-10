"""Unit tests for vision.tracker_result.TrackerResult."""

from __future__ import annotations

import pytest

from core.enums import HandLabel
from vision.hand import Hand
from vision.landmarks import LandmarkPoint, Landmarks
from vision.tracker_result import TrackerResult, TrackerResultValidationError


def make_landmarks() -> Landmarks:
    points = tuple(LandmarkPoint(x=0.5, y=0.5, z=0.0) for _ in range(21))
    return Landmarks(points=points)


def make_hand(label: HandLabel = HandLabel.RIGHT) -> Hand:
    return Hand(
        label=label, handedness_confidence=0.9, landmarks=make_landmarks()
    )


def make_result(**overrides: object) -> TrackerResult:
    defaults: dict[str, object] = {
        "hands": (),
        "timestamp": 1.0,
        "frame_width": 1280,
        "frame_height": 720,
        "inference_time_ms": 12.5,
    }
    defaults.update(overrides)
    return TrackerResult(**defaults)  # type: ignore[arg-type]


class TestTrackerResultConstruction:
    def test_valid_construction_succeeds(self) -> None:
        result = make_result()
        assert result.frame_size == (1280, 720)

    def test_rejects_negative_timestamp(self) -> None:
        with pytest.raises(TrackerResultValidationError):
            make_result(timestamp=-1.0)

    def test_rejects_non_positive_frame_width(self) -> None:
        with pytest.raises(TrackerResultValidationError):
            make_result(frame_width=0)

    def test_rejects_non_positive_frame_height(self) -> None:
        with pytest.raises(TrackerResultValidationError):
            make_result(frame_height=-10)

    def test_rejects_negative_inference_time(self) -> None:
        with pytest.raises(TrackerResultValidationError):
            make_result(inference_time_ms=-1.0)

    def test_is_immutable(self) -> None:
        result = make_result()
        with pytest.raises(Exception):
            result.timestamp = 5.0  # type: ignore[misc]


class TestTrackerResultEmptyFactory:
    def test_empty_has_no_hands(self) -> None:
        result = TrackerResult.empty(
            timestamp=0.0, frame_width=640, frame_height=480
        )
        assert result.has_hands is False
        assert result.hand_count == 0
        assert result.hands == ()


class TestTrackerResultHandAccess:
    def test_has_hands_true_when_hands_present(self) -> None:
        result = make_result(hands=(make_hand(),))
        assert result.has_hands is True
        assert result.hand_count == 1

    def test_hand_by_label_returns_matching_hand(self) -> None:
        left = make_hand(HandLabel.LEFT)
        right = make_hand(HandLabel.RIGHT)
        result = make_result(hands=(left, right))
        assert result.hand_by_label(HandLabel.LEFT) is left
        assert result.hand_by_label(HandLabel.RIGHT) is right

    def test_hand_by_label_returns_none_when_absent(self) -> None:
        result = make_result(hands=(make_hand(HandLabel.RIGHT),))
        assert result.hand_by_label(HandLabel.LEFT) is None

    def test_primary_hand_returns_first_hand(self) -> None:
        first = make_hand(HandLabel.LEFT)
        second = make_hand(HandLabel.RIGHT)
        result = make_result(hands=(first, second))
        assert result.primary_hand() is first

    def test_primary_hand_returns_none_when_empty(self) -> None:
        result = make_result(hands=())
        assert result.primary_hand() is None
