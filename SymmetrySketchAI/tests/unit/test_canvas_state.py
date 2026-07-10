"""Unit tests for domain.entities.canvas_state."""
from __future__ import annotations

import pytest

from core.enums import DrawingState, SymmetryMode
from core.exceptions import DrawingError
from domain.entities.brush import Brush, BrushStyle
from domain.entities.canvas_state import (
    CanvasState,
    CanvasStateValidationError,
    ToolMode,
)
from domain.entities.ids import new_layer_id


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_construction(self):
        state = CanvasState()
        assert state.zoom == 1.0
        assert state.pan_x == 0.0
        assert state.pan_y == 0.0
        assert state.current_layer_id is None
        assert isinstance(state.current_brush, Brush)
        assert state.symmetry_mode is SymmetryMode.NONE
        assert state.tool_mode is ToolMode.BRUSH
        assert state.grid_enabled is False
        assert state.snap_enabled is False
        assert state.selected_stroke_ids == ()
        assert state.drawing_state is DrawingState.IDLE

    def test_custom_construction(self):
        layer_id = new_layer_id()
        state = CanvasState(
            zoom=2.5,
            current_layer_id=layer_id,
            symmetry_mode=SymmetryMode.RADIAL,
            tool_mode=ToolMode.ERASER,
            drawing_state=DrawingState.DRAWING,
        )
        assert state.zoom == 2.5
        assert state.current_layer_id == layer_id
        assert state.symmetry_mode is SymmetryMode.RADIAL
        assert state.tool_mode is ToolMode.ERASER
        assert state.drawing_state is DrawingState.DRAWING

    def test_canvas_state_validation_error_is_a_drawing_error(self):
        assert issubclass(CanvasStateValidationError, DrawingError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    @pytest.mark.parametrize("bad_zoom", [0.0, -1.0, 0.01, 100.0])
    def test_rejects_invalid_zoom(self, bad_zoom):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(zoom=bad_zoom)

    @pytest.mark.parametrize("bad_dim", [0.0, -1.0])
    def test_rejects_invalid_canvas_width(self, bad_dim):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(canvas_width=bad_dim)

    @pytest.mark.parametrize("bad_dim", [0.0, -1.0])
    def test_rejects_invalid_canvas_height(self, bad_dim):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(canvas_height=bad_dim)

    def test_rejects_non_brush_current_brush(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(current_brush="not-a-brush")  # type: ignore[arg-type]

    def test_rejects_non_symmetry_mode(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(symmetry_mode="radial")  # type: ignore[arg-type]

    def test_rejects_non_tool_mode(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(tool_mode="brush")  # type: ignore[arg-type]

    def test_rejects_non_drawing_state(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(drawing_state="idle")  # type: ignore[arg-type]

    def test_rejects_invalid_grid_size(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(grid_size=-5.0)

    def test_rejects_invalid_snap_threshold(self):
        with pytest.raises(CanvasStateValidationError):
            CanvasState(snap_threshold=-1.0)

    def test_boundary_values_are_valid(self):
        CanvasState(zoom=0.05)
        CanvasState(zoom=64.0)


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

class TestClone:
    def test_clone_with_no_overrides_produces_equal_state(self):
        state = CanvasState(zoom=1.5)
        clone = state.clone()
        assert clone == state
        assert clone is not state

    def test_clone_with_overrides(self):
        state = CanvasState(zoom=1.0)
        clone = state.clone(zoom=3.0)
        assert clone.zoom == 3.0
        assert state.zoom == 1.0

    def test_clone_validates_overrides(self):
        state = CanvasState()
        with pytest.raises(CanvasStateValidationError):
            state.clone(zoom=-1.0)


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

class TestReset:
    def test_reset_restores_defaults(self):
        state = CanvasState(
            zoom=5.0,
            pan_x=100.0,
            pan_y=-50.0,
            current_layer_id=new_layer_id(),
            symmetry_mode=SymmetryMode.MANDALA,
            tool_mode=ToolMode.SELECTION,
            grid_enabled=True,
            snap_enabled=True,
            drawing_state=DrawingState.DRAWING,
        )
        state.reset()
        default = CanvasState()
        assert state.zoom == default.zoom
        assert state.pan_x == default.pan_x
        assert state.pan_y == default.pan_y
        assert state.current_layer_id is None
        assert state.symmetry_mode is SymmetryMode.NONE
        assert state.tool_mode is ToolMode.BRUSH
        assert state.grid_enabled is False
        assert state.snap_enabled is False
        assert state.drawing_state is DrawingState.IDLE

    def test_reset_preserves_object_identity(self):
        state = CanvasState(zoom=3.0)
        original_ref = state
        state.reset()
        assert state is original_ref
