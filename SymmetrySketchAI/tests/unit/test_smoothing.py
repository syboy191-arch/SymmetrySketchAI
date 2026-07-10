"""Unit tests for vision.smoothing."""
from __future__ import annotations

import pytest

from core.constants import HAND_LANDMARK_COUNT
from core.exceptions import VisionError
from vision.landmarks import Landmarks
from vision.smoothing import LandmarkSmoother, MovingAverage, SmoothingError


def make_landmarks(offset: float = 0.0) -> Landmarks:
    """Build a valid 21-point Landmarks with every coord shifted by offset."""
    return Landmarks.from_coordinates(
        [(0.01 * i + offset, 0.02 * i + offset, 0.0) for i in range(HAND_LANDMARK_COUNT)]
    )


class TestMovingAverage:
    def test_empty_average_is_zero(self):
        assert MovingAverage(3).value == 0.0

    def test_running_average(self):
        avg = MovingAverage(window_size=3)
        assert avg.add(3.0) == 3.0
        assert avg.add(5.0) == 4.0
        assert avg.add(7.0) == 5.0

    def test_window_drops_oldest(self):
        avg = MovingAverage(window_size=2)
        avg.add(10.0)
        avg.add(20.0)
        assert avg.add(30.0) == 25.0  # 10 dropped, mean(20, 30)

    def test_is_full(self):
        avg = MovingAverage(window_size=2)
        avg.add(1.0)
        assert avg.is_full is False
        avg.add(2.0)
        assert avg.is_full is True

    def test_reset(self):
        avg = MovingAverage(window_size=2)
        avg.add(1.0)
        avg.reset()
        assert avg.value == 0.0

    def test_rejects_invalid_window(self):
        with pytest.raises(SmoothingError):
            MovingAverage(window_size=0)

    def test_smoothing_error_is_a_vision_error(self):
        assert issubclass(SmoothingError, VisionError)


class TestLandmarkSmoother:
    def test_first_frame_passthrough(self):
        smoother = LandmarkSmoother(window_size=5)
        lm = make_landmarks(0.0)
        assert smoother.smooth(lm) is lm

    def test_window_size_one_disables_smoothing(self):
        smoother = LandmarkSmoother(window_size=1)
        first = make_landmarks(0.0)
        second = make_landmarks(0.5)
        assert smoother.smooth(first) is first
        assert smoother.smooth(second) is second

    def test_averages_two_frames(self):
        smoother = LandmarkSmoother(window_size=2)
        smoother.smooth(make_landmarks(0.0))
        result = smoother.smooth(make_landmarks(0.4))
        # Each coord is the mean of the two frames -> offset 0.2 added.
        assert result.points[0].x == pytest.approx(0.2)
        assert result.points[0].y == pytest.approx(0.2)

    def test_output_always_has_21_points(self):
        smoother = LandmarkSmoother(window_size=3)
        for i in range(4):
            result = smoother.smooth(make_landmarks(0.1 * i))
            assert len(result.points) == HAND_LANDMARK_COUNT

    def test_reset_clears_history(self):
        smoother = LandmarkSmoother(window_size=3)
        smoother.smooth(make_landmarks(0.0))
        smoother.reset()
        assert smoother.is_full is False
        lm = make_landmarks(0.9)
        # After reset, next frame is treated as the first again.
        assert smoother.smooth(lm) is lm

    def test_rejects_invalid_window(self):
        with pytest.raises(SmoothingError):
            LandmarkSmoother(window_size=0)