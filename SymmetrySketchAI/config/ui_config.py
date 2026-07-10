"""UI subsystem configuration.

Design rationale:
    Window and panel layout defaults for the not-yet-built ``ui``
    package. Kept independent of ``renderer_config`` because the
    application window is a UI-shell concern, distinct from the canvas
    surface it hosts (a canvas can be resized independently of the
    window, e.g. when panels are toggled).
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH
from core.enums import ApplicationTheme
from core.exceptions import InvalidConfigurationValueError

_MIN_WINDOW_DIMENSION_PX = 640


@dataclass(frozen=True, slots=True)
class UIConfig:
    """Window, theme, and panel visibility settings.

    Attributes:
        theme: Active color theme.
        window_width: Initial application window width in pixels.
        window_height: Initial application window height in pixels.
        start_maximized: Whether the window opens maximized, ignoring
            ``window_width``/``window_height`` for the initial size.
        show_layers_panel: Whether the layers panel is visible on
            startup.
        show_brush_panel: Whether the brush settings panel is visible
            on startup.
        show_timeline_panel: Whether the timeline/history panel is
            visible on startup.
        show_camera_preview: Whether the raw camera feed preview is
            visible on startup.
        ui_scale: Multiplier applied to UI element sizing, for
            high-DPI displays or accessibility.
    """

    theme: ApplicationTheme = ApplicationTheme.DARK
    window_width: int = DEFAULT_WINDOW_WIDTH
    window_height: int = DEFAULT_WINDOW_HEIGHT
    start_maximized: bool = False
    show_layers_panel: bool = True
    show_brush_panel: bool = True
    show_timeline_panel: bool = True
    show_camera_preview: bool = True
    ui_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.window_width < _MIN_WINDOW_DIMENSION_PX:
            raise InvalidConfigurationValueError(
                f"window_width must be at least {_MIN_WINDOW_DIMENSION_PX}px."
            )
        if self.window_height < _MIN_WINDOW_DIMENSION_PX:
            raise InvalidConfigurationValueError(
                f"window_height must be at least {_MIN_WINDOW_DIMENSION_PX}px."
            )
        if self.ui_scale <= 0:
            raise InvalidConfigurationValueError("ui_scale must be positive.")
