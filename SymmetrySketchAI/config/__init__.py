"""Configuration package for SymmetrySketch AI.

Each module in this package owns exactly one subsystem's live,
user-adjustable configuration, expressed as a validated, immutable
dataclass. Hard limits and non-configurable defaults live in
``core.constants`` instead; these dataclasses typically reference those
constants as their default values.
"""

from __future__ import annotations

from config.app_config import AppConfig
from config.brush_config import BrushConfig
from config.export_config import ExportConfig
from config.renderer_config import RendererConfig
from config.tracker_config import TrackerConfig
from config.ui_config import UIConfig

__all__ = [
    "AppConfig",
    "BrushConfig",
    "ExportConfig",
    "RendererConfig",
    "TrackerConfig",
    "UIConfig",
]
