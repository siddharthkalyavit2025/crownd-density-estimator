"""
API Blueprint Registration Module.

Provides a centralized function to register all API blueprints
with the Flask application instance.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask import Flask


def register_blueprints(app: "Flask") -> None:
    """Register all API blueprints with the Flask application.

    Each blueprint is mounted under the ``/api`` URL prefix so that
    every endpoint is reachable at ``/api/<route>``.

    Args:
        app: The Flask application instance to register blueprints with.
    """
    from .routes_predict import predict_bp
    from .routes_health import health_bp
    from .routes_analytics import analytics_bp
    from .routes_video import video_bp

    app.register_blueprint(predict_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api")
    app.register_blueprint(video_bp, url_prefix="/api")
