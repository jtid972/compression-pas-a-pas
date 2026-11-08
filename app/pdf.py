# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) pour la génération de code.
"""PDF : compression des images + structure PDF 1.5 (flux d'objets), et conversion en
Word / PowerPoint modifiables (reconnaissance de texte pour les PDF scannés)."""
import io
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw

from .common import UserError

EXTENSIONS = {".pdf"}
# niveau -> (résolution cible des images en dpi, qualité JPEG)
LEVELS = {"impression": (200, 80), "equilibre": (150, 75), "ecran": (110, 65)}
OCR_DPI = 300

OPTIONS = [
    {"key": "niveau", "label": "Images du PDF", "type": "choice", "default": "equilibre",
     "choices": [["impression", "Impression (200 dpi)"], ["equilibre", "Entre web et impression (150 dpi)"],
                 ["ecran", "Écran uniquement (110 dpi)"]]},
    {"key": "conversion", "label": "Fournir aussi une version modifiable", "type": "choice",
     "default": "aucune",
     "choices": [["aucune", "Non, seulement le PDF compressé"], ["word", "Word (.docx)"],
                 ["powerpoint", "PowerPoint (.pptx)"], ["les_deux", "Word et PowerPoint"]]},
]


# ------------------------------------------------------------------ reconnaissance de texte
def tesseract_cmd():
    cmd = os.environ.get("TESSERACT_CMD") or shutil.which("tesseract")
    if not cmd and os.name == "nt":
        p = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Tesseract-OCR" / "tesseract.exe"
        cmd = str(p) if p.exists() else None
    return cmd


def ocr_langs():
    cmd = tesseract_cmd()
    if not cmd:
        return []
    r = subprocess.run([cmd, "--list-langs"], capture_output=True, text=True, check=False)
    langs = [line.strip() for line in r.stdout.splitlines()[1:] if line.strip()]
    wanted = [lang for lang in ("fra", "eng") if lang in langs]
    return wanted or langs[:1]


def ocr_lines(png: Path):
    """Lignes reconnues : [(x0, y0, x1, y1, texte, (bloc, paragraphe))] en pixels."""
    cmd, langs = tesseract_cmd(), ocr_langs()
    r = subprocess.run([cmd, str(png), "stdout", "-l", "+".join(langs), "tsv"],
                       capture_output=True, text=True, check=False, encoding="utf-8", errors="replace")
    if r.returncode:
        raise UserError("Échec de la reconnaissance de texte : " + r.stderr[-200:])
    lines: dict = {}
    for row in r.stdout.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or c[0] != "5" or not c[11].strip():
            continue
        key = (int(c[2]), int(c[3]), int(c[4]))  # bloc, paragraphe, ligne
        x, y, w, h = map(int, c[6:10])
        if key not in lines:
            lines[key] = [x, y, x + w, y + h, []]
        ln = lines[key]
        ln[0], ln[1], ln[2], ln[3] = min(ln[0], x), min(ln[1], y), max(ln[2], x + w), max(ln[3], y + h)
        ln[4].append(c[11])
    return [(*v[:4], " ".join(v[4]), k[:2]) for k, v in sorted(lines.items())]


# ------------------------------------------------------------------ analyse
def _scanned(doc) -> tuple[bool, int]:
    scanned = 0
    for page in doc:
        if len(page.get_text().strip()) > 30:
            continue
        area = abs(page.rect)
        cover = sum(abs(r) for img in page.get_images(full=True) for r in page.get_image_rects(img[0]))
        if area and cover / area > 0.5:
            scanned += 1
    return scanned > len(doc) / 2, scanned


def analyze(path: Path) -> dict:
    try:
        doc = pymupdf.open(path)
    except Exception as e:  # noqa: BLE001
        raise UserError("PDF illisible ou endommagé.") from e
    if doc.needs_pass:
        raise UserError("Ce PDF est protégé par un mot de passe.")
    scanned, n_scan = _scanned(doc)
    images = sum(len(p.get_images()) for p in doc)
    ocr = bool(tesseract_cmd() and ocr_langs())
    label = f"PDF · {len(doc)} page(s) · {images} image(s)" + (" · document scanné" if scanned else "")
    notes = []
    if scanned:
        notes.append("PDF scanné détecté : la version modifiable utilisera la reconnaissance de texte (OCR)."
                     if ocr else "PDF scanné détecté, mais la reconnaissance de texte (Tesseract) n'est pas "
                     "installée : la conversion en document modifiable n'est pas disponible.")
    return {"pages": len(doc), "images": images, "scanned": scanned, "ocr_available": ocr,
            "label": label, "notes": notes}


# ------------------------------------------------------------------ compression
def compress_pdf(path: Path, out: Path, level: str):
    dpi, quality = LEVELS[level]
    doc = pymupdf.open(path)
    doc.rewrite_images(dpi_threshold=int(dpi * 1.25), dpi_target=dpi, quality=quality)
    try:
        doc.subset_fonts()  # ne garde que les caractères utilisés des polices intégrées
    except Exception:  # noqa: BLE001
        pass
    doc.save(out, garbage=4, deflate=True, clean=True, use_objstms=1)  # PDF 1.5 : flux d'objets
    doc.close()
    if out.stat().st_size >= path.stat().st_size:  # déjà optimisé : on garde l'original
        shutil.copyfile(path, out)


def estimate(path: Path, work: Path, opts: dict, info: dict, progress=lambda p: None) -> dict:
    out = work / f"estimation_{opts['niveau']}.pdf"
    progress(-1)
    compress_pdf(path, out, opts["niveau"])
    return {"size": out.stat().st_size, "exact": True, "file": out}


# ------------------------------------------------------------------ conversions
def _page_png(page, dpi) -> Path:
    tmp = Path(tempfile.mkstemp(suffix=".png")[1])
    page.get_pixmap(dpi=dpi).save(tmp)
    return tmp


def to_docx(pdf: Path, out: Path, scanned: bool, progress):
    if not scanned:
        from pdf2docx import Converter
        cv = Converter(str(pdf))
        try:
            cv.convert(str(out))
        finally:
            cv.close()
        return
    from docx import Document
    from docx.shared import Pt
    doc = pymupdf.open(pdf)
    d = Document()
    d.styles["Normal"].font.size = Pt(11)
    for i, page in enumerate(doc):
        png = _page_png(page, OCR_DPI)
        try:
            lines = ocr_lines(png)
        finally:
            png.unlink(missing_ok=True)
        paras: dict = {}
        for *_, text, key in lines:
            paras.setdefault(key, []).append(text)
        for words in paras.values():
            d.add_paragraph(" ".join(words))
        if i < len(doc) - 1:
            d.add_page_break()
        progress((i + 1) / len(doc) * 100)
    d.save(out)


def _rgb(c: int):
    from pptx.dml.color import RGBColor
    return RGBColor((c >> 16) & 255, (c >> 8) & 255, c & 255)


def to_pptx(pdf: Path, out: Path, scanned: bool, progress):
    """Une diapositive par page : fond = page sans son texte (images et dessins conservés),
    textes en zones de texte modifiables à leur place."""
    from pptx import Presentation
    from pptx.enum.text import MSO_AUTO_SIZE
    from pptx.util import Emu, Pt

    doc = pymupdf.open(pdf)
    first = doc[0].rect
    scale = min(1.0, 4000 / max(first.width, first.height))  # limite PowerPoint : 56 pouces
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(int(first.width * scale * 12700)), Emu(int(first.height * scale * 12700))
    sw, sh = prs.slide_width / 12700, prs.slide_height / 12700
    blank = prs.slide_layouts[6]

    def box(slide, x0, y0, x1, y1, s, ox, oy):
        tb = slide.shapes.add_textbox(Emu(int((ox + x0 * s) * 12700)), Emu(int((oy + y0 * s) * 12700)),
                                      Emu(int(max(1, (x1 - x0) * s + 2) * 12700)),
                                      Emu(int(max(1, (y1 - y0) * s) * 12700)))
        tf = tb.text_frame
        tf.word_wrap = False
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        return tf

    for i, page in enumerate(doc):
        r = page.rect
        s = min(sw / r.width, sh / r.height)
        ox, oy = (sw - r.width * s) / 2, (sh - r.height * s) / 2
        slide = prs.slides.add_slide(blank)
        if scanned:
            png = _page_png(page, OCR_DPI)
            try:
                lines = ocr_lines(png)
                im = Image.open(png).convert("RGB")
            finally:
                png.unlink(missing_ok=True)
            bg_color = sorted(im.resize((64, 64)).getdata())[64 * 64 // 2]  # couleur du papier
            draw = ImageDraw.Draw(im)
            for x0, y0, x1, y1, *_ in lines:
                draw.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 2], fill=bg_color)
            im = im.resize((int(r.width * 150 / 72), int(r.height * 150 / 72)), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=72, optimize=True)
            px = 72 / OCR_DPI
            slide.shapes.add_picture(io.BytesIO(buf.getvalue()), Emu(int(ox * 12700)), Emu(int(oy * 12700)),
                                     Emu(int(r.width * s * 12700)), Emu(int(r.height * s * 12700)))
            for x0, y0, x1, y1, text, _ in lines:
                tf = box(slide, x0 * px, y0 * px, x1 * px, y1 * px, s, ox, oy)
                run = tf.paragraphs[0].add_run()
                run.text = text
                run.font.size = Pt(max(4, (y1 - y0) * px * s * 1.05))
        else:
            blocks = [b for b in page.get_text("dict")["blocks"] if b["type"] == 0]
            bg = pymupdf.open()
            bg.insert_pdf(doc, from_page=i, to_page=i)
            bp = bg[0]
            for b in blocks:
                bp.add_redact_annot(b["bbox"], fill=False)
            bp.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE,
                                graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                                text=pymupdf.PDF_REDACT_TEXT_REMOVE)
            pix = bp.get_pixmap(dpi=150)
            im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=75, optimize=True)
            slide.shapes.add_picture(io.BytesIO(buf.getvalue()), Emu(int(ox * 12700)), Emu(int(oy * 12700)),
                                     Emu(int(r.width * s * 12700)), Emu(int(r.height * s * 12700)))
            for b in blocks:
                x0, y0, x1, y1 = b["bbox"]
                tf = box(slide, x0, y0, x1, y1, s, ox, oy)
                for n, line in enumerate(b["lines"]):
                    p = tf.paragraphs[0] if n == 0 else tf.add_paragraph()
                    for span in line["spans"]:
                        if not span["text"]:
                            continue
                        run = p.add_run()
                        run.text = span["text"]
                        f = run.font
                        f.size = Pt(max(4, span["size"] * s))
                        f.bold = bool(span["flags"] & 16)
                        f.italic = bool(span["flags"] & 2)
                        f.color.rgb = _rgb(span["color"])
                        name = span["font"].split("+")[-1].split("-")[0].split(",")[0]
                        if name:
                            f.name = name
        progress((i + 1) / len(doc) * 100)
    prs.save(out)


def _shrink_office(path: Path, level: str):
    """Recompresse les images du document produit (même réglage que le PDF)."""
    from . import office
    tmp = path.parent / ("_tmp_" + path.name)
    tmp.mkdir(exist_ok=True)
    try:
        res = office.compress(path, tmp, {"niveau": level, "jpeg": True}, {"name": path.name})[0]
        if res.stat().st_size < path.stat().st_size:
            res.replace(path)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def compress(path: Path, out_dir: Path, opts: dict, info: dict, progress=lambda p: None,
             cached: Path | None = None, stage=lambda s: None) -> list[Path]:
    stem = Path(info["name"]).stem
    pdf_out = out_dir / (stem + "_compresse.pdf")
    if cached and cached.exists():
        shutil.copyfile(cached, pdf_out)
    else:
        stage("Compression du PDF")
        progress(-1)
        compress_pdf(path, pdf_out, opts["niveau"])
    outputs = [pdf_out]
    conv = opts.get("conversion", "aucune")
    if conv != "aucune":
        scanned = info["scanned"]
        if scanned and not info["ocr_available"]:
            raise UserError("PDF scanné : la reconnaissance de texte (Tesseract) n'est pas installée.")
        src = pdf_out  # on convertit le PDF déjà compressé : images plus légères dans le résultat
        if conv in ("word", "les_deux"):
            stage("Conversion en Word" + (" (reconnaissance de texte)" if scanned else ""))
            progress(-1 if not scanned else 0)
            docx = out_dir / (stem + "_modifiable.docx")
            to_docx(src, docx, scanned, progress)
            _shrink_office(docx, opts["niveau"])
            outputs.append(docx)
        if conv in ("powerpoint", "les_deux"):
            stage("Conversion en PowerPoint" + (" (reconnaissance de texte)" if scanned else ""))
            progress(0)
            pptx = out_dir / (stem + "_modifiable.pptx")
            to_pptx(src, pptx, scanned, progress)
            _shrink_office(pptx, opts["niveau"])
            outputs.append(pptx)
    return outputs
