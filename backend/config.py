"""
config.py — Configuration management for the Crowd Density Estimator backend.

Provides environment-specific configuration classes and a factory function
``get_config()`` that selects the appropriate config based on the ``APP_ENV``
environment variable.
"""

from __future__ import annotations

import os
from typing import Dict, Optional, Set


# Resolve the absolute path to the backend/ directory so that all derived
# paths remain stable regardless of the working directory at startup.
_BACKEND_DIR: str = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    """Shared configuration defaults used by every environment."""

    # ── Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "change-me-in-production")

    # ── Database ──────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(_BACKEND_DIR, 'crowd_density.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False

    # ── File handling ─────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER: str = os.path.join(_BACKEND_DIR, "uploads")
    OUTPUT_FOLDER: str = os.path.join(_BACKEND_DIR, "outputs")
    LOG_FOLDER: str = os.path.join(_BACKEND_DIR, "logs")

    ALLOWED_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    ALLOWED_VIDEO_EXTENSIONS: Set[str] = {".mp4", ".avi", ".mov", ".mkv"}

    # ── Model ─────────────────────────────────────────────────────────────
    MODEL_PATH: str = os.path.join(_BACKEND_DIR, os.pardir, "csrnet_final.pth")

    # ── Rate limiting ─────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 30


class DevelopmentConfig(BaseConfig):
    """Configuration for local development."""

    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"


class ProductionConfig(BaseConfig):
    """Configuration for production deployment."""

    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"


class TestingConfig(BaseConfig):
    """Configuration for the test-suite."""

    TESTING: bool = True
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"


# ── Config registry ──────────────────────────────────────────────────────────

_CONFIG_MAP: Dict[str, type] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(config_name: Optional[str] = None) -> BaseConfig:
    """Return the configuration instance that matches ``APP_ENV``.

    Args:
        config_name: Optional override for the environment name.
            When *None*, falls back to the ``APP_ENV`` env var.

    Falls back to :class:`DevelopmentConfig` when the environment variable is
    not set or contains an unrecognised value.

    Returns:
        An instance of the appropriate configuration class.
    """
    env: str = (config_name or os.environ.get("APP_ENV", "development")).lower()
    config_cls = _CONFIG_MAP.get(env, DevelopmentConfig)
    return config_cls()
