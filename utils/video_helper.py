"""Video helper for Playwright regression recordings.

Captures, trims to last 20 seconds on failure, and manages video artifacts.
"""

import os
import time
from pathlib import Path
from typing import Optional


def get_videos_dir() -> Path:
    """Return Path to reports/videos directory, ensuring it exists."""
    v_dir = Path("reports/videos")
    v_dir.mkdir(parents=True, exist_ok=True)
    return v_dir


def find_videos() -> list[Path]:
    """Find failure video files in reports/videos directory.
    
    Prefers processed last20s mp4 videos, then mp4, then webm.
    """
    v_dir = get_videos_dir()
    last20s = sorted(v_dir.glob("*last20s*.mp4"), key=os.path.getmtime, reverse=True)
    if last20s:
        return last20s

    mp4s = sorted(v_dir.glob("*.mp4"), key=os.path.getmtime, reverse=True)
    if mp4s:
        return mp4s

    webms = sorted(v_dir.glob("*.webm"), key=os.path.getmtime, reverse=True)
    return webms


def trim_video_to_last_n_seconds(source_video: Path, max_seconds: int = 20) -> Optional[Path]:
    """Trim a video file to the last N seconds (default 20s) and export as MP4."""
    if not source_video.exists() or source_video.stat().st_size == 0:
        return None

    v_dir = get_videos_dir()
    output_path = v_dir / f"failure_last20s_{int(time.time())}.mp4"

    try:
        import cv2
        cap = cv2.VideoCapture(str(source_video))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720

        if total_frames <= 0 or fps <= 0:
            cap.release()
            return source_video

        duration = total_frames / fps
        start_frame = max(0, total_frames - int(max_seconds * fps))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()
        out.release()

        if output_path.exists() and output_path.stat().st_size > 1000:
            return output_path
    except Exception as e:
        print(f"[WARNING] Could not trim video with cv2: {e}")

    return source_video


def clean_passed_videos() -> None:
    """Remove video files after successful test runs to save disk and bandwidth."""
    v_dir = get_videos_dir()
    for f in v_dir.glob("*.*"):
        try:
            f.unlink()
        except Exception:
            pass
