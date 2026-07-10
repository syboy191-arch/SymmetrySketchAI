"""Strongly-typed identifier wrappers.

Design rationale:
    Using raw ``str`` for every kind of id invites bugs where a
    ``LayerId`` is accidentally passed to a function expecting a
    ``StrokeId`` -- both are just strings to the type checker. Wrapping
    each id kind with ``typing.NewType`` costs nothing at runtime (they
    remain plain ``str`` instances) but lets static analysis (mypy/pyright)
    catch these mistakes before they ship.
"""

from __future__ import annotations

import uuid
from typing import NewType

StrokeId = NewType("StrokeId", str)
LayerId = NewType("LayerId", str)
ProjectId = NewType("ProjectId", str)


def new_stroke_id() -> StrokeId:
    """Generate a new globally-unique :class:`StrokeId`."""
    return StrokeId(str(uuid.uuid4()))


def new_layer_id() -> LayerId:
    """Generate a new globally-unique :class:`LayerId`."""
    return LayerId(str(uuid.uuid4()))


def new_project_id() -> ProjectId:
    """Generate a new globally-unique :class:`ProjectId`."""
    return ProjectId(str(uuid.uuid4()))
