"""Prepare a portrait photo for ASCII conversion.

1. Remove the background (rembg if available, else OpenCV GrabCut).
2. Boost local contrast with CLAHE so the face has real highlights/shadows.
3. Composite onto pure white -> background becomes blank space in ASCII.

Usage: python scripts/prep_photo.py source-photo.jpg [out.png]
"""
import sys

import cv2
import numpy as np
from PIL import Image


def remove_background(img_rgb: np.ndarray) -> np.ndarray:
    """Return an alpha mask (0..255) for the subject."""
    try:
        from rembg import new_session, remove

        session = new_session("u2net_human_seg")  # small, portrait-tuned model
        out = remove(Image.fromarray(img_rgb), session=session)
        return np.array(out)[:, :, 3]
    except Exception as exc:  # model download blocked, etc.
        print(f"rembg unavailable ({exc.__class__.__name__}); using GrabCut")
        h, w = img_rgb.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        rect = (int(w * 0.03), int(h * 0.02), int(w * 0.94), int(h * 0.97))
        bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
        cv2.grabCut(cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR), mask, rect,
                    bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
        alpha = np.where((mask == 1) | (mask == 3), 255, 0).astype(np.uint8)
        alpha = cv2.morphologyEx(alpha, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
        return cv2.GaussianBlur(alpha, (9, 9), 0)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg"
    dst = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

    img = np.array(Image.open(src).convert("RGB"))
    alpha = remove_background(img).astype(np.float32) / 255.0

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray).astype(np.float32)

    out = gray * alpha + 255.0 * (1.0 - alpha)
    Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(dst)
    print(f"wrote {dst}")


if __name__ == "__main__":
    main()
