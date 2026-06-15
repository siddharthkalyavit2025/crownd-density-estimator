"""Density map → heatmap image generation.

Converts raw CSRNet density map outputs into visual heatmap images
and overlay composites for display in the frontend.
"""

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend — MUST be before pyplot import

import io
import os
import base64
import uuid
import logging
from typing import Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from PIL import Image

logger = logging.getLogger(__name__)


def generate_heatmap(
    density_map: np.ndarray,
    output_dir: str,
    prefix: str = "heatmap",
) -> Tuple[str, str]:
    """Generate a standalone heatmap image from a density map.

    Args:
        density_map: 2-D numpy array from CSRNet output.
        output_dir: Directory to save the heatmap image.
        prefix: Filename prefix.

    Returns:
        Tuple of ``(full_path, filename)`` of the saved heatmap.
    """
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.png"
    filepath = os.path.join(output_dir, filename)

    try:
        fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=100)
        im = ax.imshow(density_map, cmap="jet", interpolation="bilinear")
        plt.colorbar(im, ax=ax, shrink=0.8, label="Density")
        ax.set_axis_off()
        fig.tight_layout(pad=0.5)
        fig.savefig(filepath, bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)

        logger.info("Heatmap saved: %s (shape: %s)", filename, density_map.shape)
        return filepath, filename

    except Exception:
        plt.close("all")
        logger.exception("Failed to generate heatmap")
        raise


def generate_overlay(
    original_image_path: str,
    density_map: np.ndarray,
    output_dir: str,
    alpha: float = 0.5,
    prefix: str = "overlay",
) -> Tuple[str, str]:
    """Generate a heatmap overlaid on the original image.

    Args:
        original_image_path: Path to the original uploaded image.
        density_map: 2-D numpy array from CSRNet output.
        output_dir: Directory to save the overlay image.
        alpha: Blending factor (0 = original only, 1 = heatmap only).
        prefix: Filename prefix.

    Returns:
        Tuple of ``(full_path, filename)`` of the saved overlay.
    """
    filename = f"{prefix}_{uuid.uuid4().hex[:12]}.png"
    filepath = os.path.join(output_dir, filename)

    try:
        original = Image.open(original_image_path).convert("RGB")
        orig_w, orig_h = original.size

        # Normalise density map to [0, 1]
        dm = density_map.astype(np.float64).copy()
        dm_min, dm_max = dm.min(), dm.max()
        if dm_max - dm_min > 1e-8:
            dm = (dm - dm_min) / (dm_max - dm_min)
        else:
            dm = np.zeros_like(dm)

        # Apply jet colourmap → RGBA float array (H, W, 4)
        colormap = cm.get_cmap("jet")
        heatmap_rgba = colormap(dm)

        # Convert to RGB uint8 PIL image and resize
        heatmap_rgb = (heatmap_rgba[:, :, :3] * 255).astype(np.uint8)
        heatmap_image = Image.fromarray(heatmap_rgb, "RGB")
        heatmap_image = heatmap_image.resize((orig_w, orig_h), Image.BILINEAR)

        # Blend
        blended = Image.blend(original, heatmap_image, alpha=alpha)
        blended.save(filepath, "PNG")

        logger.info("Overlay saved: %s (%dx%d)", filename, orig_w, orig_h)
        return filepath, filename

    except Exception:
        logger.exception("Failed to generate overlay")
        raise


def generate_heatmap_base64(density_map: np.ndarray) -> str:
    """Generate a heatmap and return as a base64-encoded PNG data-URI.

    Args:
        density_map: 2-D numpy array from CSRNet output.

    Returns:
        Base64 string with ``data:image/png;base64,`` prefix.
    """
    try:
        fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=100)
        im = ax.imshow(density_map, cmap="jet", interpolation="bilinear")
        plt.colorbar(im, ax=ax, shrink=0.8, label="Density")
        ax.set_axis_off()
        fig.tight_layout(pad=0.5)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.1)
        plt.close(fig)

        buf.seek(0)
        encoded = base64.b64encode(buf.read()).decode("utf-8")

        logger.debug("Generated base64 heatmap (%d chars)", len(encoded))
        return f"data:image/png;base64,{encoded}"

    except Exception:
        plt.close("all")
        logger.exception("Failed to generate base64 heatmap")
        raise
