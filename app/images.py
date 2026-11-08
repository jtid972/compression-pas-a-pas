# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) pour la génération de code.
"""Images : redimensionnement Full HD / HD Ready, même format (ou JPEG en option)."""
from pathlib import Path

from PIL import Image, ImageOps

from .common import QUALITY, RESOLUTIONS, UserError, encode, fit, has_alpha, resize

EXTENSIONS = {".jpg", ".jpeg", ".jpe", ".png", ".webp", ".tif", ".tiff", ".bmp", ".gif",
              ".heic", ".heif", ".avif"}
FORMAT_NAMES = {"JPEG": "JPEG", "MPO": "JPEG", "PNG": "PNG", "WEBP": "WebP", "TIFF": "TIFF",
                "BMP": "BMP", "GIF": "GIF", "HEIF": "HEIC/HEIF", "AVIF": "AVIF"}

OPTIONS = [
    {"key": "resolution", "label": "Taille maximale", "type": "choice", "default": "fullhd",
     "choices": [["fullhd", "Full HD (1920 × 1080 max)"], ["hdready", "HD Ready (1280 × 720 max)"],
                 ["original", "Taille d'origine"]]},
    {"key": "qualite", "label": "Qualité", "type": "choice", "default": "equilibree",
     "choices": [["haute", "Haute"], ["equilibree", "Équilibrée"], ["compacte", "Compacte"]]},
    {"key": "jpeg", "label": "Convertir en JPEG (le plus léger ; la transparence devient un fond blanc)",
     "type": "bool", "default": False},
    {"key": "couleurs", "label": "PNG : réduire à 256 couleurs (logos, captures d'écran)",
     "type": "bool", "default": False, "only_format": "PNG"},
]


def analyze(path: Path) -> dict:
    try:
        im = Image.open(path)
    except Exception as e:  # noqa: BLE001
        raise UserError("Image illisible ou format non reconnu.") from e
    fmt = "JPEG" if im.format == "MPO" else im.format
    if getattr(im, "n_frames", 1) > 1 and im.format not in ("MPO",):
        raise UserError("Les images animées ou multipages ne sont pas prises en charge pour le moment.")
    w, h = ImageOps.exif_transpose(im).size
    alpha = has_alpha(im)
    return {"format": fmt, "width": w, "height": h, "alpha": alpha,
            "label": f"Image {FORMAT_NAMES.get(fmt, fmt)} · {w} × {h}" + (" · transparence" if alpha else "")}


def compress(path: Path, out_dir: Path, opts: dict, info: dict, progress=lambda p: None) -> list[Path]:
    im = Image.open(path)
    icc = im.info.get("icc_profile")
    im = ImageOps.exif_transpose(im)  # applique la rotation de l'appareil photo (EXIF supprimé ensuite)
    size = fit(im.width, im.height, RESOLUTIONS[opts["resolution"]])
    im = resize(im, size)
    progress(50)
    fmt = "JPEG" if opts["jpeg"] else info["format"]
    data = encode(im, fmt, QUALITY[opts["qualite"]], png_colors=opts.get("couleurs"), icc=icc)
    ext = ".jpg" if opts["jpeg"] and info["format"] != "JPEG" else path.suffix.lower()
    out = out_dir / (Path(info["name"]).stem + "_compresse" + ext)
    out.write_bytes(data)
    progress(100)
    return [out]
