"""Polish the raw iPhone photos for listing and social use.

Non-generative edits only: neutral white balance, white/black points,
midtone lift, gentle local contrast, light sharpening. No objects are
added, removed, or recolored, so polished photos need no disclaimer.

    python3 -I polish.py ../IMG_0611.jpeg ...   (default: every ../*.jpeg)
Writes carousel/edited/<name>.jpg at full resolution.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
OUT = HERE / "edited"

TARGET_MEDIAN = 0.60   # bright, airy interiors without blowing the walls
WB_STRENGTH = 0.75     # how far to pull the wall/ceiling cast toward neutral
WARMTH = 1.012         # a touch of warmth after neutralizing


def luminance(a):
    return a[..., 0] * 0.2126 + a[..., 1] * 0.7152 + a[..., 2] * 0.0722


def polish(src: Path) -> Path:
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    a = np.asarray(im, dtype=np.float32) / 255.0

    # Measure on a small copy so stats are cheap and stable.
    small = np.asarray(im.resize((im.width // 8, im.height // 8)), dtype=np.float32) / 255.0
    L = luminance(small)
    mx, mn = small.max(2), small.min(2)
    sat = (mx - mn) / (mx + 1e-6)

    # White balance from walls/ceiling: bright-ish, low-saturation pixels.
    mask = (L > 0.35) & (L < 0.92) & (sat < 0.15)
    if mask.mean() > 0.05:
        neutral = small[mask].mean(0)
        gains = (neutral.mean() / neutral) ** WB_STRENGTH
        gains *= np.array([WARMTH, 1.0, 1 / WARMTH], dtype=np.float32)
        a *= gains
        small *= gains

    # Levels: set black and white points from percentiles, protecting lights.
    L = luminance(small)
    black = min(np.percentile(L, 0.5), 0.06)
    white = max(np.percentile(L, 99.6), 0.80)
    a = (a - black) / (white - black) * 0.985 + 0.01
    small = (small - black) / (white - black) * 0.985 + 0.01

    # Midtone lift toward the target median with a gamma curve.
    med = float(np.median(np.clip(luminance(small), 1e-3, 1)))
    gamma = float(np.clip(np.log(TARGET_MEDIAN) / np.log(med), 0.72, 1.0))
    a = np.clip(a, 0, 1) ** gamma

    # Gentle shadow lift so dark floors and cabinets keep their detail.
    lum = luminance(a)[..., None]
    a = a + (0.08 * np.clip(0.35 - lum, 0, 0.35) / 0.35) * (1 - a)

    # Slight vibrance: boost low-saturation pixels more than saturated ones.
    gray = luminance(a)[..., None]
    s = (a.max(2, keepdims=True) - a.min(2, keepdims=True))
    a = gray + (a - gray) * (1 + 0.10 * (1 - np.clip(s * 3, 0, 1)))

    out = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))

    # Local contrast (large-radius unsharp) then fine sharpening.
    r = max(out.width, out.height) / 150
    out = out.filter(ImageFilter.UnsharpMask(radius=r, percent=18, threshold=2))
    out = out.filter(ImageFilter.UnsharpMask(radius=1.6, percent=55, threshold=3))

    OUT.mkdir(exist_ok=True)
    dst = OUT / (src.stem + ".jpg")
    # No EXIF on purpose: drops the phone's GPS tag before anything is shared.
    out.save(dst, quality=93, subsampling=0)
    print(f"{src.name}: gamma {gamma:.2f}, black {black:.3f}, white {white:.3f} -> {dst.relative_to(HERE.parent)}")
    return dst


if __name__ == "__main__":
    srcs = [Path(p) for p in sys.argv[1:]] or sorted(HERE.parent.glob("*.jpeg"))
    for p in srcs:
        polish(p.resolve())
