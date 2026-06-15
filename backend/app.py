"""Flask application factory for the Crowd Density Estimator backend.

Wires together configuration, database, blueprints, error handlers,
CORS, static file serving, and CSRNet model loading.
"""

import os
import time
import logging

from flask import Flask, send_from_directory
from flask_cors import CORS

logger = logging.getLogger(__name__)


def create_app(config_name: str = None) -> Flask:
    """Application factory.

    Args:
        config_name: Optional override (``'development'``, ``'production'``,
            ``'testing'``).  Falls back to the ``FLASK_ENV`` env var.

    Returns:
        Fully configured Flask application instance.
    """
    app = Flask(__name__)

    # ── Configuration ────────────────────────────────────────────────────
    from config import get_config
    app.config.from_object(get_config())

    # ── Logging ──────────────────────────────────────────────────────────
    from utils.logger import setup_logger
    setup_logger("crowd_density", app.config.get("LOG_FOLDER", "logs"))

    # ── CORS ─────────────────────────────────────────────────────────────
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
            ],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })

    # ── Database ─────────────────────────────────────────────────────────
    from database.db import init_db
    init_db(app)

    # ── Directories ──────────────────────────────────────────────────────
    from utils.file_manager import FileManager
    FileManager(app.config).ensure_directories()

    # ── Blueprints ───────────────────────────────────────────────────────
    from api import register_blueprints
    register_blueprints(app)

    # ── Error handlers ───────────────────────────────────────────────────
    from middleware.error_handlers import register_error_handlers
    register_error_handlers(app)

    # ── Static file serving ──────────────────────────────────────────────
    @app.route("/api/uploads/<path:filename>")
    def serve_upload(filename):
        """Serve original uploaded images."""
        return send_from_directory(
            os.path.abspath(app.config["UPLOAD_FOLDER"]), filename
        )

    @app.route("/api/outputs/<path:filename>")
    def serve_output(filename):
        """Serve generated heatmaps, overlays, and extracted frames."""
        return send_from_directory(
            os.path.abspath(app.config["OUTPUT_FOLDER"]), filename
        )

    # ── Load ML model on startup ─────────────────────────────────────────
    with app.app_context():
        try:
            from core.model_loader import ModelManager

            model_path = os.path.abspath(app.config["MODEL_PATH"])
            logger.info("Loading CSRNet model from %s ...", model_path)

            manager = ModelManager()
            manager.load_model(model_path)
            manager.warmup()

            logger.info("Model loaded and warmed up successfully.")
        except Exception as exc:
            logger.warning(
                "Model failed to load: %s  — prediction endpoints will return 503.",
                exc,
            )

    # ── Record start time ────────────────────────────────────────────────
    app.config["SERVER_START_TIME"] = time.time()

    logger.info(
        "Crowd Density Estimator backend started (env: %s)",
        app.config.get("ENV", "development"),
    )
    return app


# ── Direct execution ─────────────────────────────────────────────────────

if __name__ == "__main__":
    application = create_app()
    application.run(host="0.0.0.0", port=5000, debug=application.config.get("DEBUG", True))
