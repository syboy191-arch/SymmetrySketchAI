"""Centralized enumerations shared across all layers of SymmetrySketch AI.

Design rationale:
    Every mode, state, or classification that would otherwise be a raw
    string literal lives here. This gives us a single source of truth for
    the application's vocabulary, enables exhaustive ``match`` handling,
    and prevents typo-class bugs (e.g. ``"radial"`` vs ``"Radial"``)
    from silently breaking symmetry or brush selection.

    These enums are intentionally dependency-free (stdlib only) so that
    *every* other module -- vision, drawing, timeline, ai, export, ui --
    can import from here without risking a circular import.
"""

from __future__ import annotations

from enum import Enum, auto, unique


@unique
class SymmetryMode(Enum):
    """Supported symmetry strategies for stroke mirroring/replication."""

    NONE = auto()
    VERTICAL = auto()
    HORIZONTAL = auto()
    DIAGONAL = auto()
    RADIAL = auto()
    ROTATIONAL = auto()
    MANDALA = auto()
    MULTI_AXIS = auto()
    CUSTOM_AXIS = auto()


@unique
class BrushType(Enum):
    """Supported brush engines. New brush types are added here and then
    registered in ``drawing.brush_factory.BrushFactory``.
    """

    PENCIL = auto()
    INK = auto()
    MARKER = auto()
    NEON = auto()
    RAINBOW = auto()
    DOTTED = auto()
    CALLIGRAPHY = auto()
    WATERCOLOR = auto()
    AIRBRUSH = auto()


@unique
class GestureType(Enum):
    """Recognized hand gestures produced by the vision layer."""

    UNKNOWN = auto()
    NONE = auto()
    POINT = auto()          # Index finger extended -> draw
    PINCH = auto()          # Thumb + index pinch -> pick color / precision
    OPEN_PALM = auto()      # Stop drawing / pause
    FIST = auto()           # Erase / clear gesture
    PEACE_SIGN = auto()     # Toggle symmetry preview
    THUMBS_UP = auto()      # Commit / confirm action
    SWIPE_LEFT = auto()     # Undo
    SWIPE_RIGHT = auto()    # Redo


@unique
class HandLabel(Enum):
    """Which physical hand a tracked hand corresponds to."""

    LEFT = auto()
    RIGHT = auto()
    UNKNOWN = auto()


@unique
class LayerBlendMode(Enum):
    """Compositing mode used when the renderer flattens layers."""

    NORMAL = auto()
    MULTIPLY = auto()
    SCREEN = auto()
    OVERLAY = auto()
    ADD = auto()


@unique
class ExportFormat(Enum):
    """Supported export targets."""

    PNG = auto()
    SVG = auto()
    JSON_PROJECT = auto()
    PDF = auto()
    TIMELAPSE_VIDEO = auto()  # Reserved for future implementation.


@unique
class AICorrectionType(Enum):
    """Categories of AI-assisted stroke correction."""

    NONE = auto()
    CIRCLE = auto()
    RECTANGLE = auto()
    POLYGON = auto()
    STRAIGHT_LINE = auto()
    SYMMETRY_ALIGNMENT = auto()
    BEAUTIFICATION = auto()
    SMART_SNAP = auto()


@unique
class ApplicationTheme(Enum):
    """UI color themes."""

    DARK = auto()
    LIGHT = auto()


@unique
class DrawingState(Enum):
    """High-level state machine for the active drawing session."""

    IDLE = auto()
    TRACKING = auto()
    DRAWING = auto()
    PREVIEWING_SYMMETRY = auto()
    REPLAYING = auto()
    PAUSED = auto()


@unique
class CommandType(Enum):
    """Categories of reversible timeline commands."""

    ADD_STROKE = auto()
    DELETE_STROKE = auto()
    EDIT_STROKE = auto()
    MOVE_STROKE = auto()
    DUPLICATE_STROKE = auto()
    ADD_LAYER = auto()
    DELETE_LAYER = auto()
    REORDER_LAYER = auto()
