"""Top-level application configuration.

Design rationale:
    ``AppConfig`` holds settings that describe the application as a
    whole rather than any single subsystem (name, version, logging
    verbosity, autosave policy). Subsystem-specific settings belong in
    their own config module (``tracker_config``, ``renderer_config``,
    etc.) even though this module may compose them in a future
    "root config" aggregate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from core.constants import APP_NAME, ORGANIZATION_NAME
from core.exceptions import InvalidConfigurationValueError

_VALID_LOG_LEVELS: frozenset[int] = frozenset(
    {
        logging.DEBUG,
        logging.INFO,
        logging.WARNING,
        logging.ERROR,
        logging.CRITICAL,
    }
)


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Application-wide settings.

    Attributes:
        app_name: Display name of the application.
        organization_name: Vendor/organization name, used for
            platform-specific user-data directory conventions.
        log_level: Root logger verbosity (one of the standard
            ``logging`` module levels).
        autosave_enabled: Whether periodic autosave is active.
        autosave_interval_seconds: Seconds between autosaves. Only
            validated when ``autosave_enabled`` is ``True``.
        max_undo_history: Maximum number of timeline commands retained
            for undo, or ``-1`` for unlimited (see
            ``core.constants.UNLIMITED_HISTORY``).
    """

    app_name: str = APP_NAME
    organization_name: str = ORGANIZATION_NAME
    log_level: int = logging.INFO
    autosave_enabled: bool = True
    autosave_interval_seconds: float = 120.0
    max_undo_history: int = -1

    def __post_init__(self) -> None:
        if not self.app_name.strip():
            raise InvalidConfigurationValueError("app_name must not be empty.")
        if not self.organization_name.strip():
            raise InvalidConfigurationValueError(
                "organization_name must not be empty."
            )
        if self.log_level not in _VALID_LOG_LEVELS:
            raise InvalidConfigurationValueError(
                f"log_level {self.log_level!r} is not a standard logging level."
            )
        if self.autosave_enabled and self.autosave_interval_seconds <= 0:
            raise InvalidConfigurationValueError(
                "autosave_interval_seconds must be positive when autosave is "
                "enabled."
            )
        if self.max_undo_history < -1:
            raise InvalidConfigurationValueError(
                "max_undo_history must be -1 (unlimited) or a non-negative "
                "integer."
            )
