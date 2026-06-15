"""Video frame extraction using OpenCV.

Extracts frames from uploaded video files at configurable intervals
for batch crowd density analysis.
"""

import os
import uuid
import logging
from typing import Any, Dict, List

import cv2

logger = logging.getLogger(__name__)


def extract_frames(
    video_path: str,
    output_dir: str,
    frame_interval: int = 30,
    max_frames: int = 50,
) -> List[str]:
    """Extract frames from a video file at regular intervals.

    Args:
        video_path: Path to the video file.
        output_dir: Directory to save extracted frames as JPEG.
        frame_interval: Extract every N-th frame.
        max_frames: Maximum number of frames to extract.

    Returns:
        List of file paths to the saved frame images.

    Raises:
        ValueError: If the video cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(
        "Processing video: %d frames, %.1f FPS, interval=%d, max=%d",
        total_frames, fps, frame_interval, max_frames,
    )

    saved_paths: List[str] = []
    frame_idx = 0
    extracted = 0

    try:
        while cap.isOpened() and extracted < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % frame_interval == 0:
                filename = f"frame_{uuid.uuid4().hex[:8]}_{frame_idx:06d}.jpg"
                filepath = os.path.join(output_dir, filename)
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                saved_paths.append(filepath)
                extracted += 1

                if extracted % 10 == 0:
                    logger.debug("Extracted %d / %d frames...", extracted, max_frames)

            frame_idx += 1
    finally:
        cap.release()

    logger.info("Extracted %d frames from video.", len(saved_paths))
    return saved_paths


def get_video_info(video_path: str) -> Dict[str, Any]:
    """Return metadata about a video file.

    Args:
        video_path: Path to the video file.

    Returns:
        Dictionary with ``fps``, ``total_frames``, ``duration_seconds``,
        ``width``, ``height``, and ``codec``.

    Raises:
        ValueError: If the video cannot be opened.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
        codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
        duration = total_frames / fps if fps > 0 else 0

        return {
            "fps": round(fps, 2),
            "total_frames": total_frames,
            "duration_seconds": round(duration, 2),
            "width": width,
            "height": height,
            "codec": codec.strip(),
        }
    finally:
        cap.release()
