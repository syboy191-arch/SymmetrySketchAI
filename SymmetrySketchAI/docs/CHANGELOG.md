# Changelog

---

## Phase 1

Created

Core infrastructure

- constants.py
- enums.py
- exceptions.py
- logger.py
- paths.py

---

## Phase 2A

Created

Domain Foundations

- layer.py
- brush.py

Added unit tests.

---

## Phase 2B

Created

Editor State

- canvas_state.py
- project.py
- gesture_event.py

Added unit tests.

---

## Phase 3 — Infrastructure

Created

- events.py (thread-safe publish/subscribe EventBus)
- dependency_container.py (lazy, type-keyed DI container)

Added unit tests.

---

## Milestone 4A — Vision Foundation

Created the vision layer's tracking foundation, isolating all
OpenCV / MediaPipe types behind project-owned value objects.

- vision/tracker.py (camera capture + MediaPipe Tasks inference)
- vision/tracker_result.py
- vision/hand.py
- vision/landmarks.py
- vision/utils/coordinate_utils.py

---

## Milestone 4B — Gesture Recognition  (this release)

Added the Gesture Recognition layer on top of the Vision Foundation.
Converts raw tracked hands into debounced, semantic GestureEvents.

Created:

- vision/smoothing.py — `LandmarkSmoother`, `MovingAverage`, `SmoothingError`
- vision/gesture_classifier.py — stateless static-pose classifier
  (POINT, PINCH, OPEN_PALM, FIST, PEACE_SIGN, THUMBS_UP)
- vision/gesture_engine.py — stateful engine adding smoothing,
  frame-hold confirmation (debounce), motion-based SWIPE_LEFT/RIGHT,
  velocity, pinch pressure estimate, per-hand transition tracking, and
  optional `GestureRecognizedEvent` publication on the EventBus

Added unit tests:

- tests/unit/test_smoothing.py
- tests/unit/test_gesture_classifier.py
- tests/unit/test_gesture_engine.py

Reused existing APIs with no duplication: `core.enums.GestureType` /
`HandLabel`, `domain.entities.gesture_event.GestureEvent`,
`vision.landmarks.Landmarks`, `vision.hand.Hand`,
`vision.tracker_result.TrackerResult`, `core.events.EventBus`,
`config.tracker_config.TrackerConfig`, and
`core.exceptions.GestureRecognitionError`. No existing module changed.

---

## Current

Preparing Milestone 4C — Vision Integration Demo

---

## Milestone 4C

Vision Integration Demo (integration only -- no new business logic).

Created

- examples/__init__.py
- examples/vision_demo.py
- tests/integration/__init__.py
- tests/integration/test_vision_pipeline.py

Integrated (no modules regenerated or modified)

- HandTracker, TrackerResult, Hand, Landmarks
- GestureClassifier, GestureEngine, LandmarkSmoother
- DependencyContainer, EventBus, AppConfig, TrackerConfig

Verified the Camera -> Tracker -> GestureEngine pipeline end-to-end. The Vision
subsystem is now complete.