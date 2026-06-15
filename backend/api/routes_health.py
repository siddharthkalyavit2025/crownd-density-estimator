"""
Health-Check API Routes.

Provides ``GET /health`` for a quick liveness / readiness probe and
``GET /health/model`` for detailed model diagnostics including a
live warmup-inference latency measurement.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict

import torch
from flask import Blueprint, current_app

from core.model_loader import ModelManager
from database.models import Analysis
from utils.helpers import error_response, success_response

logger = logging.getLogger(__name__)

health_bp = Blueprint("health", __name__)

# Application version — single source of truth
APP_VERSION = "1.0.0"


@health_bp.route("/health", methods=["GET"])
def health_check() -> tuple[Dict[str, Any], int]:
    """Return overall server health status.

    **Response 200**
        JSON with status, model-loaded flag, uptime, total prediction
        count, and current server time.
    """
    try:
        model_manager = ModelManager()
        model_loaded: bool = model_manager.is_loaded
        model_device: str = str(model_manager.get_device()) if model_loaded else "n/a"

        # Uptime calculation
        start_time: float | None = current_app.config.get("SERVER_START_TIME")
        uptime_seconds: float = round(time.time() - start_time, 1) if start_time else 0.0

        # Total predictions persisted in the database
        try:
            total_predictions: int = Analysis.query.count()
        except Exception:
            total_predictions = 0

        data = {
            "status": "healthy",
            "model_loaded": model_loaded,
            "model_device": model_device,
            "uptime_seconds": uptime_seconds,
            "version": APP_VERSION,
            "total_predictions": total_predictions,
            "server_time": datetime.now(timezone.utc).isoformat(),
        }

        return success_response(data, 200)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Health-check failed")
        return error_response(f"Health check error: {exc}", 500)


@health_bp.route("/health/model", methods=["GET"])
def model_health() -> tuple[Dict[str, Any], int]:
    """Return detailed model diagnostics.

    Performs a live warmup inference on a small dummy tensor and
    reports latency, architecture summary, device, and (if GPU)
    memory statistics.

    **Response 200**
        JSON with model info, warmup latency, and optional GPU memory
        metrics.

    **Response 503**
        Model is not loaded.
    """
    try:
        model_manager = ModelManager()

        if not model_manager.is_loaded:
            return error_response("Model is not loaded. Prediction endpoints are unavailable.", 503)

        device = model_manager.get_device()
        model = model_manager.get_model()

        # Architecture description
        architecture: str = model.__class__.__name__ if model else "Unknown"
        total_params: int = sum(p.numel() for p in model.parameters()) if model else 0

        # Live warmup inference
        warmup_start = time.time()
        try:
            model_manager.warmup()
            warmup_latency_ms = round((time.time() - warmup_start) * 1000, 2)
            warmup_success = True
        except Exception as warmup_exc:
            logger.warning("Warmup inference failed: %s", warmup_exc)
            warmup_latency_ms = None
            warmup_success = False

        data: Dict[str, Any] = {
            "model_loaded": True,
            "architecture": architecture,
            "total_parameters": total_params,
            "device": str(device),
            "warmup_success": warmup_success,
            "warmup_latency_ms": warmup_latency_ms,
        }

        # GPU memory info (when running on CUDA)
        if device and str(device).startswith("cuda") and torch.cuda.is_available():
            mem_allocated = round(torch.cuda.memory_allocated(device) / (1024 ** 2), 2)
            mem_reserved = round(torch.cuda.memory_reserved(device) / (1024 ** 2), 2)
            data["gpu_memory"] = {
                "allocated_mb": mem_allocated,
                "reserved_mb": mem_reserved,
            }

        return success_response(data, 200)

    except Exception as exc:  # noqa: BLE001
        logger.exception("Model health-check failed")
        return error_response(f"Model health check error: {exc}", 500)
