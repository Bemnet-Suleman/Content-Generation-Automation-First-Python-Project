"""
Module 2: Asset Sourcing — "The Hands"
---------------------------------------
Sources every asset needed to assemble the final video.
All assets strictly follow style_profile (Dark Cinematic, Lo-fi Suspense).

  Visuals   : Pexels API → Pixabay fallback  (portrait, cinematic dark)
  Voiceover : kokoro-onnx → edge-tts fallback (en-US-GuyNeural)
  Music     : ytmusicapi + yt-dlp → FMA API fallback
  SFX       : Freesound API (2 atmospheric clips)

Output: local file paths — each sent directly to Telegram as a separate file.
Entry point: run_asset_sourcing(script_result: dict) -> dict
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

import requests

from bot.config import style_profile


# ── CONFIG ─────────────────────────────────────────────────────────────────────

PEXELS_API_KEY    = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY   = os.getenv("PIXABAY_API_KEY", "")
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")

# Style modifiers appended to every visual search (from style_profile)
_THEME = style_profile["visual_theme"].replace("_", " ")   # "dark cinematic"
STYLE_MODIFIERS = "cinematic dark high contrast moody noir"

TTS_VOICE = "en-US-GuyNeural"
ASSETS_DIR = Path("assets/module2")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

MAX_VIDEO_MB = 45   # Telegram bot limit is 50 MB — stay well under


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _run_dir() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = ASSETS_DIR / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slug(text: str, max_len: int = 30) -> str:
    return re.sub(r"[^\w]", "_", text)[:max_len]


def _download(url: str, out: Path, headers: dict | None = None, max_mb: int = MAX_VIDEO_MB) -> bool:
    """Stream-download url → out, abort if file exceeds max_mb."""
    try:
        with requests.get(url, stream=True, timeout=60, headers=headers or {}) as r:
            r.raise_for_status()
            size = 0
            with open(out, "wb") as f:
                for chunk in r.iter_content(65_536):
                    size += len(chunk)
                    if size > max_mb * 1_048_576:
                        print(f"[Module 2] {out.name} exceeded {max_mb} MB — skipping")
                        out.unlink(missing_ok=True)
                        return False
                    f.write(chunk)
        return out.exists() and out.stat().st_size > 0
    except Exception as e:
        print(f"[Module 2] Download failed ({url[:60]}...): {e}")
        out.unlink(missing_ok=True)
        return False


def _build_script_text(script: dict) -> str:
    """Join the 4 narrative parts into clean spoken text (pacing cues stripped)."""
    meat = script.get("meat", {})
    parts = [
        script.get("hook", ""),
        script.get("stakes", ""),
        meat.get("tip1", "") if isinstance(meat, dict) else "",
        meat.get("tip2", "") if isinstance(meat, dict) else "",
        meat.get("tip3", "") if isinstance(meat, dict) else "",
        script.get("cta", ""),
    ]
    text = " ".join(p.strip() for p in parts if p.strip())
    text = text.replace("<<PAUSE>>", "").replace("<<STRESS>>", "")
    return re.sub(r"\s+", " ", text).strip()


# ── VISUALS ────────────────────────────────────────────────────────────────────

def _pexels_video(keyword: str, out_dir: Path) -> str | None:
    """Download best-fitting portrait video from Pexels."""
    if not PEXELS_API_KEY:
        return None
    query = f"{keyword} {STYLE_MODIFIERS}"
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_API_KEY},
            params={"query": query, "orientation": "portrait", "size": "medium", "per_page": 5},
            timeout=15,
        )
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None
        for video in videos:
            files = sorted(
                [f for f in video.get("video_files", []) if f.get("width", 0) >= 720],
                key=lambda f: f.get("file_size", 9_999_999_999),
            )
            if not files:
                continue
            url = files[0]["link"]
            out = out_dir / f"visual_{_slug(keyword)}_pexels.mp4"
            if _download(url, out):
                print(f"[Module 2] Pexels clip saved: {out.name}")
                return str(out)
    except Exception as e:
        print(f"[Module 2] Pexels error for '{keyword}': {e}")
    return None


def _pixabay_video(keyword: str, out_dir: Path) -> str | None:
    """Fallback: portrait video from Pixabay."""
    if not PIXABAY_API_KEY:
        return None
    query = f"{keyword} {STYLE_MODIFIERS}"
    try:
        r = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": PIXABAY_API_KEY, "q": query, "orientation": "vertical", "per_page": 3},
            timeout=15,
        )
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        url = hits[0]["videos"]["medium"]["url"]
        out = out_dir / f"visual_{_slug(keyword)}_pixabay.mp4"
        if _download(url, out):
            print(f"[Module 2] Pixabay clip saved: {out.name}")
            return str(out)
    except Exception as e:
        print(f"[Module 2] Pixabay error for '{keyword}': {e}")
    return None


def fetch_visuals(keywords: list[str], out_dir: Path) -> list[str]:
    """Source 1 portrait video clip per keyword (max 3). Pexels → Pixabay."""
    paths = []
    for kw in keywords[:3]:
        print(f"[Module 2] Sourcing visual for keyword: '{kw}'")
        path = _pexels_video(kw, out_dir) or _pixabay_video(kw, out_dir)
        if path:
            paths.append(path)
        else:
            print(f"[Module 2] No visual found for '{kw}' — check API keys")
    return paths


# ── VOICEOVER ──────────────────────────────────────────────────────────────────

def generate_voiceover(script_text: str, out_dir: Path) -> str | None:
    """
    Generate voiceover audio from the full script text.
    Tier 1: kokoro-onnx (requires model files in working dir)
    Tier 2: edge-tts CLI (en-US-GuyNeural, no model download needed)
    """
    # ── Tier 1: kokoro-onnx ──────────────────────────────────────────
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf

        model_path  = "kokoro-v1.onnx"
        voices_path = "voices.json"
        if not (Path(model_path).exists() and Path(voices_path).exists()):
            raise FileNotFoundError("kokoro model files not found in working directory")

        print("[Module 2] Attempting kokoro-onnx voiceover...")
        kokoro = Kokoro(model_path, voices_path)
        samples, sr = kokoro.create(script_text, voice="af_sarah", speed=1.0, lang="en-us")
        out = out_dir / "voiceover.wav"
        sf.write(str(out), samples, sr)
        print("[Module 2] Voiceover generated via kokoro-onnx ✓")
        return str(out)
    except Exception as e:
        print(f"[Module 2] kokoro-onnx unavailable ({type(e).__name__}: {e}) — falling back to edge-tts")

    # ── Tier 2: edge-tts ─────────────────────────────────────────────
    try:
        out = out_dir / "voiceover.mp3"
        result = subprocess.run(
            ["edge-tts", "--text", script_text, "--voice", TTS_VOICE, "--write-media", str(out)],
            capture_output=True,
            text=True,
            timeout=90,
        )
        if result.returncode == 0 and out.exists() and out.stat().st_size > 0:
            print(f"[Module 2] Voiceover generated via edge-tts ({TTS_VOICE}) ✓")
            return str(out)
        print(f"[Module 2] edge-tts error: {result.stderr.strip()}")
    except Exception as e:
        print(f"[Module 2] edge-tts failed: {e}")

    return None


# ── MUSIC ──────────────────────────────────────────────────────────────────────

def _ytdlp_download(url: str, out_path: str) -> bool:
    """Download audio track from a YouTube URL via yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp", "-x",
                "--audio-format", "mp3",
                "--audio-quality", "5",
                "--max-filesize", "45m",
                "--no-playlist",
                "-o", out_path,
                url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0 and Path(out_path).exists() and Path(out_path).stat().st_size > 0
    except Exception as e:
        print(f"[Module 2] yt-dlp failed: {e}")
        return False


def _ytmusic_download(query: str, out_path: str) -> bool:
    """Search YouTube Music for query and download audio via yt-dlp."""
    try:
        from ytmusicapi import YTMusic
        ytm = YTMusic()
        results = ytm.search(query, filter="songs", limit=5)
        if not results:
            return False
        video_id = results[0].get("videoId")
        if not video_id:
            return False
        yt_url = f"https://www.youtube.com/watch?v={video_id}"
        title = results[0].get("title", "track")
        print(f"[Module 2] Downloading music: '{title}' ({video_id})")
        return _ytdlp_download(yt_url, out_path)
    except Exception as e:
        print(f"[Module 2] ytmusicapi error: {e}")
        return False


def _fma_download(out_path: str) -> bool:
    """
    Fallback: download a lo-fi/ambient track from Free Music Archive.
    Uses the public JSON API — no key required.
    """
    try:
        r = requests.get(
            "https://freemusicarchive.org/api/get/tracks.json",
            params={"genre_handle": "ambient", "limit": 10, "sort": "track_date_recorded", "d": 1},
            timeout=15,
        )
        if r.status_code != 200:
            return False
        tracks = r.json().get("dataset", [])
        for track in tracks:
            dl_url = track.get("track_file")
            if dl_url:
                if _download(dl_url, Path(out_path), max_mb=45):
                    print("[Module 2] Music sourced via FMA ✓")
                    return True
    except Exception as e:
        print(f"[Module 2] FMA error: {e}")
    return False


def fetch_music(mood_tags: list[str], out_dir: Path) -> str | None:
    """
    Source a no-copyright lo-fi background track.
    Tier 1: ytmusicapi + yt-dlp
    Tier 2: Free Music Archive API
    """
    mood_str = " ".join(mood_tags[:2]) if mood_tags else "lo-fi suspense"
    query = f"no copyright {mood_str} lo-fi instrumental background music"
    out_path = str(out_dir / "background_music.mp3")

    print(f"[Module 2] Sourcing music — query: '{query}'")
    if _ytmusic_download(query, out_path):
        print("[Module 2] Music sourced via ytmusicapi + yt-dlp ✓")
        return out_path

    print("[Module 2] ytmusicapi/yt-dlp failed — trying FMA fallback")
    if _fma_download(out_path):
        return out_path

    print("[Module 2] Music sourcing failed — all sources exhausted")
    return None


# ── SFX ────────────────────────────────────────────────────────────────────────

def fetch_sfx(out_dir: Path) -> list[str]:
    """
    Download 1-2 atmospheric SFX clips from Freesound API.
    Queries are derived from the style_profile mood (dark cinematic lo-fi).
    """
    if not FREESOUND_API_KEY:
        print("[Module 2] FREESOUND_API_KEY not set — skipping SFX")
        return []

    sfx_queries = ["dark ambient tension atmospheric", "cinematic subtle texture drone"]
    paths = []

    for i, query in enumerate(sfx_queries, 1):
        print(f"[Module 2] Sourcing SFX {i}: '{query}'")
        try:
            r = requests.get(
                "https://freesound.org/apiv2/search/text/",
                params={
                    "query": query,
                    "token": FREESOUND_API_KEY,
                    "fields": "name,previews,duration",
                    "filter": "duration:[5 TO 60]",
                    "sort": "rating_desc",
                    "page_size": 5,
                },
                timeout=15,
            )
            results = r.json().get("results", [])
            if not results:
                print(f"[Module 2] No SFX results for '{query}'")
                continue

            preview_url = results[0]["previews"]["preview-hq-mp3"]
            sfx_out = out_dir / f"sfx_{i}.mp3"
            ok = _download(
                preview_url,
                sfx_out,
                headers={"Authorization": f"Token {FREESOUND_API_KEY}"},
                max_mb=10,
            )
            if ok:
                print(f"[Module 2] SFX {i} saved: {sfx_out.name} ✓")
                paths.append(str(sfx_out))
        except Exception as e:
            print(f"[Module 2] SFX {i} error: {e}")

    return paths


# ── MAIN ENTRY POINT ───────────────────────────────────────────────────────────

def run_asset_sourcing(script_result: dict) -> dict:
    """
    Run all asset sourcing steps for a Module 1 script result.

    Returns:
      {
        "visuals"  : list[str],   # paths to video clips
        "voiceover": str | None,  # path to voiceover audio file
        "music"    : str | None,  # path to background music file
        "sfx"      : list[str],   # paths to SFX clips
        "run_dir"  : str,
      }
    """
    out_dir = _run_dir()
    print(f"[Module 2] Run directory: {out_dir}")

    script    = script_result.get("script", {})
    keywords  = script.get("keywords", [])
    mood_tags = script.get("mood_tags", [])
    script_text = _build_script_text(script)

    if not keywords:
        print("[Module 2] Warning: no keywords in script result — visuals may be generic")
        keywords = [script_result.get("niche", "cinematic dark")]

    print("[Module 2] ── STEP 1 / 4  Visuals ───────────────────────────────────")
    visuals = fetch_visuals(keywords, out_dir)

    print("[Module 2] ── STEP 2 / 4  Voiceover ────────────────────────────────")
    voiceover = generate_voiceover(script_text, out_dir)

    print("[Module 2] ── STEP 3 / 4  Background Music ─────────────────────────")
    music = fetch_music(mood_tags, out_dir)

    print("[Module 2] ── STEP 4 / 4  SFX ──────────────────────────────────────")
    sfx = fetch_sfx(out_dir)

    total = len(visuals) + (1 if voiceover else 0) + (1 if music else 0) + len(sfx)
    print(f"[Module 2] Done — {total} asset(s) ready in {out_dir}")

    return {
        "visuals":   visuals,
        "voiceover": voiceover,
        "music":     music,
        "sfx":       sfx,
        "run_dir":   str(out_dir),
    }
