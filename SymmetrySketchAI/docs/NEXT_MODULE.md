# Next Module

Current Phase

Milestone 4C — Vision Integration Demo

---

Generate ONLY

demo/vision_demo.py

(plus, if needed, a thin `demo/__init__.py`)

---

Do NOT modify

Core

Domain

Vision Foundation

Gesture Recognition

Tests

---

Do NOT regenerate

Enums

Exceptions

IDs

Stroke / Layer / Brush / CanvasState / Project / GestureEvent

Tracker / TrackerResult / Hand / Landmarks

GestureEngine / GestureClassifier / LandmarkSmoother

---

# Goal

Build a small, runnable end-to-end demo that wires the finished vision
pipeline together:

HandTracker.read_frame() → TrackerResult
→ GestureEngine.process() → GestureEvent(s)
→ print / overlay the recognized gesture live from the webcam

The demo opens the camera via `HandTracker`, feeds each `TrackerResult`
into a `GestureEngine`, and prints (or draws) the recognized gesture,
confidence, and velocity per hand in real time. It wires the
`EventBus` so a simple subscriber logs `GestureRecognizedEvent`s.

It must contain NO new business logic: it only composes existing
components. Any camera/overlay code stays inside the demo module so the
library packages remain UI-free.

---

# Why this is required BEFORE the Drawing layer

The Drawing layer (Milestone 5) consumes `GestureEvent`s to create and
mutate `Stroke` objects. Everything it does is downstream of, and
totally dependent on, the gesture stream being correct. If we start
building strokes before validating that stream end-to-end against a
**real webcam**, any flaw gets baked into the drawing pipeline and
becomes expensive to unwind.

Unit tests prove each vision component in isolation with synthetic
landmarks, but they cannot prove the *integrated, real-world* behavior
that the Drawing layer will rely on:

1. **Real MediaPipe output** — tests use hand-crafted landmarks. Only a
   live camera confirms the classifier thresholds (pinch distance,
   finger-extension deadzone) hold up against actual MediaPipe data and
   real lighting/hand variation.
2. **Smoothing vs. latency trade-off** — `SMOOTHING_WINDOW_SIZE` and
   `GESTURE_HOLD_FRAMES_TO_CONFIRM` need tuning against perceived lag.
   That judgment can only be made by feel, on live video.
3. **Swipe reliability** — motion thresholds (`SWIPE_MIN_DISPLACEMENT`,
   `SWIPE_MIN_SPEED`) must be validated against genuine hand speed so
   undo/redo don't misfire mid-stroke.
4. **Coordinate correctness** — confirms the mirrored-feed orientation
   and normalized-to-canvas mapping are right before strokes depend on
   fingertip position.
5. **Frame-rate headroom** — verifies tracking + gesture recognition
   run fast enough per frame to leave budget for rendering.

Milestone 4C is the cheap checkpoint: a throwaway-friendly harness that
de-risks the entire drawing pipeline. Once gestures are proven correct
and responsive live, Milestone 5 (Drawing) can build on solid ground.

---

Generate nothing else.