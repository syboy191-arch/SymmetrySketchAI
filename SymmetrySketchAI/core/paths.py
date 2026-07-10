"""Centralized filesystem path resolution.

Design rationale:
    Per the project's constraints, no module should hardcode model paths
    or other filesystem locations, and every path must be a
    :class:`pathlib.Path`. This module is the single place that knows
    the on-disk layout of the repository/installed application. Other
    modules (e.g. ``config/ai_config.py``) import these base paths and
    join onto them rather than constructing paths themselves.

    All paths are computed relative to this file's location, so the
    application can be relocated or installed anywhere without code
    changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

# The repository/application root -- two levels up from this file
# (SymmetrySketchAI/core/paths.py -> SymmetrySketchAI/).
PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

ASSETS_DIR: Final[Path] = PROJECT_ROOT / "assets"
ICONS_DIR: Final[Path] = ASSETS_DIR / "icons"
CURSORS_DIR: Final[Path] = ASSETS_DIR / "cursors"
FONTS_DIR: Final[Path] = ASSETS_DIR / "fonts"
THEMES_DIR: Final[Path] = ASSETS_DIR / "themes"
SHADERS_DIR: Final[Path] = ASSETS_DIR / "shaders"

MODELS_DIR: Final[Path] = PROJECT_ROOT / "models"
HAND_LANDMARKER_MODEL_PATH: Final[Path] = MODELS_DIR / "hand_landmarker.task"
SHAPE_DETECTOR_MODEL_PATH: Final[Path] = MODELS_DIR / "shape_detector.onnx"
SYMMETRY_MODEL_PATH: Final[Path] = MODELS_DIR / "symmetry_model.onnx"

CONFIG_DIR: Final[Path] = PROJECT_ROOT / "config"
DOCS_DIR: Final[Path] = PROJECT_ROOT / "docs"
PLUGINS_DIR: Final[Path] = PROJECT_ROOT / "plugins"

# User-writable locations (logs, autosaves, user projects). Kept outside
# the read-only application tree.
USER_DATA_DIR: Final[Path] = Path.home() / ".symmetrysketch_ai"
LOGS_DIR: Final[Path] = USER_DATA_DIR / "logs"
AUTOSAVE_DIR: Final[Path] = USER_DATA_DIR / "autosave"
USER_PROJECTS_DIR: Final[Path] = USER_DATA_DIR / "projects"
USER_PLUGINS_DIR: Final[Path] = USER_DATA_DIR / "plugins"


def ensure_user_directories_exist() -> None:
    """Create all user-writable directories if they do not already exist.

    This is idempotent and safe to call on every application startup.
    It intentionally does *not* touch the read-only application tree
    (``assets/``, ``models/``, etc.), which is expected to already exist
    as part of the installed application.
    """
    for directory in (
        USER_DATA_DIR,
        LOGS_DIR,
        AUTOSAVE_DIR,
        USER_PROJECTS_DIR,
        USER_PLUGINS_DIR,
    ):
        directory.mkdir(parents=True, exist_ok=True)
