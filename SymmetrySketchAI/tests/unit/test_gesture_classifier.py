"""Unit tests for vision.gesture_classifier.GestureClassifier."""
from __future__ import annotations

import pytest

from core.enums import GestureType, HandLabel
from core.exceptions import GestureRecognitionError
from vision.gesture_classifier import GestureClassification, GestureClassifier
from vision.hand import Hand
from vision.landmarks import HandLandmarkIndex, Landmarks

# A neutral "open palm" template (right hand): all fingers extended (tips
# above pips), thumb abducted to the left of its MCP. Indices follow
# HandLandmarkIndex. Image y grows downward, so "up" means smaller y.
_BASE: dict[int, tuple[float, float, float]] = {
    0: (0.50, 0.90, 0.0),   # WRIST
    1: (0.42, 0.84, 0.0),   # THUMB_CMC
    2: (0.38, 0.80, 0.0),   # THUMB_MCP
    3: (0.34, 0.76, 0.0),   # THUMB_IP
    4: (0.30, 0.72, 0.0),   # THUMB_TIP (extended, left of MCP)
    5: (0.46, 0.66, 0.0),   # INDEX_MCP
    6: (0.46, 0.56, 0.0),   # INDEX_PIP
    7: (0.46, 0.49, 0.0),   # INDEX_DIP
    8: (0.46, 0.42, 0.0),   # INDEX_TIP (extended)
    9: (0.51, 0.65, 0.0),   # MIDDLE_MCP
    10: (0.51, 0.55, 0.0),  # MIDDLE_PIP
    11: (0.51, 0.48, 0.0),  # MIDDLE_DIP
    12: (0.51, 0.41, 0.0),  # MIDDLE_TIP (extended)
    13: (0.56, 0.66, 0.0),  # RING_MCP
    14: (0.56, 0.57, 0.0),  # RING_PIP
    15: (0.56, 0.50, 0.0),  # RING_DIP
    16: (0.56, 0.43, 0.0),  # RING_TIP (extended)
    17: (0.61, 0.68, 0.0),  # PINKY_MCP
    18: (0.61, 0.60, 0.0),  # PINKY_PIP
    19: (0.61, 0.55, 0.0),  # PINKY_DIP
    20: (0.61, 0.50, 0.0),  # PINKY_TIP (extended)
}

# Tip/pip index pairs for the four fingers.
_FINGER_TIPS = {
    "index": (HandLandmarkIndex.INDEX_FINGER_TIP, HandLandmarkIndex.INDEX_FINGER_PIP),
    "middle": (HandLandmarkIndex.MIDDLE_FINGER_TIP, HandLandmarkIndex.MIDDLE_FINGER_PIP),
    "ring": (HandLandmarkIndex.RING_FINGER_TIP, HandLandmarkIndex.RING_FINGER_PIP),
    "pinky": (HandLandmarkIndex.PINKY_TIP, HandLandmarkIndex.PINKY_PIP),
}


def make_hand(
    folded: tuple[str, ...] = (),
    thumb_folded: bool = False,
    pinch: bool = False,
    label: HandLabel = HandLabel.RIGHT,
) -> Hand:
    """Build a Hand from the open-palm template with fingers folded.

    Folding a finger places its tip 0.10 below its PIP (curled). The
    thumb, when folded, is moved into the palm (right of its MCP).
    """
    pts = dict(_BASE)
    for finger in folded:
        tip_index, pip_index = _FINGER_TIPS[finger]
        pip = pts[int(pip_index)]
        tip = pts[int(tip_index)]
        pts[int(tip_index)] = (tip[0], pip[1] + 0.10, tip[2])
    if thumb_folded:
        pts[4] = (0.50, 0.74, 0.0)  # right of MCP (0.38) -> not extended
    if pinch:
        pts[4] = pts[8]  # thumb tip coincides with index tip
    coords = [pts[i] for i in range(21)]
    return Hand(
        label=label,
        handedness_confidence=0.99,
        landmarks=Landmarks.from_coordinates(coords),
    )


class TestStaticGestures:
    def test_open_palm(self):
        result = GestureClassifier().classify(make_hand())
        assert result.gesture_type is GestureType.OPEN_PALM

    def test_point(self):
        hand = make_hand(folded=("middle", "ring", "pinky"), thumb_folded=True)
        result = GestureClassifier().classify(hand)
        assert result.gesture_type is GestureType.POINT

    def test_peace_sign(self):
        hand = make_hand(folded=("ring", "pinky"), thumb_folded=True)
        result = GestureClassifier().classify(hand)
        assert result.gesture_type is GestureType.PEACE_SIGN

    def test_fist(self):
        hand = make_hand(
            folded=("index", "middle", "ring", "pinky"), thumb_folded=True
        )
        result = GestureClassifier().classify(hand)
        assert result.gesture_type is GestureType.FIST

    def test_thumbs_up(self):
        hand = make_hand(folded=("index", "middle", "ring", "pinky"))
        result = GestureClassifier().classify(hand)
        assert result.gesture_type is GestureType.THUMBS_UP

    def test_pinch_takes_priority(self):
        result = GestureClassifier().classify(make_hand(pinch=True))
        assert result.gesture_type is GestureType.PINCH


class TestConfidence:
    def test_confidence_in_range(self):
        result = GestureClassifier().classify(make_hand())
        assert 0.0 <= result.confidence <= 1.0

    def test_clear_pose_has_positive_confidence(self):
        result = GestureClassifier().classify(make_hand())
        assert result.confidence > 0.0

    def test_pinch_confidence_higher_when_closer(self):
        classifier = GestureClassifier()
        touching = classifier.classify(make_hand(pinch=True))
        assert touching.gesture_type is GestureType.PINCH
        assert touching.confidence > 0.5


class TestHandedness:
    def test_left_hand_thumb_direction(self):
        # Mirror the template thumb to the right side for a left hand.
        pts = dict(_BASE)
        pts[2] = (0.62, 0.80, 0.0)  # THUMB_MCP
        pts[4] = (0.70, 0.72, 0.0)  # THUMB_TIP (right of MCP -> extended L)
        for finger in ("index", "middle", "ring", "pinky"):
            tip_index, pip_index = _FINGER_TIPS[finger]
            pip = pts[int(pip_index)]
            tip = pts[int(tip_index)]
            pts[int(tip_index)] = (tip[0], pip[1] + 0.10, tip[2])
        hand = Hand(
            label=HandLabel.LEFT,
            handedness_confidence=0.99,
            landmarks=Landmarks.from_coordinates([pts[i] for i in range(21)]),
        )
        result = GestureClassifier().classify(hand)
        assert result.gesture_type is GestureType.THUMBS_UP


class TestResultType:
    def test_returns_gesture_classification(self):
        result = GestureClassifier().classify(make_hand())
        assert isinstance(result, GestureClassification)