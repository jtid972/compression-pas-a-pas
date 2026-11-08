# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later  (voir LICENSE et NOTICE.md ; licence commerciale possible)
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) et de Mistral Vibe (IA Mistral) pour la génération de code.
"""Compression pas à pas : allège vidéos, images, documents bureautiques et PDF,
avec estimation du gain avant lancement."""
import base64
import json
import os
import queue
import re
import secrets
import shutil
import threading
import time
import uuid
import zipfile
from pathlib import Path

from fastapi import Body, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__, images, office, pdf, video
from .common import UserError, human

APP_NAME = "Compression pas à pas"
BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get("DATA_DIR", BASE.parent / "data"))
WORK = DATA / "work"
WORK.mkdir(parents=True, exist_ok=True)
KEEP_HOURS = float(os.environ.get("KEEP_HOURS", "24"))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "4096"))
MIN_GAIN = float(os.environ.get("MIN_GAIN", "10"))   # en dessous : traitement déconseillé
PASSWORD = os.environ.get("APP_PASSWORD", "")
# AGPL-3.0, article 13 : les utilisateurs à distance doivent pouvoir obtenir le code source.
SOURCE_URL = os.environ.get("SOURCE_URL", "https://github.com/jtid972/compression-pas-a-pas")

MODULES = {"video": video, "image": images, "office": office, "pdf": pdf}
EST_KEYS = {"video": ["resolution", "qualite", "son"], "image": ["resolution", "qualite", "jpeg", "couleurs"],
            "office": ["niveau", "jpeg"], "pdf": ["niveau"]}
PUBLIC = ("/healthz", "/manifest.webmanifest", "/sw.js", "/static/icons/")

app = FastAPI(title=APP_NAME, version=__version__)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
files: dict[str, dict] = {}
jobs: dict[str, dict] = {}
lock = threading.Lock()
work_queue: "queue.Queue[str]" = queue.Queue()


# ---------------------------------------------------------------- mot de passe (facultatif)
@app.middleware("http")
async def basic_auth(request: Request, call_next):
    if PASSWORD and not request.url.path.startswith(PUBLIC):
        ok = False
        h = request.headers.get("authorization", "")
        if h.lower().startswith("basic "):
            try:
                _, _, pwd = base64.b64decode(h[6:]).decode("utf-8").partition(":")
                ok = secrets.compare_digest(pwd.encode(), PASSWORD.encode())
            except Exception:  # noqa: BLE001
                ok = False
        if not ok:
            return Response("Mot de passe requis", status_code=401,
                            headers={"WWW-Authenticate": 'Basic realm="Compression pas a pas"'})
    return await call_next(request)


# ---------------------------------------------------------------- types de fichiers
def kind_of(ext: str) -> str:
    for kind, mod in MODULES.items():
        if ext in mod.EXTENSIONS:
            return kind
    if ext in office.LEGACY:
        raise UserError(f"Les anciens fichiers {ext} ne sont pas pris en charge : ouvrez-le et enregistrez-le "
                        "au format actuel (.docx, .pptx, .xlsx ou OpenDocument), puis recommencez.")
    raise UserError(f"Type de fichier non pris en charge ({ext or 'sans extension'}).")


def options_for(f: dict) -> list:
    opts = []
    for o in MODULES[f["kind"]].OPTIONS:
        if o.get("only_format") and f["info"].get("format") != o["only_format"]:
            continue
        if o.get("needs_audio") and not f["info"].get("audio"):
            continue
        opts.append(o)
    return opts


def normalize(f: dict, raw: dict) -> dict:
    out = {}
    for o in options_for(f):
        v = raw.get(o["key"], o["default"])
        if o["type"] == "bool":
            out[o["key"]] = v in (True, "true", "1", 1, "on")
        else:
            out[o["key"]] = v if v in [c[0] for c in o["choices"]] else o["default"]
    if f["kind"] == "image":
        out.setdefault("couleurs", False)
    if f["kind"] == "video":
        out.setdefault("son", "aucun")
        out.setdefault("mp3", False)
    return out


def est_key(f: dict, opts: dict) -> str:
    return json.dumps({k: opts.get(k) for k in EST_KEYS[f["kind"]]}, sort_keys=True)


def pct(g: float) -> str:
    """99,9 % plutôt que 100 % ; 4,2 % plutôt que 4 %."""
    return f"{g:.1f}".replace(".", ",") if g >= 99 or g < 10 else f"{g:.0f}"


def verdict(original: int, size: int, exact: bool) -> dict:
    gain = (original - size) / original * 100 if original else 0
    approx = "" if exact else "environ "
    if gain <= 0:
        advice, msg = "aucun", "Le fichier ne serait pas plus léger : il est déjà optimisé, inutile de lancer le traitement."
    elif gain < MIN_GAIN:
        advice, msg = "faible", (f"Gain estimé de {approx}{pct(gain)} % seulement (moins de {MIN_GAIN:.0f} %) : "
                                 "il n'est pas conseillé de lancer le traitement.")
    else:
        advice, msg = "ok", f"Gain estimé : {approx}{pct(gain)} % ({human(original)} → {human(size)})."
    return {"original": original, "size": size, "gain_pct": round(gain, 1), "exact": exact,
            "advice": advice, "message": msg}


# ---------------------------------------------------------------- travaux
def upd(jid: str, **kw):
    with lock:
        jobs[jid].update(kw)


def do_estimate(jid: str):
    j = jobs[jid]
    f = files[j["fid"]]
    opts = j["options"]
    key = est_key(f, opts)
    if key in f["cache"]:
        upd(jid, result=f["cache"][key]["verdict"])
        return
    mod = MODULES[f["kind"]]
    work = Path(f["dir"]) / ("est_" + uuid.uuid4().hex[:8])
    work.mkdir()
    upd(jid, stage="Estimation du gain", progress=0)
    prog = lambda p: upd(jid, progress=round(p, 1))  # noqa: E731
    if f["kind"] in ("video", "pdf"):
        est = mod.estimate(Path(f["path"]), work, opts, f["info"], prog)
    else:
        out = mod.compress(Path(f["path"]), work, opts, f["info"], prog)[0]
        est = {"size": out.stat().st_size, "exact": True, "file": out}
    v = verdict(f["size"], est["size"], est["exact"])
    f["cache"][key] = {"verdict": v, "file": str(est["file"]) if est.get("file") else None}
    upd(jid, result=v)


def do_run(jid: str):
    j = jobs[jid]
    f = files[j["fid"]]
    opts = j["options"]
    mod = MODULES[f["kind"]]
    src = Path(f["path"])
    out_dir = Path(f["dir"]) / ("resultat_" + jid)
    out_dir.mkdir()
    prog = lambda p: upd(jid, progress=round(p, 1))  # noqa: E731
    stage = lambda s: upd(jid, stage=s)  # noqa: E731
    c = f["cache"].get(est_key(f, opts), {})
    cached = Path(c["file"]) if c.get("file") and Path(c["file"]).exists() else None
    stage("Compression")
    if f["kind"] == "video":
        outputs = mod.compress(src, out_dir, opts, f["info"], prog, cached=cached)
    elif f["kind"] == "pdf":
        outputs = mod.compress(src, out_dir, opts, f["info"], prog, cached=cached, stage=stage)
    elif cached:
        target = out_dir / cached.name
        shutil.copyfile(cached, target)
        outputs = [target]
    else:
        outputs = mod.compress(src, out_dir, opts, f["info"], prog)

    note = ""
    main = outputs[0]
    if main.stat().st_size >= f["size"]:
        same_format = main.suffix.lower() == src.suffix.lower()
        if same_format:
            main.unlink()
            main = out_dir / f["name"]
            shutil.copyfile(src, main)
            outputs[0] = main
            note = "Le fichier était déjà optimisé : l'original est conservé tel quel."
    final = main.stat().st_size
    result = {**verdict(f["size"], final, True), "note": note,
              "files": [{"name": o.name, "size": o.stat().st_size} for o in outputs]}
    if len(outputs) > 1:
        stage("Création du ZIP")
        zpath = out_dir / (Path(f["name"]).stem + "_compression.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_STORED) as z:
            for o in outputs:
                z.write(o, o.name)
        download = zpath
    else:
        download = main
    upd(jid, result=result, download=str(download))


def worker():
    while True:
        jid = work_queue.get()
        upd(jid, status="running")
        try:
            (do_estimate if jobs[jid]["type"] == "estimate" else do_run)(jid)
            upd(jid, status="done", progress=100, stage="Terminé")
        except UserError as e:
            upd(jid, status="error", message=str(e))
        except Exception as e:  # noqa: BLE001
            upd(jid, status="error", message=f"Erreur inattendue : {e}"[:500])


def cleaner():
    while True:
        limit = time.time() - KEEP_HOURS * 3600
        for d in WORK.iterdir():
            if d.is_dir() and d.stat().st_mtime < limit:
                shutil.rmtree(d, ignore_errors=True)
                with lock:
                    files.pop(d.name, None)
        time.sleep(3600)


threading.Thread(target=worker, daemon=True).start()
threading.Thread(target=cleaner, daemon=True).start()


async def save_upload(file: UploadFile) -> dict:
    fid = uuid.uuid4().hex[:12]
    d = WORK / fid
    d.mkdir()
    name = Path(file.filename or "fichier").name
    ext = Path(name).suffix.lower()
    path = d / ("source" + re.sub(r"[^.a-z0-9]", "", ext[:8]))
    size, limit = 0, MAX_UPLOAD_MB * 1024 * 1024
    with open(path, "wb") as out:  # noqa: ASYNC230
        while chunk := await file.read(1 << 20):
            size += len(chunk)
            if size > limit:
                out.close()
                shutil.rmtree(d, ignore_errors=True)
                raise HTTPException(413, f"Fichier trop gros (limite {MAX_UPLOAD_MB} Mo)")
            out.write(chunk)
    try:
        kind = kind_of(ext)
        info = MODULES[kind].analyze(path)
    except UserError as e:
        shutil.rmtree(d, ignore_errors=True)
        raise HTTPException(422, str(e)) from e
    info["name"] = name
    f = {"id": fid, "name": name, "ext": ext, "path": str(path), "dir": str(d), "size": size,
         "kind": kind, "info": info, "cache": {}}
    with lock:
        files[fid] = f
    return f


def public(f: dict) -> dict:
    return {"id": f["id"], "name": f["name"], "size": f["size"], "size_h": human(f["size"]), "kind": f["kind"],
            "label": f["info"].get("label", ""), "notes": f["info"].get("notes", []),
            "legacy_note": "Ancien format vidéo : le résultat sera en MP4, lisible partout."
            if f["info"].get("legacy") else "", "options": options_for(f)}


def new_job(fid: str, typ: str, raw: dict) -> dict:
    f = files.get(fid)
    if not f:
        raise HTTPException(404, "Fichier introuvable (le serveur a peut-être redémarré) : renvoyez-le.")
    jid = uuid.uuid4().hex[:12]
    with lock:
        jobs[jid] = {"id": jid, "fid": fid, "type": typ, "options": normalize(f, raw or {}),
                     "status": "queued", "stage": "En attente", "progress": 0}
    work_queue.put(jid)
    return {"job": jid}


# ---------------------------------------------------------------- API
@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/config")
def config():
    return {"name": APP_NAME, "version": __version__, "source_url": SOURCE_URL, "license": "AGPL-3.0-or-later",
            "min_gain": MIN_GAIN, "max_upload_mb": MAX_UPLOAD_MB}


@app.post("/api/files")
async def upload(file: UploadFile = File(...)):
    return public(await save_upload(file))


@app.get("/api/files/{fid}")
def file_info(fid: str):
    f = files.get(fid)
    if not f:
        raise HTTPException(404, "Fichier introuvable")
    return public(f)


@app.post("/api/files/{fid}/estimate")
def estimate(fid: str, options: dict = Body(default={})):  # noqa: B008
    return new_job(fid, "estimate", options)


@app.post("/api/files/{fid}/run")
def run(fid: str, options: dict = Body(default={})):  # noqa: B008
    return new_job(fid, "run", options)


@app.get("/api/jobs/{jid}")
def job_status(jid: str):
    j = jobs.get(jid)
    if not j:
        raise HTTPException(404, "Travail introuvable")
    pos = list(work_queue.queue).index(jid) + 1 if jid in work_queue.queue else 0
    return {k: v for k, v in j.items() if k != "download"} | {"queue_position": pos}


@app.get("/api/jobs/{jid}/download")
def download(jid: str):
    j = jobs.get(jid)
    if not j or j.get("status") != "done" or not j.get("download"):
        raise HTTPException(404, "Résultat pas encore prêt")
    p = Path(j["download"])
    return FileResponse(p, filename=p.name)


# Partage depuis un téléphone (application installée) : « Partager » → Compression pas à pas
@app.post("/share")
async def share(file: UploadFile = File(...)):
    try:
        f = await save_upload(file)
    except HTTPException as e:
        return RedirectResponse(f"/?erreur={e.detail}", status_code=303)
    return RedirectResponse(f"/?fichier={f['id']}", status_code=303)


# ---------------------------------------------------------------- application installable (PWA)
@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(BASE / "static" / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(BASE / "static" / "sw.js", media_type="application/javascript",
                        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"})


@app.get("/")
def index():
    return FileResponse(BASE / "static" / "index.html")
