# 🎨 SymmetrySketch AI

> A production-quality AI-powered desktop application for creating symmetrical digital artwork using real-time hand tracking, gesture recognition, and computer vision.

---

# 📖 Overview

SymmetrySketch AI is a modular desktop application written in **Python** that enables users to draw symmetrical artwork using hand gestures captured from a webcam.

Unlike traditional virtual painter projects, SymmetrySketch AI is designed as a **professional software engineering project**, emphasizing:

- Clean Architecture
- Domain-Driven Design (DDD)
- SOLID Principles
- Event-Driven Architecture
- Object-Oriented Programming
- Real-Time Computer Vision
- AI-assisted Drawing
- Extensibility and Maintainability

The project is being developed incrementally with production-quality standards, comprehensive documentation, unit tests, and a scalable architecture suitable for long-term growth.

---

# ✨ Vision

The goal is to create a modern AI-powered creative application capable of:

- Hand gesture drawing
- Real-time symmetry rendering
- Replayable vector-based artwork
- AI-assisted shape correction
- SVG/PNG export
- Unlimited undo/redo
- Layer management
- Timeline editing
- Plugin support
- Future cloud synchronization and collaboration

---

# 🎯 Project Goals

This project is intended to demonstrate professional skills in:

- Python Software Engineering
- Computer Vision
- MediaPipe Tasks API
- OpenCV
- Real-Time Graphics
- Software Architecture
- Design Patterns
- AI Integration
- Testing
- Documentation

---

# 🏗️ High-Level Architecture

```text
Camera
    │
    ▼
Vision Layer
    │
    ▼
Gesture Recognition
    │
    ▼
Stroke Engine
    │
    ▼
Stroke Manager
    │
    ▼
Symmetry Engine
    │
    ▼
Brush Engine
    │
    ▼
Renderer
    │
    ▼
Canvas Widget
    │
    ▼
Display
```

---

# 🎨 Rendering Philosophy

Unlike traditional painting applications,

**nothing is permanently drawn onto the canvas.**

Every drawing action creates a **Stroke** object.

Rendering occurs every frame from stored Stroke objects.

Advantages:

- Unlimited Undo/Redo
- SVG Export
- Replay
- Editing
- AI Correction
- Save/Load
- Timeline Support

---

# 🧱 Software Architecture

The project follows:

- Clean Architecture
- Domain-Driven Design (DDD)
- SOLID Principles
- Event-Driven Architecture
- Object-Oriented Design

Business logic remains independent from:

- UI
- OpenCV
- MediaPipe
- Rendering
- Export
- Persistence

---

# 📁 Project Structure

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

# 📦 Core Modules

## Core

Shared infrastructure used by the entire application.

Includes:

- Logging
- Dependency Injection
- Event System
- Configuration
- Constants
- Exceptions
- Enums
- Path Management

---

## Domain

Contains pure business objects.

No OpenCV.

No MediaPipe.

No UI.

No rendering.

Includes:

- Stroke
- Layer
- Brush
- Project
- CanvasState
- GestureEvent

---

## Vision

Responsible only for:

- Camera
- MediaPipe Tasks API
- Hand Tracking
- Gesture Recognition

Produces:

TrackerResult

Consumes:

Nothing from Drawing or Rendering.

---

## Drawing (Future)

Responsible for:

GestureEvent

↓

Stroke creation

↓

Stroke management

---

## Renderer (Future)

Responsible only for converting Stroke objects into pixels.

Never owns artwork.

---

## Timeline (Future)

Supports:

- Replay
- Undo
- Redo
- Editing

---

## AI (Future)

Will include:

- Shape Detection
- Shape Correction
- Symmetry Correction
- Drawing Assistance

---

# 🧠 Technology Stack

## Language

- Python 3.13+

## Computer Vision

- OpenCV
- MediaPipe Tasks API

## Data Structures

- Dataclasses
- Enums
- Type Hints

## Testing

- PyTest

## Graphics

- NumPy

## Documentation

- Markdown

---

------------------------------------------------------------------------

# 🧠 Technology Stack

-   Python 3.13+
-   OpenCV
-   MediaPipe Tasks API
-   NumPy
-   PyTest
-   Dataclasses
-   Type Hints
-   Git & GitHub

------------------------------------------------------------------------


------------------------------------------------------------------------

# 🔄 Development Workflow

The GitHub repository is the **single source of truth**.

Each milestone follows:

1.  Implement one subsystem
2.  Review architecture
3.  Run tests
4.  Update documentation
5.  Commit & Push
6.  Begin next milestone

------------------------------------------------------------------------


# 📐 Engineering Standards

Every module follows:

- SOLID Principles
- Type Hints
- Dataclasses
- Docstrings
- Small Methods
- Single Responsibility Principle
- Modular Design
- Comprehensive Unit Tests

---

# 🧪 Testing

The project uses **PyTest** for unit testing.

Tests are located in:

```text
tests/unit/
```

Each module includes corresponding unit tests where applicable.

---

------------------------------------------------------------------------

# 🚀 Installation

``` bash
git clone <https://github.com/syboy191-arch/SymmetrySketchAI>
cd SymmetrySketchAI

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

------------------------------------------------------------------------

------------------------------------------------------------------------

# ▶ Running

Vision demo:

``` bash
python -m examples.vision_demo
```

Run tests:

``` bash
pytest
```

------------------------------------------------------------------------


# 🚀 Current Development Status

------------------------------------------------------------------------

# ✅ Milestone Progress

  Milestone             Status
  --------------------- --------
  Core Foundation       ✅
  Domain Layer          ✅
  Infrastructure        ✅
  Vision Foundation     ✅
  Gesture Recognition   ✅
  Vision Integration    ✅
  Gesture Refinement    ✅
  Stroke Engine (5A)    ✅
  Stroke Manager (5B)   ⏳
  Renderer              ⏳
  Symmetry Engine       ⏳
  Brush Engine          ⏳
  Timeline              ⏳
  Export                ⏳
  UI                    ⏳
  AI Features           ⏳

------------------------------------------------------------------------

---

# 🗺️ Development Roadmap

## Milestone 1

Core Foundation

## Milestone 2

Domain Model

## Milestone 3

Infrastructure Foundation

## Milestone 4

Vision Layer

## Milestone 5

Drawing Pipeline

## Milestone 6

Rendering Engine

## Milestone 7

Timeline

## Milestone 8

Persistence

## Milestone 9

Export

## Milestone 10

User Interface

## Milestone 11

AI Features

## Milestone 12

Plugin System

---

------------------------------------------------------------------------

#  Roadmap

Next major milestones:

-   Milestone 5B -- Stroke Manager
-   Milestone 5C -- Renderer
-   Milestone 5D -- Symmetry Engine
-   Milestone 6 -- Brush Engine
-   Timeline & Replay
-   Export System
-   AI Features

------------------------------------------------------------------------


# 🤝 Contributing

This project is currently under active development.

The architecture emphasizes maintainability and long-term extensibility.

Contributors should follow:

- Clean Architecture
- SOLID
- Existing documentation
- Project rules inside `docs/`

---

# 📄 License

This project is currently for educational and portfolio purposes.

A formal open-source license may be added in the future.

---

# 👨‍💻 Author

**Lucky Singh**

Bachelor of Computer Applications (BCA)

Passionate about:

- Software Engineering
- Artificial Intelligence
- Computer Vision
- Full Stack Development
- Real-Time Graphics

---

# ⭐ Future Goals

- Cross-platform desktop application
- GPU acceleration
- AI-assisted artwork
- Cloud synchronization
- Collaborative drawing
- Plugin marketplace
- Animation export
- Professional digital art workflow