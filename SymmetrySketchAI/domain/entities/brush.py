"""Domain entity representing brush configuration.

A Brush is pure configuration data: the set of parameters that describe
how a stroke *should* look and behave. It contains NO drawing algorithms,
NO rendering code, and NO dependency on OpenCV/MediaPipe/NumPy/UI. Turning
this configuration into pixels is the job of an infrastructure-level
rendering component that consumes a Brush as input.

Naming note -- BrushStyle vs. core.enums.BrushType:
    ``core.enums.BrushType`` identifies which *rendering engine*
    (``drawing.brush_factory.BrushFactory``) should render a stroke, and
    is deliberately small and stable since engines are expensive to add.
    This module's ``BrushStyle`` enum is a richer, purely descriptive
    vocabulary of brush *presets/styles* (glow, neon, eraser, custom,
    ...) that a UI or preset library can offer -- it is intentionally a
    distinct concept and is named differently so the two enums are never
    confused or accidentally shadow one another when both are imported
    in the same module.

All validation errors raised here derive from
:class:`core.exceptions.DrawingError`, consistent with the rest of the
domain/drawing layer's exception hierarchy.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, unique
from typing import ClassVar

from core.exceptions import DrawingError

# --------------------------------------------------------------------------
# Constants (no magic numbers)
# --------------------------------------------------------------------------

MIN_WIDTH: float = 0.1
MAX_WIDTH: float = 500.0

MIN_OPACITY: float = 0.0
MAX_OPACITY: float = 1.0

MIN_SPACING: float = 0.01
MAX_SPACING: float = 5.0

MIN_HARDNESS: float = 0.0
MAX_HARDNESS: float = 1.0

MIN_FLOW: float = 0.0
MAX_FLOW: float = 1.0

MIN_SMOOTHING: float = 0.0
MAX_SMOOTHING: float = 1.0

MIN_JITTER: float = 0.0
MAX_JITTER: float = 1.0

MIN_GLOW_INTENSITY: float = 0.0
MAX_GLOW_INTENSITY: float = 1.0

MIN_GLOW_RADIUS: float = 0.0
MAX_GLOW_RADIUS: float = 200.0

MIN_NEON_INTENSITY: float = 0.0
MAX_NEON_INTENSITY: float = 1.0

DEFAULT_WIDTH: float = 8.0
DEFAULT_OPACITY: float = 1.0
DEFAULT_COLOR: str = "#000000"
DEFAULT_SPACING: float = 0.25
DEFAULT_HARDNESS: float = 0.8
DEFAULT_FLOW: float = 1.0
DEFAULT_SMOOTHING: float = 0.3
DEFAULT_JITTER: float = 0.0

_HEX_COLOR_LENGTH_SHORT: int = 7   # "#RRGGBB"
_HEX_COLOR_LENGTH_LONG: int = 9    # "#RRGGBBAA"


# --------------------------------------------------------------------------
# Exceptions
# --------------------------------------------------------------------------

class BrushValidationError(DrawingError):
    """Raised when constructing or mutating a Brush with invalid data."""


# --------------------------------------------------------------------------
# Enums
# --------------------------------------------------------------------------

@unique
class BrushStyle(Enum):
    """The descriptive style/preset family a brush configuration applies to.

    Distinct from :class:`core.enums.BrushType`, which selects a
    rendering engine; see the module docstring for the rationale.
    """

    PENCIL = "pencil"
    INK_PEN = "ink_pen"
    MARKER = "marker"
    AIRBRUSH = "airbrush"
    CALLIGRAPHY = "calligraphy"
    ERASER = "eraser"
    GLOW = "glow"
    NEON = "neon"
    RAINBOW = "rainbow"
    CUSTOM = "custom"


# --------------------------------------------------------------------------
# Value objects: grouped optional effect settings
# --------------------------------------------------------------------------

def _validate_range(value: float, low: float, high: float, field_name: str) -> None:
    if not (low <= value <= high):
        raise BrushValidationError(
            f"{field_name} must be between {low} and {high}, got {value}."
        )


@dataclass(frozen=True, slots=True)
class GlowSettings:
    """Glow effect configuration for a brush."""

    enabled: bool = False
    intensity: float = 0.5
    radius: float = 10.0
    color: str = "#FFFFFF"

    def __post_init__(self) -> None:
        _validate_range(self.intensity, MIN_GLOW_INTENSITY, MAX_GLOW_INTENSITY, "glow.intensity")
        _validate_range(self.radius, MIN_GLOW_RADIUS, MAX_GLOW_RADIUS, "glow.radius")
        validate_hex_color(self.color, field_name="glow.color")


@dataclass(frozen=True, slots=True)
class RainbowSettings:
    """Rainbow (multi-color cycling) effect configuration for a brush."""

    enabled: bool = False
    cycle_speed: float = 1.0
    saturation: float = 1.0
    lightness: float = 0.5

    def __post_init__(self) -> None:
        if self.cycle_speed <= 0:
            raise BrushValidationError(
                f"rainbow.cycle_speed must be positive, got {self.cycle_speed}."
            )
        _validate_range(self.saturation, 0.0, 1.0, "rainbow.saturation")
        _validate_range(self.lightness, 0.0, 1.0, "rainbow.lightness")


@dataclass(frozen=True, slots=True)
class NeonSettings:
    """Neon-glow effect configuration for a brush."""

    enabled: bool = False
    intensity: float = 0.5
    core_color: str = "#FFFFFF"
    outer_color: str = "#00FFFF"

    def __post_init__(self) -> None:
        _validate_range(self.intensity, MIN_NEON_INTENSITY, MAX_NEON_INTENSITY, "neon.intensity")
        validate_hex_color(self.core_color, field_name="neon.core_color")
        validate_hex_color(self.outer_color, field_name="neon.outer_color")


def validate_hex_color(color: str, *, field_name: str = "color") -> None:
    """Validate that ``color`` is a ``#RRGGBB`` or ``#RRGGBBAA`` hex string."""
    if (
        not isinstance(color, str)
        or not color.startswith("#")
        or len(color) not in (_HEX_COLOR_LENGTH_SHORT, _HEX_COLOR_LENGTH_LONG)
    ):
        raise BrushValidationError(
            f"{field_name} must be a '#RRGGBB' or '#RRGGBBAA' hex string, got {color!r}."
        )
    hex_digits = color[1:]
    try:
        int(hex_digits, 16)
    except ValueError as exc:
        raise BrushValidationError(
            f"{field_name} must contain only valid hex digits, got {color!r}."
        ) from exc


# --------------------------------------------------------------------------
# Entity: Brush
# --------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class Brush:
    """Immutable brush configuration.

    A Brush is a value-like entity: two brushes with identical fields are
    interchangeable. It is frozen (immutable) so that presets and
    in-flight strokes can safely share references; "mutation" is done via
    :meth:`clone`, which returns a new, validated instance.
    """

    brush_style: BrushStyle = BrushStyle.PENCIL
    width: float = DEFAULT_WIDTH
    opacity: float = DEFAULT_OPACITY
    color: str = DEFAULT_COLOR
    spacing: float = DEFAULT_SPACING
    hardness: float = DEFAULT_HARDNESS
    flow: float = DEFAULT_FLOW
    pressure_enabled: bool = True
    smoothing: float = DEFAULT_SMOOTHING
    jitter: float = DEFAULT_JITTER
    glow: GlowSettings = field(default_factory=GlowSettings)
    rainbow: RainbowSettings = field(default_factory=RainbowSettings)
    neon: NeonSettings = field(default_factory=NeonSettings)

    #: Registry of built-in presets, populated by ``_register_presets`` at
    #: import time. Kept as a ClassVar so it is not treated as a dataclass
    #: field.
    _PRESETS: ClassVar[dict[str, "Brush"]] = {}

    def __post_init__(self) -> None:
        self.validate()

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Validate every field on this brush.

        Raises:
            BrushValidationError: if any field is out of its valid range.
        """
        if not isinstance(self.brush_style, BrushStyle):
            raise BrushValidationError(
                f"brush_style must be a BrushStyle, got {type(self.brush_style)!r}."
            )
        _validate_range(self.width, MIN_WIDTH, MAX_WIDTH, "width")
        _validate_range(self.opacity, MIN_OPACITY, MAX_OPACITY, "opacity")
        validate_hex_color(self.color)
        _validate_range(self.spacing, MIN_SPACING, MAX_SPACING, "spacing")
        _validate_range(self.hardness, MIN_HARDNESS, MAX_HARDNESS, "hardness")
        _validate_range(self.flow, MIN_FLOW, MAX_FLOW, "flow")
        _validate_range(self.smoothing, MIN_SMOOTHING, MAX_SMOOTHING, "smoothing")
        _validate_range(self.jitter, MIN_JITTER, MAX_JITTER, "jitter")
        # Nested value objects validate themselves in their own
        # __post_init__, so reaching this point implies they are valid.

    # ------------------------------------------------------------------
    # Cloning / "mutation"
    # ------------------------------------------------------------------

    def clone(self, **overrides: object) -> "Brush":
        """Return a new, validated Brush with the given fields overridden.

        Since Brush is immutable, this is the supported way to derive a
        modified brush, e.g. ``brush.clone(width=12.0, color="#FF0000")``.
        """
        return replace(self, **overrides)

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------

    @classmethod
    def register_preset(cls, name: str, brush: "Brush") -> None:
        """Register a named, reusable preset brush configuration.

        Raises:
            BrushValidationError: if ``name`` is empty or ``brush`` is not
                a :class:`Brush` instance.
        """
        if not isinstance(name, str) or not name.strip():
            raise BrushValidationError("Preset name must be a non-empty string.")
        if not isinstance(brush, Brush):
            raise BrushValidationError(
                f"Preset must be a Brush instance, got {type(brush)!r}."
            )
        cls._PRESETS[name] = brush

    @classmethod
    def from_preset(cls, name: str, **overrides: object) -> "Brush":
        """Instantiate a brush from a registered preset, with optional
        field overrides applied on top.

        Raises:
            BrushValidationError: if no preset is registered under ``name``.
        """
        try:
            base = cls._PRESETS[name]
        except KeyError as exc:
            available = ", ".join(sorted(cls._PRESETS)) or "<none registered>"
            raise BrushValidationError(
                f"No brush preset named {name!r} is registered. "
                f"Available presets: {available}."
            ) from exc
        return base.clone(**overrides) if overrides else replace(base)

    @classmethod
    def available_presets(cls) -> tuple[str, ...]:
        """Return the names of all currently registered presets."""
        return tuple(sorted(cls._PRESETS))


def _register_builtin_presets() -> None:
    """Populate ``Brush._PRESETS`` with a small set of sensible defaults."""
    Brush.register_preset("pencil", Brush(brush_style=BrushStyle.PENCIL, width=3.0, hardness=0.9, flow=0.9))
    Brush.register_preset("ink_pen", Brush(brush_style=BrushStyle.INK_PEN, width=2.0, hardness=1.0, flow=1.0, spacing=0.1))
    Brush.register_preset("marker", Brush(brush_style=BrushStyle.MARKER, width=18.0, opacity=0.6, hardness=0.3, flow=0.8))
    Brush.register_preset("airbrush", Brush(brush_style=BrushStyle.AIRBRUSH, width=40.0, opacity=0.3, hardness=0.1, flow=0.4, spacing=0.05))
    Brush.register_preset(
        "glow_pen",
        Brush(
            brush_style=BrushStyle.GLOW,
            width=6.0,
            color="#00FFFF",
            glow=GlowSettings(enabled=True, intensity=0.8, radius=20.0, color="#00FFFF"),
        ),
    )
    Brush.register_preset(
        "neon_marker",
        Brush(
            brush_style=BrushStyle.NEON,
            width=10.0,
            color="#FF00FF",
            neon=NeonSettings(enabled=True, intensity=0.9, core_color="#FFFFFF", outer_color="#FF00FF"),
        ),
    )
    Brush.register_preset(
        "rainbow_brush",
        Brush(
            brush_style=BrushStyle.RAINBOW,
            width=12.0,
            rainbow=RainbowSettings(enabled=True, cycle_speed=1.5, saturation=1.0, lightness=0.5),
        ),
    )


_register_builtin_presets()
