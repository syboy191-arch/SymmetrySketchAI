"""The drawing subsystem: converts recognized gestures into editable strokes.

Milestone 5A introduces the :class:`~drawing.stroke_engine.StrokeEngine`,
the first stage of the drawing pipeline:

    GestureEvent -> StrokeEngine -> Stroke -> StrokeManager (future)
    -> Renderer (future)

Only the stroke *lifecycle* lives here. Rendering, symmetry, history,
export, and AI correction are explicitly out of scope and arrive in
later milestones.
"""

from __future__ import annotations

from drawing.stroke_engine import StrokeEngine

__all__ = ["StrokeEngine"]
