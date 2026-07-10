"""The :class:`Landmarks` value object -- all 21 MediaPipe hand landmarks.

Design rationale:
    MediaPipe's hand landmark model always returns exactly 21 3D points
    per hand, in a fixed, well-known order (wrist, then four points per
    finger). Rather than passing raw ``list[tuple[float, float, float]]``
    around -- which forces every consumer to memorize "index 4 is the
    thumb tip" -- this module wraps them in an immutable value object
    with named access, enum-indexed access, and the small set of
    geometric helpers (distance, per-finger lookup, bounding box) that
    downstream subsystems (gesture recognition in particular) need.

    This module has zero MediaPipe dependencies: :class:`Landmarks` is
    constructed from plain floats by ``tracker_result.py``, which is the
    only place MediaPipe types are ever touched.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import IntEnum, unique

from core.constants import HAND_LANDMARK_COUNT
from core.exceptions import VisionError


class LandmarkValidationError(VisionError):
    """Raised when a :class:`Landmarks` is constructed with invalid data."""


@unique
class HandLandmarkIndex(IntEnum):
    """Canonical index of each of the 21 MediaPipe hand landmarks.

    The ordering and naming follow the MediaPipe Hand Landmarker model
    specification exactly, so a raw index returned by the model can be
    mapped straight onto this enum.
    """

    WRIST = 0

    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8

    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12

    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


@unique
class Finger(IntEnum):
    """The five fingers, used to group landmarks by finger."""

    THUMB = 0
    INDEX = 1
    MIDDLE = 2
    RING = 3
    PINKY = 4


# Landmarks belonging to each finger, ordered from base (MCP/CMC) to tip.
_FINGER_LANDMARKS: dict[Finger, tuple[HandLandmarkIndex, ...]] = {
    Finger.THUMB: (
        HandLandmarkIndex.THUMB_CMC,
        HandLandmarkIndex.THUMB_MCP,
        HandLandmarkIndex.THUMB_IP,
        HandLandmarkIndex.THUMB_TIP,
    ),
    Finger.INDEX: (
        HandLandmarkIndex.INDEX_FINGER_MCP,
        HandLandmarkIndex.INDEX_FINGER_PIP,
        HandLandmarkIndex.INDEX_FINGER_DIP,
        HandLandmarkIndex.INDEX_FINGER_TIP,
    ),
    Finger.MIDDLE: (
        HandLandmarkIndex.MIDDLE_FINGER_MCP,
        HandLandmarkIndex.MIDDLE_FINGER_PIP,
        HandLandmarkIndex.MIDDLE_FINGER_DIP,
        HandLandmarkIndex.MIDDLE_FINGER_TIP,
    ),
    Finger.RING: (
        HandLandmarkIndex.RING_FINGER_MCP,
        HandLandmarkIndex.RING_FINGER_PIP,
        HandLandmarkIndex.RING_FINGER_DIP,
        HandLandmarkIndex.RING_FINGER_TIP,
    ),
    Finger.PINKY: (
        HandLandmarkIndex.PINKY_MCP,
        HandLandmarkIndex.PINKY_PIP,
        HandLandmarkIndex.PINKY_DIP,
        HandLandmarkIndex.PINKY_TIP,
    ),
}

_FINGER_TIPS: dict[Finger, HandLandmarkIndex] = {
    finger: landmarks[-1] for finger, landmarks in _FINGER_LANDMARKS.items()
}


@dataclass(frozen=True, slots=True)
class LandmarkPoint:
    """A single 3D hand landmark in MediaPipe's normalized image space.

    Attributes:
        x: Normalized horizontal position in ``[0.0, 1.0]``.
        y: Normalized vertical position in ``[0.0, 1.0]``.
        z: Landmark depth, roughly wrist-relative and scale-normalized.
            Smaller (more negative) is closer to the camera. This value
            is not strictly bounded by MediaPipe.
    """

    x: float
    y: float
    z: float = 0.0

    def distance_to(self, other: "LandmarkPoint") -> float:
        """Return the Euclidean distance to ``other`` in 3D."""
        return math.sqrt(
            (self.x - other.x) ** 2
            + (self.y - other.y) ** 2
            + (self.z - other.z) ** 2
        )

    def distance_to_2d(self, other: "LandmarkPoint") -> float:
        """Return the Euclidean distance to ``other`` ignoring depth."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def as_tuple(self) -> tuple[float, float, float]:
        """Return the ``(x, y, z)`` coordinate triple."""
        return (self.x, self.y, self.z)


@dataclass(frozen=True, slots=True)
class Landmarks:
    """All 21 normalized landmarks for a single detected hand.

    Attributes:
        points: Exactly 21 :class:`LandmarkPoint` instances, ordered per
            :class:`HandLandmarkIndex`.
    """

    points: tuple[LandmarkPoint, ...]

    def __post_init__(self) -> None:
        if len(self.points) != HAND_LANDMARK_COUNT:
            raise LandmarkValidationError(
                f"Landmarks requires exactly {HAND_LANDMARK_COUNT} points, "
                f"got {len(self.points)}."
            )

    @classmethod
    def from_coordinates(
        cls, coordinates: list[tuple[float, float, float]]
    ) -> "Landmarks":
        """Build a :class:`Landmarks` from a flat list of ``(x, y, z)``
        tuples, ordered per :class:`HandLandmarkIndex`.
        """
        return cls(points=tuple(LandmarkPoint(*c) for c in coordinates))

    def by_index(self, index: HandLandmarkIndex) -> LandmarkPoint:
        """Return the landmark at the given :class:`HandLandmarkIndex`."""
        return self.points[int(index)]

    def __getitem__(self, index: int) -> LandmarkPoint:
        return self.points[index]

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self):
        return iter(self.points)

    # ------------------------------------------------------------------
    # Named convenience properties
    # ------------------------------------------------------------------
    @property
    def wrist(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.WRIST)

    @property
    def thumb_tip(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.THUMB_TIP)

    @property
    def index_finger_tip(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.INDEX_FINGER_TIP)

    @property
    def middle_finger_tip(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.MIDDLE_FINGER_TIP)

    @property
    def ring_finger_tip(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.RING_FINGER_TIP)

    @property
    def pinky_tip(self) -> LandmarkPoint:
        return self.by_index(HandLandmarkIndex.PINKY_TIP)

    # ------------------------------------------------------------------
    # Finger-based lookup
    # ------------------------------------------------------------------
    def finger_landmarks(self, finger: Finger) -> tuple[LandmarkPoint, ...]:
        """Return the landmarks belonging to ``finger``, base to tip."""
        return tuple(self.by_index(i) for i in _FINGER_LANDMARKS[finger])

    def finger_tip(self, finger: Finger) -> LandmarkPoint:
        """Return the tip landmark of ``finger``."""
        return self.by_index(_FINGER_TIPS[finger])

    # ------------------------------------------------------------------
    # Geometric helpers
    # ------------------------------------------------------------------
    def distance_between(
        self, a: HandLandmarkIndex, b: HandLandmarkIndex
    ) -> float:
        """Return the 3D distance between two named landmarks."""
        return self.by_index(a).distance_to(self.by_index(b))

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return ``(min_x, min_y, max_x, max_y)`` over all landmarks, in
        the same normalized coordinate space as the landmarks themselves.
        """
        xs = [p.x for p in self.points]
        ys = [p.y for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def centroid(self) -> LandmarkPoint:
        """Return the centroid (average position) of all 21 landmarks."""
        n = len(self.points)
        return LandmarkPoint(
            x=sum(p.x for p in self.points) / n,
            y=sum(p.y for p in self.points) / n,
            z=sum(p.z for p in self.points) / n,
        )
