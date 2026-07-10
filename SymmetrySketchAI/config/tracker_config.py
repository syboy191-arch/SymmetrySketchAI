"""Hand-tracking (vision) subsystem configuration.

Design rationale:
    Groups everything the not-yet-built ``vision`` package will need to
    open a camera and run MediaPipe hand landmark detection. Defaults
    are pulled from ``core.constants`` so there is a single source of
    truth for "reasonable defaults" shared between this live-config
    dataclass and any hard-coded fallback paths.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import (
    CAMERA_DEFAULT_FPS,
    CAMERA_DEFAULT_HEIGHT,
    CAMERA_DEFAULT_WIDTH,
    GESTURE_HOLD_FRAMES_TO_CONFIRM,
    MAX_TRACKED_HANDS,
    MIN_HAND_DETECTION_CONFIDENCE,
    MIN_HAND_PRESENCE_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
    SMOOTHING_WINDOW_SIZE,
)
from core.exceptions import InvalidConfigurationValueError


def _validate_confidence(name: str, value: float) -> None:
    if not 0.0 <= value <= 1.0:
        raise InvalidConfigurationValueError(
            f"{name} must be between 0.0 and 1.0, got {value!r}."
        )


@dataclass(frozen=True, slots=True)
class TrackerConfig:
    """Camera and MediaPipe hand-tracking settings.

    Attributes:
        camera_index: OS device index of the capture device to open.
        camera_width: Requested capture frame width in pixels.
        camera_height: Requested capture frame height in pixels.
        camera_fps: Requested capture frame rate.
        max_tracked_hands: Maximum simultaneous hands to track.
        min_hand_detection_confidence: Minimum confidence for the
            initial hand detection stage.
        min_hand_presence_confidence: Minimum confidence for the hand
            presence score during tracking.
        min_tracking_confidence: Minimum confidence for landmark
            tracking between frames.
        smoothing_window_size: Number of recent frames averaged to
            smooth landmark jitter.
        gesture_hold_frames_to_confirm: Consecutive frames a candidate
            gesture must persist before being confirmed.
        mirror_camera_feed: Whether the raw camera feed is horizontally
            flipped before processing (typical for a "selfie view").
    """

    camera_index: int = 0
    camera_width: int = CAMERA_DEFAULT_WIDTH
    camera_height: int = CAMERA_DEFAULT_HEIGHT
    camera_fps: int = CAMERA_DEFAULT_FPS
    max_tracked_hands: int = MAX_TRACKED_HANDS
    min_hand_detection_confidence: float = MIN_HAND_DETECTION_CONFIDENCE
    min_hand_presence_confidence: float = MIN_HAND_PRESENCE_CONFIDENCE
    min_tracking_confidence: float = MIN_TRACKING_CONFIDENCE
    smoothing_window_size: int = SMOOTHING_WINDOW_SIZE
    gesture_hold_frames_to_confirm: int = GESTURE_HOLD_FRAMES_TO_CONFIRM
    mirror_camera_feed: bool = True

    def __post_init__(self) -> None:
        if self.camera_index < 0:
            raise InvalidConfigurationValueError("camera_index must be >= 0.")
        if self.camera_width <= 0 or self.camera_height <= 0:
            raise InvalidConfigurationValueError(
                "camera_width and camera_height must be positive."
            )
        if self.camera_fps <= 0:
            raise InvalidConfigurationValueError("camera_fps must be positive.")
        if self.max_tracked_hands < 1:
            raise InvalidConfigurationValueError(
                "max_tracked_hands must be at least 1."
            )
        _validate_confidence(
            "min_hand_detection_confidence", self.min_hand_detection_confidence
        )
        _validate_confidence(
            "min_hand_presence_confidence", self.min_hand_presence_confidence
        )
        _validate_confidence(
            "min_tracking_confidence", self.min_tracking_confidence
        )
        if self.smoothing_window_size < 1:
            raise InvalidConfigurationValueError(
                "smoothing_window_size must be at least 1."
            )
        if self.gesture_hold_frames_to_confirm < 1:
            raise InvalidConfigurationValueError(
                "gesture_hold_frames_to_confirm must be at least 1."
            )
