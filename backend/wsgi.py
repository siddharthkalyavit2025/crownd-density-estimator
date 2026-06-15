"""
wsgi.py — WSGI entry point for the Crowd Density Estimator backend.

Usage with Gunicorn::

    gunicorn wsgi:application --bind 0.0.0.0:5000

Usage with the Flask development server::

    python wsgi.py
"""

from __future__ import annotations

from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run()
