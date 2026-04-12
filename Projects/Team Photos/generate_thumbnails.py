#!/usr/bin/env python3
"""
generate_thumbnails.py — Team Photos thumbnail pipeline

Detects faces in team member portrait images, crops tight around the face,
and outputs 256×256px square WebP thumbnails for use as roster avatars.

Face detection uses MediaPipe Face Detection (short-range model) as the
primary detector, with OpenCV Haar cascades (frontal + profile, including
horizontally-flipped detection) retained as a fallback for images where
MediaPipe returns no result.

Priority order:
  1. Manual override from overrides.json (highest)
  2. MediaPipe face detection
  3. Haar cascade detection (frontal + profile)
  4. Centre-crop fallback (no face detected)

Dependencies:
    pip install Pillow opencv-python mediapipe

Usage:
    python generate_thumbnails.py --theme dossier
    python generate_thumbnails.py --theme dossier --dry-run
    python generate_thumbnails.py --theme dossier --padding 0.5
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

THUMBNAIL_SIZE = 256
DEFAULT_PADDING = 0.4  # 40% of face bbox on each side, tunable via --padding

# Cascade classifiers — all bundled with OpenCV, no downloads needed
_FRONTAL = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_PROFILE = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

# Detection params tuned for high-grain, high-contrast B&W images
_SCALE_FACTOR = 1.05   # finer steps for thorough search
_MIN_NEIGHBORS = 3     # permissive threshold for challenging inputs
_MIN_SIZE = (60, 60)   # minimum face size in pixels

# MediaPipe face detection setup (Tasks API, mediapipe ≥ 0.10).
# The short-range BlazeFace model is bundled alongside this script.
# Falls back gracefully to Haar if mediapipe is absent or the model file
# is not found.
_MODEL_FILE = Path(__file__).parent / "blaze_face_short_range.tflite"

try:
    import mediapipe as mp
    if not _MODEL_FILE.exists():
        raise FileNotFoundError(f"MediaPipe model not found: {_MODEL_FILE}")
    _mp_BaseOptions = mp.tasks.BaseOptions
    _mp_FaceDetector = mp.tasks.vision.FaceDetector
    _mp_FaceDetectorOptions = mp.tasks.vision.FaceDetectorOptions
    _MEDIAPIPE_AVAILABLE = True
except (ImportError, FileNotFoundError):
    _mp_BaseOptions = None
    _mp_FaceDetector = None
    _mp_FaceDetectorOptions = None
    _MEDIAPIPE_AVAILABLE = False


def setup_logging():
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")


def load_image(path: Path) -> tuple:
    """Load image as PIL Image and convert to grayscale numpy array for detection."""
    pil_img = Image.open(path)
    gray = np.array(pil_img.convert("L"))
    return pil_img, gray


def detect_face_mediapipe(pil_img: Image.Image) -> tuple | None:
    """
    Detect the largest face using MediaPipe Face Detection (Tasks API, short-range model).
    Returns (x, y, w, h) in pixel coordinates, or None if no face found.
    """
    if not _MEDIAPIPE_AVAILABLE:
        return None

    # MediaPipe Tasks API requires an RGB numpy array wrapped in mp.Image
    rgb = np.array(pil_img.convert("RGB"))
    img_h, img_w = rgb.shape[:2]
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    options = _mp_FaceDetectorOptions(
        base_options=_mp_BaseOptions(model_asset_path=str(_MODEL_FILE)),
        min_detection_confidence=0.5,
    )
    with _mp_FaceDetector.create_from_options(options) as detector:
        result = detector.detect(mp_image)

    if not result.detections:
        return None

    # Pick the detection with the largest bounding box area
    best = None
    best_area = 0
    for detection in result.detections:
        bb = detection.bounding_box
        x, y, w, h = bb.origin_x, bb.origin_y, bb.width, bb.height
        # Clamp to image bounds
        x = max(0, x)
        y = max(0, y)
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        area = w * h
        if area > best_area:
            best_area = area
            best = (x, y, w, h)

    return best


def _run_cascade(gray: np.ndarray, cascade) -> list:
    """Run a single cascade on a grayscale image. Returns list of (x,y,w,h)."""
    if not cascade:
        return []
    result = cascade.detectMultiScale(
        gray,
        scaleFactor=_SCALE_FACTOR,
        minNeighbors=_MIN_NEIGHBORS,
        minSize=_MIN_SIZE,
    )
    # detectMultiScale returns () when nothing found, ndarray otherwise
    return result.tolist() if isinstance(result, np.ndarray) else []


def detect_face_haar(gray: np.ndarray) -> tuple | None:
    """
    Detect the largest face using frontal then profile Haar cascades.
    Also tries the horizontally-flipped image for right-facing profiles.
    Returns (x, y, w, h) or None.
    """
    h, w = gray.shape[:2]

    candidates = []

    # 1. Frontal
    candidates += _run_cascade(gray, _FRONTAL)

    # 2. Profile (left-facing)
    candidates += _run_cascade(gray, _PROFILE)

    # 3. Profile (right-facing) — flip, detect, flip coordinates back
    flipped = cv2.flip(gray, 1)
    for (x, y, bw, bh) in _run_cascade(flipped, _PROFILE):
        candidates.append((w - x - bw, y, bw, bh))

    if not candidates:
        return None

    # Return the largest detected face
    return max(candidates, key=lambda r: r[2] * r[3])


def face_crop_box(bbox: tuple, img_w: int, img_h: int, padding: float) -> tuple:
    """
    Add padding around a face bounding box and make it square.
    Returns (left, top, right, bottom) for PIL crop, clamped to image bounds.
    """
    x, y, bw, bh = bbox

    # Add padding
    pad_x = int(bw * padding)
    pad_y = int(bh * padding)
    x1, y1 = x - pad_x, y - pad_y
    x2, y2 = x + bw + pad_x, y + bh + pad_y

    # Make square around the centre of the padded region
    crop_w, crop_h = x2 - x1, y2 - y1
    side = max(crop_w, crop_h)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    x1, y1 = cx - side // 2, cy - side // 2
    x2, y2 = x1 + side, y1 + side

    # Clamp to image bounds
    return (max(0, x1), max(0, y1), min(img_w, x2), min(img_h, y2))


def center_crop_box(img_w: int, img_h: int) -> tuple:
    """Fallback: centred square crop of the full image."""
    side = min(img_w, img_h)
    cx, cy = img_w // 2, img_h // 2
    return (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)


def load_overrides(theme_dir: Path) -> dict:
    """Load manual bbox overrides from overrides.json if present."""
    path = theme_dir / "overrides.json"
    if not path.exists():
        return {}
    with open(path) as f:
        data = json.load(f)
    return {k: tuple(v) for k, v in data.items() if not k.startswith("_")}


def process_image(src: Path, out: Path, padding: float, dry_run: bool, override: tuple | None = None) -> bool:
    """
    Process a single image. Logs outcome. Returns True on success.
    Never raises — logs failures and returns False.
    """
    try:
        pil_img, gray = load_image(src)
        img_w, img_h = pil_img.size

        if override:
            bbox = override
            method = "face-crop (manual override)"
        else:
            # Try MediaPipe first
            bbox = detect_face_mediapipe(pil_img)
            if bbox:
                method = "face-crop (mediapipe)"
            else:
                # Fall back to Haar cascades
                bbox = detect_face_haar(gray)
                method = "face-crop (haar fallback)" if bbox else None

        if bbox:
            crop_box = face_crop_box(bbox, img_w, img_h, padding)
            detail = f"face={bbox} crop={crop_box}"
        else:
            crop_box = center_crop_box(img_w, img_h)
            method = "centre-crop (no face detected)"
            detail = f"crop={crop_box}"

        prefix = "[DRY RUN] " if dry_run else ""
        logging.info(f"{prefix}OK  {src.name} → thumbnails/{out.name}  [{method}] {detail}")

        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            cropped = pil_img.crop(crop_box)
            thumb = cropped.resize((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.LANCZOS)
            thumb.save(out, "WEBP", quality=90)

        return True

    except Exception as exc:
        logging.warning(f"FAIL {src.name} — {exc}")
        return False


def run(theme: str, padding: float, dry_run: bool):
    base = Path(__file__).parent
    theme_dir = base / "themes" / theme
    out_dir = theme_dir / "thumbnails"

    if not theme_dir.exists():
        logging.error(f"Theme directory not found: {theme_dir}")
        sys.exit(1)

    # All webp files in the theme root — exclude the thumbnails subdirectory
    sources = sorted(p for p in theme_dir.glob("*.webp"))

    if not sources:
        logging.warning(f"No .webp source files found in {theme_dir}")
        return

    overrides = load_overrides(theme_dir)
    if overrides:
        logging.info(f"Manual overrides loaded for: {', '.join(overrides.keys())}")

    mp_status = "available" if _MEDIAPIPE_AVAILABLE else "NOT available (install mediapipe) — using Haar only"
    logging.info(
        f"Theme: {theme} | Sources: {len(sources)} | "
        f"Output: {out_dir} | Padding: {padding} | Dry run: {dry_run} | MediaPipe: {mp_status}"
    )

    ok, failed = 0, 0
    for src in sources:
        out = out_dir / src.name
        override = overrides.get(src.name)
        if process_image(src, out, padding, dry_run, override=override):
            ok += 1
        else:
            failed += 1

    logging.info(f"{'─' * 50}")
    logging.info(f"Done. {ok} succeeded, {failed} failed.")
    if failed:
        logging.warning("One or more images failed — review above and consider manual crop.")


def main():
    parser = argparse.ArgumentParser(
        description="Generate face-crop thumbnails for Team Photos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--theme", default="dossier",
        help="Theme directory name under themes/ (default: dossier)"
    )
    parser.add_argument(
        "--padding", type=float, default=DEFAULT_PADDING,
        help=f"Padding as fraction of face bbox on each side (default: {DEFAULT_PADDING})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be done without writing any files"
    )
    args = parser.parse_args()

    setup_logging()
    run(args.theme, args.padding, args.dry_run)


if __name__ == "__main__":
    main()
