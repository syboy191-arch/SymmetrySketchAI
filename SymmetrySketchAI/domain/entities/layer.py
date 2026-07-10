"""Domain entity representing a single drawing layer.

A Layer is a pure domain object: it owns a collection of strokes and a set
of presentation-agnostic properties (visibility, opacity, blend mode,
z-index, etc.). It performs NO rendering, has NO knowledge of the UI layer,
and has NO knowledge of undo/redo history. Those concerns belong to other
layers of the architecture (application/services, infrastructure/rendering).

This module intentionally reuses the project's existing single sources of
truth rather than redefining them:

- Blend modes come from :class:`core.enums.LayerBlendMode`, not a
  locally-defined enum, so there is exactly one blend-mode vocabulary in
  the codebase.
- All Layer-specific errors derive from :class:`core.exceptions.DrawingError`
  (the project's domain/drawing error root), never from bare ``Exception``.
- Layer identifiers are produced via :func:`domain.entities.ids.new_layer_id`,
  matching the ``NewType``-based identifier scheme used everywhere else.
- Bounding-box geometry is delegated to :meth:`domain.entities.stroke.Stroke.bounding_box`
  per stroke rather than recomputed here, so there is exactly one place
  that knows how to compute a bounding box from a point sequence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator

from core.enums import LayerBlendMode
from core.exceptions import DrawingError
from domain.entities.ids import LayerId, new_layer_id
from domain.entities.stroke import Stroke

# --------------------------------------------------------------------------
# Constants (no magic numbers)
# --------------------------------------------------------------------------

MIN_OPACITY: float = 0.0
MAX_OPACITY: float = 1.0
DEFAULT_OPACITY: float = 1.0
DEFAULT_LAYER_NAME: str = "Untitled Layer"
DEFAULT_Z_INDEX: int = 0


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class LayerValidationError(DrawingError):
    """Raised when constructing or mutating a Layer with invalid data."""


class LayerOperationError(DrawingError):
    """Raised when an operation on a Layer cannot be completed logically
    (e.g. removing a stroke that does not exist)."""


# --------------------------------------------------------------------------
# Value object: bounding box
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class BoundingBox:
    """An axis-aligned bounding box in canvas space."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise LayerValidationError(
                "BoundingBox min coordinates must not exceed max coordinates: "
                f"got min=({self.min_x}, {self.min_y}), "
                f"max=({self.max_x}, {self.max_y})"
            )

    @property
    def width(self) -> float:
        """Width of the bounding box."""
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        """Height of the bounding box."""
        return self.max_y - self.min_y

    def union(self, other: "BoundingBox") -> "BoundingBox":
        """Return the smallest bounding box that contains both boxes."""
        return BoundingBox(
            min_x=min(self.min_x, other.min_x),
            min_y=min(self.min_y, other.min_y),
            max_x=max(self.max_x, other.max_x),
            max_y=max(self.max_y, other.max_y),
        )


# --------------------------------------------------------------------------
# Entity: Layer
# --------------------------------------------------------------------------

@dataclass(slots=True)
class Layer:
    """A single drawing layer within a document.

    A Layer owns an ordered collection of :class:`Stroke` objects along with
    presentation metadata (visibility, lock state, opacity, blend mode,
    z-index) and bookkeeping timestamps. It has no awareness of rendering,
    UI, or undo/redo history -- those are the responsibility of higher
    application layers.
    """

    layer_id: LayerId = field(default_factory=new_layer_id)
    name: str = DEFAULT_LAYER_NAME
    visible: bool = True
    locked: bool = False
    opacity: float = DEFAULT_OPACITY
    blend_mode: LayerBlendMode = LayerBlendMode.NORMAL
    z_index: int = DEFAULT_Z_INDEX
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _strokes: list[Stroke] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._validate_name(self.name)
        self._validate_opacity(self.opacity)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise LayerValidationError("Layer name must be a non-empty string.")

    @staticmethod
    def _validate_opacity(opacity: float) -> None:
        if not (MIN_OPACITY <= opacity <= MAX_OPACITY):
            raise LayerValidationError(
                f"Layer opacity must be between {MIN_OPACITY} and "
                f"{MAX_OPACITY}, got {opacity}."
            )

    def _touch(self) -> None:
        """Update the last-modified timestamp to now."""
        self.modified_at = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Property setters with validation
    # ------------------------------------------------------------------

    def rename(self, name: str) -> None:
        """Rename the layer."""
        self._validate_name(name)
        self.name = name
        self._touch()

    def set_opacity(self, opacity: float) -> None:
        """Set the layer opacity, validating the range."""
        self._validate_opacity(opacity)
        self.opacity = opacity
        self._touch()

    def set_blend_mode(self, blend_mode: LayerBlendMode) -> None:
        """Set the layer's blend mode."""
        if not isinstance(blend_mode, LayerBlendMode):
            raise LayerValidationError(
                f"blend_mode must be a LayerBlendMode, got {type(blend_mode)!r}."
            )
        self.blend_mode = blend_mode
        self._touch()

    def set_visible(self, visible: bool) -> None:
        """Toggle layer visibility."""
        self.visible = bool(visible)
        self._touch()

    def set_locked(self, locked: bool) -> None:
        """Toggle whether the layer is locked against edits."""
        self.locked = bool(locked)
        self._touch()

    def set_z_index(self, z_index: int) -> None:
        """Set the layer's stacking order index."""
        if not isinstance(z_index, int):
            raise LayerValidationError(
                f"z_index must be an int, got {type(z_index)!r}."
            )
        self.z_index = z_index
        self._touch()

    # ------------------------------------------------------------------
    # Stroke collection management
    # ------------------------------------------------------------------

    def add_stroke(self, stroke: Stroke) -> None:
        """Append a stroke to this layer.

        Raises:
            LayerOperationError: if the layer is locked.
            LayerValidationError: if ``stroke`` is not a :class:`Stroke`.
        """
        if self.locked:
            raise LayerOperationError("Cannot add a stroke to a locked layer.")
        if not isinstance(stroke, Stroke):
            raise LayerValidationError(
                f"add_stroke expects a Stroke, got {type(stroke)!r}."
            )
        self._strokes.append(stroke)
        self._touch()

    def remove_stroke(self, stroke: Stroke) -> None:
        """Remove a specific stroke from this layer.

        Raises:
            LayerOperationError: if the layer is locked, or the stroke is
                not present in this layer.
        """
        if self.locked:
            raise LayerOperationError("Cannot remove a stroke from a locked layer.")
        for index, existing in enumerate(self._strokes):
            if existing.stroke_id == stroke.stroke_id:
                del self._strokes[index]
                self._touch()
                return
        raise LayerOperationError(
            "Cannot remove stroke: it is not present in this layer."
        )

    def clear(self) -> None:
        """Remove all strokes from this layer.

        Raises:
            LayerOperationError: if the layer is locked.
        """
        if self.locked:
            raise LayerOperationError("Cannot clear a locked layer.")
        self._strokes.clear()
        self._touch()

    def stroke_count(self) -> int:
        """Return the number of strokes currently on this layer."""
        return len(self._strokes)

    @property
    def strokes(self) -> tuple[Stroke, ...]:
        """Read-only view of the strokes on this layer, in draw order."""
        return tuple(self._strokes)

    def __iter__(self) -> Iterator[Stroke]:
        return iter(self._strokes)

    def __len__(self) -> int:
        return self.stroke_count()

    # ------------------------------------------------------------------
    # Geometry
    # ------------------------------------------------------------------

    def bounding_box(self) -> BoundingBox | None:
        """Compute the axis-aligned bounding box covering every stroke.

        Returns:
            The union bounding box of all strokes' points, or ``None`` if
            the layer has no strokes (or no strokes have any points).
        """
        box: BoundingBox | None = None
        for stroke in self._strokes:
            if stroke.is_empty:
                continue
            # Reuse Stroke.bounding_box() rather than recomputing min/max
            # over points here, so there is a single source of truth for
            # per-stroke bounding-box geometry.
            min_x, min_y, max_x, max_y = stroke.bounding_box()
            stroke_box = BoundingBox(min_x=min_x, min_y=min_y, max_x=max_x, max_y=max_y)
            box = stroke_box if box is None else box.union(stroke_box)
        return box

    # ------------------------------------------------------------------
    # Cloning
    # ------------------------------------------------------------------

    def clone(self, *, new_id: bool = True) -> "Layer":
        """Return a deep-ish copy of this layer.

        The stroke list is copied into a new list (the individual
        :class:`Stroke` objects themselves are shared, matching how
        ``Stroke.clone`` is used elsewhere in the codebase); callers
        needing full isolation of stroke geometry should clone strokes
        individually upstream. Timestamps are refreshed for the clone.

        Args:
            new_id: If True (default), the clone receives a fresh
                :class:`LayerId`. If False, the clone keeps the same id
                (useful for snapshotting for history/undo purposes).
        """
        now = datetime.now(timezone.utc)
        return Layer(
            layer_id=new_layer_id() if new_id else self.layer_id,
            name=self.name,
            visible=self.visible,
            locked=self.locked,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            z_index=self.z_index,
            created_at=self.created_at,
            modified_at=now,
            _strokes=list(self._strokes),
        )
