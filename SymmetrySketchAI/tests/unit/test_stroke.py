"""Unit tests for domain.entities.stroke.Stroke."""

from __future__ import annotations

import pytest

from core.enums import BrushType, SymmetryMode
from core.exceptions import InvalidStrokeError
from domain.entities.ids import new_layer_id
from domain.entities.point import Point
from domain.entities.stroke import Stroke


def make_stroke(**overrides: object) -> Stroke:
    """Test helper: build a minimal valid Stroke."""
    defaults: dict[str, object] = {
        "layer_id": new_layer_id(),
        "brush_type": BrushType.PENCIL,
    }
    defaults.update(overrides)
    return Stroke(**defaults)  # type: ignore[arg-type]


class TestStrokeConstruction:
    def test_new_stroke_has_unique_id(self) -> None:
        s1 = make_stroke()
        s2 = make_stroke()
        assert s1.stroke_id != s2.stroke_id

    def test_new_stroke_is_empty(self) -> None:
        s = make_stroke()
        assert s.is_empty
        assert s.points == ()

    def test_new_stroke_is_not_finalized(self) -> None:
        s = make_stroke()
        assert s.is_finalized is False


class TestStrokePointMutation:
    def test_append_point_adds_to_points(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        s.append_point(Point(x=2.0, y=2.0))
        assert len(s.points) == 2

    def test_points_property_returns_tuple_not_list(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        assert isinstance(s.points, tuple)

    def test_points_property_is_defensive_copy(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        pts = s.points
        # Mutating a Point is impossible (frozen); mutating the returned
        # tuple is impossible by type. Appending via the public API
        # must be the only way to grow the stroke.
        s.append_point(Point(x=2.0, y=2.0))
        assert len(pts) == 1  # earlier snapshot unaffected
        assert len(s.points) == 2

    def test_append_point_after_finalize_raises(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        s.finalize()
        with pytest.raises(InvalidStrokeError):
            s.append_point(Point(x=2.0, y=2.0))

    def test_finalize_empty_stroke_raises(self) -> None:
        s = make_stroke()
        with pytest.raises(InvalidStrokeError):
            s.finalize()

    def test_finalize_sets_flag(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=0.0, y=0.0))
        s.finalize()
        assert s.is_finalized is True

    def test_replace_points_on_finalized_stroke(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=0.0, y=0.0))
        s.finalize()
        new_pts = [Point(x=5.0, y=5.0), Point(x=6.0, y=6.0)]
        s.replace_points(new_pts)
        assert len(s.points) == 2
        assert s.points[0].x == 5.0

    def test_replace_points_with_empty_list_raises(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=0.0, y=0.0))
        with pytest.raises(InvalidStrokeError):
            s.replace_points([])


class TestStrokeClone:
    def test_clone_default_gets_new_id(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        clone = s.clone()
        assert clone.stroke_id != s.stroke_id

    def test_clone_preserves_geometry(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=2.0))
        s.append_point(Point(x=3.0, y=4.0))
        clone = s.clone()
        assert [p.as_tuple() for p in clone.points] == [
            p.as_tuple() for p in s.points
        ]

    def test_clone_is_independent_of_original(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        clone = s.clone()
        clone.append_point(Point(x=9.0, y=9.0))
        assert len(s.points) == 1
        assert len(clone.points) == 2

    def test_clone_as_new_stroke_false_keeps_id(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=1.0, y=1.0))
        clone = s.clone(as_new_stroke=False)
        assert clone.stroke_id == s.stroke_id

    def test_clone_preserves_styling(self) -> None:
        s = make_stroke(
            brush_type=BrushType.NEON,
            color_rgba=(255, 0, 0, 1.0),
            base_width=12.0,
            symmetry_mode=SymmetryMode.RADIAL,
        )
        s.append_point(Point(x=0.0, y=0.0))
        clone = s.clone()
        assert clone.brush_type == BrushType.NEON
        assert clone.color_rgba == (255, 0, 0, 1.0)
        assert clone.base_width == 12.0
        assert clone.symmetry_mode == SymmetryMode.RADIAL


class TestStrokeBoundingBox:
    def test_bounding_box_of_empty_stroke_raises(self) -> None:
        s = make_stroke()
        with pytest.raises(InvalidStrokeError):
            s.bounding_box()

    def test_bounding_box_single_point(self) -> None:
        s = make_stroke()
        s.append_point(Point(x=5.0, y=5.0))
        assert s.bounding_box() == (5.0, 5.0, 5.0, 5.0)

    def test_bounding_box_multiple_points(self) -> None:
        s = make_stroke()
        for x, y in [(0.0, 0.0), (10.0, -5.0), (-3.0, 8.0)]:
            s.append_point(Point(x=x, y=y))
        assert s.bounding_box() == (-3.0, -5.0, 10.0, 8.0)


class TestSymmetryEchoMetadata:
    def test_echo_stroke_can_reference_source(self) -> None:
        source = make_stroke()
        source.append_point(Point(x=0.0, y=0.0))
        echo = make_stroke(
            is_symmetry_echo=True,
            source_stroke_id=source.stroke_id,
        )
        assert echo.is_symmetry_echo is True
        assert echo.source_stroke_id == source.stroke_id
