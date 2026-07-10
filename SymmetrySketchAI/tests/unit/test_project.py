"""Unit tests for domain.entities.project."""
from __future__ import annotations

import pytest

from core.enums import BrushType
from core.exceptions import DrawingError, LayerNotFoundError
from domain.entities.ids import new_layer_id
from domain.entities.layer import Layer
from domain.entities.point import Point
from domain.entities.project import (
    Project,
    ProjectOperationError,
    ProjectStatistics,
    ProjectValidationError,
)
from domain.entities.stroke import Stroke


def make_stroke(*points: tuple[float, float]) -> Stroke:
    """Build a valid Stroke with the given points, on a fresh layer id."""
    stroke = Stroke(layer_id=new_layer_id(), brush_type=BrushType.PENCIL)
    for x, y in points:
        stroke.append_point(Point(x=x, y=y))
    return stroke


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_construction(self):
        project = Project()
        assert project.name == "Untitled Project"
        assert project.layer_count() == 0
        assert project.created_at is not None
        assert project.modified_at is not None

    def test_custom_construction(self):
        project = Project(name="My Mandala")
        assert project.name == "My Mandala"

    def test_unique_ids_by_default(self):
        assert Project().project_id != Project().project_id

    def test_default_schema_version_matches_core_constant(self):
        from core.constants import PROJECT_SCHEMA_VERSION

        assert Project().schema_version == PROJECT_SCHEMA_VERSION

    def test_project_errors_are_drawing_errors(self):
        assert issubclass(ProjectValidationError, DrawingError)
        assert issubclass(ProjectOperationError, DrawingError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    @pytest.mark.parametrize("bad_name", ["", "   ", None, 123])
    def test_rejects_invalid_name_on_construction(self, bad_name):
        with pytest.raises(ProjectValidationError):
            Project(name=bad_name)

    def test_rename_validates(self):
        project = Project()
        with pytest.raises(ProjectValidationError):
            project.rename("")
        project.rename("Renamed")
        assert project.name == "Renamed"

    @pytest.mark.parametrize("bad_version", ["", "   ", None])
    def test_rejects_invalid_schema_version(self, bad_version):
        with pytest.raises(ProjectValidationError):
            Project(schema_version=bad_version)


# ---------------------------------------------------------------------------
# Layer management
# ---------------------------------------------------------------------------

class TestLayerManagement:
    def test_add_layer(self):
        project = Project()
        layer = Layer(name="Base")
        project.add_layer(layer)
        assert project.layer_count() == 1
        assert project.layers == (layer,)

    def test_add_layer_rejects_wrong_type(self):
        project = Project()
        with pytest.raises(ProjectValidationError):
            project.add_layer("not-a-layer")  # type: ignore[arg-type]

    def test_add_layer_updates_modified_at(self):
        import time

        project = Project()
        original = project.modified_at
        time.sleep(0.001)
        project.add_layer(Layer())
        assert project.modified_at > original

    def test_remove_layer(self):
        project = Project()
        layer = Layer()
        project.add_layer(layer)
        project.remove_layer(layer.layer_id)
        assert project.layer_count() == 0

    def test_remove_layer_not_found_raises(self):
        project = Project()
        with pytest.raises(LayerNotFoundError):
            project.remove_layer(new_layer_id())

    def test_remove_layer_clears_current_layer_reference(self):
        project = Project()
        layer = Layer()
        project.add_layer(layer)
        project.canvas_state.current_layer_id = layer.layer_id
        project.remove_layer(layer.layer_id)
        assert project.canvas_state.current_layer_id is None

    def test_duplicate_layer(self):
        project = Project()
        layer = Layer(name="Original")
        layer.add_stroke(make_stroke((0, 0), (1, 1)))
        project.add_layer(layer)
        duplicate = project.duplicate_layer(layer.layer_id)
        assert duplicate.layer_id != layer.layer_id
        assert duplicate.name == layer.name
        assert duplicate.stroke_count() == layer.stroke_count()
        assert project.layer_count() == 2
        assert project.layers[1] is duplicate

    def test_duplicate_layer_not_found_raises(self):
        project = Project()
        with pytest.raises(LayerNotFoundError):
            project.duplicate_layer(new_layer_id())

    def test_move_layer(self):
        project = Project()
        first, second, third = Layer(name="A"), Layer(name="B"), Layer(name="C")
        for layer in (first, second, third):
            project.add_layer(layer)
        project.move_layer(third.layer_id, 0)
        assert [layer.name for layer in project.layers] == ["C", "A", "B"]

    def test_move_layer_not_found_raises(self):
        project = Project()
        project.add_layer(Layer())
        with pytest.raises(LayerNotFoundError):
            project.move_layer(new_layer_id(), 0)

    def test_move_layer_out_of_range_raises(self):
        project = Project()
        layer = Layer()
        project.add_layer(layer)
        with pytest.raises(ProjectOperationError):
            project.move_layer(layer.layer_id, 5)

    def test_find_layer_returns_layer(self):
        project = Project()
        layer = Layer()
        project.add_layer(layer)
        assert project.find_layer(layer.layer_id) is layer

    def test_find_layer_returns_none_when_absent(self):
        project = Project()
        assert project.find_layer(new_layer_id()) is None

    def test_iteration_and_len(self):
        project = Project()
        first, second = Layer(), Layer()
        project.add_layer(first)
        project.add_layer(second)
        assert list(project) == [first, second]
        assert len(project) == 2

    def test_layers_view_is_read_only_tuple(self):
        project = Project()
        project.add_layer(Layer())
        assert isinstance(project.layers, tuple)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

class TestStatistics:
    def test_statistics_on_empty_project(self):
        stats = Project().statistics()
        assert stats == ProjectStatistics(
            layer_count=0, visible_layer_count=0, stroke_count=0, point_count=0
        )

    def test_statistics_counts_layers_strokes_and_points(self):
        project = Project()

        visible_layer = Layer(name="Visible")
        visible_layer.add_stroke(make_stroke((0, 0), (1, 1), (2, 2)))
        visible_layer.add_stroke(make_stroke((0, 0)))

        hidden_layer = Layer(name="Hidden")
        hidden_layer.set_visible(False)
        hidden_layer.add_stroke(make_stroke((0, 0), (1, 1)))

        project.add_layer(visible_layer)
        project.add_layer(hidden_layer)

        stats = project.statistics()
        assert stats.layer_count == 2
        assert stats.visible_layer_count == 1
        assert stats.stroke_count == 3
        assert stats.point_count == 6

    def test_statistics_is_a_snapshot_not_live(self):
        project = Project()
        layer = Layer()
        project.add_layer(layer)
        stats_before = project.statistics()
        layer.add_stroke(make_stroke((0, 0)))
        stats_after = project.statistics()
        assert stats_before.stroke_count == 0
        assert stats_after.stroke_count == 1
