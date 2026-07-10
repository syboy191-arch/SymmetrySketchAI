"""Unit tests for vision.hand.Hand."""

from __future__ import annotations

import pytest

from core.enums import HandLabel
from vision.hand import Hand, HandValidationError
from vision.landmarks import LandmarkPoint, Landmarks


def make_landmarks() -> Landmarks:
    points = tuple(
        LandmarkPoint(x=i / 20.0, y=1.0 - i / 20.0, z=0.0) for i in range(21)
    )
    return Landmarks(points=points)


def make_hand(**overrides: object) -> Hand:
    defaults: dict[str, object] = {
        "label": HandLabel.RIGHT,
        "handedness_confidence": 0.9,
        "landmarks": make_landmarks(),
    }
    defaults.update(overrides)
    return Hand(**defaults)  # type: ignore[arg-type]


class TestHandConstruction:
    def test_valid_construction_succeeds(self) -> None:
        hand = make_hand()
        assert hand.label is HandLabel.RIGHT
        assert hand.handedness_confidence == pytest.approx(0.9)

    def test_rejects_confidence_above_one(self) -> None:
        with pytest.raises(HandValidationError):
            make_hand(handedness_confidence=1.5)

    def test_rejects_negative_confidence(self) -> None:
        with pytest.raises(HandValidationError):
            make_hand(handedness_confidence=-0.1)

    def test_is_immutable(self) -> None:
        hand = make_hand()
        with pytest.raises(Exception):
            hand.label = HandLabel.LEFT  # type: ignore[misc]


class TestHandLabelHelpers:
    def test_is_left_true_for_left_hand(self) -> None:
        hand = make_hand(label=HandLabel.LEFT)
        assert hand.is_left is True
        assert hand.is_right is False

    def test_is_right_true_for_right_hand(self) -> None:
        hand = make_hand(label=HandLabel.RIGHT)
        assert hand.is_right is True
        assert hand.is_left is False

    def test_unknown_label_is_neither(self) -> None:
        hand = make_hand(label=HandLabel.UNKNOWN)
        assert hand.is_left is False
        assert hand.is_right is False


class TestHandBoundingBox:
    def test_bounding_box_delegates_to_landmarks(self) -> None:
        hand = make_hand()
        assert hand.bounding_box() == hand.landmarks.bounding_box()

    def test_bounding_box_center_is_midpoint(self) -> None:
        hand = make_hand()
        min_x, min_y, max_x, max_y = hand.bounding_box()
        center_x, center_y = hand.bounding_box_center()
        assert center_x == pytest.approx((min_x + max_x) / 2.0)
        assert center_y == pytest.approx((min_y + max_y) / 2.0)
