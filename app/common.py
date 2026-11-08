# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) pour la génération de code.
"""Outils communs aux différents types de fichiers."""
import io

from PIL import Image

try:  # HEIC / HEIF (photos d'iPhone)
    import pillow_heif

    pillow_heif.register_heif_opener()
    HEIF = True
except Exception:  # noqa: BLE001
    HEIF = False

Image.MAX_IMAGE_PIXELS = 400_000_000  # grandes numérisations acceptées, bombes de décompression refusées

# Cadres maximaux (paysage) ; inversés automatiquement pour les images en portrait
RESOLUTIONS = {"fullhd": (1920, 1080), "hdready": (1280, 720), "original": None}
QUALITY = {"haute": 90, "equilibree": 82, "compacte": 70}


class UserError(Exception):
    """Erreur à afficher telle quelle à l'utilisateur."""


def fit(w: int, h: int, box):
    """Dimensions réduites pour tenir dans `box` (sans jamais agrandir)."""
    if not box:
        return w, h
    bw, bh = box if w >= h else (box[1], box[0])
    f = min(1.0, bw / w, bh / h)
    return max(1, round(w * f)), max(1, round(h * f))


def fit_long_side(w: int, h: int, max_side: int):
    f = min(1.0, max_side / max(w, h))
    return max(1, round(w * f)), max(1, round(h * f))


def has_alpha(im: Image.Image) -> bool:
    if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
        return im.convert("RGBA").getchannel("A").getextrema()[0] < 255
    return False


def flatten(im: Image.Image, color="white") -> Image.Image:
    """Supprime la transparence (fond blanc) et renvoie une image RVB."""
    if im.mode in ("RGB", "L"):
        return im
    if im.mode == "CMYK":
        return im.convert("RGB")
    rgba = im.convert("RGBA")
    bg = Image.new("RGB", rgba.size, color)
    bg.paste(rgba, mask=rgba.getchannel("A"))
    return bg


def resize(im: Image.Image, size) -> Image.Image:
    if im.size == tuple(size):
        return im
    if im.mode in ("P", "1"):
        im = im.convert("RGBA" if has_alpha(im) else "RGB")
    return im.resize(size, Image.Resampling.LANCZOS)


def encode(im: Image.Image, fmt: str, quality: int, png_colors=False, icc=None) -> bytes:
    """Encode une image dans le format demandé, avec des réglages de compression."""
    buf = io.BytesIO()
    extra = {"icc_profile": icc} if icc else {}
    if fmt == "JPEG":
        if im.mode not in ("RGB", "L", "CMYK"):
            im = flatten(im)
        im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True, **extra)
    elif fmt == "PNG":
        if png_colors and im.mode not in ("P", "1", "L"):
            alpha = has_alpha(im)
            im = im.convert("RGBA" if alpha else "RGB")
            method = Image.Quantize.FASTOCTREE if alpha else Image.Quantize.MEDIANCUT
            im = im.quantize(256, method=method, dither=Image.Dither.FLOYDSTEINBERG)
        im.save(buf, "PNG", optimize=True, **extra)
    elif fmt == "WEBP":
        im.save(buf, "WEBP", quality=quality, method=6, **extra)
    elif fmt == "TIFF":
        im.save(buf, "TIFF", compression="tiff_adobe_deflate", **extra)
    elif fmt == "GIF":
        im.save(buf, "GIF", optimize=True)
    elif fmt == "BMP":
        (im if im.mode in ("RGB", "L", "P", "1") else flatten(im)).save(buf, "BMP")
    elif fmt == "HEIF":
        if not HEIF:
            raise UserError("Le format HEIC/HEIF n'est pas disponible sur cette installation.")
        im.save(buf, "HEIF", quality=quality)
    elif fmt == "AVIF":
        im.save(buf, "AVIF", quality=quality)
    else:
        raise UserError(f"Format d'image non pris en charge : {fmt}")
    return buf.getvalue()


def human(n: float) -> str:
    for unit in ("o", "Ko", "Mo", "Go"):
        if abs(n) < 1024 or unit == "Go":
            return f"{n:.0f} {unit}" if unit == "o" else f"{n:.1f} {unit}".replace(".", ",")
        n /= 1024
    return str(n)
