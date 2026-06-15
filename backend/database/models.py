"""SQLAlchemy ORM models for the Crowd Density Estimator."""

from datetime import datetime, timezone
from typing import Any, Dict

from .db import db


class Analysis(db.Model):
    """Stores the result of a single crowd density analysis.

    Each row captures the model prediction, generated artefacts, timing
    information, and density-map statistics for one uploaded image.
    """

    __tablename__ = "analyses"

    # Using analysis_id as PK to match routes_predict.py field naming
    analysis_id = db.Column(db.String(8), primary_key=True)
    original_image_path = db.Column(db.String(512), nullable=True)
    heatmap_path = db.Column(db.String(512), nullable=True)
    overlay_path = db.Column(db.String(512), nullable=True)
    estimated_count = db.Column(db.Float, nullable=False)
    density_status = db.Column(db.String(50), nullable=False)
    inference_time_ms = db.Column(db.Float, nullable=False)
    max_density = db.Column(db.Float, nullable=True)
    mean_density = db.Column(db.Float, nullable=True)
    image_width = db.Column(db.Integer, nullable=True)
    image_height = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the record to a JSON-friendly dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "original_image_path": self.original_image_path,
            "heatmap_path": self.heatmap_path,
            "overlay_path": self.overlay_path,
            "estimated_count": self.estimated_count,
            "density_status": self.density_status,
            "inference_time_ms": self.inference_time_ms,
            "max_density": self.max_density,
            "mean_density": self.mean_density,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<Analysis {self.analysis_id}: "
            f"count={self.estimated_count}, status={self.density_status}>"
        )
