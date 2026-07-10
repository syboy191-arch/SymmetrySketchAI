# Current Project Structure

SymmetrySketchAI/

  core/
    constants.py
    enums.py
    exceptions.py
    logger.py
    paths.py
    events.py
    dependency_container.py

  config/
    tracker_config.py
    (app / renderer / brush / export / ui configs)

  domain/
    entities/
      ids.py
      point.py
      stroke.py
      layer.py
      brush.py
      canvas_state.py
      project.py
      gesture_event.py

  vision/
    tracker.py
    tracker_result.py
    hand.py
    landmarks.py
    smoothing.py            # NEW (Milestone 4B)
    gesture_classifier.py   # NEW (Milestone 4B)
    gesture_engine.py       # NEW (Milestone 4B)
    models/
      hand_landmarker.task
    utils/
      coordinate_utils.py

  drawing/                  # Future (Milestone 5)

  timeline/                 # Future

  ui/                       # Future

  ai/                       # Future

  export/                   # Future

  persistence/              # Future

  tests/
    unit/
      test_point.py
      test_stroke.py
      test_layer.py
      test_brush.py
      test_canvas_state.py
      test_project.py
      test_gesture_event.py
      test_smoothing.py            # NEW (Milestone 4B)
      test_gesture_classifier.py   # NEW (Milestone 4B)
      test_gesture_engine.py       # NEW (Milestone 4B)

  docs/
    AI_CONTEXT.md
    ARCHITECTURE.md
    CHANGELOG.md
    MODULE_STATUS.md
    NEXT_MODULE.md
    PROJECT_RULES.md
    PROJECT_TREE.md

  assets/

  models/

  # Updated Structure (Milestone 4C)

SymmetrySketchAI/

    core/

    config/

    domain/
        entities/

    vision/
        utils/
        models/

    examples/            <- new (Milestone 4C)
        __init__.py
        vision_demo.py

    tests/
        unit/
        integration/     <- new (Milestone 4C)
            __init__.py
            test_vision_pipeline.py

    docs/

    assets/

    models/