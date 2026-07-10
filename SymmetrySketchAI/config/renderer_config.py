"""Rendering/canvas subsystem configuration.

Design rationale:
    The not-yet-built ``drawing`` package's renderer needs to know
    target frame rate, canvas dimensions, and background color. These
    are separated from ``brush_config`` because they describe the
    *surface* being drawn on, not the *tool* doing the drawing.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import DEFAULT_REPLAY_FPS, INFINITE_CANVAS_CHUNK_SIZE_PX
from core.exceptions import InvalidConfigurationValueError

_RGBA_CHANNEL_MIN = 0
_RGBA_CHANNEL_MAX = 255


def _validate_rgba(name: str, color: tuple[int, int, int, int]) -> None:
    if len(color) != 4:
        raise InvalidConfigurationValueError(
            f"{name} must be an (r, g, b, a) 4-tuple, got {color!r}."
        )
    for channel in color:
        if not _RGBA_CHANNEL_MIN <= channel <= _RGBA_CHANNEL_MAX:
            raise InvalidConfigurationValueError(
                f"{name} channel values must be in "
                f"[{_RGBA_CHANNEL_MIN}, {_RGBA_CHANNEL_MAX}], got {color!r}."
            )


@dataclass(frozen=True, slots=True)
class RendererConfig:
    """Canvas and rendering surface settings.

    Attributes:
        target_fps: Target frame rate for the live drawing/preview loop.
        canvas_width: Initial visible canvas width in pixels.
        canvas_height: Initial visible canvas height in pixels.
        background_color: Canvas background as an (r, g, b, a) tuple,
            each channel in ``[0, 255]``.
        infinite_canvas_enabled: Whether the canvas extends beyond the
            initial viewport using chunked scrolling.
        canvas_chunk_size_px: Side length of one infinite-canvas chunk,
            used only when ``infinite_canvas_enabled`` is ``True``.
        antialiasing_enabled: Whether stroke rendering is antialiased.
        symmetry_guide_opacity: Opacity (0.0-1.0) of the symmetry axis
            guide overlay.
    """

    target_fps: int = DEFAULT_REPLAY_FPS
    canvas_width: int = 1920
    canvas_height: int = 1080
    background_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    infinite_canvas_enabled: bool = False
    canvas_chunk_size_px: int = INFINITE_CANVAS_CHUNK_SIZE_PX
    antialiasing_enabled: bool = True
    symmetry_guide_opacity: float = 0.35

    def __post_init__(self) -> None:
        if self.target_fps <= 0:
            raise InvalidConfigurationValueError("target_fps must be positive.")
        if self.canvas_width <= 0 or self.canvas_height <= 0:
            raise InvalidConfigurationValueError(
                "canvas_width and canvas_height must be positive."
            )
        _validate_rgba("background_color", self.background_color)
        if self.canvas_chunk_size_px <= 0:
            raise InvalidConfigurationValueError(
                "canvas_chunk_size_px must be positive."
            )
        if not 0.0 <= self.symmetry_guide_opacity <= 1.0:
            raise InvalidConfigurationValueError(
                "symmetry_guide_opacity must be between 0.0 and 1.0."
            )
