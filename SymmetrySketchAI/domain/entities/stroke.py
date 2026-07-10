"""The :class:`Stroke` entity -- the single source of truth for a drawn mark.

Design rationale:
    The entire rendering model hinges on this class: "never draw
    permanently onto the canvas... represent every drawing action as a
    Stroke object... the renderer rebuilds each frame from the current
    collection of strokes." Concretely, that means:

      * A ``Stroke`` must be fully self-describing: its points, brush
        type, color, width, symmetry mode it was created under, and the
        layer/timestamp it belongs to. A renderer with only a list of
        ``Stroke`` objects (and nothing else) must be able to reproduce
        the exact drawing.
      * ``Stroke`` has *identity* (a ``StrokeId``) and a lifecycle --
        unlike ``Point``, two strokes with identical geometry are still
        distinct strokes. This is why it's a regular (non-frozen)
        dataclass with an id, not a value object.
      * Points are stored internally as a list (append-heavy during live
        gesture capture) but only ever exposed externally as an
        immutable ``tuple`` via the ``points`` property. This preserves
        the non-destructive guarantee: no external module (renderer, AI
        corrector, exporter) can mutate a stroke's geometry by holding a
        reference to its point collection.
      * Mutation of a *finalized* stroke (used by AI correction, "edit
        stroke" in the timeline) goes through explicit, validated methods
        (`replace_points`) rather than direct list access, so every
        mutation path can enforce invariants (non-empty, etc.) in one place.
      * `is_finalized` distinguishes an in-progress stroke (still being
        streamed from the gesture engine) from a committed one, since
        several consumers (timeline, symmetry engine's "commit" step)
        care about this distinction.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from core.enums import BrushType, SymmetryMode
from core.exceptions import InvalidStrokeError
from domain.entities.ids import LayerId, StrokeId, new_stroke_id
from domain.entities.point import Point


@dataclass(slots=True)
class Stroke:
    """A single drawn mark: an ordered sequence of points plus styling.

    Attributes:
        stroke_id: Globally-unique identifier for this stroke.
        layer_id: The layer this stroke belongs to.
        brush_type: Which brush engine rendered/should render this stroke.
        color_rgba: Base color as ``(r, g, b, a)``, each in ``[0, 255]``
            for r/g/b and ``[0, 1]`` for alpha. Individual brushes (e.g.
            rainbow) may derive per-segment colors from this base at
            render time without mutating it.
        base_width: Base stroke width in pixels before pressure/velocity
            modulation is applied by the brush engine.
        symmetry_mode: The symmetry mode active when this stroke was
            created. Stored so replay and re-render are faithful even if
            the user later changes the *current* symmetry mode.
        is_symmetry_echo: ``True`` if this stroke is a generated mirror/
            copy of a user-drawn "source" stroke, ``False`` if it is the
            original. Lets the UI/timeline treat the source and its
            echoes as a logical group without needing a separate join
            table for the common case.
        source_stroke_id: If ``is_symmetry_echo`` is ``True``, the id of
            the original stroke this one was generated from.
        created_at: Wall-clock Unix timestamp of stroke creation, used
            for timeline ordering and timelapse export.
        is_finalized: ``False`` while a stroke is still being actively
            drawn (points still streaming in from the gesture engine);
            ``True`` once committed to the stroke manager/history.
    """

    layer_id: LayerId
    brush_type: BrushType
    color_rgba: tuple[int, int, int, float] = (0, 0, 0, 1.0)
    base_width: float = 6.0
    symmetry_mode: SymmetryMode = SymmetryMode.NONE
    is_symmetry_echo: bool = False
    source_stroke_id: StrokeId | None = None
    stroke_id: StrokeId = field(default_factory=new_stroke_id)
    created_at: float = field(default_factory=time.time)
    is_finalized: bool = False
    _points: list[Point] = field(default_factory=list)

    @property
    def points(self) -> tuple[Point, ...]:
        """Immutable view of this stroke's points.

        Returning a tuple (rather than the internal list) prevents
        external code from appending/removing points behind the
        stroke's back, which would silently violate the non-destructive
        editing guarantee.
        """
        return tuple(self._points)

    @property
    def is_empty(self) -> bool:
        """Whether this stroke has no points yet."""
        return len(self._points) == 0

    def append_point(self, point: Point) -> None:
        """Append a new sample point to an in-progress stroke.

        Raises:
            InvalidStrokeError: If called on a stroke already marked
                finalized. Finalized strokes must be modified only via
                :meth:`replace_points`, so every mutation of committed
                data is explicit and auditable (important for undo/redo
                and AI correction, which need to know exactly what
                changed).
        """
        if self.is_finalized:
            raise InvalidStrokeError(
                f"Cannot append_point to finalized stroke {self.stroke_id}; "
                "use replace_points() instead."
            )
        self._points.append(point)

    def finalize(self) -> None:
        """Mark this stroke as complete and immutable-by-default.

        Raises:
            InvalidStrokeError: If the stroke has no points, since a
                zero-point stroke has no geometry to render, export, or
                replay -- treated as a construction error rather than a
                degenerate-but-valid stroke.
        """
        if self.is_empty:
            raise InvalidStrokeError(
                f"Cannot finalize stroke {self.stroke_id} with zero points."
            )
        self.is_finalized = True

    def replace_points(self, new_points: list[Point]) -> None:
        """Replace this stroke's entire point sequence.

        This is the sanctioned mutation path for already-finalized
        strokes, used by:
          * AI correction (e.g. snapping a hand-drawn circle to a
            perfect one).
          * Timeline "edit stroke" commands.
          * Symmetry re-projection when a source stroke is edited and
            its echoes must be regenerated.

        Args:
            new_points: The full replacement point sequence. Must be
                non-empty.

        Raises:
            InvalidStrokeError: If ``new_points`` is empty.
        """
        if not new_points:
            raise InvalidStrokeError(
                f"Cannot replace_points on stroke {self.stroke_id} with an "
                "empty list."
            )
        self._points = list(new_points)

    def clone(self, *, as_new_stroke: bool = True) -> "Stroke":
        """Return a deep-enough copy of this stroke.

        Args:
            as_new_stroke: If ``True`` (default), the clone receives a
                fresh :class:`StrokeId` and is suitable for use by
                "duplicate stroke" or as a symmetry echo. If ``False``,
                the clone keeps the same id -- used internally when a
                module needs a mutable working copy without changing
                stroke identity (e.g. building an AI-corrected preview
                before deciding whether to commit it).

        Returns:
            A new :class:`Stroke` instance. Points are immutable
            :class:`Point` objects, so copying the list is a sufficient
            deep copy -- no point's internal state can be mutated later
            to corrupt the original.
        """
        cloned = Stroke(
            layer_id=self.layer_id,
            brush_type=self.brush_type,
            color_rgba=self.color_rgba,
            base_width=self.base_width,
            symmetry_mode=self.symmetry_mode,
            is_symmetry_echo=self.is_symmetry_echo,
            source_stroke_id=self.source_stroke_id,
            is_finalized=self.is_finalized,
        )
        cloned._points = list(self._points)
        if not as_new_stroke:
            cloned.stroke_id = self.stroke_id
        return cloned

    def bounding_box(self) -> tuple[float, float, float, float]:
        """Return the axis-aligned bounding box as ``(min_x, min_y, max_x, max_y)``.

        Raises:
            InvalidStrokeError: If the stroke has no points, since a
                bounding box is undefined for empty geometry.
        """
        if self.is_empty:
            raise InvalidStrokeError(
                f"Cannot compute bounding_box for empty stroke {self.stroke_id}."
            )
        xs = [p.x for p in self._points]
        ys = [p.y for p in self._points]
        return (min(xs), min(ys), max(xs), max(ys))
