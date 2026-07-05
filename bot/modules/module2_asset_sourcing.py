"""
Module 2: Asset Sourcing — "The Hands"
---------------------------------------
All assets strictly follow style_profile (Dark Cinematic, Lo-fi Suspense).

  Visuals   : Pexels (portrait, 720–1080px) → Pixabay fallback
              Zero-result retry: strips query to main noun and retries once.
              401 propagates as PexelsAuthError so the bot can alert the user.
  Voiceover : HF parler-tts (parler-tts-medium-v1) → edge-tts AndrewNeural → BrianNeural
  Music     : ytmusicapi + yt-dlp → FMA API fallback
  SFX       : Freesound API (2 atmospheric clips)
  Mixing    : pydub — music ducked to –20 dB below voiceover level

Entry point: run_asset_sourcing(script_result, chat_id, custom_style) -> dict
  Returns: visuals, voiceover, music, music_mixed, sfx, failures, run_dir
"""

import os
import random
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv, find_dotenv
from groq import Groq

from bot.config import style_profile

load_dotenv(find_dotenv())

# ── CONFIG ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")
HF_TOKEN = os.getenv("HF_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

STYLE_MODIFIERS = "cinematic dark high contrast moody noir"
ASSETS_DIR = BASE_DIR / "assets" / "module2"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def _which(program: str) -> bool:
    return shutil.which(program) is not None


def generate_dynamic_style(niche: str, custom_style: dict = None) -> dict:
    """Generate a dynamic style profile using AI based on the niche, or use custom if provided."""
    if custom_style:
        return custom_style

    if not GROQ_API_KEY:
        return style_profile  # fallback to static

    try:
        client = Groq(api_key=GROQ_API_KEY)
        prompt = f"""
        Generate a custom style profile for a viral short-form video about "{niche}".
        Return ONLY a valid JSON object with these keys:
        {{
            "visual_theme": "string (e.g., dark_cinematic, bright_modern)",
            "font": "string (e.g., Montserrat-Bold)",
            "caption_color": "string (hex, e.g., #FFD700)",
            "music_genre": "string (e.g., Lo-fi Suspense)"
        }}
        Make it engaging and fitting for the niche.
        """
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.7
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        import json
        style = json.loads(raw)
        return style
    except Exception as e:
        print(f"[M2] Style generation failed: {e}")
        return style_profile  # fallback

MAX_VIDEO_MB = 45
MAX_VIDEO_DURATION_SEC = 40
VIDEO_SOURCES = ["pexels"]  # Disabled Pixabay due to issues


# ── CUSTOM EXCEPTIONS ──────────────────────────────────────────────────────────


class PexelsAuthError(Exception):
    """Raised when Pexels returns 401 — lets the bot send a targeted alert."""


# ── HELPERS ────────────────────────────────────────────────────────────────────


def _run_dir() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = ASSETS_DIR / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def _slug(text: str, max_len: int = 30) -> str:
    return re.sub(r"[^\w]", "_", text)[:max_len]


def _main_noun(query: str) -> str:
    """Return only the first meaningful word from the query (the main noun)."""
    words = [w for w in query.split() if len(w) > 2]
    return words[0] if words else query.split()[0]


def _download(
    url: str, out: Path, headers: dict | None = None, max_mb: int = MAX_VIDEO_MB
) -> bool:
    """Stream-download url → out; abort if file exceeds max_mb."""
    try:
        with requests.get(url, stream=True, timeout=60, headers=headers or {}) as r:
            r.raise_for_status()
            size = 0
            with open(out, "wb") as f:
                for chunk in r.iter_content(65_536):
                    size += len(chunk)
                    if size > max_mb * 1_048_576:
                        print(f"[M2] {out.name} > {max_mb} MB — skipped")
                        out.unlink(missing_ok=True)
                        return False
                    f.write(chunk)
        return out.exists() and out.stat().st_size > 0
    except Exception as e:
        print(f"[M2] Download error ({url[:60]}): {e}")
        out.unlink(missing_ok=True)
        return False


def _probe_video(path: Path) -> tuple[bool, str | None]:
    """Validate downloaded video with ffprobe when available."""
    if not path.exists() or path.stat().st_size == 0:
        return False, "Video file is empty or missing"

    if _which("ffprobe"):
        try:
            res = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration,size",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if res.returncode != 0:
                return False, f"ffprobe failed: {res.stderr.strip()}"
            lines = [line.strip() for line in res.stdout.splitlines() if line.strip()]
            if len(lines) < 2:
                return False, "ffprobe returned invalid metadata"
            duration = float(lines[0])
            if duration <= 0:
                return False, "Video duration is zero"
            if duration > MAX_VIDEO_DURATION_SEC:
                return False, f"Video too long ({duration:.1f}s)"
            return True, None
        except Exception as e:
            return False, f"ffprobe error: {e}"

    if path.stat().st_size < 300_000:
        return False, "Video file too small to be valid"
    return True, None


def _build_script_text(script: dict) -> str:
    """Join 4-part narrative into clean spoken text (pacing cues stripped)."""
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


def _pexels_search(query: str) -> list[dict]:
    """
    Call Pexels video search.
    Raises PexelsAuthError on 401.
    Returns empty list on zero results.
    """
    r = requests.get(
        "https://api.pexels.com/videos/search",
        headers={"Authorization": PEXELS_API_KEY},
        params={"query": query, "orientation": "portrait", "per_page": 3},
        timeout=15,
    )
    if r.status_code == 401:
        raise PexelsAuthError("Pexels API key is invalid (401 Unauthorized)")
    r.raise_for_status()
    return r.json().get("videos", [])


def _best_pexels_file(video: dict) -> str | None:
    """Pick the first video file with 720 ≤ width ≤ 1080 (portrait, memory-safe)."""
    candidates = [
        f for f in video.get("video_files", []) if 720 <= f.get("width", 0) <= 1080
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda f: f.get("file_size", 9_999_999_999))
    return candidates[0]["link"]


def _pexels_video(keyword: str, out_dir: Path) -> tuple[str | None, str | None]:
    """
    Download one portrait clip from Pexels.
    Returns (path, failure_reason) — exactly one is None.
    Raises PexelsAuthError if key is invalid.
    """
    if not PEXELS_API_KEY:
        return None, "PEXELS_API_KEY not set"

    full_query = f"{keyword} {STYLE_MODIFIERS}"
    try:
        videos = _pexels_search(full_query)

        # Zero-result retry: strip to main noun
        if not videos:
            noun = _main_noun(keyword)
            print(f"[M2] Pexels: 0 results for '{full_query}' — retrying with '{noun}'")
            videos = _pexels_search(noun)

        if not videos:
            return None, f"Pexels: 0 results for '{keyword}' (even after noun retry)"

        for video in videos:
            url = _best_pexels_file(video)
            if not url:
                continue
            out = out_dir / f"visual_{_slug(keyword)}_pexels.mp4"
            if _download(url, out):
                print(f"[M2] Pexels ✓ {out.name}")
                return str(out), None

        return None, f"Pexels: no file in 720–1080px range for '{keyword}'"
    except PexelsAuthError:
        raise
    except Exception as e:
        return None, f"Pexels error for '{keyword}': {e}"


_PIXABAY_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}


def _pixabay_hit_url(hit: dict) -> str | None:
    """
    Navigate hit['videos'] per the Pixabay docs.
    Prefers 'medium'; falls back to 'small'.
    """
    videos = hit.get("videos", {})
    for size in ("medium", "small"):
        entry = videos.get(size, {})
        url = entry.get("url", "")
        if url:
            return url
    return None


def _pixabay_search(query: str) -> list[dict]:
    """Single Pixabay API call. Returns hits list."""
    r = requests.get(
        "https://pixabay.com/api/videos/",
        headers=_PIXABAY_HEADERS,
        params={
            "key": PIXABAY_API_KEY,
            "q": query,
            "orientation": "vertical",
            "per_page": 3,
        },
        timeout=15,
    )
    r.raise_for_status()
    return r.json().get("hits", [])


def _pixabay_video(keyword: str, out_dir: Path) -> tuple[str | None, str | None]:
    """
    Fallback: portrait video from Pixabay.
    Exact traversal: hit['videos']['medium']['url'] → hit['videos']['small']['url'].
    Zero-result retry: strips keyword to main noun and retries once.
    """
    if not PIXABAY_API_KEY:
        return None, "PIXABAY_API_KEY not set"

    full_query = f"{keyword} {STYLE_MODIFIERS}"
    try:
        hits = _pixabay_search(full_query)

        if not hits:
            noun = _main_noun(keyword)
            print(
                f"[M2] Pixabay: 0 results for '{full_query}' — retrying with '{noun}'"
            )
            hits = _pixabay_search(noun)

        if not hits:
            return None, f"Pixabay: 0 results for '{keyword}' (even after noun retry)"

        for hit in hits:
            url = _pixabay_hit_url(hit)
            if not url:
                continue
            out = out_dir / f"visual_{_slug(keyword)}_pixabay.mp4"
            if _download(url, out):
                print(f"[M2] Pixabay ✓ {out.name}")
                return str(out), None

        return None, f"Pixabay: no downloadable file found for '{keyword}'"
    except Exception as e:
        return None, f"Pixabay error for '{keyword}': {e}"


def fetch_visuals(keywords: list[str], out_dir: Path) -> tuple[list[str], list[str]]:
    """
    Source 1 portrait clip per keyword (max 3).
    Returns (paths, failures).
    Raises PexelsAuthError if Pexels key is invalid.
    """
    paths, failures = [], []
    for kw in keywords[:3]:
        print(f"[M2] Visual → '{kw}'")
        sources = VIDEO_SOURCES.copy()  # Now only Pexels
        success = False
        for source in sources:
            if source == "pixabay":
                path, reason = _pixabay_video(kw, out_dir)
            else:
                try:
                    path, reason = _pexels_video(kw, out_dir)
                except PexelsAuthError:
                    raise

            if not path:
                failures.append(f"{source.capitalize()} '{kw}': {reason}")
                continue

            validated, validation_reason = _probe_video(Path(path))
            if not validated:
                failures.append(f"{source.capitalize()} '{kw}' invalid: {validation_reason}")
                Path(path).unlink(missing_ok=True)
                continue

            paths.append(path)
            success = True
            break

        if not success:
            failures.append(f"No valid visual found for '{kw}'")
    return paths, failures


# ── VOICEOVER ──────────────────────────────────────────────────────────────────

_PARLER_URLS = [
    "https://router.huggingface.co/hf-inference/models/parler-tts/parler-tts-large-v1",
]


def _parler_tts(text: str, out: Path) -> tuple[bool, str | None]:
    """
    HF Inference Router — parler-tts/parler-tts-large-v1
    Tries the Hugging Face router endpoint.
    Returns (success, error_detail).
    error_detail is set (with URL + status) on any non-200 response.
    """
    if not HF_TOKEN:
        return False, None  # silently skip; no key configured

    voice_description = (
        "A deep, clear male voice with a calm and confident tone, "
        "speaking at a measured pace. The recording is clean with no background noise."
    )
    last_detail = None
    for url in _PARLER_URLS:
        try:
            r = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Accept": "audio/wav",
                },
                json={"inputs": text, "parameters": {"description": voice_description}},
                timeout=120,
            )
            if r.status_code == 200:
                out.write_bytes(r.content)
                if out.stat().st_size > 0:
                    return True, None
                detail = f"parler-tts 200 OK but response body was empty.\nURL tried: {url}"
                print(f"[M2] {detail}")
                return False, detail

            detail = (
                f"parler-tts HTTP {r.status_code} from:\n"
                f"<code>{url}</code>\n"
                f"Body: <code>{r.text[:300]}</code>"
            )
            print(f"[M2] {detail}")
            if r.status_code == 404:
                last_detail = detail
                continue
            return False, detail
        except Exception as e:
            last_detail = f"parler-tts request error: {e}\nURL: {url}"
            print(f"[M2] {last_detail}")
            continue
    return False, last_detail or "parler-tts request failed for all endpoints"


def _edge_tts(text: str, voice: str, out: Path) -> bool:
    """Run edge-tts CLI for the given voice. Handles long text by splitting."""
    if not _which("edge-tts"):
        print("[M2] edge-tts binary not found on PATH. Install the edge-tts package.")
        return False

    # Split long text into chunks to avoid timeout
    words = text.split()
    chunks = []
    current_chunk = []
    for word in words:
        current_chunk.append(word)
        if len(current_chunk) >= 50:  # 50 words per chunk
            chunks.append(" ".join(current_chunk))
            current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    if len(chunks) == 1:
        # Short text, generate directly
        try:
            res = subprocess.run(
                ["edge-tts", "--text", text, "--voice", voice, "--write-media", str(out)],
                capture_output=True,
                text=True,
                timeout=300,
            )
            if res.returncode != 0:
                print(f"[M2] edge-tts failed: {res.stderr.strip()}")
            return res.returncode == 0 and out.exists() and out.stat().st_size > 0
        except Exception as e:
            print(f"[M2] edge-tts ({voice}) error: {e}")
            return False
    else:
        # Long text, generate chunks and concatenate
        try:
            from pydub import AudioSegment
            combined = AudioSegment.empty()
            for i, chunk in enumerate(chunks):
                chunk_out = out.parent / f"chunk_{i}.mp3"
                res = subprocess.run(
                    ["edge-tts", "--text", chunk, "--voice", voice, "--write-media", str(chunk_out)],
                    capture_output=True,
                    text=True,
                    timeout=120,  # shorter for chunks
                )
                if res.returncode != 0:
                    print(f"[M2] edge-tts chunk {i} failed: {res.stderr.strip()}")
                    return False
                if not chunk_out.exists():
                    print(f"[M2] edge-tts chunk {i} file not created")
                    return False
                chunk_audio = AudioSegment.from_file(chunk_out)
                combined += chunk_audio
                chunk_out.unlink()  # clean up
            combined.export(str(out), format="mp3")
            return out.exists() and out.stat().st_size > 0
        except Exception as e:
            print(f"[M2] edge-tts ({voice}) concatenation error: {e}")
            return False


def generate_voiceover(
    script_text: str, out_dir: Path
) -> tuple[str | None, str, str | None]:
    """
    Generate voiceover. Returns (path, engine_label, hf_error).
    hf_error is always None since HF is disabled.
    Tier 1: edge-tts (en-US-AndrewNeural)
    Tier 2: edge-tts (en-US-BrianNeural)
    """
    # HF parler-tts disabled due to endpoint issues

    # Tier 1 — edge-tts AndrewNeural
    print("[M2] Voiceover → edge-tts (AndrewNeural)...")
    out = out_dir / "voiceover.mp3"
    if _edge_tts(script_text, "en-US-AndrewNeural", out):
        print("[M2] Voiceover ✓ edge-tts AndrewNeural")
        return str(out), "edge-tts AndrewNeural"

    # Tier 2 — edge-tts BrianNeural
    print("[M2] AndrewNeural failed — trying BrianNeural...")
    out2 = out_dir / "voiceover_brian.mp3"
    if _edge_tts(script_text, "en-US-BrianNeural", out2):
        print("[M2] Voiceover ✓ edge-tts BrianNeural")
        return str(out2), "edge-tts BrianNeural"

    return None, "all TTS engines failed"


# ── AUDIO MIXING ───────────────────────────────────────────────────────────────


def mix_music_under_voice(
    voiceover_path: str, music_path: str, out_dir: Path
) -> str | None:
    """
    Duck background music to –20 dB below voiceover using pydub.
    Loops/trims music to match voiceover duration.
    Returns path to mixed MP3, or None on failure.
    """
    try:
        if not _which("ffmpeg"):
            print("[M2] ffmpeg not found. Install FFmpeg and add it to PATH for audio mixing.")
            return None
        from pydub import AudioSegment

        print("[M2] Mixing: loading audio files...")
        voice = AudioSegment.from_file(voiceover_path)
        music = AudioSegment.from_file(music_path)

        # Loop music until it covers the full voiceover length
        while len(music) < len(voice):
            music = music + music
        music = music[: len(voice)]

        # Duck music so it sits –20 dB below the voiceover's average loudness
        target_dBFS = voice.dBFS - 20.0
        adjustment = target_dBFS - music.dBFS
        music = music + adjustment

        mixed = voice.overlay(music)
        out = out_dir / "mixed_audio.mp3"
        mixed.export(str(out), format="mp3", bitrate="192k")
        print(
            f"[M2] Mixed audio ✓ (voice {voice.dBFS:.1f} dBFS | music ducked to {target_dBFS:.1f} dBFS)"
        )
        return str(out)
    except Exception as e:
        print(f"[M2] Audio mixing failed: {e}")
        return None


# ── MUSIC ──────────────────────────────────────────────────────────────────────


def _ytmusic_download(query: str, out_path: str) -> bool:
    if not _which("yt-dlp"):
        print("[M2] yt-dlp not found on PATH. Skipping YouTube download.")
        return False
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
        print(f"[M2] yt-dlp downloading: {results[0].get('title', video_id)}")
        res = subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                "mp3",
                "--audio-quality",
                "5",
                "--max-filesize",
                "45m",
                "--no-playlist",
                "-o",
                out_path,
                yt_url,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return (
            res.returncode == 0
            and Path(out_path).exists()
            and Path(out_path).stat().st_size > 0
        )
    except Exception as e:
        print(f"[M2] ytmusicapi error: {e}")
        return False


def _fma_download(out_path: str, mood_str: str) -> bool:
    genre = "electronic" if "electronic" in mood_str.lower() else "ambient"
    try:
        r = requests.get(
            "https://freemusicarchive.org/api/get/tracks.json",
            params={
                "genre_handle": genre,
                "limit": 20,  # increased limit
                "sort": "track_downloads",  # sort by downloads
                "d": 1,
            },
            timeout=15,
        )
        if r.status_code != 200:
            print(f"[M2] FMA API error: {r.status_code}")
            return False
        data = r.json()
        tracks = data.get("dataset", [])
        if not tracks:
            print(f"[M2] FMA no tracks for genre {genre}")
            return False
        for track in tracks:
            dl_url = track.get("track_file")
            if dl_url:
                print(f"[M2] Trying FMA track: {track.get('track_title', 'unknown')}")
                if _download(dl_url, Path(out_path), max_mb=45):
                    print("[M2] Music ✓ FMA")
                    return True
    except Exception as e:
        print(f"[M2] FMA error: {e}")
    return False


def fetch_music(mood_tags: list[str], out_dir: Path) -> tuple[str | None, str | None]:
    """Returns (path, failure_reason)."""
    mood_str = " ".join(mood_tags[:2]) if mood_tags else "lo-fi instrumental"
    query = f"{mood_str} background music"
    out_path = str(out_dir / "background_music.mp3")
    print(f"[M2] Music → '{query}'")

    if _ytmusic_download(query, out_path):
        return out_path, None
    print("[M2] ytmusicapi/yt-dlp failed — trying FMA")
    if _fma_download(out_path, mood_str):
        return out_path, None
    print("[M2] FMA failed — using hardcoded fallback")
    # Hardcoded fallback: public domain ambient track
    fallback_url = "https://freesound.org/data/previews/316/316847_5123451-lq.mp3"  # Example public domain sound
    if _download(fallback_url, Path(out_path), max_mb=10):
        print("[M2] Music ✓ Fallback")
        return out_path, None
    # If even fallback fails, create a silent audio or something, but for now, return None
    return None, "All music sources failed — no background music"


# ── SFX ────────────────────────────────────────────────────────────────────────


def fetch_sfx(out_dir: Path) -> tuple[list[str], list[str]]:
    """Returns (paths, failures)."""
    if not FREESOUND_API_KEY:
        return [], ["FREESOUND_API_KEY not set — SFX skipped"]

    queries = ["dark ambient tension atmospheric", "cinematic subtle texture drone"]
    paths, failures = [], []

    for i, query in enumerate(queries, 1):
        print(f"[M2] SFX {i} → '{query}'")
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
                failures.append(f"SFX {i}: no Freesound results for '{query}'")
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
                print(f"[M2] SFX {i} ✓ {sfx_out.name}")
                paths.append(str(sfx_out))
            else:
                failures.append(f"SFX {i}: download failed for '{query}'")
        except Exception as e:
            failures.append(f"SFX {i}: {e}")

    return paths, failures


# ── MAIN ENTRY POINT ───────────────────────────────────────────────────────────


def run_asset_sourcing(script_result: dict, chat_id: int = None, custom_style: dict = None) -> dict:
    """
    Source all assets for a Module 1 script result.

    Returns:
      visuals      : list[str]   — video clip paths
      voiceover    : str | None  — voiceover audio path
      voiceover_engine: str      — which engine was used
      music        : str | None  — raw music path
      music_mixed  : str | None  — music ducked –20 dB under voice (pydub)
      sfx          : list[str]   — SFX paths
      failures     : list[str]   — human-readable failure descriptions
      run_dir      : str
    """
    out_dir = _run_dir()
    print(f"[M2] Run dir: {out_dir}")
    failures: list[str] = []

    niche = script_result.get("niche", "general")
    dynamic_style = generate_dynamic_style(niche, custom_style)
    global STYLE_MODIFIERS
    STYLE_MODIFIERS = f"{dynamic_style['visual_theme'].replace('_', ' ')} high contrast moody noir"

    script = script_result.get("script", {})
    keywords = script.get("keywords", []) or [script_result.get("niche", "cinematic")]
    mood_tags = [dynamic_style['music_genre']] + script.get("mood_tags", [])
    script_text = _build_script_text(script)

    # ── Step 1: Visuals ──────────────────────────────────────────────────────
    print("[M2] ── 1/4  Visuals ────────────────────────────────────────────────")
    try:
        visuals, vis_failures = fetch_visuals(keywords, out_dir)
        failures.extend(vis_failures)
    except PexelsAuthError as e:
        visuals = []
        failures.append(f"❌ Pexels Auth: {e}")
        # Re-raise so bot.py can send the dedicated alert message
        raise

    # ── Step 2: Voiceover ────────────────────────────────────────────────────
    print("[M2] ── 2/4  Voiceover ──────────────────────────────────────────────")
    voiceover, vo_engine = generate_voiceover(script_text, out_dir)
    if not voiceover:
        failures.append(f"Voiceover: {vo_engine}")

    # ── Step 3: Music ────────────────────────────────────────────────────────
    print("[M2] ── 3/4  Music ──────────────────────────────────────────────────")
    music, music_fail = fetch_music(mood_tags, out_dir)
    if not music:
        failures.append(f"Music: {music_fail}")

    # ── Step 4: SFX ──────────────────────────────────────────────────────────
    print("[M2] ── 4/4  SFX ────────────────────────────────────────────────────")
    sfx, sfx_failures = fetch_sfx(out_dir)
    failures.extend(sfx_failures)

    # ── Audio mixing ─────────────────────────────────────────────────────────
    music_mixed = None
    if voiceover and music:
        print("[M2] ── Mixing audio (pydub –20 dB duck) ────────────────────────")
        music_mixed = mix_music_under_voice(voiceover, music, out_dir)
        if not music_mixed:
            failures.append("Audio mixing: pydub mix failed")

    total = len(visuals) + (1 if voiceover else 0) + (1 if music else 0) + len(sfx)
    print(f"[M2] Complete — {total} asset(s) | {len(failures)} failure(s)")

    return {
        "visuals": visuals,
        "voiceover": voiceover,
        "voiceover_engine": vo_engine,
        "music": music,
        "music_mixed": music_mixed,
        "sfx": sfx,
        "failures": failures,
        "run_dir": str(out_dir),
    }
