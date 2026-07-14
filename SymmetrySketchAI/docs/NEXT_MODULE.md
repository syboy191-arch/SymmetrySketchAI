# Next Development Task

Last Updated: July 2026

---

# Current Project Status

Current Milestone

> **Milestone 5A — Stroke Engine** ✅ Complete

Current Development Phase

> **Drawing Pipeline**

The Vision subsystem is complete and feature frozen.

The project has successfully transitioned from computer vision into the drawing architecture.

The next milestone continues building the drawing subsystem.

---

# Next Milestone

## Milestone 5B — Stroke Manager

---

# Objective

Implement the Stroke Manager.

The Stroke Manager will become the central repository for every completed Stroke object.

It is responsible for managing strokes.

It is **NOT** responsible for rendering.

It is **NOT** responsible for symmetry.

It is **NOT** responsible for replay.

Those responsibilities belong to future modules.

---

# Responsibilities

The Stroke Manager should support

- Store completed strokes
- Remove strokes
- Retrieve strokes
- Clear all strokes
- Track active stroke
- Track completed strokes
- Prepare for Undo
- Prepare for Redo
- Layer association
- Stroke lookup

---

# Expected Data Flow

Camera

↓

Tracker

↓

Gesture Engine

↓

GestureEvent

↓

Stroke Engine

↓

Stroke Manager

↓

Renderer (Future)

↓

Canvas

---

# Files to Create

Create ONLY

```text
drawing/

    stroke_manager.py
```

Generate

```text
tests/

    unit/

        test_stroke_manager.py
```

No additional modules.

No renderer.

No symmetry.

No replay.

---

# Existing Modules That Must Be Reused

Reuse existing

- Stroke
- Point
- Brush
- Layer
- Stroke Engine

Do NOT duplicate any domain entities.

---

# Files That Must Not Change

Do not modify

```text
vision/

core/

config/

domain/

examples/

stroke_engine.py
```

unless a critical bug prevents Milestone 5B from functioning.

---

# Architecture Rules

The Stroke Manager owns Stroke storage.

The Renderer will never own strokes.

The Renderer will request strokes from the Stroke Manager.

The Stroke Manager must not know anything about

- OpenCV
- MediaPipe
- Camera
- Rendering
- UI

Keep it completely independent.

---

# Future Compatibility

Design the API for future support of

- Undo
- Redo
- Replay
- Timeline
- Layer editing
- SVG export
- PNG export
- AI editing

Do not implement those features.

Only prepare the architecture.

---

# Testing

Generate unit tests covering

- Add Stroke
- Remove Stroke
- Clear All
- Multiple Strokes
- Empty Manager
- Active Stroke
- Invalid Removal
- Retrieval APIs

Do not require

- Camera
- MediaPipe
- OpenCV
- GUI

---

# Definition of Done

Milestone 5B is complete only if

- Stroke Manager stores strokes correctly.
- Existing Stroke objects are reused.
- No Vision code is modified.
- No Renderer is implemented.
- Unit tests pass.
- Documentation is updated.

---

# Workflow

Before implementing the milestone

1. Read the GitHub repository.
2. Read README.md.
3. Read every file inside docs/.
4. Inspect the current architecture.

Do not narrate this process.

Use the repository as the only source of truth.

---

# Expected Deliverables

- stroke_manager.py
- test_stroke_manager.py
- Updated documentation
- Pull Request summary
- Recommended Git commit message

---

# Milestone After 5B

Milestone 5C — Renderer

The Renderer will be responsible for drawing every Stroke onto the canvas.

It will never permanently modify pixels.

Every frame will be rendered entirely from Stroke objects.

This architectural decision enables

- Undo
- Replay
- SVG Export
- AI Editing
- Symmetry Rendering

without redesigning the project.