# SymmetrySketch AI

# Project Overview

SymmetrySketch AI is a production-quality desktop application written in Python.

The application enables users to create symmetrical digital artwork using real-time hand tracking and gesture recognition through a webcam.

Unlike a traditional virtual painter, every drawing is represented internally as editable **Stroke** objects rather than permanently modifying pixels. This architecture enables advanced features such as undo/redo, replay, SVG export, symmetry correction, AI-assisted editing, and future animation support.

The project is intended to demonstrate professional software engineering practices, including:

- Clean Architecture
- Domain-Driven Design (DDD)
- SOLID Principles
- Dependency Injection
- Event-Driven Architecture
- Computer Vision
- Real-Time Graphics
- Modular Software Design
- Automated Testing

This is **not** a tutorial project.

This is **not** a prototype.

The project is designed to resemble a production-quality desktop application.

---

# Current Project Status

## Completed Milestones

### Phase 1

- Core Infrastructure

### Phase 2

- Domain Layer

### Phase 3

- Infrastructure Layer
- Event Bus
- Dependency Injection

### Milestone 4A

- Vision Foundation
- MediaPipe Tasks Integration
- Camera Pipeline
- Hand Tracking

### Milestone 4B

- Gesture Recognition
- Gesture Classification
- Landmark Smoothing

### Milestone 4C

- Vision Integration Demo
- End-to-End Vision Pipeline
- HUD
- FPS Display
- Landmark Rendering
- Bounding Boxes

### Milestone 4D

- Gesture Recognition Refinement
- Improved Classification Accuracy
- Rule Ordering Improvements
- Gesture Stability Improvements

### Milestone 5A

- Drawing Layer Introduced
- Stroke Engine
- Stroke Lifecycle
- GestureEvent → Stroke Conversion
- Unit Tests

---

# Current Architecture

The project currently follows the pipeline:

Camera

↓

Tracker

↓

TrackerResult

↓

Gesture Engine

↓

GestureEvent

↓

Stroke Engine

↓

Stroke Manager (Upcoming)

↓

Renderer (Upcoming)

↓

Canvas

---

# Technology Stack

- Python 3.13+
- OpenCV
- MediaPipe Tasks API
- NumPy
- PyTest

---

# Architectural Principles

The project follows:

- Clean Architecture
- Domain-Driven Design
- SOLID Principles
- Event-Driven Design
- Dependency Injection
- Modular Components
- Test-Driven Development

---

# Vision Layer Status

The Vision subsystem is considered feature complete.

It includes:

- Camera Capture
- MediaPipe Integration
- Hand Tracking
- Landmark Detection
- Gesture Recognition
- Gesture Classification
- Gesture Smoothing
- Vision Integration Demo

Only bug fixes and performance improvements should be made to this subsystem going forward.

---

# Drawing Layer Status

The Drawing subsystem has begun.

Completed:

- Stroke Engine

Upcoming:

- Stroke Manager
- Renderer
- Symmetry Engine
- Brush Engine

---

# Future Roadmap

Upcoming milestones include:

- Stroke Manager
- Renderer
- Canvas System
- Symmetry Engine
- Brush Engine
- Undo / Redo
- Timeline
- Replay System
- SVG Export
- PNG Export
- AI Shape Detection
- AI Shape Correction
- AI Symmetry Correction
- Layer Editing
- Animation Support
- Plugin System

---

# Repository Policy

The GitHub repository is the single source of truth.

Documentation must always reflect the latest repository state.

AI assistants contributing to the project should inspect the repository before implementing new functionality.

The Vision subsystem should not be rewritten.

Each milestone should modify only the modules within its defined scope.