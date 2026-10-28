"""Render the floor plan carousel and its caption from a content file.

    python3 -I render.py [hampton-west.json]

Photo lookup per slide, first match wins:
    staged/<IMG>.png|jpg|jpeg|webp   (ChatGPT-staged; adds the disclaimer)
    edited/<IMG>.jpg                  (from polish.py)
    ../<IMG>.jpeg                     (raw)

Writes slides/NN-<label>.png (1080x1350) and CAPTION.md.
"""
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

HERE = Path(__file__).resolve().parent
BUILD = HERE / "build"
SLIDES = HERE / "slides"
W, H = 1080, 1350


def find_photo(name):
    for ext in ("png", "jpg", "jpeg", "webp", "PNG", "JPG", "JPEG"):
        p = HERE / "staged" / f"{name}.{ext}"
        if p.exists():
            return p, True
    for p in (HERE / "edited" / f"{name}.jpg", HERE.parent / f"{name}.jpeg"):
        if p.exists():
            return p, False
    raise FileNotFoundError(f"No photo found for {name}")


def crop(name, w, h, focus=(0.5, 0.5)):
    """Crop around a focus point to w x h, resize, and save into build/."""
    src, staged = find_photo(name)
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    ratio = w / h
    if im.width / im.height > ratio:
        cw, ch = round(im.height * ratio), im.height
    else:
        cw, ch = im.width, round(im.width / ratio)
    x = min(max(round(im.width * focus[0] - cw / 2), 0), im.width - cw)
    y = min(max(round(im.height * focus[1] - ch / 2), 0), im.height - ch)
    im = im.crop((x, y, x + cw, y + ch)).resize((w, h), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=0.8, percent=35, threshold=2))
    out = BUILD / f"{name}-{w}x{h}.jpg"
    im.save(out, quality=95, subsampling=0)
    return out.name, staged


def esc(s):
    return html.escape(s, quote=True)


def topbar(c):
    return (f'<div class="scrim-top"></div><div class="topbar"><span>{esc(c["plan"])}</span>'
            f'<span>{esc(c["community"])}</span></div>')


def page(body, cls=""):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            '<link rel="stylesheet" href="../style.css"></head>'
            f'<body><div class="slide {cls}">{body}</div></body></html>')


def build_slide(s, i, n, c):
    disc = c["staging_disclaimer"]
    t = s["type"]
    if t == "cover":
        img, staged = crop(s["photo"], W, H, s.get("focus", (0.5, 0.5)))
        body = (f'<img class="photo full" src="{img}">'
                f'<div class="scrim-bottom"></div>'
                f'<div class="copy"><div class="kicker">{esc(s["kicker"])}</div>'
                f'<h1>{esc(s["title"])}</h1><div class="sub">{esc(s["sub"])}</div></div>'
                f'<div class="swipe">{esc(s["swipe"])}<span class="arrow">&rarr;</span></div>')
        if staged:
            body += f'<div class="disclaimer-overlay">{esc(disc)}</div>'
        return page(body, "cover"), staged

    if t == "close":
        img, staged = crop(s["photo"], W, 560, s.get("focus", (0.5, 0.5)))
        specs = "".join(f"<li>{esc(x)}</li>" for x in s["specs"])
        cta = esc(s["cta"]).replace(esc(c["phone"]), f'<span class="phone">{esc(c["phone"])}</span>')
        body = (f'<img class="photo band" src="{img}">{topbar(c)}'
                f'<div class="content"><h2>{esc(s["title"])}</h2><ul>{specs}</ul>'
                f'<div class="cta">{cta}</div>'
                + (f'<div class="disclaimer">{esc(disc)}</div>' if staged else "")
                + f'<div class="footer">{esc(c["site"])}</div></div>')
        return page(body, "close"), staged

    if t == "split":
        (a, sa), (b, sb) = (crop(p, 537, H, f) for p, f in zip(s["photos"], s["focuses"]))
        photos = f'<img class="photo left" src="{a}"><img class="photo right" src="{b}">'
        staged = sa or sb
    else:
        img, staged = crop(s["photo"], W, H, s.get("focus", (0.5, 0.5)))
        photos = f'<img class="photo full" src="{img}">'

    card = (f'<div class="card"><div class="label"><span class="num">{i - 1:02d}</span>'
            f'{esc(s["label"])}</div><h2>{esc(s["title"])}</h2><p>{esc(s["body"])}</p>'
            + (f'<div class="disclaimer">{esc(disc)}</div>' if staged else "")
            + "</div>")
    return page(photos + topbar(c) + card), staged


def slug(s):
    key = s.get("label") or s["type"]
    return "".join(ch if ch.isalnum() else "-" for ch in key.lower()).strip("-")


def main(content_path):
    c = json.loads(Path(content_path).read_text())
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir()
    SLIDES.mkdir(exist_ok=True)
    for old in SLIDES.glob("*.png"):
        old.unlink()

    n = len(c["slides"])
    jobs, staged_slides = [], []
    for i, s in enumerate(c["slides"], 1):
        doc, staged = build_slide(s, i, n, c)
        name = f"{i:02d}-{slug(s)}"
        (BUILD / f"{name}.html").write_text(doc)
        jobs.append(name)
        if staged:
            staged_slides.append(i)

    subprocess.run(["node", str(HERE / "shoot.cjs"), str(BUILD), str(SLIDES), *jobs], check=True)
    write_caption(c, jobs, staged_slides)
    print(f"Rendered {n} slides to {SLIDES.relative_to(HERE.parent)}/"
          + (f" (staged: slides {', '.join(map(str, staged_slides))})" if staged_slides else " (no staged photos)"))


def write_caption(c, jobs, staged_slides):
    paras = list(c["caption"])
    if staged_slides:
        paras.append(c["staging_disclaimer"])
    lines = [f"# {c['plan']} floor plan carousel", "",
             f"{len(jobs)} slides, 1080x1350 (4:5) for Instagram and Facebook. Files are in `slides/`, in posting order.", "",
             "## Caption", "", "\n\n".join(paras), "",
             "## First comment", "", c["first_comment"], "",
             "## Alt text (one per slide)", ""]
    for i, (s, name) in enumerate(zip(c["slides"], jobs), 1):
        lines.append(f"{i}. `{name}.png`: {s['alt']}")
    lines += ["", "## Staging status", ""]
    if staged_slides:
        lines.append(f"Virtually staged photos appear on slides {', '.join(map(str, staged_slides))}. "
                     "The disclaimer is printed on those slides and added to the caption.")
    else:
        lines.append("No staged photos yet; every slide is a real, color-corrected photo, so no disclaimer is needed. "
                     "See STAGING.md to drop staged versions in.")
    lines += ["", "## Facts", "", c["facts_source"], ""]
    (HERE / "CAPTION.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "hampton-west.json")
