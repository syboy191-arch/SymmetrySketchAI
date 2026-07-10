"""Unit tests for domain.entities.layer."""
from __future__ import annotations

import time

import pytest

from core.enums import BrushType, LayerBlendMode
from core.exceptions import DrawingError
from domain.entities.ids import new_layer_id
from domain.entities.layer import (
    BoundingBox,
    Layer,
    LayerOperationError,
    LayerValidationError,
)
from domain.entities.point import Point
from domain.entities.stroke import Stroke


def make_stroke(*points: tuple[float, float]) -> Stroke:
    """Build a valid, finalized-or-not Stroke with the given points."""
    stroke = Stroke(layer_id=new_layer_id(), brush_type=BrushType.PENCIL)
    for x, y in points:
        stroke.append_point(Point(x=x, y=y))
    return stroke


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_construction(self):
        layer = Layer()
        assert layer.name == "Untitled Layer"
        assert layer.visible is True
        assert layer.locked is False
        assert layer.opacity == 1.0
        assert layer.blend_mode is LayerBlendMode.NORMAL
        assert layer.z_index == 0
        assert layer.stroke_count() == 0

    def test_custom_construction(self):
        layer = Layer(name="Sketch", opacity=0.5, blend_mode=LayerBlendMode.MULTIPLY, z_index=3)
        assert layer.name == "Sketch"
        assert layer.opacity == 0.5
        assert layer.blend_mode is LayerBlendMode.MULTIPLY
        assert layer.z_index == 3

    def test_unique_ids_by_default(self):
        assert Layer().layer_id != Layer().layer_id

    def test_created_and_modified_timestamps_set(self):
        layer = Layer()
        assert layer.created_at is not None
        assert layer.modified_at is not None

    def test_layer_errors_are_drawing_errors(self):
        # Layer-specific errors must integrate with the project's exception
        # hierarchy (core.exceptions.DrawingError), not raise bare Exception.
        assert issubclass(LayerValidationError, DrawingError)
        assert issubclass(LayerOperationError, DrawingError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    @pytest.mark.parametrize("bad_name", ["", "   ", None, 123])
    def test_rejects_invalid_name_on_construction(self, bad_name):
        with pytest.raises(LayerValidationError):
            Layer(name=bad_name)

    @pytest.mark.parametrize("bad_opacity", [-0.1, 1.1, -5, 2])
    def test_rejects_invalid_opacity_on_construction(self, bad_opacity):
        with pytest.raises(LayerValidationError):
            Layer(opacity=bad_opacity)

    def test_rename_validates(self):
        layer = Layer()
        with pytest.raises(LayerValidationError):
            layer.rename("")
        layer.rename("New Name")
        assert layer.name == "New Name"

    def test_set_opacity_validates(self):
        layer = Layer()
        with pytest.raises(LayerValidationError):
            layer.set_opacity(1.5)
        layer.set_opacity(0.25)
        assert layer.opacity == 0.25

    def test_set_blend_mode_rejects_non_enum(self):
        layer = Layer()
        with pytest.raises(LayerValidationError):
            layer.set_blend_mode("multiply")  # type: ignore[arg-type]

    def test_set_z_index_rejects_non_int(self):
        layer = Layer()
        with pytest.raises(LayerValidationError):
            layer.set_z_index(1.5)  # type: ignore[arg-type]

    def test_boundary_opacity_values_are_valid(self):
        Layer(opacity=0.0)
        Layer(opacity=1.0)


# ---------------------------------------------------------------------------
# Mutators update modified_at
# ---------------------------------------------------------------------------

class TestTouchOnMutation:
    def test_rename_updates_modified_at(self):
        layer = Layer()
        original = layer.modified_at
        time.sleep(0.001)
        layer.rename("Renamed")
        assert layer.modified_at > original

    def test_add_stroke_updates_modified_at(self):
        layer = Layer()
        original = layer.modified_at
        time.sleep(0.001)
        layer.add_stroke(make_stroke((0, 0)))
        assert layer.modified_at > original


# ---------------------------------------------------------------------------
# Stroke collection management
# ---------------------------------------------------------------------------

class TestStrokeOperations:
    def test_add_stroke(self):
        layer = Layer()
        stroke = make_stroke((0, 0), (1, 1))
        layer.add_stroke(stroke)
        assert layer.stroke_count() == 1
        assert layer.strokes == (stroke,)

    def test_add_stroke_rejects_wrong_type(self):
        layer = Layer()
        with pytest.raises(LayerValidationError):
            layer.add_stroke("not a stroke")  # type: ignore[arg-type]

    def test_add_stroke_fails_when_locked(self):
        layer = Layer(locked=True)
        with pytest.raises(LayerOperationError):
            layer.add_stroke(make_stroke((0, 0)))

    def test_remove_stroke(self):
        layer = Layer()
        stroke = make_stroke((0, 0))
        layer.add_stroke(stroke)
        layer.remove_stroke(stroke)
        assert layer.stroke_count() == 0

    def test_remove_stroke_not_present_raises(self):
        layer = Layer()
        with pytest.raises(LayerOperationError):
            layer.remove_stroke(make_stroke((0, 0)))

    def test_remove_stroke_fails_when_locked(self):
        layer = Layer()
        stroke = make_stroke((0, 0))
        layer.add_stroke(stroke)
        layer.set_locked(True)
        with pytest.raises(LayerOperationError):
            layer.remove_stroke(stroke)

    def test_clear(self):
        layer = Layer()
        layer.add_stroke(make_stroke((0, 0)))
        layer.add_stroke(make_stroke((1, 1)))
        layer.clear()
        assert layer.stroke_count() == 0

    def test_clear_fails_when_locked(self):
        layer = Layer(locked=True)
        with pytest.raises(LayerOperationError):
            layer.clear()

    def test_iteration_and_len(self):
        layer = Layer()
        s1, s2 = make_stroke((0, 0)), make_stroke((1, 1))
        layer.add_stroke(s1)
        layer.add_stroke(s2)
        assert list(layer) == [s1, s2]
        assert len(layer) == 2

    def test_strokes_view_is_read_only_tuple(self):
        layer = Layer()
        layer.add_stroke(make_stroke((0, 0)))
        assert isinstance(layer.strokes, tuple)


# ---------------------------------------------------------------------------
# Bounding box
# ---------------------------------------------------------------------------

class TestBoundingBox:
    def test_empty_layer_has_no_bounding_box(self):
        assert Layer().bounding_box() is None

    def test_single_stroke_bounding_box(self):
        layer = Layer()
        layer.add_stroke(make_stroke((0, 0), (10, 5)))
        box = layer.bounding_box()
        assert box == BoundingBox(min_x=0, min_y=0, max_x=10, max_y=5)

    def test_multiple_strokes_union_bounding_box(self):
        layer = Layer()
        layer.add_stroke(make_stroke((0, 0), (5, 5)))
        layer.add_stroke(make_stroke((-3, 2), (8, 20)))
        box = layer.bounding_box()
        assert box == BoundingBox(min_x=-3, min_y=0, max_x=8, max_y=20)

    def test_stroke_with_no_points_is_ignored(self):
        layer = Layer()
        layer.add_stroke(make_stroke())
        assert layer.bounding_box() is None

    def test_bounding_box_rejects_inverted_coordinates(self):
        with pytest.raises(LayerValidationError):
            BoundingBox(min_x=5, min_y=0, max_x=0, max_y=10)

    def test_bounding_box_width_and_height(self):
        box = BoundingBox(min_x=0, min_y=0, max_x=10, max_y=4)
        assert box.width == 10
        assert box.height == 4


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

class TestClone:
    def test_clone_copies_fields(self):
        layer = Layer(name="Original", opacity=0.7, blend_mode=LayerBlendMode.SCREEN, z_index=2)
        layer.add_stroke(make_stroke((0, 0)))
        clone = layer.clone()
        assert clone.name == layer.name
        assert clone.opacity == layer.opacity
        assert clone.blend_mode == layer.blend_mode
        assert clone.z_index == layer.z_index
        assert clone.stroke_count() == layer.stroke_count()

    def test_clone_gets_new_id_by_default(self):
        layer = Layer()
        clone = layer.clone()
        assert clone.layer_id != layer.layer_id

    def test_clone_can_preserve_id(self):
        layer = Layer()
        clone = layer.clone(new_id=False)
        assert clone.layer_id == layer.layer_id

    def test_clone_stroke_list_is_independent(self):
        layer = Layer()
        layer.add_stroke(make_stroke((0, 0)))
        clone = layer.clone()
        clone.add_stroke(make_stroke((1, 1)))
        assert layer.stroke_count() == 1
        assert clone.stroke_count() == 2
