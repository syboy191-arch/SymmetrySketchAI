"""Unit tests for drawing.stroke_engine.StrokeEngine.

All GestureEvents are mocked from synthetic landmark tuples -- no camera,
MediaPipe, OpenCV, or GUI is required.
"""
from __future__ import annotations

import pytest

from core.constants import HAND_LANDMARK_COUNT, MAX_PRESSURE
from core.enums import BrushType, GestureType, HandLabel, SymmetryMode
from core.exceptions import InvalidStrokeError
from domain.entities.gesture_event import GestureEvent
from domain.entities.ids import new_layer_id
from drawing.stroke_engine import DRAWING_LANDMARK_INDEX, StrokeEngine


def make_event(
    x: float = 0.5,
    y: float = 0.5,
    *,
    timestamp: float = 0.0,
    velocity: float = 0.0,
    with_landmarks: bool = True,
) -> GestureEvent:
    """Build a mock POINT GestureEvent whose index fingertip is (x, y)."""
    landmarks: tuple[tuple[float, float, float], ...] = ()
    if with_landmarks:
        pts = [(0.0, 0.0, 0.0)] * HAND_LANDMARK_COUNT
        pts[DRAWING_LANDMARK_INDEX] = (x, y, 0.0)
        landmarks = tuple(pts)
    return GestureEvent(
        gesture_type=GestureType.POINT,
        hand_label=HandLabel.RIGHT,
        timestamp=timestamp,
        velocity=velocity,
        landmarks=landmarks,
    )


@pytest.fixture
def engine() -> StrokeEngine:
    return StrokeEngine(layer_id=new_layer_id())


class TestStart:
    def test_start_creates_active_non_empty_stroke(self, engine):
        stroke = engine.start_stroke(make_event(0.1, 0.2))
        assert engine.has_active_stroke() is True
        assert engine.current_stroke() is stroke
        assert stroke.is_finalized is False
        assert len(stroke.points) == 1
        assert stroke.points[0].as_tuple() == (0.1, 0.2)

    def test_start_while_active_raises(self, engine):
        engine.start_stroke(make_event())
        with pytest.raises(InvalidStrokeError):
            engine.start_stroke(make_event())

    def test_start_uses_engine_settings(self):
        layer = new_layer_id()
        engine = StrokeEngine(
            layer_id=layer,
            brush_type=BrushType.INK,
            color_rgba=(255, 0, 0, 1.0),
            base_width=12.0,
            symmetry_mode=SymmetryMode.RADIAL,
        )
        stroke = engine.start_stroke(make_event())
        assert stroke.layer_id == layer
        assert stroke.brush_type is BrushType.INK
        assert stroke.color_rgba == (255, 0, 0, 1.0)
        assert stroke.base_width == 12.0
        assert stroke.symmetry_mode is SymmetryMode.RADIAL


class TestAppend:
    def test_append_adds_points_in_order(self, engine):
        engine.start_stroke(make_event(0.0, 0.0))
        engine.append_point(make_event(0.1, 0.1))
        engine.append_point(make_event(0.2, 0.2))
        stroke = engine.current_stroke()
        assert [p.as_tuple() for p in stroke.points] == [
            (0.0, 0.0), (0.1, 0.1), (0.2, 0.2)
        ]

    def test_append_without_active_raises(self, engine):
        with pytest.raises(InvalidStrokeError):
            engine.append_point(make_event())

    def test_append_returns_point_with_fixed_pressure(self, engine):
        engine.start_stroke(make_event())
        point = engine.append_point(
            make_event(0.3, 0.4, timestamp=1.0, velocity=2.5)
        )
        assert point.as_tuple() == (0.3, 0.4)
        assert point.pressure == MAX_PRESSURE
        assert point.timestamp == 1.0
        assert point.velocity == 2.5


class TestFinish:
    def test_finish_returns_finalized_stroke_and_goes_idle(self, engine):
        engine.start_stroke(make_event(0.0, 0.0))
        engine.append_point(make_event(0.5, 0.5))
        stroke = engine.finish_stroke()
        assert stroke.is_finalized is True
        assert len(stroke.points) == 2
        assert engine.has_active_stroke() is False
        assert engine.current_stroke() is None

    def test_finish_without_active_raises(self, engine):
        with pytest.raises(InvalidStrokeError):
            engine.finish_stroke()

    def test_single_point_stroke_finishes(self, engine):
        engine.start_stroke(make_event(0.7, 0.7))
        stroke = engine.finish_stroke()
        assert stroke.is_finalized is True
        assert len(stroke.points) == 1


class TestCancelReset:
    def test_cancel_discards_active(self, engine):
        engine.start_stroke(make_event())
        engine.cancel()
        assert engine.has_active_stroke() is False
        assert engine.current_stroke() is None

    def test_cancel_while_idle_is_noop(self, engine):
        engine.cancel()  # must not raise
        assert engine.has_active_stroke() is False

    def test_reset_discards_active(self, engine):
        engine.start_stroke(make_event())
        engine.reset()
        assert engine.has_active_stroke() is False


class TestLongAndSequential:
    def test_long_stroke(self, engine):
        engine.start_stroke(make_event(0.0, 0.0))
        for i in range(1, 1000):
            engine.append_point(
                make_event(i / 1000.0, i / 1000.0, timestamp=i * 0.001)
            )
        stroke = engine.finish_stroke()
        assert len(stroke.points) == 1000

    def test_multiple_sequential_strokes_are_distinct(self, engine):
        first = engine.start_stroke(make_event(0.1, 0.1))
        engine.append_point(make_event(0.2, 0.2))
        finished_first = engine.finish_stroke()

        second = engine.start_stroke(make_event(0.8, 0.8))
        finished_second = engine.finish_stroke()

        assert finished_first.stroke_id != finished_second.stroke_id
        assert finished_first is first
        assert finished_second is second
        assert len(finished_first.points) == 2
        assert len(finished_second.points) == 1


class TestLandmarks:
    def test_event_without_landmarks_raises_on_start(self, engine):
        with pytest.raises(InvalidStrokeError):
            engine.start_stroke(make_event(with_landmarks=False))

    def test_event_without_landmarks_raises_on_append(self, engine):
        engine.start_stroke(make_event())
        with pytest.raises(InvalidStrokeError):
            engine.append_point(make_event(with_landmarks=False))

    def test_start_failure_leaves_engine_idle(self, engine):
        with pytest.raises(InvalidStrokeError):
            engine.start_stroke(make_event(with_landmarks=False))
        assert engine.has_active_stroke() is False


class TestConfigure:
    def test_configure_affects_next_stroke_only(self, engine):
        engine.start_stroke(make_event())
        engine.configure(brush_type=BrushType.MARKER)
        assert engine.current_stroke().brush_type is not BrushType.MARKER
        engine.finish_stroke()
        next_stroke = engine.start_stroke(make_event())
        assert next_stroke.brush_type is BrushType.MARKER