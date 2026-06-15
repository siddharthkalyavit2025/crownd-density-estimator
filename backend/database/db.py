"""Database initialisation and session management."""

import logging

from flask_sqlalchemy import SQLAlchemy

logger = logging.getLogger(__name__)

# Global SQLAlchemy instance — shared across the application
db = SQLAlchemy()


def init_db(app) -> None:
    """Initialise the database with the Flask application.

    Registers the SQLAlchemy extension, imports all ORM models so they are
    known to the metadata, and creates any missing tables.

    Args:
        app: Flask application instance.
    """
    db.init_app(app)
    with app.app_context():
        # Import models so SQLAlchemy registers them before create_all()
        from . import models  # noqa: F401

        db.create_all()
        logger.info("Database initialised — all tables created.")
