"""Pure coordinate conversion utilities for the vision layer.

Design rationale:
    MediaPipe reports landmarks in normalized ``[0.0, 1.0]`` image space.
    Downstream consumers need pixel-space (for camera-frame overlays) or
    canvas-space (for mapping a fingertip onto the drawing surface)
    coordinates. Centralizing these conversions here keeps every other
    vision module free of coordinate-math duplication and keeps this
    module itself free of any business logic -- it only converts numbers,
    it never decides what those numbers mean.
"""

from __future__ import annotations


def normalized_to_pixel(
    x: float, y: float, frame_width: int, frame_height: int
) -> tuple[float, float]:
    """Convert normalized ``[0.0, 1.0]`` coordinates to pixel coordinates.

    Args:
        x: Normalized horizontal position.
        y: Normalized vertical position.
        frame_width: Frame width in pixels.
        frame_height: Frame height in pixels.

    Returns:
        ``(pixel_x, pixel_y)``.
    """
    return (x * frame_width, y * frame_height)


def pixel_to_normalized(
    pixel_x: float, pixel_y: float, frame_width: int, frame_height: int
) -> tuple[float, float]:
    """Convert pixel coordinates to normalized ``[0.0, 1.0]`` coordinates.

    Args:
        pixel_x: Horizontal position in pixels.
        pixel_y: Vertical position in pixels.
        frame_width: Frame width in pixels.
        frame_height: Frame height in pixels.

    Returns:
        ``(x, y)`` normalized to ``[0.0, 1.0]``.

    Raises:
        ValueError: If either frame dimension is not positive.
    """
    if frame_width <= 0 or frame_height <= 0:
        raise ValueError("frame_width and frame_height must be positive.")
    return (pixel_x / frame_width, pixel_y / frame_height)


def normalized_to_canvas(
    x: float,
    y: float,
    canvas_width: float,
    canvas_height: float,
    offset_x: float = 0.0,
    offset_y: float = 0.0,
) -> tuple[float, float]:
    """Convert normalized ``[0.0, 1.0]`` coordinates to canvas-space
    coordinates.

    Args:
        x: Normalized horizontal position.
        y: Normalized vertical position.
        canvas_width: Width of the target canvas region, in canvas units.
        canvas_height: Height of the target canvas region, in canvas
            units.
        offset_x: Horizontal offset to add after scaling, allowing the
            mapped region to be positioned anywhere on an infinite
            canvas.
        offset_y: Vertical offset to add after scaling.

    Returns:
        ``(canvas_x, canvas_y)``.
    """
    return (x * canvas_width + offset_x, y * canvas_height + offset_y)


def clamp_normalized(value: float) -> float:
    """Clamp a coordinate value into the valid ``[0.0, 1.0]`` range.

    MediaPipe landmarks can occasionally fall slightly outside this
    range (e.g. a fingertip just past the frame edge); callers that need
    a strictly in-frame coordinate should clamp with this first.
    """
    return max(0.0, min(1.0, value))


def mirror_x(x: float) -> float:
    """Mirror a normalized horizontal coordinate around the frame's
    vertical center axis (``x' = 1.0 - x``).

    Used to compensate for a camera feed that is shown in "selfie view"
    (see ``TrackerConfig.mirror_camera_feed``).
    """
    return 1.0 - x


def scale_distance(
    distance: float, frame_width: int, frame_height: int
) -> float:
    """Convert a normalized-space distance into an approximate pixel-space
    distance, using the frame diagonal as the scale reference.

    This is an approximation (normalized x/y are independently scaled by
    width/height, so a true conversion depends on direction), suitable
    for magnitude comparisons such as pinch-distance thresholds rather
    than precise geometry.
    """
    diagonal = (frame_width**2 + frame_height**2) ** 0.5
    reference_diagonal = (1.0**2 + 1.0**2) ** 0.5
    return distance * (diagonal / reference_diagonal)
