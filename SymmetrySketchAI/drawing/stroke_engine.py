"""The :class:`StrokeEngine` -- first stage of the drawing pipeline.

Design rationale:
    Per the project data flow

        GestureEvent -> StrokeEngine -> Stroke -> StrokeManager (future)
        -> Renderer (future)

    the Stroke Engine is the single component that turns the vision
    layer's semantic :class:`~domain.entities.gesture_event.GestureEvent`
    stream into editable :class:`~domain.entities.stroke.Stroke` objects.
    It owns *only* the stroke lifecycle -- start, append, finish, cancel,
    reset -- and nothing else. It does not render, mirror, export, replay,
    manage history, or perform AI correction; those are downstream
    responsibilities of later milestones, kept out by design so this
    class has a single reason to change (SRP).

    The engine reuses the existing domain entities verbatim
    (:class:`Point`, :class:`Stroke`) and the project's shared
    vocabularies (:class:`core.enums.BrushType`,
    :class:`core.enums.SymmetryMode`). It introduces no new domain model.

    A gesture event carries its hand landmarks as raw ``(x, y, z)``
    triples in MediaPipe's normalized image space. The drawing point is
    the index fingertip -- the same point the gesture engine uses to
    drive motion -- looked up via the single source of truth for
    landmark ordering, :class:`vision.landmarks.HandLandmarkIndex`
    (a dependency-free enum, no OpenCV/MediaPipe). Mapping those
    normalized coordinates into canvas space is deliberately deferred to
    a later milestone; see the known-limitations note in the PR summary.
"""

from __future__ import annotations

from typing import Final

from core.constants import DEFAULT_BRUSH_WIDTH_PX, MAX_PRESSURE
from core.enums import BrushType, SymmetryMode
from core.exceptions import InvalidStrokeError
from domain.entities.gesture_event import GestureEvent
from domain.entities.ids import LayerId
from domain.entities.point import Point
from domain.entities.stroke import Stroke
from vision.landmarks import HandLandmarkIndex

# ---------------------------------------------------------------------------
# Defaults (no magic numbers). Reused from the project's single sources of
# truth wherever one already exists.
# ---------------------------------------------------------------------------

DEFAULT_BRUSH_TYPE: Final[BrushType] = BrushType.PENCIL
DEFAULT_STROKE_COLOR_RGBA: Final[tuple[int, int, int, float]] = (0, 0, 0, 1.0)
DEFAULT_BASE_WIDTH: Final[float] = DEFAULT_BRUSH_WIDTH_PX
DEFAULT_SYMMETRY_MODE: Final[SymmetryMode] = SymmetryMode.NONE

DEFAULT_POINT_PRESSURE: Final[float] = MAX_PRESSURE
"""Fixed point pressure for Milestone 5A. Pressure detection is a future
milestone, so every sampled point keeps the neutral full-pressure value."""

DRAWING_LANDMARK_INDEX: Final[int] = int(HandLandmarkIndex.INDEX_FINGER_TIP)
"""The landmark used as the drawing tip: the index fingertip."""


class StrokeEngine:
    """Converts a stream of :class:`GestureEvent` objects into editable
    :class:`Stroke` objects, one stroke per start/finish cycle.

    The engine is a small state machine with two states: *idle* (no
    active stroke) and *drawing* (an active, not-yet-finalized stroke is
    accumulating points). Lifecycle:

        idle    --start_stroke-->  drawing
        drawing --append_point-->  drawing
        drawing --finish_stroke--> idle    (returns the finalized Stroke)
        drawing --cancel-->        idle    (discards the active Stroke)
        (any)   --reset-->         idle    (discards everything)

    Usage:
        >>> engine = StrokeEngine(layer_id=my_layer_id)
        >>> engine.start_stroke(event)
        >>> engine.append_point(next_event)
        >>> stroke = engine.finish_stroke()
    """

    __slots__ = (
        "_layer_id",
        "_brush_type",
        "_color_rgba",
        "_base_width",
        "_symmetry_mode",
        "_active",
    )

    def __init__(
        self,
        layer_id: LayerId,
        *,
        brush_type: BrushType = DEFAULT_BRUSH_TYPE,
        color_rgba: tuple[int, int, int, float] = DEFAULT_STROKE_COLOR_RGBA,
        base_width: float = DEFAULT_BASE_WIDTH,
        symmetry_mode: SymmetryMode = DEFAULT_SYMMETRY_MODE,
    ) -> None:
        """Construct a :class:`StrokeEngine`.

        Args:
            layer_id: The layer new strokes are created on.
            brush_type: Brush engine recorded on new strokes.
            color_rgba: Base color recorded on new strokes.
            base_width: Base width (px) recorded on new strokes.
            symmetry_mode: Symmetry mode recorded on new strokes, so
                replay/re-render stays faithful even if the *current*
                mode changes later.
        """
        self._layer_id = layer_id
        self._brush_type = brush_type
        self._color_rgba = color_rgba
        self._base_width = base_width
        self._symmetry_mode = symmetry_mode
        self._active: Stroke | None = None

    # ------------------------------------------------------------------
    # Configuration (applies to the *next* stroke started)
    # ------------------------------------------------------------------
    def configure(
        self,
        *,
        layer_id: LayerId | None = None,
        brush_type: BrushType | None = None,
        color_rgba: tuple[int, int, int, float] | None = None,
        base_width: float | None = None,
        symmetry_mode: SymmetryMode | None = None,
    ) -> None:
        """Update the styling used for subsequently started strokes.

        Only provided fields change. Settings are captured into a stroke
        at :meth:`start_stroke` time, so calling this mid-stroke affects
        only the *next* stroke, never the currently active one. This is
        the extension point future milestones (symmetry, brush switching)
        use without touching the lifecycle methods.
        """
        if layer_id is not None:
            self._layer_id = layer_id
        if brush_type is not None:
            self._brush_type = brush_type
        if color_rgba is not None:
            self._color_rgba = color_rgba
        if base_width is not None:
            self._base_width = base_width
        if symmetry_mode is not None:
            self._symmetry_mode = symmetry_mode

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start_stroke(self, event: GestureEvent) -> Stroke:
        """Begin a new stroke, seeding it with the event's first point.

        Returns the new active :class:`Stroke` (not yet finalized). By
        seeding the first point here, the engine can never produce an
        empty stroke through the normal flow.

        Raises:
            InvalidStrokeError: If a stroke is already active, or the
                event carries no landmarks to derive a point from. On the
                no-landmarks error the engine remains idle (no partial
                stroke is retained).
        """
        if self._active is not None:
            raise InvalidStrokeError(
                "Cannot start a new stroke while one is already active; "
                "finish_stroke() or cancel() first."
            )
        first_point = self._point_from_event(event)
        stroke = Stroke(
            layer_id=self._layer_id,
            brush_type=self._brush_type,
            color_rgba=self._color_rgba,
            base_width=self._base_width,
            symmetry_mode=self._symmetry_mode,
        )
        stroke.append_point(first_point)
        self._active = stroke
        return stroke

    def append_point(self, event: GestureEvent) -> Point:
        """Append the event's sampled point to the active stroke.

        Returns the appended :class:`Point`.

        Raises:
            InvalidStrokeError: If there is no active stroke, or the
                event carries no landmarks.
        """
        if self._active is None:
            raise InvalidStrokeError(
                "Cannot append_point without an active stroke; "
                "call start_stroke() first."
            )
        point = self._point_from_event(event)
        self._active.append_point(point)
        return point

    def finish_stroke(self) -> Stroke:
        """Finalize and return the active stroke, returning to idle.

        Raises:
            InvalidStrokeError: If there is no active stroke to finish.
        """
        if self._active is None:
            raise InvalidStrokeError(
                "Cannot finish_stroke without an active stroke."
            )
        stroke = self._active
        stroke.finalize()
        self._active = None
        return stroke

    def cancel(self) -> None:
        """Discard the active stroke, if any, returning to idle.

        Idempotent: cancelling while idle is a safe no-op, since
        cancelling "nothing" is not an error condition.
        """
        self._active = None

    def reset(self) -> None:
        """Discard all engine state (equivalent to :meth:`cancel` today).

        Kept as a distinct method so future milestones can extend it to
        clear additional accumulated state without changing callers.
        """
        self._active = None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def has_active_stroke(self) -> bool:
        """Return whether a stroke is currently being drawn."""
        return self._active is not None

    def current_stroke(self) -> Stroke | None:
        """Return the active (in-progress) stroke, or ``None`` if idle.

        The live stroke is returned by reference (no copy), keeping the
        per-frame path allocation-free.
        """
        return self._active

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _point_from_event(self, event: GestureEvent) -> Point:
        """Build a :class:`Point` from a gesture event's index fingertip.

        Pressure is fixed at :data:`DEFAULT_POINT_PRESSURE` (pressure
        detection is a future milestone). ``timestamp`` and ``velocity``
        are carried straight from the event -- both are already computed
        by the gesture engine, so no finite differences are recomputed.

        Raises:
            InvalidStrokeError: If the event has no landmarks.
        """
        landmarks = event.landmarks
        if not landmarks:
            raise InvalidStrokeError(
                "GestureEvent carries no landmarks; cannot derive a drawing point."
            )
        x, y, _z = landmarks[DRAWING_LANDMARK_INDEX]
        return Point(
            x=x,
            y=y,
            pressure=DEFAULT_POINT_PRESSURE,
            timestamp=event.timestamp,
            velocity=event.velocity,
        )
