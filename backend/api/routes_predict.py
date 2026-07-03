"""
Prediction API Routes.

Provides the core ``POST /predict`` endpoint that accepts an uploaded
image, runs CSRNet crowd-density inference, generates heatmap and
overlay visualisations, persists an ``Analysis`` record, and returns
a structured JSON response.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict

from flask import Blueprint, current_app, request

from core.heatmap import generate_heatmap, generate_overlay
from core.inference import classify_density, run_inference
from database.db import db
from database.models import Analysis
from middleware.rate_limiter import rate_limit
from middleware.validators import validate_image_file
from utils.file_manager import FileManager
from utils.helpers import (
    error_response,
    format_inference_time,
    generate_analysis_id,
    success_response,
)

logger = logging.getLogger(__name__)

predict_bp = Blueprint("predict", __name__)


@predict_bp.route("/predict", methods=["POST"])
@rate_limit()
def predict() -> tuple[Dict[str, Any], int]:
    """Run crowd-density prediction on an uploaded image.

    **Request**
        ``POST /api/predict``
        Content-Type: ``multipart/form-data``
        Field: ``image`` – the image file to analyse.

    **Response 200**
        JSON object containing estimated count, density status,
        heatmap / overlay URLs, and timing information.

    **Error responses**
        * 400 – missing or invalid image file
        * 500 – inference or processing failure
        * 503 – model not loaded
    """
    # ------------------------------------------------------------------ #
    # 1. Validate the uploaded file
    # ------------------------------------------------------------------ #
    if "image" not in request.files:
        logger.warning("Predict request received without 'image' field")
        return error_response("No image file provided. Include an 'image' field in multipart/form-data.", 400)

    image_file = request.files["image"]

    validation_error = validate_image_file(image_file)
    if validation_error:
        logger.warning("Image validation failed: %s", validation_error)
        return error_response(validation_error, 400)

    try:
        # -------------------------------------------------------------- #
        # 2. Save the uploaded file
        # -------------------------------------------------------------- #
        file_manager = FileManager(current_app.config)
        saved_path, upload_filename = file_manager.save_upload(image_file)
        logger.info("Upload saved to %s", saved_path)

        # -------------------------------------------------------------- #
        # 3. Run inference
        # -------------------------------------------------------------- #
        start_time = time.time()
        inference_result = run_inference(saved_path)
        elapsed_ms = (time.time() - start_time) * 1000

        estimated_count: float = inference_result["estimated_count"]
        density_map = inference_result["density_map"]
        image_width: int = inference_result["image_dimensions"]["width"]
        image_height: int = inference_result["image_dimensions"]["height"]

        # -------------------------------------------------------------- #
        # 4. Post-processing – heatmap, overlay, classify
        # -------------------------------------------------------------- #
        heatmap_path, heatmap_filename = generate_heatmap(
            density_map, current_app.config["OUTPUT_FOLDER"]
        )
        overlay_path, overlay_filename = generate_overlay(
            saved_path, density_map, current_app.config["OUTPUT_FOLDER"]
        )
        density_status: str = classify_density(estimated_count)

        # Density-map statistics
        density_map_stats = {
            "max_density": float(density_map.max()),
            "mean_density": float(density_map.mean()),
        }

        # -------------------------------------------------------------- #
        # 5. Persist to database
        # -------------------------------------------------------------- #
        analysis_id = generate_analysis_id()

        analysis = Analysis(
            analysis_id=analysis_id,
            estimated_count=estimated_count,
            density_status=density_status,
            inference_time_ms=round(elapsed_ms, 2),
            heatmap_path=heatmap_filename,
            overlay_path=overlay_filename,
            original_image_path=upload_filename,
            image_width=image_width,
            image_height=image_height,
            max_density=density_map_stats["max_density"],
            mean_density=density_map_stats["mean_density"],
        )

        db.session.add(analysis)
        db.session.commit()
        logger.info(
            "Analysis %s persisted – count=%.1f, status=%s",
            analysis_id,
            estimated_count,
            density_status,
        )

        # -------------------------------------------------------------- #
        # 6. Build response
        # -------------------------------------------------------------- #
        data = {
            "analysis_id": analysis_id,
            "estimated_count": round(estimated_count, 1),
            "density_status": density_status,
            "inference_time": format_inference_time(elapsed_ms),
            "heatmap_url": f"/api/outputs/{heatmap_filename}",
            "overlay_url": f"/api/outputs/{overlay_filename}",
            "original_url": f"/api/uploads/{upload_filename}",
            "density_map_stats": density_map_stats,
            "image_dimensions": {"width": image_width, "height": image_height},
            "timestamp": analysis.created_at.isoformat() + "Z"
            if analysis.created_at
            else None,
        }

        return success_response(data, 200)

    except FileNotFoundError as exc:
        logger.error("File not found during prediction: %s", exc, exc_info=True)
        db.session.rollback()
        return error_response("File processing error. Please try again.", 500)

    except RuntimeError as exc:
        # Covers model-not-loaded / inference failures raised by core layer
        logger.error("Inference runtime error: %s", exc, exc_info=True)
        db.session.rollback()
        return error_response("Model inference failed. The model may not be loaded.", 503)

    except Exception as exc:  # noqa: BLE001 – catch-all for unexpected errors
        logger.exception("Unexpected error in /predict")
        db.session.rollback()
        return error_response("Internal server error. Please try again.", 500)
