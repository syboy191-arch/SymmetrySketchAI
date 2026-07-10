"""Brush/stroke-tool subsystem configuration.

Design rationale:
    Default brush parameters used to initialize a new stroke before the
    user has customized brush settings for a session. The not-yet-built
    ``drawing`` package's brush factory will read this to construct the
    default :class:`domain.entities.brush.Brush` on startup.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import (
    DEFAULT_BRUSH_WIDTH_PX,
    DEFAULT_MANDALA_SEGMENTS,
    DEFAULT_PRESSURE,
    DEFAULT_ROTATIONAL_SEGMENTS,
    MAX_BRUSH_WIDTH_PX,
    MAX_PRESSURE,
    MAX_ROTATIONAL_SEGMENTS,
    MIN_BRUSH_WIDTH_PX,
    MIN_DISTANCE_BETWEEN_POINTS_PX,
    MIN_PRESSURE,
    MIN_ROTATIONAL_SEGMENTS,
    SPLINE_INTERPOLATION_SAMPLES,
)
from core.enums import BrushType, SymmetryMode
from core.exceptions import InvalidConfigurationValueError


@dataclass(frozen=True, slots=True)
class BrushConfig:
    """Default brush and symmetry settings applied to new strokes.

    Attributes:
        default_brush_type: Brush engine selected when a session starts.
        default_width_px: Default brush stroke width in pixels.
        default_pressure: Default simulated pressure for input devices
            (e.g. hand tracking) that don't report real pressure.
        min_distance_between_points_px: Minimum spacing enforced between
            consecutive recorded stroke points, to avoid oversampling.
        spline_interpolation_samples: Number of interpolated samples
            generated per spline segment when smoothing a stroke.
        default_symmetry_mode: Symmetry mode active when a session
            starts.
        default_rotational_segments: Segment count used for
            ``SymmetryMode.ROTATIONAL``.
        default_mandala_segments: Segment count used for
            ``SymmetryMode.MANDALA``.
    """

    default_brush_type: BrushType = BrushType.PENCIL
    default_width_px: float = DEFAULT_BRUSH_WIDTH_PX
    default_pressure: float = DEFAULT_PRESSURE
    min_distance_between_points_px: float = MIN_DISTANCE_BETWEEN_POINTS_PX
    spline_interpolation_samples: int = SPLINE_INTERPOLATION_SAMPLES
    default_symmetry_mode: SymmetryMode = SymmetryMode.NONE
    default_rotational_segments: int = DEFAULT_ROTATIONAL_SEGMENTS
    default_mandala_segments: int = DEFAULT_MANDALA_SEGMENTS

    def __post_init__(self) -> None:
        if not MIN_BRUSH_WIDTH_PX <= self.default_width_px <= MAX_BRUSH_WIDTH_PX:
            raise InvalidConfigurationValueError(
                f"default_width_px must be between {MIN_BRUSH_WIDTH_PX} and "
                f"{MAX_BRUSH_WIDTH_PX}, got {self.default_width_px!r}."
            )
        if not MIN_PRESSURE <= self.default_pressure <= MAX_PRESSURE:
            raise InvalidConfigurationValueError(
                f"default_pressure must be between {MIN_PRESSURE} and "
                f"{MAX_PRESSURE}, got {self.default_pressure!r}."
            )
        if self.min_distance_between_points_px <= 0:
            raise InvalidConfigurationValueError(
                "min_distance_between_points_px must be positive."
            )
        if self.spline_interpolation_samples < 1:
            raise InvalidConfigurationValueError(
                "spline_interpolation_samples must be at least 1."
            )
        if not (
            MIN_ROTATIONAL_SEGMENTS
            <= self.default_rotational_segments
            <= MAX_ROTATIONAL_SEGMENTS
        ):
            raise InvalidConfigurationValueError(
                "default_rotational_segments must be between "
                f"{MIN_ROTATIONAL_SEGMENTS} and {MAX_ROTATIONAL_SEGMENTS}."
            )
        if not (
            MIN_ROTATIONAL_SEGMENTS
            <= self.default_mandala_segments
            <= MAX_ROTATIONAL_SEGMENTS
        ):
            raise InvalidConfigurationValueError(
                "default_mandala_segments must be between "
                f"{MIN_ROTATIONAL_SEGMENTS} and {MAX_ROTATIONAL_SEGMENTS}."
            )
