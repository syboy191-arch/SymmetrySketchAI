# SymmetrySketch AI

# Project Tree

Last Updated: July 2026

This document reflects the **current repository structure**.

The GitHub repository is the authoritative source of truth.

Only update this file after the repository structure changes.

---

# Repository Structure

```text
SymmetrySketchAI/

│
├── README.md
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
│
├── ai/
│
├── assets/
│
├── config/
│   ├── __init__.py
│   ├── app_config.py
│   ├── tracker_config.py
│   ├── renderer_config.py
│   ├── brush_config.py
│   ├── export_config.py
│   └── ui_config.py
│
├── core/
│   ├── __init__.py
│   ├── constants.py
│   ├── dependency_container.py
│   ├── enums.py
│   ├── events.py
│   ├── exceptions.py
│   ├── logger.py
│   ├── paths.py
│   └── utils/
│
├── docs/
│   ├── AI_CONTEXT.md
│   ├── ARCHITECTURE.md
│   ├── CHANGELOG.md
│   ├── MODULE_STATUS.md
│   ├── NEXT_MODULE.md
│   ├── PROJECT_RULES.md
│   └── PROJECT_TREE.md
│
├── domain/
│   ├── __init__.py
│   └── entities/
│       ├── __init__.py
│       ├── brush.py
│       ├── canvas_state.py
│       ├── gesture_event.py
│       ├── ids.py
│       ├── layer.py
│       ├── point.py
│       ├── project.py
│       └── stroke.py
│
├── drawing/
│   ├── __init__.py
│   └── stroke_engine.py
│
├── examples/
│   ├── __init__.py
│   └── vision_demo.py
│
├── export/
│
├── models/
│
├── persistence/
│
├── tests/
│   ├── __init__.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_vision_pipeline.py
│   │
│   └── unit/
│       ├── __init__.py
│       ├── test_brush.py
│       ├── test_canvas_state.py
│       ├── test_events.py
│       ├── test_gesture_classifier.py
│       ├── test_gesture_engine.py
│       ├── test_gesture_event.py
│       ├── test_hand.py
│       ├── test_landmarks.py
│       ├── test_layer.py
│       ├── test_point.py
│       ├── test_project.py
│       ├── test_smoothing.py
│       ├── test_stroke.py
│       ├── test_stroke_engine.py
│       ├── test_tracker.py
│       └── test_tracker_result.py
│
├── timeline/
│
├── ui/
│
└── vision/
    ├── __init__.py
    ├── gesture_classifier.py
    ├── gesture_engine.py
    ├── hand.py
    ├── landmarks.py
    ├── smoothing.py
    ├── tracker.py
    ├── tracker_result.py
    │
    ├── models/
    │   └── hand_landmarker.task
    │
    └── utils/
        ├── __init__.py
        └── coordinate_utils.py
```

---

# Folder Responsibilities

## core/

Shared infrastructure used throughout the application.

Includes:

- Logging
- Events
- Dependency Injection
- Constants
- Exceptions
- Shared Enums

---

## config/

Application configuration.

Each subsystem owns its own configuration module.

---

## domain/

Pure business objects.

Contains no OpenCV, MediaPipe, rendering, or UI logic.

---

## vision/

Computer Vision subsystem.

Responsible only for:

- Camera
- MediaPipe
- Hand Tracking
- Gesture Recognition

Feature Frozen.

---

## drawing/

Drawing pipeline.

Currently contains:

- Stroke Engine

Future:

- Stroke Manager
- Renderer
- Symmetry Engine
- Brush Engine

---

## tests/

Contains

- Unit Tests
- Integration Tests

No production code.

---

## docs/

Living project documentation.

Always keep synchronized with the repository.

---

## examples/

Runnable demonstrations.

Current:

- Vision Integration Demo

Future:

- Drawing Demo
- Renderer Demo
- Symmetry Demo

---

# Repository Rules

- Never duplicate existing modules.
- Never regenerate completed subsystems.
- Keep Vision isolated from Drawing.
- Keep Domain independent.
- Maintain Clean Architecture.
- Update this file whenever the folder structure changes.

---

# Current Development Phase

Drawing Pipeline

Current Milestone

Milestone 5A — Stroke Engine

Next Milestone

Milestone 5B — Stroke Manager