"""Unit tests for domain.entities.brush."""
from __future__ import annotations

import pytest

from core.exceptions import DrawingError
from domain.entities.brush import (
    Brush,
    BrushStyle,
    BrushValidationError,
    GlowSettings,
    NeonSettings,
    RainbowSettings,
    validate_hex_color,
)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestConstruction:
    def test_default_construction(self):
        brush = Brush()
        assert brush.brush_style is BrushStyle.PENCIL
        assert brush.width == 8.0
        assert brush.opacity == 1.0
        assert brush.color == "#000000"
        assert brush.pressure_enabled is True

    def test_custom_construction(self):
        brush = Brush(brush_style=BrushStyle.MARKER, width=20.0, color="#FF00FF")
        assert brush.brush_style is BrushStyle.MARKER
        assert brush.width == 20.0
        assert brush.color == "#FF00FF"

    def test_brush_is_immutable(self):
        brush = Brush()
        with pytest.raises(Exception):
            brush.width = 99.0  # type: ignore[misc]

    def test_brush_validation_error_is_a_drawing_error(self):
        # BrushValidationError must integrate with the project's exception
        # hierarchy (core.exceptions.DrawingError), not raise bare Exception.
        assert issubclass(BrushValidationError, DrawingError)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidation:
    @pytest.mark.parametrize("bad_width", [0.0, -1.0, 501.0])
    def test_rejects_invalid_width(self, bad_width):
        with pytest.raises(BrushValidationError):
            Brush(width=bad_width)

    @pytest.mark.parametrize("bad_opacity", [-0.1, 1.1])
    def test_rejects_invalid_opacity(self, bad_opacity):
        with pytest.raises(BrushValidationError):
            Brush(opacity=bad_opacity)

    @pytest.mark.parametrize("bad_spacing", [0.0, 5.1])
    def test_rejects_invalid_spacing(self, bad_spacing):
        with pytest.raises(BrushValidationError):
            Brush(spacing=bad_spacing)

    @pytest.mark.parametrize("bad_hardness", [-0.1, 1.1])
    def test_rejects_invalid_hardness(self, bad_hardness):
        with pytest.raises(BrushValidationError):
            Brush(hardness=bad_hardness)

    @pytest.mark.parametrize("bad_flow", [-0.1, 1.1])
    def test_rejects_invalid_flow(self, bad_flow):
        with pytest.raises(BrushValidationError):
            Brush(flow=bad_flow)

    @pytest.mark.parametrize("bad_smoothing", [-0.1, 1.1])
    def test_rejects_invalid_smoothing(self, bad_smoothing):
        with pytest.raises(BrushValidationError):
            Brush(smoothing=bad_smoothing)

    @pytest.mark.parametrize("bad_jitter", [-0.1, 1.1])
    def test_rejects_invalid_jitter(self, bad_jitter):
        with pytest.raises(BrushValidationError):
            Brush(jitter=bad_jitter)

    def test_rejects_non_brush_style(self):
        with pytest.raises(BrushValidationError):
            Brush(brush_style="pencil")  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        "bad_color", ["000000", "#00000", "#GGGGGG", "", None, "#12345678901"]
    )
    def test_rejects_invalid_color(self, bad_color):
        with pytest.raises(BrushValidationError):
            Brush(color=bad_color)  # type: ignore[arg-type]

    def test_accepts_short_and_long_hex_colors(self):
        validate_hex_color("#AABBCC")
        validate_hex_color("#AABBCCDD")

    def test_boundary_values_are_valid(self):
        Brush(width=0.1, opacity=0.0, spacing=0.01, hardness=0.0, flow=0.0, smoothing=0.0, jitter=0.0)
        Brush(width=500.0, opacity=1.0, spacing=5.0, hardness=1.0, flow=1.0, smoothing=1.0, jitter=1.0)


class TestEffectSettingsValidation:
    def test_glow_settings_validates_intensity_and_radius(self):
        with pytest.raises(BrushValidationError):
            GlowSettings(intensity=1.5)
        with pytest.raises(BrushValidationError):
            GlowSettings(radius=-1.0)
        GlowSettings(intensity=0.5, radius=10.0)

    def test_glow_settings_validates_color(self):
        with pytest.raises(BrushValidationError):
            GlowSettings(color="not-a-color")

    def test_rainbow_settings_validates_cycle_speed(self):
        with pytest.raises(BrushValidationError):
            RainbowSettings(cycle_speed=0.0)
        with pytest.raises(BrushValidationError):
            RainbowSettings(cycle_speed=-2.0)

    def test_rainbow_settings_validates_saturation_and_lightness(self):
        with pytest.raises(BrushValidationError):
            RainbowSettings(saturation=1.5)
        with pytest.raises(BrushValidationError):
            RainbowSettings(lightness=-0.5)

    def test_neon_settings_validates_intensity_and_colors(self):
        with pytest.raises(BrushValidationError):
            NeonSettings(intensity=2.0)
        with pytest.raises(BrushValidationError):
            NeonSettings(core_color="bad")
        with pytest.raises(BrushValidationError):
            NeonSettings(outer_color="bad")

    def test_brush_propagates_nested_effect_validation_errors(self):
        with pytest.raises(BrushValidationError):
            Brush(glow=GlowSettings(intensity=5.0))


# ---------------------------------------------------------------------------
# Clone
# ---------------------------------------------------------------------------

class TestClone:
    def test_clone_with_no_overrides_produces_equal_brush(self):
        brush = Brush(width=10.0)
        clone = brush.clone()
        assert clone == brush
        assert clone is not brush

    def test_clone_with_overrides(self):
        brush = Brush(width=10.0, color="#123456")
        clone = brush.clone(width=25.0)
        assert clone.width == 25.0
        assert clone.color == "#123456"
        assert brush.width == 10.0  # original untouched

    def test_clone_validates_overrides(self):
        brush = Brush()
        with pytest.raises(BrushValidationError):
            brush.clone(width=-5.0)


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

class TestPresets:
    def test_builtin_presets_registered(self):
        presets = Brush.available_presets()
        assert "pencil" in presets
        assert "ink_pen" in presets
        assert "marker" in presets
        assert "airbrush" in presets
        assert "glow_pen" in presets
        assert "neon_marker" in presets
        assert "rainbow_brush" in presets

    def test_from_preset_returns_configured_brush(self):
        brush = Brush.from_preset("marker")
        assert brush.brush_style is BrushStyle.MARKER

    def test_from_preset_with_overrides(self):
        brush = Brush.from_preset("pencil", color="#FF0000")
        assert brush.color == "#FF0000"
        assert brush.brush_style is BrushStyle.PENCIL

    def test_from_unknown_preset_raises(self):
        with pytest.raises(BrushValidationError):
            Brush.from_preset("does_not_exist")

    def test_register_custom_preset(self):
        custom = Brush(brush_style=BrushStyle.CUSTOM, width=42.0)
        Brush.register_preset("my_custom", custom)
        assert Brush.from_preset("my_custom").width == 42.0

    def test_register_preset_rejects_empty_name(self):
        with pytest.raises(BrushValidationError):
            Brush.register_preset("", Brush())

    def test_register_preset_rejects_non_brush(self):
        with pytest.raises(BrushValidationError):
            Brush.register_preset("bad", "not-a-brush")  # type: ignore[arg-type]

    def test_preset_instances_are_independent(self):
        b1 = Brush.from_preset("pencil")
        b2 = Brush.from_preset("pencil")
        assert b1 == b2
        assert b1 is not b2
