"""Utility functions for the Crowd Density Estimator backend."""

import uuid
from typing import Any, Dict, Optional, Tuple

from flask import jsonify




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



