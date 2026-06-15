"""
utils/file_manager.py — File management utilities for the Crowd Density Estimator.

Provides the :class:`FileManager` helper that wraps common filesystem
operations such as saving uploads, generating heatmap images, and purging
stale files.
"""

from __future__ import annotations

import os
import time
import uuid
from typing import Optional

import numpy as np
from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename as _secure_filename

import logging

logger = logging.getLogger(__name__)


class FileManager:
    """High-level file-system helper initialised from the Flask app config.

    Args:
        config: A mapping (or Flask ``app.config`` proxy) containing at least
            ``UPLOAD_FOLDER``, ``OUTPUT_FOLDER``, and ``LOG_FOLDER``.
    """

    def __init__(self, config: dict) -> None:
        self.upload_folder: str = config["UPLOAD_FOLDER"]
        self.output_folder: str = config["OUTPUT_FOLDER"]
        self.log_folder: str = config["LOG_FOLDER"]

    # ── Directory management ──────────────────────────────────────────────

    def ensure_directories(self) -> None:
        """Create ``uploads/``, ``outputs/``, and ``logs/`` if they do not exist."""
        for folder in (self.upload_folder, self.output_folder, self.log_folder):
            os.makedirs(folder, exist_ok=True)
            logger.debug("Ensured directory exists: %s", folder)

    # ── Upload helpers ────────────────────────────────────────────────────

    @staticmethod
    def secure_filename(filename: str) -> str:
        """Return a sanitised version of *filename* safe for filesystem storage.

        Delegates to :func:`werkzeug.utils.secure_filename`.
        """
        return _secure_filename(filename)

    def save_upload(
        self,
        file_storage: FileStorage,
        prefix: str = "upload",
    ) -> tuple[str, str]:
        """Persist a :class:`~werkzeug.datastructures.FileStorage` to disk.

        The file is saved with a UUID-based name to avoid collisions.

        Args:
            file_storage: The incoming file from a Flask request.
            prefix: A short prefix prepended to the generated filename.

        Returns:
            A tuple of ``(absolute_path, filename)``.
        """
        original = file_storage.filename or "unknown"
        ext = os.path.splitext(original)[1].lower()
        unique_name = f"{prefix}_{uuid.uuid4().hex[:12]}{ext}"
        dest = os.path.join(self.upload_folder, unique_name)

        file_storage.save(dest)
        logger.info("Saved upload → %s (original: %s)", dest, original)
        return dest, unique_name

    # ── Output helpers ────────────────────────────────────────────────────

    def save_heatmap(
        self,
        image_array: np.ndarray,
        prefix: str = "heatmap",
    ) -> str:
        """Save a NumPy array as a PNG image in the output folder.

        Args:
            image_array: An array of shape ``(H, W)`` or ``(H, W, C)`` with
                dtype ``uint8`` or values in ``[0, 1]`` (float).
            prefix: A short prefix prepended to the generated filename.

        Returns:
            The absolute path of the saved PNG file.
        """
        unique_name = f"{prefix}_{uuid.uuid4().hex[:12]}.png"
        dest = os.path.join(self.output_folder, unique_name)

        # Normalise float arrays to uint8.
        if image_array.dtype != np.uint8:
            image_array = (image_array * 255).clip(0, 255).astype(np.uint8)

        img = Image.fromarray(image_array)
        img.save(dest, format="PNG")
        logger.info("Saved heatmap → %s", dest)
        return dest

    # ── Path helpers ──────────────────────────────────────────────────────

    def get_upload_path(self, filename: str) -> str:
        """Return the full path for *filename* inside the upload folder."""
        return os.path.join(self.upload_folder, filename)

    def get_output_path(self, filename: str) -> str:
        """Return the full path for *filename* inside the output folder."""
        return os.path.join(self.output_folder, filename)

    # ── Housekeeping ──────────────────────────────────────────────────────

    def cleanup_old_files(self, max_age_hours: float = 24) -> int:
        """Delete files in ``uploads/`` and ``outputs/`` older than *max_age_hours*.

        Args:
            max_age_hours: Maximum file age in hours before deletion.

        Returns:
            The number of files deleted.
        """
        cutoff = time.time() - (max_age_hours * 3600)
        deleted = 0

        for folder in (self.upload_folder, self.output_folder):
            if not os.path.isdir(folder):
                continue
            for entry in os.listdir(folder):
                filepath = os.path.join(folder, entry)
                if not os.path.isfile(filepath):
                    continue
                if os.path.getmtime(filepath) < cutoff:
                    try:
                        os.remove(filepath)
                        deleted += 1
                        logger.debug("Deleted stale file: %s", filepath)
                    except OSError as exc:
                        logger.warning("Failed to delete %s: %s", filepath, exc)

        logger.info("Cleanup complete — removed %d stale file(s).", deleted)
        return deleted
