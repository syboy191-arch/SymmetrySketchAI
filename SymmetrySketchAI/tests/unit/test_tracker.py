"""Unit tests for vision.tracker.HandTracker.

None of these tests require a real webcam, a real MediaPipe model file,
or network access. Camera capture (``cv2.VideoCapture``) and the
MediaPipe ``HandLandmarker`` are fully mocked.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from config.tracker_config import TrackerConfig
from core.enums import HandLabel
from core.exceptions import (
    CameraNotAvailableError,
    HandLandmarkerInitializationError,
)
from vision.tracker import HandTracker, TrackerStartedEvent, TrackerStoppedEvent


def _make_mock_category(name: str, score: float = 0.95) -> SimpleNamespace:
    return SimpleNamespace(category_name=name, score=score)


def _make_mock_landmark(x: float, y: float, z: float = 0.0) -> SimpleNamespace:
    return SimpleNamespace(x=x, y=y, z=z)


def _make_raw_result(num_hands: int) -> SimpleNamespace:
    hand_landmarks = [
        [_make_mock_landmark(i / 20.0, i / 20.0, 0.0) for i in range(21)]
        for _ in range(num_hands)
    ]
    handedness = [
        [_make_mock_category("Right" if h % 2 == 0 else "Left")]
        for h in range(num_hands)
    ]
    return SimpleNamespace(hand_landmarks=hand_landmarks, handedness=handedness)


@pytest.fixture
def mock_camera() -> MagicMock:
    capture = MagicMock()
    capture.isOpened.return_value = True
    frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    capture.read.return_value = (True, frame)
    return capture


@pytest.fixture
def mock_landmarker() -> MagicMock:
    landmarker = MagicMock()
    landmarker.detect.return_value = _make_raw_result(num_hands=1)
    return landmarker


class TestHandTrackerLifecycle:
    def test_start_opens_camera_and_landmarker(
        self, mock_camera: MagicMock, mock_landmarker: MagicMock
    ) -> None:
        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.__str__.return_value = "/fake/hand_landmarker.task"

            tracker = HandTracker(config=TrackerConfig())
            tracker.start()

            assert tracker.is_running is True
            tracker.stop()

    def test_start_raises_when_camera_unavailable(
        self, mock_landmarker: MagicMock
    ) -> None:
        unavailable_camera = MagicMock()
        unavailable_camera.isOpened.return_value = False

        with patch("cv2.VideoCapture", return_value=unavailable_camera):
            tracker = HandTracker(config=TrackerConfig())
            with pytest.raises(CameraNotAvailableError):
                tracker.start()

    def test_start_raises_when_model_missing(
        self, mock_camera: MagicMock
    ) -> None:
        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HAND_LANDMARKER_MODEL_PATH"
        ) as mock_path:
            mock_path.exists.return_value = False

            tracker = HandTracker(config=TrackerConfig())
            with pytest.raises(HandLandmarkerInitializationError):
                tracker.start()

    def test_stop_is_safe_before_start(self) -> None:
        tracker = HandTracker(config=TrackerConfig())
        tracker.stop()  # should not raise
        assert tracker.is_running is False

    def test_double_start_is_idempotent(
        self, mock_camera: MagicMock, mock_landmarker: MagicMock
    ) -> None:
        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            tracker = HandTracker(config=TrackerConfig())
            tracker.start()
            tracker.start()  # should not reopen or raise
            assert tracker.is_running is True
            tracker.stop()

    def test_context_manager_starts_and_stops(
        self, mock_camera: MagicMock, mock_landmarker: MagicMock
    ) -> None:
        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            with HandTracker(config=TrackerConfig()) as tracker:
                assert tracker.is_running is True
            assert tracker.is_running is False

    def test_publishes_lifecycle_events(
        self, mock_camera: MagicMock, mock_landmarker: MagicMock
    ) -> None:
        from core.events import EventBus

        bus = EventBus()
        started_events: list[TrackerStartedEvent] = []
        stopped_events: list[TrackerStoppedEvent] = []
        bus.subscribe(TrackerStartedEvent, started_events.append)
        bus.subscribe(TrackerStoppedEvent, stopped_events.append)

        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            tracker = HandTracker(config=TrackerConfig(), event_bus=bus)
            tracker.start()
            tracker.stop()

        assert len(started_events) == 1
        assert len(stopped_events) == 1


class TestHandTrackerReadFrame:
    def test_read_frame_raises_if_not_started(self) -> None:
        tracker = HandTracker(config=TrackerConfig())
        with pytest.raises(CameraNotAvailableError):
            tracker.read_frame()

    def test_read_frame_returns_tracker_result(
        self, mock_camera: MagicMock, mock_landmarker: MagicMock
    ) -> None:
        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            tracker = HandTracker(config=TrackerConfig())
            tracker.start()
            result = tracker.read_frame()
            tracker.stop()

        assert result.has_hands is True
        assert result.hand_count == 1
        assert result.frame_size == (1280, 720)
        assert result.hands[0].label is HandLabel.RIGHT

    def test_read_frame_raises_when_capture_fails(
        self, mock_landmarker: MagicMock
    ) -> None:
        failing_camera = MagicMock()
        failing_camera.isOpened.return_value = True
        failing_camera.read.return_value = (False, None)

        with patch("cv2.VideoCapture", return_value=failing_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=mock_landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            tracker = HandTracker(config=TrackerConfig())
            tracker.start()
            with pytest.raises(CameraNotAvailableError):
                tracker.read_frame()
            tracker.stop()

    def test_read_frame_with_no_hands_returns_empty(
        self, mock_camera: MagicMock
    ) -> None:
        landmarker = MagicMock()
        landmarker.detect.return_value = _make_raw_result(num_hands=0)

        with patch("cv2.VideoCapture", return_value=mock_camera), patch(
            "vision.tracker.HandLandmarker.create_from_options",
            return_value=landmarker,
        ), patch("vision.tracker.HAND_LANDMARKER_MODEL_PATH") as mock_path:
            mock_path.exists.return_value = True

            tracker = HandTracker(config=TrackerConfig())
            tracker.start()
            result = tracker.read_frame()
            tracker.stop()

        assert result.has_hands is False
        assert result.hand_count == 0
