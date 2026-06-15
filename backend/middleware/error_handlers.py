"""Custom exceptions and global Flask error handlers.

All API error responses follow a consistent envelope::

    {
        "success": false,
        "error": {
            "message": "Human-readable description",
            "code": "MACHINE_READABLE_CODE"
        }
    }
"""

import logging

from flask import jsonify
from werkzeug.exceptions import RequestEntityTooLarge

logger = logging.getLogger(__name__)


# ── Custom Exceptions ──────────────────────────────────────────────────────

class InvalidFileError(Exception):
    """Raised when an uploaded file is invalid."""

    def __init__(self, message: str = "Invalid file uploaded") -> None:
        self.message = message
        self.status_code = 400
        super().__init__(self.message)


class FileTooLargeError(Exception):
    """Raised when an uploaded file exceeds the size limit."""

    def __init__(self, message: str = "File size exceeds the maximum limit") -> None:
        self.message = message
        self.status_code = 413
        super().__init__(self.message)


class ModelNotLoadedError(Exception):
    """Raised when the ML model is not available for inference."""

    def __init__(
        self, message: str = "ML model is not loaded. Please try again later."
    ) -> None:
        self.message = message
        self.status_code = 503
        super().__init__(self.message)


class InferenceError(Exception):
    """Raised when model inference fails."""

    def __init__(
        self, message: str = "An error occurred during model inference"
    ) -> None:
        self.message = message
        self.status_code = 500
        super().__init__(self.message)


# ── Error Handler Registration ─────────────────────────────────────────────

def _make_error_response(message: str, code: str, status_code: int):
    """Create a standardised JSON error response."""
    response = jsonify({
        "success": False,
        "error": {
            "message": message,
            "code": code,
        },
    })
    response.status_code = status_code
    return response


def register_error_handlers(app) -> None:
    """Register global error handlers on the Flask application.

    Args:
        app: Flask application instance.
    """

    @app.errorhandler(InvalidFileError)
    def handle_invalid_file(error):
        logger.warning("Invalid file: %s", error.message)
        return _make_error_response(error.message, "INVALID_FILE", error.status_code)

    @app.errorhandler(FileTooLargeError)
    def handle_file_too_large(error):
        logger.warning("File too large: %s", error.message)
        return _make_error_response(error.message, "FILE_TOO_LARGE", error.status_code)

    @app.errorhandler(ModelNotLoadedError)
    def handle_model_not_loaded(error):
        logger.error("Model not loaded: %s", error.message)
        return _make_error_response(
            error.message, "MODEL_UNAVAILABLE", error.status_code
        )

    @app.errorhandler(InferenceError)
    def handle_inference_error(error):
        logger.error("Inference error: %s", error.message)
        return _make_error_response(
            error.message, "INFERENCE_FAILED", error.status_code
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_request_too_large(error):
        logger.warning("Request entity too large")
        return _make_error_response(
            "File size exceeds the maximum allowed limit (16 MB).",
            "FILE_TOO_LARGE",
            413,
        )

    @app.errorhandler(404)
    def handle_not_found(error):
        return _make_error_response(
            "The requested resource was not found.", "NOT_FOUND", 404
        )

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        return _make_error_response(
            "Method not allowed.", "METHOD_NOT_ALLOWED", 405
        )

    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error("Internal server error: %s", error)
        return _make_error_response(
            "An unexpected internal server error occurred.",
            "INTERNAL_ERROR",
            500,
        )

    logger.debug("Error handlers registered.")
