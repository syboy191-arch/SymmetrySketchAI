# SymmetrySketch AI

## Project Overview

SymmetrySketch AI is a production-quality desktop application written in Python.

The application allows users to create symmetrical artwork using real-time hand tracking through a webcam.

This project is designed to demonstrate:

- Software Engineering
- Computer Vision
- Clean Architecture
- Object-Oriented Programming
- Real-Time Graphics
- AI-assisted Drawing

This is NOT a tutorial project.

This is NOT a prototype.

The project should be built as if it were a commercial desktop application.

---

# Current Development Phase

Milestone 4B — Gesture Recognition (complete)

Next: Milestone 4C — Vision Integration Demo

---

# Technology Stack

Python 3.13+

OpenCV

MediaPipe Tasks API

NumPy

PyTest

pathlib

dataclasses

Enums

Type Hints

---

# Design Philosophy

The project follows:

- Clean Architecture
- Domain Driven Design
- SOLID Principles
- Event Driven Architecture
- Object-Based Rendering

---

# Rendering Philosophy

The renderer never owns artwork.

Every drawing action creates a Stroke object.

Rendering is performed every frame from Stroke objects.

Nothing is permanently painted onto the canvas.

---

# Vision Layer Data Flow

Camera
→ HandTracker            (OpenCV + MediaPipe, isolated here)
→ TrackerResult          (project-owned value object, one per frame)
→ GestureEngine          (smoothing + debounce + motion + velocity)
→ GestureEvent(s)        (immutable, consumed by the Stroke Engine)

The `GestureEngine` owns a `LandmarkSmoother` and a stateless
`GestureClassifier`. The classifier decides the pose of a single frame;
the engine decides what the user is doing over time (confirmation,
swipes, transitions) and emits `GestureEvent`s, optionally publishing
`GestureRecognizedEvent` on the shared `EventBus`.

---

# Current Status

Completed:

Core (incl. events + dependency_container)

Domain

Vision Foundation (tracker, landmarks, hand, tracker_result)

Gesture Recognition (smoothing, classifier, engine)

Remaining:

Vision Integration Demo (4C)

Drawing

Rendering

Timeline

Persistence

Export

UI

AI

Plugins