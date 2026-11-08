"""Tests de bout en bout : images, bureautique, PDF (+ conversions), vidéo, application installable."""
import io
import os
import shutil
import subprocess
import tempfile
import time
import zipfile

import pytest

os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="cpap-"))

from fastapi.testclient import TestClient
from PIL import Image, ImageFilter

from app import main

client = TestClient(main.app)


def photo(w=3000, h=2000):
    base = Image.radial_gradient("L").resize((w, h)).convert("RGB")
    noise = Image.effect_noise((w, h), 40).convert("RGB")
    return Image.blend(base, noise, 0.3).filter(ImageFilter.GaussianBlur(1))


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("media")
    p = photo()
    p.save(d / "photo.jpg", quality=97)
    p.save(d / "photo.png")
    Image.new("RGB", (64, 64), "white").save(d / "petit.png", optimize=True)
    from docx import Document
    from docx.shared import Cm
    doc = Document()
    doc.add_paragraph("Rapport")
    doc.add_picture(str(d / "photo.png"), width=Cm(15))
    doc.save(d / "rapport.docx")
    import openpyxl
    from openpyxl.drawing.image import Image as XImage
    wb = openpyxl.Workbook()
    wb.active.add_image(XImage(str(d / "photo.png")), "B2")
    wb.save(d / "tableau.xlsx")
    import pymupdf
    pdf = pymupdf.open()
    page = pdf.new_page()
    page.insert_text((72, 72), "Rapport annuel 2026", fontsize=20)
    page.insert_image(pymupdf.Rect(72, 100, 520, 400), filename=str(d / "photo.png"))
    pdf.save(d / "natif.pdf")
    src = pymupdf.open()
    sp = src.new_page()
    sp.insert_text((72, 100), "Ouvrez le menu Fichier puis Enregistrer", fontsize=16)
    pix = sp.get_pixmap(dpi=300)
    scan_png = d / "scan.png"
    pix.save(scan_png)
    sc = pymupdf.open()
    sc.new_page().insert_image(sc[0].rect, filename=str(scan_png))
    sc.save(d / "scan.pdf")
    ff = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    subprocess.run(ff + ["-f", "lavfi", "-i", "testsrc2=s=1920x1080:d=4:r=25", "-f", "lavfi", "-i",
                         "sine=f=440:d=4", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "10",
                         "-c:a", "aac", "-b:a", "256k", str(d / "video.mp4")], check=True)
    subprocess.run(ff + ["-f", "lavfi", "-i", "testsrc2=s=1280x720:d=3:r=25", "-c:v", "libx264",
                         "-preset", "ultrafast", "-crf", "10", str(d / "muette.mp4")], check=True)
    (d / "ancien.doc").write_bytes(b"\xd0\xcf\x11\xe0 ancien format")
    return d


def wait(jid):
    for _ in range(600):
        j = client.get(f"/api/jobs/{jid}").json()
        if j["status"] in ("done", "error"):
            return j
        time.sleep(0.2)
    raise AssertionError("délai dépassé")


def upload(path):
    with open(path, "rb") as f:
        return client.post("/api/files", files={"file": (path.name, f)})


def estimate_and_run(path, **opts):
    f = upload(path).json()
    est = wait(client.post(f"/api/files/{f['id']}/estimate", json=opts).json()["job"])
    assert est["status"] == "done", est.get("message")
    run = wait(client.post(f"/api/files/{f['id']}/run", json=opts).json()["job"])
    assert run["status"] == "done", run.get("message")
    dl = client.get(f"/api/jobs/{run['id']}/download")
    assert dl.status_code == 200
    return f, est["result"], run["result"], dl.content


def test_image_meme_format_et_estimation_exacte(media):
    f, est, res, data = estimate_and_run(media / "photo.jpg")
    assert est["size"] == res["size"] and res["gain_pct"] > 50
    im = Image.open(io.BytesIO(data))
    assert im.format == "JPEG" and im.size == (1620, 1080)  # 3:2 dans un cadre 1920 × 1080


def test_image_hdready_et_conversion_jpeg(media):
    _, _, res, data = estimate_and_run(media / "photo.png", resolution="hdready", jpeg=True)
    im = Image.open(io.BytesIO(data))
    assert im.format == "JPEG" and im.size == (1080, 720)
    assert res["files"][0]["name"].endswith(".jpg")


def test_gain_faible_deconseille_et_original_conserve(media):
    _, est, res, data = estimate_and_run(media / "petit.png")
    assert est["advice"] in ("faible", "aucun")
    assert data == (media / "petit.png").read_bytes()  # déjà optimisé : original rendu tel quel


def test_word_images_recompressees_et_document_valide(media):
    _, est, res, data = estimate_and_run(media / "rapport.docx")
    assert res["gain_pct"] > 50
    z = zipfile.ZipFile(io.BytesIO(data))
    assert any(n.endswith(".jpeg") for n in z.namelist())  # photo PNG → JPEG à l'intérieur
    from docx import Document
    doc = Document(io.BytesIO(data))
    assert doc.paragraphs[0].text == "Rapport" and len(doc.inline_shapes) == 1


def test_excel(media):
    _, _, res, data = estimate_and_run(media / "tableau.xlsx")
    assert res["gain_pct"] > 50
    import openpyxl
    openpyxl.load_workbook(io.BytesIO(data))


def test_pdf_compression_et_conversions(media):
    _, est, res, data = estimate_and_run(media / "natif.pdf", conversion="les_deux")
    z = zipfile.ZipFile(io.BytesIO(data))
    names = z.namelist()
    assert {"natif_compresse.pdf", "natif_modifiable.docx", "natif_modifiable.pptx"} <= set(names)
    from docx import Document
    from pptx import Presentation
    assert "Rapport annuel" in "".join(p.text for p in Document(io.BytesIO(z.read("natif_modifiable.docx"))).paragraphs)
    prs = Presentation(io.BytesIO(z.read("natif_modifiable.pptx")))
    assert "Rapport annuel" in "".join(s.text_frame.text for s in prs.slides[0].shapes if s.has_text_frame)


@pytest.mark.skipif(not main.pdf.tesseract_cmd(), reason="Tesseract non installé")
def test_pdf_scanne_ocr(media):
    f = upload(media / "scan.pdf").json()
    assert "scanné" in f["label"]
    _, _, _, data = estimate_and_run(media / "scan.pdf", conversion="word")
    z = zipfile.ZipFile(io.BytesIO(data))
    from docx import Document
    text = " ".join(p.text for p in Document(io.BytesIO(z.read("scan_modifiable.docx"))).paragraphs).lower()
    assert "fichier" in text and "enregistrer" in text, text


def test_video_fullhd_et_mp3(media):
    f, est, res, data = estimate_and_run(media / "video.mp4", resolution="hdready", mp3=True)
    assert [x["name"] for x in res["files"]] == ["video_compresse.mp4", "video_son.mp3"]
    z = zipfile.ZipFile(io.BytesIO(data))
    tmp = tempfile.mkdtemp()
    z.extractall(tmp)
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height", "-of", "csv=p=0", os.path.join(tmp, "video_compresse.mp4")],
                         capture_output=True, text=True, check=True).stdout.strip()
    assert out == "1280,720"
    shutil.rmtree(tmp)


def test_video_muette_sans_reglage_son(media):
    f = upload(media / "muette.mp4").json()
    assert "son" not in [o["key"] for o in f["options"]]


def test_ancien_format_refuse(media):
    r = upload(media / "ancien.doc")
    assert r.status_code == 422 and "enregistrez" in r.json()["detail"]


def test_pwa_et_partage(media):
    assert client.get("/manifest.webmanifest").json()["share_target"]["action"] == "/share"
    assert client.get("/sw.js").headers["content-type"].startswith("application/javascript")
    with open(media / "photo.jpg", "rb") as f:
        r = client.post("/share", files={"file": ("photo.jpg", f)}, follow_redirects=False)
    assert r.status_code == 303 and "fichier=" in r.headers["location"]
    fid = r.headers["location"].split("fichier=")[1]
    assert client.get(f"/api/files/{fid}").json()["kind"] == "image"


def test_mot_de_passe(monkeypatch):
    monkeypatch.setattr(main, "PASSWORD", "secret")
    assert client.get("/api/config").status_code == 401
    assert client.get("/healthz").status_code == 200
    assert client.get("/manifest.webmanifest").status_code == 200
    assert client.get("/api/config", auth=("x", "secret")).status_code == 200
