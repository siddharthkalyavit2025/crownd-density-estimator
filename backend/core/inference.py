"""Inference pipeline for CSRNet crowd density estimation.

Handles image preprocessing, model inference, and result extraction.
Does NOT perform any model training — inference only.
"""

import time
import logging
from typing import Any, Dict, Tuple, Union

import torch
import numpy as np
from PIL import Image
from torchvision import transforms

from .model_loader import ModelManager

logger = logging.getLogger(__name__)

# ImageNet normalisation — must match what was used during CSRNet training
IMAGE_TRANSFORM = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def preprocess_image(
    image_input: Union[str, Image.Image],
) -> Tuple[torch.Tensor, Image.Image]:
    """Load and preprocess an image for CSRNet inference.

    Args:
        image_input: Either a file path string or a PIL Image.

    Returns:
        Tuple of (preprocessed tensor ``[1, 3, H, W]``, original PIL Image).

    Raises:
        ValueError: If *image_input* is not a supported type.
        FileNotFoundError: If a path is given but does not exist.
    """
    if isinstance(image_input, str):
        original_image = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        original_image = image_input.convert("RGB")
    else:
        raise ValueError(f"Unsupported image input type: {type(image_input)}")

    img_tensor = IMAGE_TRANSFORM(original_image)
    img_tensor = img_tensor.unsqueeze(0)  # batch dimension → [1, 3, H, W]

    # Move to the same device as the model
    manager = ModelManager()
    device = manager.get_device()
    img_tensor = img_tensor.to(device)

    logger.debug("Preprocessed image: shape=%s, device=%s", img_tensor.shape, device)
    return img_tensor, original_image


def run_inference(image_input: Union[str, Image.Image]) -> Dict[str, Any]:
    """Run CSRNet inference on an image and return full results.

    Args:
        image_input: File path or PIL Image to analyse.

    Returns:
        Dictionary with keys:
            - ``estimated_count`` (float): Predicted crowd count
            - ``density_map`` (np.ndarray): 2-D density map
            - ``inference_time_ms`` (float): Time in milliseconds
            - ``image_dimensions`` (dict): ``{'width': int, 'height': int}``
            - ``max_density`` (float): Peak value in density map
            - ``mean_density`` (float): Mean value in density map
    """
    manager = ModelManager()
    model = manager.get_model()

    start = time.perf_counter()

    # Preprocess
    img_tensor, original_image = preprocess_image(image_input)
    width, height = original_image.size

    # Forward pass — no gradient tracking
    with torch.no_grad():
        output = model(img_tensor)

    # Extract scalars
    predicted_count = abs(output.sum().item())  # abs guards against negative artefacts
    density_map = output.squeeze().cpu().numpy()

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Density map statistics
    max_density = float(np.max(density_map)) if density_map.size > 0 else 0.0
    mean_density = float(np.mean(density_map)) if density_map.size > 0 else 0.0

    result: Dict[str, Any] = {
        "estimated_count": round(predicted_count, 1),
        "density_map": density_map,
        "inference_time_ms": round(elapsed_ms, 2),
        "image_dimensions": {"width": width, "height": height},
        "max_density": round(max_density, 6),
        "mean_density": round(mean_density, 6),
    }

    logger.info(
        "Inference complete: count=%.1f, time=%.1fms, map_shape=%s",
        result["estimated_count"],
        result["inference_time_ms"],
        density_map.shape,
    )
    return result


def classify_density(count: float) -> str:
    """Classify crowd density level based on estimated count.

    Args:
        count: Estimated crowd count.

    Returns:
        Human-readable density classification string.
    """
    if count < 20:
        return "Low Density"
    elif count < 50:
        return "Moderate Density"
    elif count < 150:
        return "High Density"
    else:
        return "Critical Density"
