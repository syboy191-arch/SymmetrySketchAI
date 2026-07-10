"""Export subsystem configuration.

Design rationale:
    Centralizes defaults for the not-yet-built ``export`` package's
    exporters (PNG, SVG, PDF, project JSON). Kept separate from
    ``persistence`` concerns: this config governs *rendering output
    for the user*, not the internal ``.ssaproj`` save format.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import DEFAULT_PNG_DPI
from core.enums import ExportFormat
from core.exceptions import InvalidConfigurationValueError


@dataclass(frozen=True, slots=True)
class ExportConfig:
    """Default settings for exporting canvases to external formats.

    Attributes:
        default_format: Export format pre-selected in the export dialog.
        png_dpi: Dots-per-inch used when rasterizing PNG exports.
        svg_precision: Number of decimal places retained for SVG path
            coordinates.
        include_metadata: Whether exporters embed project metadata
            (title, author, symmetry settings) into the output file
            where the format supports it.
        transparent_background: Whether PNG/SVG exports omit the canvas
            background color, producing an alpha-transparent output.
    """

    default_format: ExportFormat = ExportFormat.PNG
    png_dpi: int = DEFAULT_PNG_DPI
    svg_precision: int = 3
    include_metadata: bool = True
    transparent_background: bool = False

    def __post_init__(self) -> None:
        if self.png_dpi <= 0:
            raise InvalidConfigurationValueError("png_dpi must be positive.")
        if not 0 <= self.svg_precision <= 10:
            raise InvalidConfigurationValueError(
                "svg_precision must be between 0 and 10 decimal places."
            )
