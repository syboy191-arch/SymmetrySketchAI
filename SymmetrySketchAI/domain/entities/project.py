"""Domain entity representing a single saved drawing (a "project").

A Project is a pure domain aggregate: it owns an ordered collection of
:class:`domain.entities.layer.Layer` objects plus a :class:`CanvasState`
snapshot and bookkeeping metadata (name, schema version, timestamps). It
performs NO serialization, has NO knowledge of JSON/file formats, and has
NO dependency on the persistence subsystem -- turning a Project into
bytes on disk (and back) is the job of an infrastructure-level
``persistence`` module that consumes/produces a Project, not this module.

This module intentionally reuses the project's existing single sources of
truth rather than redefining them:

- Project identifiers are produced via
  :func:`domain.entities.ids.new_project_id`, matching the
  ``NewType``-based identifier scheme used everywhere else.
- The default schema version comes from
  :data:`core.constants.PROJECT_SCHEMA_VERSION`, not a locally-duplicated
  version string.
- Missing-layer lookups reuse :class:`core.exceptions.LayerNotFoundError`
  (already defined for exactly this purpose) rather than a new exception.
- All other Project-specific errors derive from
  :class:`core.exceptions.DrawingError`, never from bare ``Exception``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator, NamedTuple

from core.constants import PROJECT_SCHEMA_VERSION
from core.exceptions import DrawingError, LayerNotFoundError
from domain.entities.canvas_state import CanvasState
from domain.entities.ids import LayerId, ProjectId, new_project_id
from domain.entities.layer import Layer

# --------------------------------------------------------------------------
# Constants (no magic numbers)
# --------------------------------------------------------------------------

DEFAULT_PROJECT_NAME: str = "Untitled Project"


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class ProjectValidationError(DrawingError):
    """Raised when constructing or mutating a Project with invalid data."""


class ProjectOperationError(DrawingError):
    """Raised when an operation on a Project cannot be completed logically
    (e.g. moving a layer to an out-of-range position).
    """


# --------------------------------------------------------------------------
# Value object: statistics snapshot
# --------------------------------------------------------------------------

class ProjectStatistics(NamedTuple):
    """A point-in-time summary of a project's size/complexity."""

    layer_count: int
    visible_layer_count: int
    stroke_count: int
    point_count: int


# --------------------------------------------------------------------------
# Entity: Project
# --------------------------------------------------------------------------

@dataclass(slots=True)
class Project:
    """A single saved drawing: metadata, layers, and editor state.

    A Project owns an ordered collection of :class:`Layer` objects (draw
    order == list order) along with a :class:`CanvasState` snapshot and
    bookkeeping timestamps. It has no awareness of file formats, undo/redo
    history, or rendering -- those are the responsibility of other
    application layers.
    """

    project_id: ProjectId = field(default_factory=new_project_id)
    name: str = DEFAULT_PROJECT_NAME
    schema_version: str = PROJECT_SCHEMA_VERSION
    canvas_state: CanvasState = field(default_factory=CanvasState)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _layers: list[Layer] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self._validate_name(self.name)
        self._validate_schema_version(self.schema_version)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ProjectValidationError("Project name must be a non-empty string.")

    @staticmethod
    def _validate_schema_version(schema_version: str) -> None:
        if not isinstance(schema_version, str) or not schema_version.strip():
            raise ProjectValidationError(
                "Project schema_version must be a non-empty string."
            )

    def _touch(self) -> None:
        """Update the last-modified timestamp to now."""
        self.modified_at = datetime.now(timezone.utc)

    def _index_of(self, layer_id: LayerId) -> int:
        for index, layer in enumerate(self._layers):
            if layer.layer_id == layer_id:
                return index
        raise LayerNotFoundError(
            f"No layer with id {layer_id!r} exists in project {self.project_id!r}."
        )

    # ------------------------------------------------------------------
    # Property setters with validation
    # ------------------------------------------------------------------

    def rename(self, name: str) -> None:
        """Rename the project."""
        self._validate_name(name)
        self.name = name
        self._touch()

    # ------------------------------------------------------------------
    # Layer collection management
    # ------------------------------------------------------------------

    def add_layer(self, layer: Layer) -> None:
        """Append a layer to the top of the project's layer stack.

        Raises:
            ProjectValidationError: if ``layer`` is not a :class:`Layer`.
        """
        if not isinstance(layer, Layer):
            raise ProjectValidationError(
                f"add_layer expects a Layer, got {type(layer)!r}."
            )
        self._layers.append(layer)
        self._touch()

    def remove_layer(self, layer_id: LayerId) -> None:
        """Remove the layer with the given id.

        Raises:
            LayerNotFoundError: if no layer with ``layer_id`` exists.
        """
        index = self._index_of(layer_id)
        del self._layers[index]
        if self.canvas_state.current_layer_id == layer_id:
            self.canvas_state.current_layer_id = None
        self._touch()

    def duplicate_layer(self, layer_id: LayerId) -> Layer:
        """Duplicate the layer with the given id and insert the copy
        directly above the original.

        Returns:
            The newly created :class:`Layer` duplicate.

        Raises:
            LayerNotFoundError: if no layer with ``layer_id`` exists.
        """
        index = self._index_of(layer_id)
        duplicate = self._layers[index].clone(new_id=True)
        self._layers.insert(index + 1, duplicate)
        self._touch()
        return duplicate

    def move_layer(self, layer_id: LayerId, new_index: int) -> None:
        """Move the layer with the given id to ``new_index`` in the stack.

        Args:
            layer_id: The layer to move.
            new_index: The target position in the layer list.

        Raises:
            LayerNotFoundError: if no layer with ``layer_id`` exists.
            ProjectOperationError: if ``new_index`` is out of range.
        """
        current_index = self._index_of(layer_id)
        if not (0 <= new_index < len(self._layers)):
            raise ProjectOperationError(
                f"move_layer target index {new_index} is out of range for "
                f"{len(self._layers)} layer(s)."
            )
        layer = self._layers.pop(current_index)
        self._layers.insert(new_index, layer)
        self._touch()

    def find_layer(self, layer_id: LayerId) -> Layer | None:
        """Return the layer with the given id, or ``None`` if not found.

        Unlike :meth:`remove_layer`/:meth:`duplicate_layer`/:meth:`move_layer`,
        which require the layer to exist, this is a safe lookup for
        callers that need to check presence without handling an exception.
        """
        for layer in self._layers:
            if layer.layer_id == layer_id:
                return layer
        return None

    @property
    def layers(self) -> tuple[Layer, ...]:
        """Read-only view of the project's layers, in draw order."""
        return tuple(self._layers)

    def layer_count(self) -> int:
        """Return the number of layers currently in the project."""
        return len(self._layers)

    def __iter__(self) -> Iterator[Layer]:
        return iter(self._layers)

    def __len__(self) -> int:
        return self.layer_count()

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(self) -> ProjectStatistics:
        """Compute a point-in-time summary of this project's size.

        Returns:
            A :class:`ProjectStatistics` with layer/stroke/point counts.
        """
        stroke_count = 0
        point_count = 0
        visible_layer_count = 0
        for layer in self._layers:
            if layer.visible:
                visible_layer_count += 1
            for stroke in layer:
                stroke_count += 1
                point_count += len(stroke.points)
        return ProjectStatistics(
            layer_count=len(self._layers),
            visible_layer_count=visible_layer_count,
            stroke_count=stroke_count,
            point_count=point_count,
        )
