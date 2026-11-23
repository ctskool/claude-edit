"""Builds the collage look's assets from the source images in src/, into assets/vox/ beside this file.

The sources are generated images (paper textures, newspaper pages, halftone cut-outs on magenta, tape, pin, paperclip). Everything
else is made here: torn-edge masks, scraps and clippings baked with a white torn-fibre edge, the keyed cut-outs, the marker SVGs.
Written 2026-11-16 after the first copy of these assets, which lived only in a scratch work folder, was removed by a disk clean-up.

Usage: python templates/ivory/build_kit/looks/collage/make_assets.py
       then python templates/ivory/build_kit/new_project.py <id>, which copies assets/vox into a project that lacks it.
       A project that already has a file keeps its copy: delete work/<id>/v2/editorial/assets/vox first to take the new ones.
"""
import math, random, shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter

HERE = Path(__file__).resolve().parent
SRC, OUT = HERE / "src", HERE / "assets" / "vox"
CUT = OUT / "cut"


def torn(w, h, seed, m):
    """An L mask of a hand-torn rectangle: the edge wanders slowly, with a little fibre fuzz and no saw teeth."""
    r = random.Random(seed); S = 3; W, H, M = w * S, h * S, m * S

    def edge(n):
        v, cur = [], 0.0
        for _ in range(n):
            cur = cur * 0.93 + r.uniform(-1, 1) * 0.22
            v.append(cur * 0.55 + r.uniform(-1, 1) * 0.07)
        return v
    step = 9 * S; nx, ny = W // step, H // step; pts = []
    for i, d in enumerate(edge(nx)): pts.append((M + i * (W - 2 * M) / nx, M + d * M))
    for i, d in enumerate(edge(ny)): pts.append((W - M - d * M, M + i * (H - 2 * M) / ny))
    for i, d in enumerate(edge(nx)): pts.append((W - M - i * (W - 2 * M) / nx, H - M - d * M))
    for i, d in enumerate(edge(ny)): pts.append((M + d * M, H - M - i * (H - 2 * M) / ny))
    im = Image.new("L", (W, H), 0); ImageDraw.Draw(im).polygon(pts, fill=255)
    return im.filter(ImageFilter.GaussianBlur(1.6 * S)).point(lambda p: 255 if p > 128 else 0).filter(ImageFilter.GaussianBlur(0.5 * S)).resize((w, h), Image.LANCZOS)


def mask(name, w, h, seed, m):
    rgba = Image.new("RGBA", (w, h), (255, 255, 255, 0)); rgba.putalpha(torn(w, h, seed, m)); rgba.save(OUT / name)


def tex(name, w, h, pos=(0.5, 0.5)):
    im = Image.open(SRC / f"{name}.png").convert("RGB"); sc = max(w / im.width, h / im.height) * 1.02
    im = im.resize((int(im.width * sc) + 1, int(im.height * sc) + 1), Image.LANCZOS)
    x, y = int((im.width - w) * pos[0]), int((im.height - h) * pos[1])
    return im.crop((x, y, x + w, y + h))


def bake(name, w, h, seed, m, fill, rim=(244, 240, 230), dots=True, rimw=7):
    """A torn scrap as one image: the body (a colour with a halftone screen, or a picture) inside a thin paper-white torn edge."""
    outer = torn(w, h, seed, m); rng = np.random.default_rng(seed)
    noise = Image.fromarray((rng.random((h // 6 + 1, w // 6 + 1)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(2))
    soft = np.asarray(outer.filter(ImageFilter.GaussianBlur(rimw))).astype(np.float32)
    thr = 205 + (np.asarray(noise).astype(np.float32) - 128) * 0.28
    inner = Image.fromarray(((soft > thr) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    paper = tex("whitepaper", w, h)
    if isinstance(fill, tuple):
        body = ImageChops.multiply(Image.new("RGB", (w, h), fill), paper.point(lambda p: min(255, int(p * 1.06))))
        if dots:
            d = Image.new("L", (w, h), 0); dr = ImageDraw.Draw(d)
            for yy in range(0, h, 15):
                for xx in range(0, w, 15): dr.ellipse((xx + 4, yy + 4, xx + 10.5, yy + 10.5), fill=78)
            body = Image.composite(Image.new("RGB", (w, h), (0, 0, 0)), body, d.filter(ImageFilter.GaussianBlur(0.5)))
    else:
        body = fill
    edge = ImageChops.multiply(Image.new("RGB", (w, h), rim), paper)
    out = Image.composite(body, edge, inner).convert("RGBA"); out.putalpha(outer); out.save(OUT / f"{name}.png")


def key(name, size, red_head=False, darken=None):
    """A cut-out photographed on flat magenta, keyed to transparency with the spill pulled out of its edge."""
    im = Image.open(SRC / f"{name}.png").convert("RGB"); im.thumbnail((size, size), Image.LANCZOS); a = np.asarray(im).astype(np.int32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = np.clip((np.minimum(r, b) - g) / (90.0 if red_head or darken else 110.0), 0, 1)
    if red_head: mag = np.where((r > 150) & (b < 120), 0, mag)
    al = Image.fromarray((255 * (1 - mag)).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    spill = np.zeros_like(r) if red_head else np.clip(np.minimum(r, b) - g, 0, 255)
    a2 = a.copy(); a2[..., 0] -= spill; a2[..., 2] -= spill
    rgb = Image.fromarray(np.clip(a2, 0, 255).astype(np.uint8))
    if darken: rgb = ImageEnhance.Color(ImageEnhance.Brightness(rgb).enhance(darken)).enhance(1.35)
    out = rgb.convert("RGBA"); out.putalpha(al)
    if red_head or darken or name == "paperclip": out = out.crop(out.getbbox())
    out.save(CUT / f"{name}.png")


def svgs():
    r = random.Random(9)
    def ring(cx, cy, rx, ry, turns=2.15):
        p = []
        for i in range(140):
            a = -1.9 + turns * 2 * math.pi * i / 139; k = 1 + 0.035 * math.sin(a * 3.1) + 0.02 * i / 139
            p.append(f"{cx + rx * k * math.cos(a):.1f},{cy + ry * k * math.sin(a):.1f}")
        return "M" + " L".join(p)
    (OUT / "ring.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400"><path d="{ring(200, 200, 172, 160)}" fill="none" stroke="#d93a26" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>', encoding="utf8")
    u = "M8,22 " + " ".join(f"L{8 + i * 9.6:.1f},{22 + 7 * math.sin(i * 0.5) + r.uniform(-3, 3):.1f}" for i in range(1, 41))
    (OUT / "scribble.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 44" preserveAspectRatio="none"><path d="{u}" fill="none" stroke="#d93a26" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>', encoding="utf8")
    arrow = lambda col: f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><g fill="none" stroke="{col}" stroke-width="13" stroke-linecap="round" stroke-linejoin="round"><path d="M176,172 C150,120 112,82 40,48"/><path d="M92,34 L38,47 L62,98"/></g></svg>'
    for n, c in (("arrow-k", "#141414"), ("arrow-y", "#fff200"), ("arrow-r", "#d93a26")): (OUT / f"{n}.svg").write_text(arrow(c), encoding="utf8")
    marks = lambda col, lo, hi: f'<svg xmlns="http://www.w3.org/2000/svg" width="270" height="270"><g stroke="{col}" stroke-width="1.5"><path d="M0,0.75H270M0.75,0V270" opacity="{lo}"/><path d="M-14,0.75H14M0.75,-14V14M256,0.75H284M270.75,-14V14M-14,270.75H14M0.75,256V284" opacity="{hi}"/></g></svg>'
    (OUT / "marks-faint.svg").write_text(marks("#000", ".10", ".38"), encoding="utf8")
    (OUT / "marks-k.svg").write_text(marks("#000", ".35", "1"), encoding="utf8"); (OUT / "marks-w.svg").write_text(marks("#fff", ".35", "1"), encoding="utf8")
    r2 = random.Random(3)
    top = " ".join(f"L{x},{6 + r2.uniform(-2.5, 2.5):.1f}" for x in range(10, 391, 20)); bot = " ".join(f"L{x},{54 + r2.uniform(-2.5, 2.5):.1f}" for x in range(390, 9, -20))
    (OUT / "swipe.svg").write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 60" preserveAspectRatio="none"><path d="M4,9 {top} L397,12 L394,30 L398,50 {bot} L3,52 L7,30 Z" fill="#fff200"/></svg>', encoding="utf8")


def main():
    CUT.mkdir(parents=True, exist_ok=True)
    # paper textures, kept small: a large texture dropped out of the browser's decode cache and left one step with blank sheets
    for n, w in (("whitepaper", 720), ("yellowpaper", 600), ("darkpaper", 540), ("greypaper", 810)):
        im = Image.open(SRC / f"{n}.png").convert("RGB"); im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(OUT / f"{n}.png")
    mask("torn-a.png", 1000, 720, 1, 22); mask("torn-b.png", 1000, 720, 2, 22); mask("torn-strip.png", 900, 180, 4, 9); mask("torn-sq.png", 500, 500, 5, 20); mask("torn-tall.png", 700, 900, 6, 24)
    bake("scrap-teal", 700, 580, 11, 26, (47, 128, 136)); bake("scrap-red", 700, 600, 12, 26, (217, 81, 44)); bake("scrap-blue", 700, 580, 13, 26, (44, 95, 163))
    bake("scrap-yellow", 1000, 720, 14, 22, (255, 240, 0), dots=False); bake("scrap-yellow-sq", 500, 500, 15, 20, (255, 240, 0), dots=False)
    for i, n in enumerate(("newsprint", "newsprint2", "newsprint3")):
        bake(f"clip-{i + 1}", 700, 900, 20 + i, 24, tex(n, 700, 900), rim=(236, 226, 200), rimw=5)
    bake("clip-wide", 1000, 720, 31, 22, tex("newsprint", 1000, 720, (0.3, 0.7)), rim=(236, 226, 200), rimw=5)
    for n in ("crt", "brush", "magnifier", "pointer", "camera", "megaphone"): key(n, 700)
    key("tape", 600, darken=0.84); key("paperclip", 600); key("pin", 600, red_head=True)
    svgs()
    font = Path("C:/Windows/Fonts/ariblk.ttf")
    if font.is_file(): shutil.copy2(font, OUT / "ariblk.ttf")  # Arial Black: fine for Chase's own videos, a free font is needed before this ships publicly
    print(len(list(OUT.rglob("*.*"))), "files in", OUT)


if __name__ == "__main__":
    main()
