# Compression pas à pas — Copyright (c) 2026 Johan TIDAS
# SPDX-License-Identifier: AGPL-3.0-or-later
# Code réalisé avec l'assistance de Claude (IA d'Anthropic) pour la génération de code.
"""Vidéos : Full HD / HD Ready, même conteneur, son réglable, MP3 séparé en option."""
import json
import subprocess
from pathlib import Path

from .common import RESOLUTIONS, UserError, fit

EXTENSIONS = {".mp4", ".m4v", ".mov", ".mkv", ".webm", ".avi", ".3gp", ".ts", ".mts", ".m2ts",
              ".wmv", ".flv", ".mpg", ".mpeg", ".ogv"}
# extension -> (codec vidéo, codec audio, format ffmpeg, extension de sortie)
CONTAINERS = {
    ".mp4": ("x264", "aac", "mp4", ".mp4"), ".m4v": ("x264", "aac", "mp4", ".m4v"),
    ".mov": ("x264", "aac", "mov", ".mov"), ".3gp": ("x264", "aac", "3gp", ".3gp"),
    ".mkv": ("x264", "aac", "matroska", ".mkv"), ".webm": ("vp9", "libopus", "webm", ".webm"),
    ".avi": ("x264", "libmp3lame", "avi", ".avi"), ".ts": ("x264", "aac", "mpegts", ".ts"),
    ".mts": ("x264", "aac", "mpegts", ".mts"), ".m2ts": ("x264", "aac", "mpegts", ".m2ts"),
}
LEGACY = {".wmv", ".flv", ".mpg", ".mpeg", ".ogv"}  # anciens formats : convertis en MP4
CRF = {"haute": (21, 30), "equilibree": (24, 34), "compacte": (28, 38)}  # (x264, vp9)
AUDIO = {"normal": (128, 2), "reduit": (96, 2), "mono": (64, 1), "aucun": None}

OPTIONS = [
    {"key": "resolution", "label": "Définition maximale", "type": "choice", "default": "fullhd",
     "choices": [["fullhd", "Full HD (1920 × 1080 max)"], ["hdready", "HD Ready (1280 × 720 max)"],
                 ["original", "Définition d'origine"]]},
    {"key": "qualite", "label": "Qualité de l'image", "type": "choice", "default": "equilibree",
     "choices": [["haute", "Haute"], ["equilibree", "Équilibrée"], ["compacte", "Compacte"]]},
    {"key": "son", "label": "Son", "type": "choice", "default": "normal", "needs_audio": True,
     "choices": [["normal", "Normal (128 kbit/s)"], ["reduit", "Réduit (96 kbit/s)"],
                 ["mono", "Mono (64 kbit/s)"], ["aucun", "Sans son"]]},
    {"key": "mp3", "label": "Fournir aussi le son à part, en MP3", "type": "bool", "default": False,
     "needs_audio": True},
]


def analyze(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json",
                          str(path)], capture_output=True, text=True, check=False)
    if out.returncode:
        raise UserError("Vidéo illisible (format non reconnu par ffmpeg).")
    info = json.loads(out.stdout)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"
              and not s.get("disposition", {}).get("attached_pic")), None)
    if not v:
        raise UserError("Ce fichier ne contient pas de vidéo.")
    a = next((s for s in streams if s.get("codec_type") == "audio"), None)
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(float(sd["rotation"]))
    rot = rot or int(v.get("tags", {}).get("rotate", 0) or 0)
    if abs(rot) % 180 == 90:
        w, h = h, w
    dur = float(info.get("format", {}).get("duration") or v.get("duration") or 0)
    if not dur or not w:
        raise UserError("Durée ou dimensions de la vidéo introuvables.")
    ext = path.suffix.lower()
    m, s = divmod(int(dur), 60)
    label = f"Vidéo {ext[1:].upper()} · {w} × {h} · {m} min {s:02d} s" + ("" if a else " · sans son")
    return {"width": w, "height": h, "duration": dur, "audio": bool(a), "vcodec": v.get("codec_name"),
            "ext": ext, "legacy": ext in LEGACY, "label": label}


def _target(info, opts):
    w, h = fit(info["width"], info["height"], RESOLUTIONS[opts["resolution"]])
    return max(2, w // 2 * 2), max(2, h // 2 * 2)  # dimensions paires (exigé par H.264)


def _container(info):
    return CONTAINERS[".mp4"] if info["legacy"] else CONTAINERS[info["ext"]]


def _cmd(src, out, info, opts, start=None, length=None, audio=True, progress=False):
    vc, ac, fmt, _ = _container(info)
    crf264, crf_vp9 = CRF[opts["qualite"]]
    w, h = _target(info, opts)
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    if start is not None:
        cmd += ["-ss", f"{start:.2f}"]
    cmd += ["-i", str(src)]
    if length:
        cmd += ["-t", f"{length:.2f}"]
    if progress:
        cmd += ["-progress", "pipe:1", "-nostats"]
    cmd += ["-map", "0:v:0", "-vf", f"scale={w}:{h}:flags=lanczos,format=yuv420p"]
    if vc == "x264":
        cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf264)]
    else:
        cmd += ["-c:v", "libvpx-vp9", "-crf", str(crf_vp9), "-b:v", "0",
                "-deadline", "good", "-cpu-used", "5", "-row-mt", "1"]
    a = AUDIO[opts["son"]]
    if audio and a and info["audio"]:
        cmd += ["-map", "0:a:0", "-c:a", ac, "-b:a", f"{a[0]}k", "-ac", str(a[1])]
    else:
        cmd += ["-an"]
    if fmt in ("mp4", "mov", "3gp"):
        cmd += ["-movflags", "+faststart"]
    cmd += ["-f", fmt, str(out)]
    return cmd


def _run(cmd, duration, progress):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    for line in p.stdout:
        if line.startswith("out_time_us=") and duration:
            try:
                progress(min(99.0, int(line.split("=")[1]) / 1e6 / duration * 100))
            except ValueError:
                pass
    err = p.stderr.read()
    if p.wait():
        raise UserError("Échec de l'encodage vidéo : " + err[-300:])


def estimate(path: Path, work: Path, opts: dict, info: dict, progress=lambda p: None) -> dict:
    """Estime la taille finale en encodant 3 courts extraits (ou toute la vidéo si elle est courte)."""
    dur = info["duration"]
    if dur <= 40:
        out = work / ("estimation" + _container(info)[3])
        _run(_cmd(path, out, info, opts, progress=True), dur, progress)
        return {"size": out.stat().st_size, "exact": True, "file": out}
    sample = 6.0
    total = 0
    for i, frac in enumerate((0.15, 0.5, 0.85)):
        out = work / f"extrait{i}{_container(info)[3]}"
        subprocess.run(_cmd(path, out, info, opts, start=dur * frac, length=sample, audio=False),
                       capture_output=True, check=True)
        total += out.stat().st_size
        out.unlink(missing_ok=True)
        progress((i + 1) / 3 * 100)
    video_bps = total / (3 * sample)
    a = AUDIO[opts["son"]]
    audio_bps = (a[0] * 1000 / 8) if a and info["audio"] else 0
    return {"size": int((video_bps + audio_bps) * dur * 1.02), "exact": False}


def compress(path: Path, out_dir: Path, opts: dict, info: dict, progress=lambda p: None,
             cached: Path | None = None) -> list[Path]:
    stem = Path(info["name"]).stem
    out = out_dir / (stem + "_compresse" + _container(info)[3])
    if cached and cached.exists():
        cached.replace(out)
    else:
        _run(_cmd(path, out, info, opts, progress=True), info["duration"], progress)
    outputs = [out]
    if opts.get("mp3") and info["audio"]:
        mono = opts["son"] == "mono"
        mp3 = out_dir / (stem + "_son.mp3")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path), "-vn",
                            "-c:a", "libmp3lame", "-b:a", "64k" if mono else "128k",
                            "-ac", "1" if mono else "2", str(mp3)], capture_output=True, text=True, check=False)
        if r.returncode:
            raise UserError("Échec de l'extraction MP3 : " + r.stderr[-300:])
        outputs.append(mp3)
    return outputs
