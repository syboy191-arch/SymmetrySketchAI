"""Unit tests for domain.entities.point.Point."""

from __future__ import annotations

import math

import pytest

from core.exceptions import InvalidStrokeError
from domain.entities.point import Point


class TestPointConstruction:
    def test_default_construction_uses_full_pressure(self) -> None:
        p = Point(x=1.0, y=2.0)
        assert p.pressure == 1.0
        assert p.timestamp == 0.0
        assert p.velocity == 0.0

    def test_rejects_pressure_above_max(self) -> None:
        with pytest.raises(InvalidStrokeError):
            Point(x=0.0, y=0.0, pressure=1.5)

    def test_rejects_pressure_below_min(self) -> None:
        with pytest.raises(InvalidStrokeError):
            Point(x=0.0, y=0.0, pressure=-0.1)

    def test_rejects_negative_timestamp(self) -> None:
        with pytest.raises(InvalidStrokeError):
            Point(x=0.0, y=0.0, timestamp=-1.0)

    def test_is_immutable(self) -> None:
        p = Point(x=0.0, y=0.0)
        with pytest.raises(Exception):
            p.x = 5.0  # type: ignore[misc]


class TestPointGeometry:
    def test_distance_to_computes_euclidean_distance(self) -> None:
        a = Point(x=0.0, y=0.0)
        b = Point(x=3.0, y=4.0)
        assert a.distance_to(b) == pytest.approx(5.0)

    def test_distance_to_is_symmetric(self) -> None:
        a = Point(x=1.0, y=1.0)
        b = Point(x=4.0, y=5.0)
        assert a.distance_to(b) == pytest.approx(b.distance_to(a))

    def test_distance_to_self_is_zero(self) -> None:
        a = Point(x=2.0, y=3.0)
        assert a.distance_to(a) == pytest.approx(0.0)

    def test_with_offset_translates_coordinates(self) -> None:
        p = Point(x=1.0, y=1.0, pressure=0.7, timestamp=2.0, velocity=3.0)
        moved = p.with_offset(dx=10.0, dy=-5.0)
        assert moved.x == pytest.approx(11.0)
        assert moved.y == pytest.approx(-4.0)

    def test_with_offset_preserves_non_positional_fields(self) -> None:
        p = Point(x=0.0, y=0.0, pressure=0.42, timestamp=1.23, velocity=9.9)
        moved = p.with_offset(dx=1.0, dy=1.0)
        assert moved.pressure == p.pressure
        assert moved.timestamp == p.timestamp
        assert moved.velocity == p.velocity

    def test_with_offset_does_not_mutate_original(self) -> None:
        p = Point(x=0.0, y=0.0)
        _ = p.with_offset(dx=5.0, dy=5.0)
        assert p.x == 0.0
        assert p.y == 0.0

    def test_as_tuple_returns_xy_pair(self) -> None:
        p = Point(x=3.5, y=-2.5)
        assert p.as_tuple() == (3.5, -2.5)
