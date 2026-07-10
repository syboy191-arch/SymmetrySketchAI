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

Phase 3A

Infrastructure

Current module:

core/events.py

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

# Current Status

Completed:

Core

Domain

Remaining:

Infrastructure

Vision

Gesture

Drawing

Rendering

Timeline

Persistence

Export

UI

AI

Plugins