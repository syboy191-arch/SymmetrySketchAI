"""Landmark smoothing utilities for the vision layer.

Design rationale:
    MediaPipe landmark output jitters frame-to-frame even for a
    perfectly still hand. Feeding that raw jitter into gesture
    classification produces flickering, unstable gestures, and feeding
    it into the (future) stroke engine produces shaky lines. This
    module provides small, pure, dependency-free smoothers that average
    recent samples over a fixed window, trading a few frames of latency
    for stable output.

    Everything here is stdlib-only and side-effect free: no OpenCV, no
    MediaPipe, no NumPy. Smoothers are stateful *helpers* owned by the
    gesture engine -- they hold a rolling window but contain no gesture
    business logic themselves, keeping them trivially unit-testable in a
    headless environment.
"""

from __future__ import annotations

from collections import deque

from core.constants import HAND_LANDMARK_COUNT, SMOOTHING_WINDOW_SIZE
from core.exceptions import VisionError
from vision.landmarks import Landmarks


class SmoothingError(VisionError):
    """Raised when a smoother is constructed with invalid parameters."""


class MovingAverage:
    """A fixed-window moving average over scalar values.

    Once the window is full, the oldest sample is dropped as each new
    one is added, so the average always reflects the most recent
    ``window_size`` samples.
    """

    __slots__ = ("_window",)

    def __init__(self, window_size: int = SMOOTHING_WINDOW_SIZE) -> None:
        if window_size < 1:
            raise SmoothingError(
                f"window_size must be at least 1, got {window_size!r}."
            )
        self._window: deque[float] = deque(maxlen=window_size)

    def add(self, value: float) -> float:
        """Add ``value`` and return the new moving average."""
        self._window.append(value)
        return self.value

    @property
    def value(self) -> float:
        """Return the current average, or ``0.0`` if no samples yet."""
        if not self._window:
            return 0.0
        return sum(self._window) / len(self._window)

    @property
    def window_size(self) -> int:
        """Return the configured maximum window size."""
        return self._window.maxlen or 0

    @property
    def is_full(self) -> bool:
        """Return whether the window has reached ``window_size`` samples."""
        return len(self._window) == self._window.maxlen

    def reset(self) -> None:
        """Clear all buffered samples."""
        self._window.clear()


class LandmarkSmoother:
    """Smooths a stream of :class:`~vision.landmarks.Landmarks`.

    Each of the 21 landmarks is averaged independently across the most
    recent ``window_size`` frames. A ``window_size`` of ``1`` disables
    smoothing (every frame is passed through unchanged), which is useful
    for tests and for latency-sensitive callers.
    """

    __slots__ = ("_window_size", "_history")

    def __init__(self, window_size: int = SMOOTHING_WINDOW_SIZE) -> None:
        if window_size < 1:
            raise SmoothingError(
                f"window_size must be at least 1, got {window_size!r}."
            )
        self._window_size = window_size
        self._history: deque[Landmarks] = deque(maxlen=window_size)

    def smooth(self, landmarks: Landmarks) -> Landmarks:
        """Add ``landmarks`` to the window and return the smoothed result.

        The first sample (or any sample when ``window_size == 1``) is
        returned unchanged, since there is nothing to average against.
        """
        self._history.append(landmarks)
        count = len(self._history)
        if count == 1:
            return landmarks

        averaged: list[tuple[float, float, float]] = []
        for i in range(HAND_LANDMARK_COUNT):
            sum_x = sum(frame.points[i].x for frame in self._history)
            sum_y = sum(frame.points[i].y for frame in self._history)
            sum_z = sum(frame.points[i].z for frame in self._history)
            averaged.append((sum_x / count, sum_y / count, sum_z / count))
        return Landmarks.from_coordinates(averaged)

    @property
    def window_size(self) -> int:
        """Return the configured smoothing window size."""
        return self._window_size

    @property
    def is_full(self) -> bool:
        """Return whether the window has reached ``window_size`` frames."""
        return len(self._history) == self._window_size

    def reset(self) -> None:
        """Clear buffered frames (e.g. when a hand leaves the frame)."""
        self._history.clear()