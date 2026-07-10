"""Static hand-pose gesture classification.

Design rationale:
    :class:`GestureClassifier` maps a single frame's :class:`~vision.hand.Hand`
    onto a :class:`core.enums.GestureType`. It is deliberately *pure and
    stateless*: given the same landmarks it always returns the same
    classification, with no frame history, no smoothing, and no camera
    access. All temporal concerns (debouncing, motion-based swipes,
    velocity) live in :class:`vision.gesture_engine.GestureEngine`, which
    owns this classifier.

    Because it is stateless and dependency-free (no OpenCV/MediaPipe),
    it is exhaustively unit-testable by handing it synthetic landmark
    sets, and it can be swapped for an ML-based classifier later without
    touching the engine (dependency inversion).

    Recognized static poses: POINT, PINCH, OPEN_PALM, FIST, PEACE_SIGN,
    THUMBS_UP. Anything else is UNKNOWN. SWIPE_LEFT / SWIPE_RIGHT are
    motion gestures and are intentionally NOT handled here -- they
    require frame-to-frame history and are detected by the engine.

This module reuses the project's single sources of truth:
    - Gesture vocabulary: :class:`core.enums.GestureType`.
    - Handedness: :class:`core.enums.HandLabel` (via the passed ``Hand``).
    - Landmark access: :class:`vision.landmarks.Landmarks` named helpers.
    - Errors: :class:`core.exceptions.GestureRecognitionError`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from core.enums import GestureType, HandLabel
from core.exceptions import GestureRecognitionError
from vision.hand import Hand
from vision.landmarks import HandLandmarkIndex, Landmarks

# ---------------------------------------------------------------------------
# Tuning constants (no magic numbers). All in normalized [0, 1] image space.
# ---------------------------------------------------------------------------

PINCH_DISTANCE_THRESHOLD: Final[float] = 0.06
"""Max 2D thumb-tip/index-tip distance to be considered a pinch."""

FINGER_EXTENSION_DEADZONE: Final[float] = 0.02
"""Minimum normalized extension score before a digit counts as extended."""

CONFIDENCE_GAIN: Final[float] = 2.5
"""Scales the mean digit-decision margin into a [0, 1] confidence."""

# Canonical (thumb, index, middle, ring, pinky) extension patterns.
_PATTERNS: Final[dict[tuple[bool, bool, bool, bool, bool], GestureType]] = {
    (False, False, False, False, False): GestureType.FIST,
    (False, True, False, False, False): GestureType.POINT,
    (False, True, True, False, False): GestureType.PEACE_SIGN,
    (True, True, True, True, True): GestureType.OPEN_PALM,
    (True, False, False, False, False): GestureType.THUMBS_UP,
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


@dataclass(frozen=True, slots=True)
class GestureClassification:
    """The result of classifying a single frame's hand pose.

    Attributes:
        gesture_type: The recognized static gesture (or UNKNOWN).
        confidence: Classifier confidence in ``[0.0, 1.0]``.
    """

    gesture_type: GestureType
    confidence: float


class GestureClassifier:
    """Classifies a single :class:`Hand` into a :class:`GestureType`.

    Thresholds are injectable so the engine (or tests) can tune
    sensitivity without editing this class.
    """

    __slots__ = ("_pinch_threshold", "_deadzone", "_confidence_gain")

    def __init__(
        self,
        pinch_threshold: float = PINCH_DISTANCE_THRESHOLD,
        extension_deadzone: float = FINGER_EXTENSION_DEADZONE,
        confidence_gain: float = CONFIDENCE_GAIN,
    ) -> None:
        self._pinch_threshold = pinch_threshold
        self._deadzone = extension_deadzone
        self._confidence_gain = confidence_gain

    def classify(self, hand: Hand) -> GestureClassification:
        """Classify ``hand`` into a static gesture.

        Raises:
            GestureRecognitionError: If classification fails on otherwise
                valid landmark data.
        """
        try:
            landmarks = hand.landmarks

            # Pinch takes priority: thumb and index tips nearly touching,
            # regardless of the other fingers' state.
            pinch_distance = landmarks.thumb_tip.distance_to_2d(
                landmarks.index_finger_tip
            )
            if pinch_distance < self._pinch_threshold:
                confidence = _clamp01(
                    (self._pinch_threshold - pinch_distance)
                    / self._pinch_threshold
                )
                return GestureClassification(GestureType.PINCH, confidence)

            states, margins = self._digit_states(landmarks, hand.label)
            gesture = _PATTERNS.get(states)
            if gesture is None:
                return GestureClassification(GestureType.UNKNOWN, 0.0)

            confidence = _clamp01(
                (sum(margins) / len(margins)) * self._confidence_gain
            )
            return GestureClassification(gesture, confidence)
        except GestureRecognitionError:
            raise
        except Exception as error:  # noqa: BLE001 - re-raised as domain error
            raise GestureRecognitionError(
                f"Failed to classify gesture: {error}"
            ) from error

    # ------------------------------------------------------------------
    # Internal: per-digit extension detection
    # ------------------------------------------------------------------
    def _digit_states(
        self, landmarks: Landmarks, label: HandLabel
    ) -> tuple[tuple[bool, bool, bool, bool, bool], tuple[float, ...]]:
        """Return ``((thumb, index, middle, ring, pinky), margins)``.

        A finger is "extended" when its tip is above (smaller image ``y``
        than) its PIP joint. The thumb is handled separately along ``x``
        because it abducts sideways rather than curling vertically; its
        direction depends on which hand it is.
        """
        min_x, min_y, max_x, max_y = landmarks.bounding_box()
        hand_height = max(max_y - min_y, 1e-6)
        hand_width = max(max_x - min_x, 1e-6)

        # Four fingers: (tip index, pip index).
        finger_joints = (
            (HandLandmarkIndex.INDEX_FINGER_TIP, HandLandmarkIndex.INDEX_FINGER_PIP),
            (HandLandmarkIndex.MIDDLE_FINGER_TIP, HandLandmarkIndex.MIDDLE_FINGER_PIP),
            (HandLandmarkIndex.RING_FINGER_TIP, HandLandmarkIndex.RING_FINGER_PIP),
            (HandLandmarkIndex.PINKY_TIP, HandLandmarkIndex.PINKY_PIP),
        )

        finger_states: list[bool] = []
        margins: list[float] = []
        for tip_index, pip_index in finger_joints:
            tip = landmarks.by_index(tip_index)
            pip = landmarks.by_index(pip_index)
            score = (pip.y - tip.y) / hand_height  # + when tip above pip
            finger_states.append(score > self._deadzone)
            margins.append(abs(score))

        thumb_extended, thumb_margin = self._thumb_state(
            landmarks, label, hand_width
        )

        states = (
            thumb_extended,
            finger_states[0],
            finger_states[1],
            finger_states[2],
            finger_states[3],
        )
        all_margins = (thumb_margin, *margins)
        return states, all_margins

    def _thumb_state(
        self, landmarks: Landmarks, label: HandLabel, hand_width: float
    ) -> tuple[bool, float]:
        """Return ``(extended, margin)`` for the thumb.

        The thumb points away from the palm horizontally. For a right
        hand the extended thumb sits to the left of its MCP (smaller
        ``x``); for a left hand, to the right. When handedness is
        unknown we fall back to the absolute horizontal separation.
        """
        tip = landmarks.by_index(HandLandmarkIndex.THUMB_TIP)
        mcp = landmarks.by_index(HandLandmarkIndex.THUMB_MCP)

        if label is HandLabel.RIGHT:
            score = (mcp.x - tip.x) / hand_width
        elif label is HandLabel.LEFT:
            score = (tip.x - mcp.x) / hand_width
        else:
            score = abs(tip.x - mcp.x) / hand_width - self._deadzone
        return score > self._deadzone, abs(score)