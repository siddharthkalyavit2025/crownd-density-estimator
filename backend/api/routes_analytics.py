"""Analytics endpoints — history, statistics, and per-analysis CRUD."""

import os
import logging
from typing import Any, Dict

from flask import Blueprint, request
from sqlalchemy import func, desc, asc

from database.db import db
from database.models import Analysis
from utils.helpers import success_response, error_response
from middleware.validators import validate_pagination

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)


# ── GET /analytics/history ─────────────────────────────────────────────────

@analytics_bp.route("/analytics/history", methods=["GET"])
def get_history():
    """Return paginated analysis history.

    Query Parameters:
        page (int): Page number (default 1).
        per_page (int): Results per page (default 20, max 100).
        sort_by (str): Column to sort by (default ``created_at``).
        order (str): ``'asc'`` or ``'desc'`` (default ``'desc'``).
    """
    try:
        page, per_page = validate_pagination(
            request.args.get("page"),
            request.args.get("per_page"),
        )
        sort_by = request.args.get("sort_by", "created_at")
        order = request.args.get("order", "desc")

        allowed_sort = {
            "created_at", "estimated_count", "density_status", "inference_time_ms"
        }
        if sort_by not in allowed_sort:
            sort_by = "created_at"

        col = getattr(Analysis, sort_by)
        query = Analysis.query.order_by(
            asc(col) if order == "asc" else desc(col)
        )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return success_response({
            "analyses": [a.to_dict() for a in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": pagination.total,
                "total_pages": pagination.pages,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
        })

    except Exception as exc:
        logger.error("Failed to fetch history: %s", exc)
        return error_response(f"Failed to fetch analysis history: {exc}", 500)


# ── GET /analytics/stats ───────────────────────────────────────────────────

@analytics_bp.route("/analytics/stats", methods=["GET"])
def get_stats():
    """Return aggregate statistics across all analyses."""
    try:
        total = Analysis.query.count()

        if total == 0:
            return success_response({
                "total_analyses": 0,
                "average_count": 0,
                "peak_count": 0,
                "min_count": 0,
                "average_inference_ms": 0,
                "density_distribution": {},
                "recent_trend": [],
            })

        stats = db.session.query(
            func.avg(Analysis.estimated_count).label("avg_count"),
            func.max(Analysis.estimated_count).label("max_count"),
            func.min(Analysis.estimated_count).label("min_count"),
            func.avg(Analysis.inference_time_ms).label("avg_inference"),
        ).first()

        # Per-status counts
        dist_rows = (
            db.session.query(Analysis.density_status, func.count(Analysis.analysis_id))
            .group_by(Analysis.density_status)
            .all()
        )
        density_distribution = {row[0]: row[1] for row in dist_rows}

        # Last 10 analyses (chronological order)
        recent = (
            Analysis.query.order_by(desc(Analysis.created_at)).limit(10).all()
        )
        recent_trend = [a.estimated_count for a in reversed(recent)]

        return success_response({
            "total_analyses": total,
            "average_count": round(float(stats.avg_count or 0), 1),
            "peak_count": round(float(stats.max_count or 0), 1),
            "min_count": round(float(stats.min_count or 0), 1),
            "average_inference_ms": round(float(stats.avg_inference or 0), 1),
            "density_distribution": density_distribution,
            "recent_trend": recent_trend,
        })

    except Exception as exc:
        logger.error("Failed to compute stats: %s", exc)
        return error_response(f"Failed to compute statistics: {exc}", 500)


# ── GET /analytics/<id> ────────────────────────────────────────────────────

@analytics_bp.route("/analytics/<analysis_id>", methods=["GET"])
def get_analysis(analysis_id: str):
    """Return a single analysis by ID."""
    analysis = db.session.get(Analysis, analysis_id)
    if not analysis:
        return error_response(f"Analysis '{analysis_id}' not found.", 404)
    return success_response(analysis.to_dict())


# ── DELETE /analytics/<id> ─────────────────────────────────────────────────

@analytics_bp.route("/analytics/<analysis_id>", methods=["DELETE"])
def delete_analysis(analysis_id: str):
    """Delete an analysis record and its associated files."""
    try:
        analysis = db.session.get(Analysis, analysis_id)
        if not analysis:
            return error_response(f"Analysis '{analysis_id}' not found.", 404)

        # Remove associated files from disk
        for filepath in [
            analysis.original_image_path,
            analysis.heatmap_path,
            analysis.overlay_path,
        ]:
            if filepath and os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    logger.debug("Deleted file: %s", filepath)
                except OSError as e:
                    logger.warning("Failed to delete %s: %s", filepath, e)

        db.session.delete(analysis)
        db.session.commit()

        logger.info("Deleted analysis: %s", analysis_id)
        return success_response({
            "message": f"Analysis '{analysis_id}' deleted successfully."
        })

    except Exception as exc:
        db.session.rollback()
        logger.error("Failed to delete analysis %s: %s", analysis_id, exc)
        return error_response(f"Failed to delete analysis: {exc}", 500)
