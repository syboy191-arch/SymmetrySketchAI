"""Unit tests for the config package's validated dataclasses."""

from __future__ import annotations

import logging

import pytest

from config.app_config import AppConfig
from config.brush_config import BrushConfig
from config.export_config import ExportConfig
from config.renderer_config import RendererConfig
from config.tracker_config import TrackerConfig
from config.ui_config import UIConfig
from core.enums import ApplicationTheme, BrushType, ExportFormat, SymmetryMode
from core.exceptions import InvalidConfigurationValueError


class TestAppConfig:
    def test_default_construction_succeeds(self) -> None:
        config = AppConfig()
        assert config.log_level == logging.INFO

    def test_is_immutable(self) -> None:
        config = AppConfig()
        with pytest.raises(Exception):
            config.app_name = "Other"  # type: ignore[misc]

    def test_rejects_empty_app_name(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            AppConfig(app_name="   ")

    def test_rejects_empty_organization_name(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            AppConfig(organization_name="")

    def test_rejects_non_standard_log_level(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            AppConfig(log_level=12345)

    def test_rejects_non_positive_autosave_interval_when_enabled(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            AppConfig(autosave_enabled=True, autosave_interval_seconds=0.0)

    def test_allows_any_autosave_interval_when_disabled(self) -> None:
        config = AppConfig(autosave_enabled=False, autosave_interval_seconds=0.0)
        assert config.autosave_interval_seconds == 0.0

    def test_rejects_max_undo_history_below_unlimited_sentinel(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            AppConfig(max_undo_history=-2)

    def test_allows_unlimited_undo_history_sentinel(self) -> None:
        config = AppConfig(max_undo_history=-1)
        assert config.max_undo_history == -1


class TestTrackerConfig:
    def test_default_construction_succeeds(self) -> None:
        TrackerConfig()

    def test_rejects_negative_camera_index(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(camera_index=-1)

    def test_rejects_non_positive_camera_width(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(camera_width=0)

    def test_rejects_non_positive_camera_height(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(camera_height=-10)

    def test_rejects_non_positive_fps(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(camera_fps=0)

    def test_rejects_zero_max_tracked_hands(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(max_tracked_hands=0)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range_detection_confidence(self, value: float) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(min_hand_detection_confidence=value)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range_presence_confidence(self, value: float) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(min_hand_presence_confidence=value)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range_tracking_confidence(self, value: float) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(min_tracking_confidence=value)

    def test_accepts_boundary_confidence_values(self) -> None:
        config = TrackerConfig(
            min_hand_detection_confidence=0.0,
            min_hand_presence_confidence=1.0,
            min_tracking_confidence=0.5,
        )
        assert config.min_hand_detection_confidence == 0.0

    def test_rejects_zero_smoothing_window(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(smoothing_window_size=0)

    def test_rejects_zero_gesture_hold_frames(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            TrackerConfig(gesture_hold_frames_to_confirm=0)


class TestRendererConfig:
    def test_default_construction_succeeds(self) -> None:
        RendererConfig()

    def test_rejects_non_positive_fps(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(target_fps=0)

    def test_rejects_non_positive_canvas_dimensions(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(canvas_width=0)
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(canvas_height=-1)

    def test_rejects_wrong_length_background_color(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(background_color=(255, 255, 255))  # type: ignore[arg-type]

    @pytest.mark.parametrize("color", [(-1, 0, 0, 0), (0, 0, 0, 256)])
    def test_rejects_out_of_range_color_channel(
        self, color: tuple[int, int, int, int]
    ) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(background_color=color)

    def test_rejects_non_positive_chunk_size(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(canvas_chunk_size_px=0)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range_symmetry_guide_opacity(
        self, value: float
    ) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            RendererConfig(symmetry_guide_opacity=value)


class TestBrushConfig:
    def test_default_construction_succeeds(self) -> None:
        config = BrushConfig()
        assert config.default_brush_type == BrushType.PENCIL
        assert config.default_symmetry_mode == SymmetryMode.NONE

    def test_rejects_width_below_minimum(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_width_px=0.0)

    def test_rejects_width_above_maximum(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_width_px=99999.0)

    @pytest.mark.parametrize("value", [-0.1, 1.1])
    def test_rejects_out_of_range_pressure(self, value: float) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_pressure=value)

    def test_rejects_non_positive_min_distance(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(min_distance_between_points_px=0.0)

    def test_rejects_zero_spline_samples(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(spline_interpolation_samples=0)

    def test_rejects_rotational_segments_out_of_range(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_rotational_segments=1)
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_rotational_segments=1000)

    def test_rejects_mandala_segments_out_of_range(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            BrushConfig(default_mandala_segments=1)


class TestExportConfig:
    def test_default_construction_succeeds(self) -> None:
        config = ExportConfig()
        assert config.default_format == ExportFormat.PNG

    def test_rejects_non_positive_dpi(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            ExportConfig(png_dpi=0)

    @pytest.mark.parametrize("value", [-1, 11])
    def test_rejects_out_of_range_svg_precision(self, value: int) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            ExportConfig(svg_precision=value)

    def test_accepts_boundary_svg_precision(self) -> None:
        assert ExportConfig(svg_precision=0).svg_precision == 0
        assert ExportConfig(svg_precision=10).svg_precision == 10


class TestUIConfig:
    def test_default_construction_succeeds(self) -> None:
        config = UIConfig()
        assert config.theme == ApplicationTheme.DARK

    def test_rejects_window_width_below_minimum(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            UIConfig(window_width=100)

    def test_rejects_window_height_below_minimum(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            UIConfig(window_height=100)

    def test_rejects_non_positive_ui_scale(self) -> None:
        with pytest.raises(InvalidConfigurationValueError):
            UIConfig(ui_scale=0.0)

    def test_is_immutable(self) -> None:
        config = UIConfig()
        with pytest.raises(Exception):
            config.theme = ApplicationTheme.LIGHT  # type: ignore[misc]
