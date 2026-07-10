"""Custom exception hierarchy for SymmetrySketch AI.

Design rationale:
    Per the project's engineering standards, generic exceptions
    (``Exception``, ``ValueError`` used ad hoc, etc.) must not be raised
    across module boundaries. Every layer raises a specific subclass of
    :class:`SymmetrySketchError`, which lets callers -- especially the UI
    layer, which must never crash on a recoverable error -- catch
    precisely what they can handle.

    Each subsystem gets its own exception subtree so that, e.g., a
    ``VisionError`` can be caught and handled (falling back to mouse
    input) without accidentally swallowing an unrelated ``ExportError``.
"""

from __future__ import annotations


class SymmetrySketchError(Exception):
    """Root exception for all application-specific errors.

    All custom exceptions in this codebase must inherit from this class
    (directly or via a subsystem-level intermediate), never from
    ``Exception`` directly. This allows a single top-level
    ``except SymmetrySketchError`` to catch any application error while
    still letting unexpected/unmapped errors (real bugs) propagate.
    """


# --------------------------------------------------------------------------
# Vision layer
# --------------------------------------------------------------------------
class VisionError(SymmetrySketchError):
    """Base class for errors originating in the vision subsystem."""


class CameraNotAvailableError(VisionError):
    """Raised when the configured camera device cannot be opened."""


class HandLandmarkerInitializationError(VisionError):
    """Raised when the MediaPipe hand landmarker model fails to load."""


class GestureRecognitionError(VisionError):
    """Raised when gesture classification fails on valid landmark data."""


# --------------------------------------------------------------------------
# Domain / drawing layer
# --------------------------------------------------------------------------
class DrawingError(SymmetrySketchError):
    """Base class for errors originating in the drawing subsystem."""


class InvalidStrokeError(DrawingError):
    """Raised when a :class:`Stroke` is malformed (e.g. no points)."""


class LayerNotFoundError(DrawingError):
    """Raised when an operation references a non-existent layer id."""


class StrokeNotFoundError(DrawingError):
    """Raised when an operation references a non-existent stroke id."""


class BrushNotRegisteredError(DrawingError):
    """Raised when a requested :class:`BrushType` has no registered
    implementation in the ``BrushFactory``.
    """


class SymmetryConfigurationError(DrawingError):
    """Raised when a symmetry mode is given an invalid configuration
    (e.g. zero rotational segments, an axis outside canvas bounds).
    """


# --------------------------------------------------------------------------
# Timeline layer
# --------------------------------------------------------------------------
class TimelineError(SymmetrySketchError):
    """Base class for errors originating in the timeline subsystem."""


class NothingToUndoError(TimelineError):
    """Raised when undo is requested but the history stack is empty."""


class NothingToRedoError(TimelineError):
    """Raised when redo is requested but the redo stack is empty."""


class CommandExecutionError(TimelineError):
    """Raised when a :class:`Command` fails to execute or reverse."""


# --------------------------------------------------------------------------
# AI layer
# --------------------------------------------------------------------------
class AIError(SymmetrySketchError):
    """Base class for errors originating in the AI subsystem."""


class ModelLoadError(AIError):
    """Raised when an ONNX/AI model fails to load from disk."""


class InferenceError(AIError):
    """Raised when model inference fails on otherwise valid input."""


class ShapeDetectionError(AIError):
    """Raised when shape recognition cannot process the given stroke."""


# --------------------------------------------------------------------------
# Export layer
# --------------------------------------------------------------------------
class ExportError(SymmetrySketchError):
    """Base class for errors originating in the export subsystem."""


class UnsupportedExportFormatError(ExportError):
    """Raised when an :class:`ExportFormat` has no registered exporter."""


class ExportWriteError(ExportError):
    """Raised when writing the exported file to disk fails."""


# --------------------------------------------------------------------------
# Persistence layer
# --------------------------------------------------------------------------
class PersistenceError(SymmetrySketchError):
    """Base class for errors originating in the persistence subsystem."""


class ProjectLoadError(PersistenceError):
    """Raised when a project file cannot be parsed or is incompatible."""


class ProjectSaveError(PersistenceError):
    """Raised when a project file cannot be written to disk."""


class SchemaValidationError(PersistenceError):
    """Raised when project JSON fails schema validation."""


# --------------------------------------------------------------------------
# Configuration layer
# --------------------------------------------------------------------------
class ConfigurationError(SymmetrySketchError):
    """Base class for errors originating from invalid configuration."""


class MissingConfigurationValueError(ConfigurationError):
    """Raised when a required configuration value is absent."""


class InvalidConfigurationValueError(ConfigurationError):
    """Raised when a configuration value fails validation (e.g. a path
    that does not exist, or a numeric value outside its allowed range).
    """
