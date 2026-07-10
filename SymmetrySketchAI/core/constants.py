"""Centralized constants for SymmetrySketch AI.

Design rationale:
    Per the project's engineering standards, magic numbers must not be
    scattered through the codebase. Every tunable numeric or string
    default that isn't user-configurable at runtime (those belong in
    ``config/``) lives here instead. Grouping by concern (vision,
    drawing, timeline, ui) keeps this file navigable as it grows.

    Values here are *defaults and hard limits*, not live configuration.
    Live, user-adjustable configuration belongs in the ``config/``
    package's dataclasses, which may reference these constants as their
    default values.
"""

from __future__ import annotations

from typing import Final

# --------------------------------------------------------------------------
# Application metadata
# --------------------------------------------------------------------------
APP_NAME: Final[str] = "SymmetrySketch AI"
ORGANIZATION_NAME: Final[str] = "SymmetrySketch"

# --------------------------------------------------------------------------
# Vision / hand tracking
# --------------------------------------------------------------------------
MAX_TRACKED_HANDS: Final[int] = 2
MIN_HAND_DETECTION_CONFIDENCE: Final[float] = 0.5
MIN_HAND_PRESENCE_CONFIDENCE: Final[float] = 0.5
MIN_TRACKING_CONFIDENCE: Final[float] = 0.5
HAND_LANDMARK_COUNT: Final[int] = 21
SMOOTHING_WINDOW_SIZE: Final[int] = 5
GESTURE_HOLD_FRAMES_TO_CONFIRM: Final[int] = 3
CAMERA_DEFAULT_WIDTH: Final[int] = 1280
CAMERA_DEFAULT_HEIGHT: Final[int] = 720
CAMERA_DEFAULT_FPS: Final[int] = 30

# --------------------------------------------------------------------------
# Drawing / stroke geometry
# --------------------------------------------------------------------------
DEFAULT_BRUSH_WIDTH_PX: Final[float] = 6.0
MIN_BRUSH_WIDTH_PX: Final[float] = 0.5
MAX_BRUSH_WIDTH_PX: Final[float] = 200.0
DEFAULT_PRESSURE: Final[float] = 1.0
MIN_PRESSURE: Final[float] = 0.0
MAX_PRESSURE: Final[float] = 1.0
MIN_DISTANCE_BETWEEN_POINTS_PX: Final[float] = 1.5
SPLINE_INTERPOLATION_SAMPLES: Final[int] = 16
INFINITE_CANVAS_CHUNK_SIZE_PX: Final[int] = 2048

# --------------------------------------------------------------------------
# Symmetry
# --------------------------------------------------------------------------
DEFAULT_ROTATIONAL_SEGMENTS: Final[int] = 6
MIN_ROTATIONAL_SEGMENTS: Final[int] = 2
MAX_ROTATIONAL_SEGMENTS: Final[int] = 64
DEFAULT_MANDALA_SEGMENTS: Final[int] = 12

# --------------------------------------------------------------------------
# Timeline / history
# --------------------------------------------------------------------------
UNLIMITED_HISTORY: Final[int] = -1
DEFAULT_REPLAY_FPS: Final[int] = 60

# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------
DEFAULT_PNG_DPI: Final[int] = 300
PROJECT_FILE_EXTENSION: Final[str] = ".ssaproj"
PROJECT_SCHEMA_VERSION: Final[str] = "1.0.0"

# --------------------------------------------------------------------------
# UI
# --------------------------------------------------------------------------
DEFAULT_WINDOW_WIDTH: Final[int] = 1600
DEFAULT_WINDOW_HEIGHT: Final[int] = 950
