"""The :class:`TrackerResult` value object -- one frame of tracking output.

Design rationale:
    ``tracker.py`` runs MediaPipe inference once per frame. Rather than
    returning MediaPipe's own result type (which would leak a third-party
    dependency into every downstream consumer -- gesture recognition,
    drawing, ui), it converts each frame's output into this project-owned,
    dependency-free value object. This is the sanctioned conversion
    boundary: no MediaPipe object should ever exist outside ``tracker.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.enums import HandLabel
from core.exceptions import VisionError
from vision.hand import Hand


class TrackerResultValidationError(VisionError):
    """Raised when a :class:`TrackerResult` is constructed with invalid
    data.
    """


@dataclass(frozen=True, slots=True)
class TrackerResult:
    """The complete output of running the hand tracker on one frame.

    Attributes:
        hands: All hands detected in this frame, in model output order.
        timestamp: Seconds since the tracking session started
            (monotonic), matching :class:`domain.entities.point.Point`'s
            timestamp convention.
        frame_width: Width of the source camera frame, in pixels.
        frame_height: Height of the source camera frame, in pixels.
        inference_time_ms: Wall-clock time spent running inference on
            this frame, in milliseconds.
    """

    hands: tuple[Hand, ...]
    timestamp: float
    frame_width: int
    frame_height: int
    inference_time_ms: float

    def __post_init__(self) -> None:
        if self.timestamp < 0.0:
            raise TrackerResultValidationError(
                f"timestamp cannot be negative, got {self.timestamp!r}."
            )
        if self.frame_width <= 0 or self.frame_height <= 0:
            raise TrackerResultValidationError(
                "frame_width and frame_height must be positive, got "
                f"({self.frame_width!r}, {self.frame_height!r})."
            )
        if self.inference_time_ms < 0.0:
            raise TrackerResultValidationError(
                "inference_time_ms cannot be negative, got "
                f"{self.inference_time_ms!r}."
            )

    @property
    def has_hands(self) -> bool:
        """Return whether at least one hand was detected this frame."""
        return len(self.hands) > 0

    @property
    def hand_count(self) -> int:
        """Return the number of hands detected this frame."""
        return len(self.hands)

    @property
    def frame_size(self) -> tuple[int, int]:
        """Return ``(frame_width, frame_height)`` in pixels."""
        return (self.frame_width, self.frame_height)

    def hand_by_label(self, label: HandLabel) -> Hand | None:
        """Return the first detected hand matching ``label``, or ``None``
        if no such hand was detected this frame.
        """
        for hand in self.hands:
            if hand.label is label:
                return hand
        return None

    def primary_hand(self) -> Hand | None:
        """Return the first detected hand, or ``None`` if none were
        detected. "Primary" is defined as model output order, which
        MediaPipe generally reports in descending detection confidence.
        """
        return self.hands[0] if self.hands else None

    @classmethod
    def empty(
        cls,
        timestamp: float,
        frame_width: int,
        frame_height: int,
        inference_time_ms: float = 0.0,
    ) -> "TrackerResult":
        """Build a :class:`TrackerResult` representing a frame in which
        no hands were detected.
        """
        return cls(
            hands=(),
            timestamp=timestamp,
            frame_width=frame_width,
            frame_height=frame_height,
            inference_time_ms=inference_time_ms,
        )
