"""Utility functions for the Crowd Density Estimator backend."""

import time
import uuid
from typing import Any, Dict, Optional, Tuple

from flask import jsonify


class TimingContext:
    """Context manager for measuring elapsed time in milliseconds.

    Usage::

        with TimingContext() as timer:
            do_work()
        print(f"Took {timer.elapsed_ms:.1f} ms")
    """

    def __init__(self) -> None:
        self.start_time: float = 0
        self.end_time: float = 0
        self.elapsed_ms: float = 0

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000
        return False


def format_inference_time(ms: float) -> str:
    """Format inference time in human-readable format.

    Args:
        ms: Elapsed time in milliseconds.

    Returns:
        Formatted string like ``'42 ms'`` or ``'1.20 s'``.
    """
    if ms < 1000:
        return f"{ms:.0f} ms"
    else:
        return f"{ms / 1000:.2f} s"


def classify_density(count: float, thresholds: Optional[Dict[str, int]] = None) -> str:
    """Classify crowd density based on estimated count.

    Args:
        count: Estimated crowd count.
        thresholds: Optional dict with keys ``'low'``, ``'moderate'``, ``'high'``.

    Returns:
        One of ``'Low Density'``, ``'Moderate Density'``,
        ``'High Density'``, or ``'Critical Density'``.
    """
    if thresholds is None:
        thresholds = {"low": 20, "moderate": 50, "high": 150}

    if count < thresholds.get("low", 20):
        return "Low Density"
    elif count < thresholds.get("moderate", 50):
        return "Moderate Density"
    elif count < thresholds.get("high", 150):
        return "High Density"
    else:
        return "Critical Density"


def generate_analysis_id() -> str:
    """Generate a short 8-character unique analysis ID."""
    return uuid.uuid4().hex[:8]


def success_response(data: Any, status_code: int = 200) -> Tuple:
    """Create a standardised JSON success envelope.

    Args:
        data: Payload to embed under the ``'data'`` key.
        status_code: HTTP status code (default 200).

    Returns:
        ``(Response, status_code)`` tuple for Flask.
    """
    return jsonify({"success": True, "data": data}), status_code


def error_response(
    message: str, status_code: int = 400, error_code: Optional[str] = None
) -> Tuple:
    """Create a standardised JSON error envelope.

    Args:
        message: Human-readable error description.
        status_code: HTTP status code.
        error_code: Optional machine-readable error code.

    Returns:
        ``(Response, status_code)`` tuple for Flask.
    """
    error_body: Dict[str, Any] = {"message": message}
    if error_code:
        error_body["code"] = error_code
    return jsonify({"success": False, "error": error_body}), status_code


def get_file_size_str(size_bytes: int) -> str:
    """Convert bytes to a human-readable file-size string.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Formatted string like ``'2.4 MB'``.
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
