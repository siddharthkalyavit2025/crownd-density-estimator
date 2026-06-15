"""
utils/logger.py — Structured logging setup for the Crowd Density Estimator.

Provides :func:`setup_logger` which returns a :class:`logging.Logger` with:

* A **RotatingFileHandler** (10 MB max, 5 backups) that writes JSON-like
  structured records to the ``logs/`` directory.
* A **StreamHandler** with ANSI-coloured output for developer convenience.
"""

from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional


# ── ANSI colour codes ────────────────────────────────────────────────────────

_COLOURS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    """A log formatter that injects ANSI colour codes around the level name."""

    def __init__(self, fmt: str, datefmt: Optional[str] = None) -> None:
        super().__init__(fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        colour = _COLOURS.get(record.levelname, "")
        record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


class _StructuredFormatter(logging.Formatter):
    """Emit a JSON-like single-line record suitable for log aggregation."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        message = record.getMessage()
        return (
            f'{{"timestamp": "{self.formatTime(record, self.datefmt)}", '
            f'"level": "{record.levelname}", '
            f'"logger": "{record.name}", '
            f'"module": "{record.module}", '
            f'"function": "{record.funcName}", '
            f'"line": {record.lineno}, '
            f'"message": "{message}"}}'
        )


def setup_logger(
    name: str,
    log_dir: Optional[str] = None,
    level: int = logging.DEBUG,
) -> logging.Logger:
    """Create and return a fully-configured :class:`logging.Logger`.

    Args:
        name: Logger name (typically ``__name__`` of the calling module).
        log_dir: Directory for log files.  Created if it does not exist.
                 Defaults to ``<backend>/logs`` when *None*.
        level: Minimum log level.  Defaults to ``DEBUG``.

    Returns:
        A :class:`logging.Logger` instance with both file and console handlers.
    """
    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers when called multiple times.
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Resolve the log directory.
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # ── File handler (structured / JSON-like) ─────────────────────────────
    log_file = os.path.join(log_dir, f"{name}.log")
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(
        _StructuredFormatter(datefmt="%Y-%m-%dT%H:%M:%S"),
    )

    # ── Console handler (coloured) ────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_fmt = "%(asctime)s │ %(levelname)-18s │ %(name)s │ %(message)s"
    console_handler.setFormatter(
        _ColouredFormatter(console_fmt, datefmt="%H:%M:%S"),
    )

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
