# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) et de Mistral Vibe (IA Mistral) pour la génération de code.
"""Documents bureautiques (Word, PowerPoint, Excel, LibreOffice, OnlyOffice) :
recompression des images intégrées ; le document garde son format et reste modifiable."""
import io
import re
import zipfile
from pathlib import Path

from PIL import Image

from .common import UserError, encode, fit_long_side, has_alpha, resize

# OnlyOffice enregistre nativement en .docx / .xlsx / .pptx : même traitement.
EXTENSIONS = {".docx", ".docm", ".dotx", ".pptx", ".pptm", ".potx", ".ppsx", ".xlsx", ".xlsm", ".xltx",
              ".odt", ".ott", ".odp", ".otp", ".ods", ".ots", ".odg"}
LEGACY = {".doc", ".ppt", ".xls", ".rtf", ".pps", ".pot", ".dot", ".xlt"}
KINDS = {".docx": "Word", ".docm": "Word", ".dotx": "Word", ".pptx": "PowerPoint", ".pptm": "PowerPoint",
         ".potx": "PowerPoint", ".ppsx": "PowerPoint", ".xlsx": "Excel", ".xlsm": "Excel", ".xltx": "Excel",
         ".odt": "LibreOffice Writer", ".ott": "LibreOffice Writer", ".odp": "LibreOffice Impress",
         ".otp": "LibreOffice Impress", ".ods": "LibreOffice Calc", ".ots": "LibreOffice Calc",
         ".odg": "LibreOffice Draw"}
# niveau -> (plus grand côté en pixels, qualité JPEG)
LEVELS = {"impression": (2480, 85), "equilibre": (1754, 80), "ecran": (1280, 75)}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}

OPTIONS = [
    {"key": "niveau", "label": "Images du document", "type": "choice", "default": "equilibre",
     "choices": [["impression", "Impression (≈ 300 dpi sur A4, 2480 px max)"],
                 ["equilibre", "Entre web et impression (≈ 150 dpi sur A4, 1754 px max)"],
                 ["ecran", "Écran uniquement (1280 px max)"]]},
    {"key": "jpeg", "label": "Convertir les photos PNG en JPEG à l'intérieur (le document garde son format)",
     "type": "bool", "default": True},
]


def _is_media(name: str) -> bool:
    low = name.lower()
    return ("/media/" in low or low.startswith("pictures/") or low == "docprops/thumbnail.jpeg") \
        and Path(low).suffix in IMAGE_EXT


def analyze(path: Path) -> dict:
    ext = path.suffix.lower()
    try:
        with zipfile.ZipFile(path) as z:
            media = [i for i in z.infolist() if _is_media(i.filename)]
    except zipfile.BadZipFile as e:
        raise UserError("Document illisible (fichier endommagé ou protégé par mot de passe ?).") from e
    size = sum(i.file_size for i in media)
    from .common import human
    return {"images": len(media), "images_size": size,
            "label": f"Document {KINDS.get(ext, ext)} · {len(media)} image(s) intégrée(s), {human(size)}"}


def _recompress(data: bytes, max_side: int, quality: int, allow_jpeg: bool):
    """Renvoie (nouvelles données, nouvelle extension ou None) ou None si pas de gain."""
    try:
        im = Image.open(io.BytesIO(data))
        im.load()
    except Exception:  # noqa: BLE001  (EMF, WMF, SVG… : laissés tels quels)
        return None
    fmt = "JPEG" if im.format == "MPO" else im.format
    if getattr(im, "n_frames", 1) > 1 and im.format != "MPO":
        return None
    icc = im.info.get("icc_profile")
    im = resize(im, fit_long_side(im.width, im.height, max_side))
    best = None
    if fmt in ("JPEG", "PNG", "WEBP", "TIFF", "BMP", "GIF"):
        best = (encode(im, fmt, quality, icc=icc), None)
    if allow_jpeg and fmt in ("PNG", "TIFF", "BMP") and not has_alpha(im):
        j = encode(im, "JPEG", quality, icc=icc)
        if best is None or len(j) < len(best[0]) * 0.7:  # photo : le JPEG est nettement plus léger
            best = (j, ".jpeg")
    if best and len(best[0]) < len(data) * 0.95:
        return best
    return None


def _fix_ooxml_content_types(xml: bytes, renamed: dict) -> bytes:
    s = xml.decode("utf-8")
    if not re.search(r'Extension="jpeg"', s, re.IGNORECASE):
        s = s.replace("</Types>", '<Default Extension="jpeg" ContentType="image/jpeg"/></Types>')
    for new in renamed.values():
        s = re.sub(r'(<Override PartName="/' + re.escape(new) + r'" ContentType=")[^"]+"',
                   r'\1image/jpeg"', s)
    return s.encode("utf-8")


def _fix_odf_manifest(xml: bytes, renamed: dict) -> bytes:
    s = xml.decode("utf-8")
    for new in renamed.values():
        s = re.sub(r'(<manifest:file-entry[^>]*manifest:full-path="' + re.escape(new) + r'"[^>]*/>)',
                   lambda m: re.sub(r'manifest:media-type="[^"]*"', 'manifest:media-type="image/jpeg"',
                                    m.group(1)), s)
    return s.encode("utf-8")


def compress(path: Path, out_dir: Path, opts: dict, info: dict, progress=lambda p: None) -> list[Path]:
    max_side, quality = LEVELS[opts["niveau"]]
    out = out_dir / (Path(info["name"]).stem + "_compresse" + path.suffix.lower())
    with zipfile.ZipFile(path) as zin:
        items = zin.infolist()
        names = {i.filename for i in items}
        media = [i for i in items if _is_media(i.filename)]
        new_data, renamed = {}, {}
        for n, item in enumerate(media):
            res = _recompress(zin.read(item), max_side, quality, opts.get("jpeg", True))
            if res:
                data, new_ext = res
                if new_ext:
                    target = str(Path(item.filename).with_suffix(new_ext)).replace("\\", "/")
                    if target in names:
                        target = target[: -len(new_ext)] + "_c" + new_ext
                    renamed[item.filename] = target
                    names.add(target)
                new_data[item.filename] = data
            progress((n + 1) / max(1, len(media)) * 90)

        def patch(name: str, data: bytes) -> bytes:
            if not renamed or not name.lower().endswith((".xml", ".rels")):
                return data
            for old, new in renamed.items():
                # les références sont relatives (media/image1.png, Pictures/x.png) ou absolues (/word/media/…)
                old_rel, new_rel = old.split("/", 1)[1] if "/media/" in old else old, \
                    new.split("/", 1)[1] if "/media/" in new else new
                data = data.replace(old_rel.encode(), new_rel.encode())
            if name == "[Content_Types].xml":
                data = _fix_ooxml_content_types(data, renamed)
            if name == "META-INF/manifest.xml":
                data = _fix_odf_manifest(data, renamed)
            return data

        with zipfile.ZipFile(out, "w") as zout:
            for item in items:  # même ordre ; « mimetype » reste en tête et non compressé (ODF)
                data = new_data.get(item.filename) or zin.read(item)
                name = renamed.get(item.filename, item.filename)
                data = patch(item.filename, data)
                ctype = zipfile.ZIP_STORED if item.filename == "mimetype" else zipfile.ZIP_DEFLATED
                zi = zipfile.ZipInfo(name, date_time=item.date_time)
                zi.compress_type = ctype
                zi.external_attr = item.external_attr
                zout.writestr(zi, data)
    progress(100)
    return [out]
