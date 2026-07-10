"""The :class:`GestureEvent` value object -- pure data emitted by the
future Gesture Engine (vision layer) for the Stroke Engine to consume.

Design rationale:
    Per the project's data flow (Camera -> Tracker -> Gesture Engine ->
    Stroke Engine -> ...), the Gesture Engine's *output* must be a
    self-describing, immutable snapshot: which gesture was recognized, on
    which hand, when, with what confidence, and from what raw landmark
    data. Downstream consumers (Stroke Engine) must be able to act on a
    ``GestureEvent`` without any back-reference into the vision layer's
    internals -- this keeps business logic independent of MediaPipe/
    OpenCV, per the project's Clean Architecture rule.

    ``GestureEvent`` is deliberately a frozen (immutable) dataclass, the
    same design used for :class:`domain.entities.point.Point`: two events
    with identical fields are interchangeable values, not entities with
    identity/lifecycle, so sharing/replaying them freely is always safe.

This module reuses the project's existing single sources of truth:

- ``gesture_type`` comes from :class:`core.enums.GestureType`.
- ``hand_label`` comes from :class:`core.enums.HandLabel`.
- ``landmark`` count is validated against
  :data:`core.constants.HAND_LANDMARK_COUNT`.
- ``pressure_estimate`` is validated against
  :data:`core.constants.MIN_PRESSURE`/:data:`core.constants.MAX_PRESSURE`,
  the same bounds :class:`domain.entities.point.Point` uses for pressure.
- All validation errors derive from :class:`core.exceptions.VisionError`,
  the project's existing base for vision-subsystem errors, consistent
  with :class:`core.exceptions.GestureRecognitionError` and friends.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.constants import HAND_LANDMARK_COUNT, MAX_PRESSURE, MIN_PRESSURE
from core.enums import GestureType, HandLabel
from core.exceptions import VisionError

# --------------------------------------------------------------------------
# Constants (no magic numbers)
# --------------------------------------------------------------------------

MIN_CONFIDENCE: float = 0.0
MAX_CONFIDENCE: float = 1.0


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class GestureEventValidationError(VisionError):
    """Raised when constructing a GestureEvent with invalid data."""


# --------------------------------------------------------------------------
# Entity: GestureEvent
# --------------------------------------------------------------------------

Landmark = tuple[float, float, float]
"""A single hand landmark as ``(x, y, z)`` in normalized MediaPipe space."""


@dataclass(frozen=True, slots=True)
class GestureEvent:
    """An immutable snapshot of a single recognized hand gesture.

    Attributes:
        gesture_type: The gesture classification for this event.
        hand_label: Which physical hand produced this event.
        timestamp: Seconds since tracking started (monotonic, not
            wall-clock), matching the convention used by
            :attr:`domain.entities.point.Point.timestamp`.
        confidence: Classifier confidence in ``[0.0, 1.0]``.
        landmarks: The raw hand landmarks this classification was derived
            from, as a tuple of ``(x, y, z)`` triples. Empty is allowed
            (e.g. a synthetic/replayed event), but a non-empty tuple must
            contain exactly :data:`core.constants.HAND_LANDMARK_COUNT`
            entries, matching the MediaPipe hand model's output shape.
        velocity: Instantaneous speed of the tracked point driving this
            gesture, in canvas units per second. Defaults to ``0.0``.
        pressure_estimate: Simulated pressure in ``[0.0, 1.0]`` derived
            from gesture dynamics (e.g. pinch depth), used the same way
            :attr:`domain.entities.point.Point.pressure` is used
            downstream to drive brush width.
        previous_gesture_type: The gesture type immediately preceding
            this one for the same hand, or ``None`` if this is the first
            event in a tracking session. Enables the Stroke Engine to
            detect state transitions (e.g. POINT -> FIST) without keeping
            its own gesture history.
    """

    gesture_type: GestureType
    hand_label: HandLabel
    timestamp: float
    confidence: float = 1.0
    landmarks: tuple[Landmark, ...] = ()
    velocity: float = 0.0
    pressure_estimate: float = MAX_PRESSURE
    previous_gesture_type: GestureType | None = None

    def __post_init__(self) -> None:
        """Validate invariants immediately, since the object is frozen
        and can never be corrected after construction.
        """
        if not isinstance(self.gesture_type, GestureType):
            raise GestureEventValidationError(
                f"gesture_type must be a GestureType, got {type(self.gesture_type)!r}."
            )
        if not isinstance(self.hand_label, HandLabel):
            raise GestureEventValidationError(
                f"hand_label must be a HandLabel, got {type(self.hand_label)!r}."
            )
        if self.timestamp < 0.0:
            raise GestureEventValidationError(
                f"GestureEvent timestamp {self.timestamp!r} cannot be negative."
            )
        if not (MIN_CONFIDENCE <= self.confidence <= MAX_CONFIDENCE):
            raise GestureEventValidationError(
                f"GestureEvent confidence {self.confidence!r} out of range "
                f"[{MIN_CONFIDENCE}, {MAX_CONFIDENCE}]."
            )
        if not (MIN_PRESSURE <= self.pressure_estimate <= MAX_PRESSURE):
            raise GestureEventValidationError(
                f"GestureEvent pressure_estimate {self.pressure_estimate!r} out "
                f"of range [{MIN_PRESSURE}, {MAX_PRESSURE}]."
            )
        if self.landmarks and len(self.landmarks) != HAND_LANDMARK_COUNT:
            raise GestureEventValidationError(
                f"GestureEvent landmarks must contain exactly "
                f"{HAND_LANDMARK_COUNT} entries when provided, got "
                f"{len(self.landmarks)}."
            )
        if self.previous_gesture_type is not None and not isinstance(
            self.previous_gesture_type, GestureType
        ):
            raise GestureEventValidationError(
                "previous_gesture_type must be a GestureType or None, got "
                f"{type(self.previous_gesture_type)!r}."
            )

    # ------------------------------------------------------------------
    # State transition helpers
    # ------------------------------------------------------------------

    @property
    def is_transition(self) -> bool:
        """Whether this event represents a change in gesture classification
        relative to :attr:`previous_gesture_type`.

        Returns ``False`` when there is no prior gesture to compare
        against (the first event in a session), since a transition
        requires two distinct states to compare.
        """
        if self.previous_gesture_type is None:
            return False
        return self.previous_gesture_type != self.gesture_type

    def transitioned_to(self, gesture_type: GestureType) -> bool:
        """Whether this event is a transition specifically *into*
        ``gesture_type`` from a different previous gesture.
        """
        return self.is_transition and self.gesture_type == gesture_type
