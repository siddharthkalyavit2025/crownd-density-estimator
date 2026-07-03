"""Video processing endpoints — frame extraction and batch analysis."""

import os
import logging

from flask import Blueprint, request, current_app

from utils.helpers import (
    success_response,
    error_response,
    generate_analysis_id,
    format_inference_time,
)
from utils.file_manager import FileManager
from middleware.rate_limiter import rate_limit
from middleware.validators import validate_video_file
from core.video_processor import extract_frames, get_video_info
from core.inference import run_inference, classify_density
from core.heatmap import generate_heatmap
from database.db import db
from database.models import Analysis

logger = logging.getLogger(__name__)

video_bp = Blueprint("video", __name__)


# ── POST /video/extract-frames ─────────────────────────────────────────────

@video_bp.route("/video/extract-frames", methods=["POST"])
@rate_limit()
def extract_video_frames():
    """Upload a video and extract frames at a configurable interval.

    Request:
        ``multipart/form-data`` with a ``video`` field.

    Query Parameters:
        frame_interval (int): Extract every N-th frame (default 30).
        max_frames (int): Maximum frames to extract (default 20).
    """
    try:
        if "video" not in request.files:
            return error_response(
                'No video file provided. Use field name "video".', 400
            )

        video_file = request.files["video"]
        allowed_exts = current_app.config.get(
            "ALLOWED_VIDEO_EXTENSIONS", {".mp4", ".avi", ".mov", ".mkv"}
        )
        validation_err = validate_video_file(video_file, allowed_exts)
        if validation_err:
            return error_response(validation_err, 400)

        frame_interval = request.args.get("frame_interval", 30, type=int)
        max_frames = request.args.get("max_frames", 20, type=int)

        # Save video
        file_manager = FileManager(current_app.config)
        video_path, video_filename = file_manager.save_upload(
            video_file, prefix="video"
        )

        # Video metadata
        info = get_video_info(video_path)

        # Extract frames into the outputs directory
        output_dir = current_app.config.get("OUTPUT_FOLDER", "outputs")
        frame_paths = extract_frames(
            video_path,
            output_dir,
            frame_interval=frame_interval,
            max_frames=max_frames,
        )

        frame_urls = [
            f"/api/outputs/{os.path.basename(p)}" for p in frame_paths
        ]

        return success_response({
            "video_info": info,
            "frames_extracted": len(frame_paths),
            "frame_urls": frame_urls,
            "frame_interval": frame_interval,
        })

    except Exception as exc:
        logger.error("Frame extraction failed: %s", exc, exc_info=True)
        return error_response(f"Video processing failed: {exc}", 500)


# ── POST /video/analyze-batch ──────────────────────────────────────────────

@video_bp.route("/video/analyze-batch", methods=["POST"])
@rate_limit()
def analyze_batch():
    """Run crowd density analysis on a batch of frame images.

    Request Body (JSON)::

        {
            "frame_urls": ["/api/outputs/frame_001.jpg", ...]
        }
    """
    try:
        data = request.get_json(silent=True)
        if not data or "frame_urls" not in data:
            return error_response(
                'Request body must contain a "frame_urls" array.', 400
            )

        frame_urls = data["frame_urls"]
        if not isinstance(frame_urls, list) or len(frame_urls) == 0:
            return error_response('"frame_urls" must be a non-empty array.', 400)

        output_dir = current_app.config.get("OUTPUT_FOLDER", "outputs")
        results = []
        counts = []

        for idx, url in enumerate(frame_urls):
            try:
                filename = os.path.basename(url)
                frame_path = os.path.join(output_dir, filename)

                if not os.path.exists(frame_path):
                    results.append({
                        "frame_index": idx,
                        "frame_url": url,
                        "error": f"Frame file not found: {filename}",
                    })
                    continue

                # Inference
                inf = run_inference(frame_path)
                status = classify_density(inf["estimated_count"])

                # Heatmap
                _, heatmap_fname = generate_heatmap(
                    inf["density_map"], output_dir, prefix="batch_heatmap"
                )

                count = inf["estimated_count"]
                counts.append(count)

                # Persist
                aid = generate_analysis_id()
                analysis = Analysis(
                    analysis_id=aid,
                    original_image_path=filename,
                    heatmap_path=heatmap_fname,
                    estimated_count=count,
                    density_status=status,
                    inference_time_ms=inf["inference_time_ms"],
                    max_density=inf["max_density"],
                    mean_density=inf["mean_density"],
                    image_width=inf["image_dimensions"]["width"],
                    image_height=inf["image_dimensions"]["height"],
                )
                db.session.add(analysis)

                results.append({
                    "frame_index": idx,
                    "frame_url": url,
                    "analysis_id": aid,
                    "estimated_count": count,
                    "density_status": status,
                    "inference_time": format_inference_time(inf["inference_time_ms"]),
                    "heatmap_url": f"/api/outputs/{heatmap_fname}",
                })

            except Exception as frame_exc:
                logger.error("Failed to analyse frame %d: %s", idx, frame_exc)
                results.append({
                    "frame_index": idx,
                    "frame_url": url,
                    "error": str(frame_exc),
                })

        db.session.commit()

        # Summary
        summary = {}
        if counts:
            summary = {
                "total_frames_analyzed": len(counts),
                "average_count": round(sum(counts) / len(counts), 1),
                "max_count": round(max(counts), 1),
                "min_count": round(min(counts), 1),
                "total_errors": len(frame_urls) - len(counts),
            }

        return success_response({"results": results, "summary": summary})

    except Exception as exc:
        db.session.rollback()
        logger.error("Batch analysis failed: %s", exc, exc_info=True)
        return error_response(f"Batch analysis failed: {exc}", 500)
