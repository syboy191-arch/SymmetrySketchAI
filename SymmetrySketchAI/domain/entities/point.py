"""The :class:`Point` value object -- the atomic unit of all drawing data.

Design rationale:
    ``Point`` is deliberately a frozen (immutable) dataclass. Points are
    *values*, not entities with identity or lifecycle: two points with
    the same coordinates, pressure, and timestamp are interchangeable.
    Immutability means a ``Point`` can be freely shared between a live
    stroke, its replay history, and an AI-corrected copy without any
    risk of one consumer mutating data another depends on -- critical
    for the non-destructive editing and replay requirements.

    Fields beyond ``x``/``y`` are included now rather than bolted on
    later:
      * ``pressure`` is required by pressure-simulated brush width.
      * ``timestamp`` is required by replay/timelapse and velocity calc.
      * ``velocity`` is precomputed by the stroke engine (not derived
        lazily here) so that brushes and AI models can consume it
        directly without recomputing finite differences repeatedly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from core.constants import MAX_PRESSURE, MIN_PRESSURE
from core.exceptions import InvalidStrokeError


@dataclass(frozen=True, slots=True)
class Point:
    """An immutable 2D point sampled during a drawing gesture.

    Attributes:
        x: Horizontal coordinate in canvas space (not screen space).
        y: Vertical coordinate in canvas space (not screen space).
        pressure: Simulated or real pressure in ``[0.0, 1.0]``, used to
            drive dynamic brush width.
        timestamp: Seconds since the stroke started (monotonic, not
            wall-clock), used for replay timing and velocity.
        velocity: Instantaneous speed in canvas units per second at this
            sample, precomputed by the stroke engine. Defaults to
            ``0.0`` for the first point of a stroke.
    """

    x: float
    y: float
    pressure: float = MAX_PRESSURE
    timestamp: float = 0.0
    velocity: float = 0.0

    def __post_init__(self) -> None:
        """Validate invariants immediately, since the object is frozen
        and can never be corrected after construction.
        """
        if not (MIN_PRESSURE <= self.pressure <= MAX_PRESSURE):
            raise InvalidStrokeError(
                f"Point pressure {self.pressure!r} out of range "
                f"[{MIN_PRESSURE}, {MAX_PRESSURE}]."
            )
        if self.timestamp < 0.0:
            raise InvalidStrokeError(
                f"Point timestamp {self.timestamp!r} cannot be negative."
            )

    def distance_to(self, other: "Point") -> float:
        """Return the Euclidean distance between this point and another."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def with_offset(self, dx: float, dy: float) -> "Point":
        """Return a new :class:`Point` translated by ``(dx, dy)``.

        Since ``Point`` is immutable, all transformations (used heavily
        by the symmetry engine to generate mirrored copies) return new
        instances rather than mutating in place.
        """
        return Point(
            x=self.x + dx,
            y=self.y + dy,
            pressure=self.pressure,
            timestamp=self.timestamp,
            velocity=self.velocity,
        )

    def as_tuple(self) -> tuple[float, float]:
        """Return the ``(x, y)`` coordinate pair, ignoring pressure/time."""
        return (self.x, self.y)
