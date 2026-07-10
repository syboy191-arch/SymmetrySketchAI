"""Domain entity representing the live state of the drawing editor.

A CanvasState is pure configuration/state data describing *how the canvas
is currently being viewed and interacted with*: viewport (size/zoom/pan),
the active layer and brush, the active symmetry mode, the active tool,
grid/snap settings, the current selection, and the high-level drawing
state machine position. It performs NO rendering, has NO knowledge of the
UI widget tree, and has NO dependency on OpenCV/MediaPipe/Qt/etc.

This module intentionally reuses the project's existing single sources of
truth rather than redefining them:

- Symmetry mode comes from :class:`core.enums.SymmetryMode`.
- The high-level drawing state machine comes from
  :class:`core.enums.DrawingState`, not a locally-defined equivalent.
- The active brush is a real :class:`domain.entities.brush.Brush`, not a
  duplicated brush-configuration shape.
- The active layer is referenced by :class:`domain.entities.ids.LayerId`,
  matching the ``NewType``-based identifier scheme used everywhere else.
- All CanvasState-specific errors derive from
  :class:`core.exceptions.DrawingError` (the project's domain/drawing
  error root), never from bare ``Exception``.

Naming note -- ``ToolMode``:
    No project-wide "which tool is active" enum exists yet in
    ``core.enums``. Rather than invent one there (out of scope for this
    change), ``ToolMode`` is defined locally here, the same way
    ``domain.entities.brush.BrushStyle`` is a locally-scoped enum. If a
    future module needs the same vocabulary, it should be promoted to
    ``core.enums`` at that point rather than redefined.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, unique

from core.enums import DrawingState, SymmetryMode
from core.exceptions import DrawingError
from domain.entities.brush import Brush
from domain.entities.ids import LayerId, StrokeId

# --------------------------------------------------------------------------
# Constants (no magic numbers)
# --------------------------------------------------------------------------

MIN_ZOOM: float = 0.05
MAX_ZOOM: float = 64.0
DEFAULT_ZOOM: float = 1.0

MIN_CANVAS_DIMENSION_PX: float = 1.0
MAX_CANVAS_DIMENSION_PX: float = 32768.0
DEFAULT_CANVAS_WIDTH_PX: float = 1920.0
DEFAULT_CANVAS_HEIGHT_PX: float = 1080.0

MIN_GRID_SIZE_PX: float = 1.0
MAX_GRID_SIZE_PX: float = 4096.0
DEFAULT_GRID_SIZE_PX: float = 32.0

MIN_SNAP_THRESHOLD_PX: float = 0.0
MAX_SNAP_THRESHOLD_PX: float = 200.0
DEFAULT_SNAP_THRESHOLD_PX: float = 8.0


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class CanvasStateValidationError(DrawingError):
    """Raised when constructing or mutating a CanvasState with invalid data."""


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

@unique
class ToolMode(Enum):
    """Which interaction tool is currently active on the canvas."""

    BRUSH = "brush"
    ERASER = "eraser"
    SELECTION = "selection"
    SHAPE = "shape"
    FILL = "fill"
    PAN = "pan"
    ZOOM = "zoom"


# --------------------------------------------------------------------------
# Entity: CanvasState
# --------------------------------------------------------------------------

def _validate_range(value: float, low: float, high: float, field_name: str) -> None:
    if not (low <= value <= high):
        raise CanvasStateValidationError(
            f"{field_name} must be between {low} and {high}, got {value}."
        )


@dataclass(slots=True)
class CanvasState:
    """The complete, current state of the drawing editor's viewport and tools.

    Attributes:
        canvas_width: Canvas width in canvas-space pixels.
        canvas_height: Canvas height in canvas-space pixels.
        zoom: Current viewport zoom factor (``1.0`` == 100%).
        pan_x: Horizontal viewport pan offset in canvas-space pixels.
        pan_y: Vertical viewport pan offset in canvas-space pixels.
        current_layer_id: The layer new strokes are drawn onto, or
            ``None`` if no layer is active yet (e.g. an empty project).
        current_brush: The brush configuration used for new strokes.
        symmetry_mode: The symmetry mode currently applied to new strokes.
        tool_mode: Which interaction tool is currently selected.
        grid_enabled: Whether the reference grid is visible.
        grid_size: Spacing between grid lines, in canvas-space pixels.
        snap_enabled: Whether new points snap to the grid.
        snap_threshold: Maximum distance, in canvas-space pixels, at
            which a point will snap to the grid.
        selected_stroke_ids: The strokes currently selected, if any.
        drawing_state: The high-level drawing session state machine
            position (idle, tracking, drawing, replaying, ...).
    """

    canvas_width: float = DEFAULT_CANVAS_WIDTH_PX
    canvas_height: float = DEFAULT_CANVAS_HEIGHT_PX
    zoom: float = DEFAULT_ZOOM
    pan_x: float = 0.0
    pan_y: float = 0.0
    current_layer_id: LayerId | None = None
    current_brush: Brush = field(default_factory=Brush)
    symmetry_mode: SymmetryMode = SymmetryMode.NONE
    tool_mode: ToolMode = ToolMode.BRUSH
    grid_enabled: bool = False
    grid_size: float = DEFAULT_GRID_SIZE_PX
    snap_enabled: bool = False
    snap_threshold: float = DEFAULT_SNAP_THRESHOLD_PX
    selected_stroke_ids: tuple[StrokeId, ...] = ()
    drawing_state: DrawingState = DrawingState.IDLE

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate every field on this canvas state.

        Raises:
            CanvasStateValidationError: if any field is out of its valid
                range or of the wrong type.
        """
        _validate_range(
            self.canvas_width, MIN_CANVAS_DIMENSION_PX, MAX_CANVAS_DIMENSION_PX,
            "canvas_width",
        )
        _validate_range(
            self.canvas_height, MIN_CANVAS_DIMENSION_PX, MAX_CANVAS_DIMENSION_PX,
            "canvas_height",
        )
        _validate_range(self.zoom, MIN_ZOOM, MAX_ZOOM, "zoom")
        _validate_range(self.grid_size, MIN_GRID_SIZE_PX, MAX_GRID_SIZE_PX, "grid_size")
        _validate_range(
            self.snap_threshold, MIN_SNAP_THRESHOLD_PX, MAX_SNAP_THRESHOLD_PX,
            "snap_threshold",
        )
        if not isinstance(self.current_brush, Brush):
            raise CanvasStateValidationError(
                f"current_brush must be a Brush, got {type(self.current_brush)!r}."
            )
        if not isinstance(self.symmetry_mode, SymmetryMode):
            raise CanvasStateValidationError(
                f"symmetry_mode must be a SymmetryMode, got {type(self.symmetry_mode)!r}."
            )
        if not isinstance(self.tool_mode, ToolMode):
            raise CanvasStateValidationError(
                f"tool_mode must be a ToolMode, got {type(self.tool_mode)!r}."
            )
        if not isinstance(self.drawing_state, DrawingState):
            raise CanvasStateValidationError(
                f"drawing_state must be a DrawingState, got {type(self.drawing_state)!r}."
            )

    # ------------------------------------------------------------------
    # Cloning / resetting
    # ------------------------------------------------------------------

    def clone(self, **overrides: object) -> "CanvasState":
        """Return a new, validated CanvasState with the given fields overridden.

        Since field mutation on a live ``CanvasState`` is otherwise done
        in place (it is not frozen, unlike :class:`Brush`), ``clone`` is
        the sanctioned way to derive an independent copy -- e.g. for
        snapshotting into timeline history before an undoable change.
        """
        return replace(self, **overrides)

    def reset(self) -> None:
        """Reset every field to its default value, in place.

        Used when starting a new project or discarding the current
        editor session state without discarding the CanvasState object
        identity itself (e.g. if something else holds a reference to it).
        """
        default = CanvasState()
        self.canvas_width = default.canvas_width
        self.canvas_height = default.canvas_height
        self.zoom = default.zoom
        self.pan_x = default.pan_x
        self.pan_y = default.pan_y
        self.current_layer_id = default.current_layer_id
        self.current_brush = default.current_brush
        self.symmetry_mode = default.symmetry_mode
        self.tool_mode = default.tool_mode
        self.grid_enabled = default.grid_enabled
        self.grid_size = default.grid_size
        self.snap_enabled = default.snap_enabled
        self.snap_threshold = default.snap_threshold
        self.selected_stroke_ids = default.selected_stroke_ids
        self.drawing_state = default.drawing_state
