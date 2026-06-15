"""Request validation utilities for uploaded files and pagination."""

import os
import logging
from typing import Optional, Set, Tuple

from werkzeug.datastructures import FileStorage
from PIL import Image

logger = logging.getLogger(__name__)

# Default allowed extensions
_DEFAULT_IMAGE_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
_DEFAULT_VIDEO_EXTENSIONS: Set[str] = {".mp4", ".avi", ".mov", ".mkv"}


def validate_image_file(
    file_storage: FileStorage,
    allowed_extensions: Optional[Set[str]] = None,
) -> Optional[str]:
    """Validate an uploaded image file.

    Checks:
        1. File object exists and is not ``None``
        2. Filename is not empty
        3. File extension is in the allowed set
        4. File can be opened by PIL (integrity check)

    Args:
        file_storage: Werkzeug ``FileStorage`` from the request.
        allowed_extensions: Accepted file extensions (with leading dot).

    Returns:
        ``None`` if valid, or an error message string describing the failure.
    """
    if allowed_extensions is None:
        allowed_extensions = _DEFAULT_IMAGE_EXTENSIONS

    if file_storage is None:
        return "No file provided. Please upload an image."

    if not file_storage.filename or file_storage.filename.strip() == "":
        return "Filename is empty. Please select a valid file."

    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in allowed_extensions:
        return (
            f"File type '{ext}' is not allowed. "
            f"Accepted types: {', '.join(sorted(allowed_extensions))}"
        )

    # Verify the file is actually a valid image
    try:
        file_storage.stream.seek(0)
        img = Image.open(file_storage.stream)
        img.verify()
        file_storage.stream.seek(0)  # Reset for downstream consumers
    except Exception as exc:
        return f"The uploaded file is not a valid image: {exc}"

    logger.debug("Image file validated: %s", file_storage.filename)
    return None


def validate_video_file(
    file_storage: FileStorage,
    allowed_extensions: Optional[Set[str]] = None,
) -> Optional[str]:
    """Validate an uploaded video file.

    Args:
        file_storage: Werkzeug ``FileStorage`` from the request.
        allowed_extensions: Accepted video extensions (with leading dot).

    Returns:
        ``None`` if valid, or an error message string.
    """
    if allowed_extensions is None:
        allowed_extensions = _DEFAULT_VIDEO_EXTENSIONS

    if file_storage is None:
        return "No file provided. Please upload a video."

    if not file_storage.filename or file_storage.filename.strip() == "":
        return "Filename is empty. Please select a valid video file."

    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext not in allowed_extensions:
        return (
            f"Video type '{ext}' is not allowed. "
            f"Accepted types: {', '.join(sorted(allowed_extensions))}"
        )

    logger.debug("Video file validated: %s", file_storage.filename)
    return None


def validate_pagination(
    page: Optional[str] = None,
    per_page: Optional[str] = None,
    max_per_page: int = 100,
) -> Tuple[int, int]:
    """Validate and normalise pagination query parameters.

    Args:
        page: Raw page string from query params.
        per_page: Raw per_page string from query params.
        max_per_page: Upper bound for per_page.

    Returns:
        ``(page, per_page)`` as validated integers.
    """
    try:
        page_num = int(page) if page else 1
        if page_num < 1:
            page_num = 1
    except (ValueError, TypeError):
        page_num = 1

    try:
        per_page_num = int(per_page) if per_page else 20
        if per_page_num < 1:
            per_page_num = 20
        if per_page_num > max_per_page:
            per_page_num = max_per_page
    except (ValueError, TypeError):
        per_page_num = 20

    return page_num, per_page_num
