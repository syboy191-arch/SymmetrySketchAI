"""The :class:`Hand` value object -- one detected hand for one frame.

Design rationale:
    ``Hand`` composes a :class:`~vision.landmarks.Landmarks` with the
    per-hand metadata MediaPipe reports alongside it (handedness label,
    confidence). It reuses ``core.enums.HandLabel`` rather than defining
    its own left/right enum, per the project rule against duplicated
    enums. Like every other vision object, it contains no MediaPipe
    types -- ``tracker_result.py`` is solely responsible for that
    conversion boundary.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.enums import HandLabel
from core.exceptions import VisionError
from vision.landmarks import Landmarks


class HandValidationError(VisionError):
    """Raised when a :class:`Hand` is constructed with invalid data."""


@dataclass(frozen=True, slots=True)
class Hand:
    """A single tracked hand detected in one frame.

    Attributes:
        label: Which physical hand this is (left/right/unknown).
        handedness_confidence: Model confidence in ``label``, in
            ``[0.0, 1.0]``.
        landmarks: All 21 normalized hand landmarks.
    """

    label: HandLabel
    handedness_confidence: float
    landmarks: Landmarks

    def __post_init__(self) -> None:
        if not 0.0 <= self.handedness_confidence <= 1.0:
            raise HandValidationError(
                "handedness_confidence must be between 0.0 and 1.0, got "
                f"{self.handedness_confidence!r}."
            )

    @property
    def is_left(self) -> bool:
        """Return whether this hand is classified as the left hand."""
        return self.label is HandLabel.LEFT

    @property
    def is_right(self) -> bool:
        """Return whether this hand is classified as the right hand."""
        return self.label is HandLabel.RIGHT

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return ``(min_x, min_y, max_x, max_y)`` of this hand's
        landmarks, in normalized ``[0.0, 1.0]`` coordinate space.
        """
        return self.landmarks.bounding_box()

    def bounding_box_center(self) -> tuple[float, float]:
        """Return the ``(x, y)`` center of this hand's bounding box."""
        min_x, min_y, max_x, max_y = self.bounding_box()
        return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)
