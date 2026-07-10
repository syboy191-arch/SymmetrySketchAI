# System Architecture

Camera

↓

Tracker

↓

Gesture Engine

↓

Stroke Engine

↓

Stroke Manager

↓

Symmetry Engine

↓

Brush Engine

↓

Renderer

↓

Canvas Widget

↓

Display

---

Everything is built around Stroke objects.

The renderer owns no artwork.

Domain objects never render.

Modules communicate through events.

The UI never directly manipulates the domain.

Business logic is independent of the UI.