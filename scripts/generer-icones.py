# SPDX-License-Identifier: AGPL-3.0-or-later
"""Génère les icônes de l'application installable (PWA). Usage : python scripts/generer-icones.py"""
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "app" / "static" / "icons"
BG, FG = (31, 78, 121), (255, 255, 255)  # bleu profond / blanc


def draw(size: int, maskable: bool) -> Image.Image:
    s = 4  # suréchantillonnage pour des bords lisses
    S = size * s
    im = Image.new("RGB" if maskable else "RGBA", (S, S), BG if maskable else (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if not maskable:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=BG)
    pad = S * (0.25 if maskable else 0.22)  # zone de sécurité des icônes « maskable »
    c = S / 2
    w = S - 2 * pad
    # document stylisé
    doc = [c - w * 0.30, pad, c + w * 0.30, S - pad]
    d.rounded_rectangle(doc, radius=int(w * 0.06), outline=FG, width=int(w * 0.06))
    # flèches qui compressent vers le centre
    aw = w * 0.16
    for direction in (1, -1):
        y_tip = c - direction * w * 0.06
        y_base = c - direction * w * 0.34
        d.polygon([(c - aw, y_base), (c + aw, y_base), (c, y_tip)], fill=FG)
    d.rectangle([c - w * 0.22, c - w * 0.025, c + w * 0.22, c + w * 0.025], fill=FG)
    return im.resize((size, size), Image.Resampling.LANCZOS)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (192, 512):
        draw(size, False).save(OUT / f"icon-{size}.png", optimize=True)
    draw(512, True).save(OUT / "icon-maskable-512.png", optimize=True)
    draw(180, True).save(OUT / "apple-touch-icon.png", optimize=True)
    draw(32, False).save(OUT / "favicon-32.png", optimize=True)
    print("Icônes générées dans", OUT)
