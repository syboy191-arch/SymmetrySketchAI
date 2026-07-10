"""Application-wide logging configuration.

Design rationale:
    A single ``get_logger`` factory ensures consistent formatting and
    handler configuration across every module, while still giving each
    module its own named logger (``vision.tracker``, ``drawing.renderer``,
    etc.) for fine-grained filtering. Business logic modules should log
    through this rather than using ``print``, so log output can be
    redirected, filtered, or captured in tests.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from core.paths import LOGS_DIR, ensure_user_directories_exist

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_LOG_FILE_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_LOG_FILE_BACKUP_COUNT = 3

_configured = False


def _configure_root_logger(level: int) -> None:
    """Attach console and rotating-file handlers to the root logger.

    This is invoked lazily, once, the first time :func:`get_logger` is
    called, so importing this module has no side effects on its own.
    """
    global _configured
    if _configured:
        return

    ensure_user_directories_exist()

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=LOGS_DIR / "symmetrysketch.log",
        maxBytes=_LOG_FILE_MAX_BYTES,
        backupCount=_LOG_FILE_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger("symmetrysketch")
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    _configured = True


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a namespaced logger under the ``symmetrysketch`` root.

    Args:
        name: Dotted module name, e.g. ``"vision.tracker"``. Convention:
            pass ``__name__`` from the calling module.
        level: Logging level for the *root* application logger. Only
            takes effect the first time this function is called, since
            handler configuration is a one-time, process-wide setup.

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    _configure_root_logger(level)
    return logging.getLogger(f"symmetrysketch.{name}")
