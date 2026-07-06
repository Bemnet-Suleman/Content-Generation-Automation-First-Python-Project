"""
Module 3: The Assembly
----------------------
Combines Module 1 script + Module 2 assets into final vertical video.

  Video: Concatenate visuals, resize to 1080x1920, loop/slow to match voiceover.
  Audio: Voiceover + ducked music + SFX at visual cues.
  Captions: Synced word highlights using style_profile font/color.
  Polish: Vignette and contrast filters.

Entry point: run_assembly(script_result, assets) -> str (output .mp4 path)
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
        TextClip, ColorClip, concatenate_videoclips
    )
    from moviepy.video.fx import speedx, resize
    from moviepy.audio.fx import volumex
    from pydub import AudioSegment
    import pysubs2
    MOVIEPY_IMPORT_ERROR = None
except Exception as exc:
    VideoFileClip = AudioFileClip = CompositeVideoClip = CompositeAudioClip = TextClip = ColorClip = concatenate_videoclips = None
    speedx = resize = None
    volumex = None
    AudioSegment = None
    pysubs2 = None
    MOVIEPY_IMPORT_ERROR = exc

from bot.config import style_profile
from bot.modules.module2_asset_sourcing import _build_script_text

# ── CONFIG ─────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE_DIR / "assets" / "module2"

def _get_voiceover_duration(voiceover_path: str) -> float:
    """Get duration of voiceover audio."""
    if not voiceover_path or not Path(voiceover_path).exists():
        return 0.0
    audio = AudioSegment.from_file(voiceover_path)
    return len(audio) / 1000.0

def _generate_subtitles(script_text: str, voiceover_path: str) -> List[Dict]:
    """Generate word-by-word timestamps for captions."""
    # Simple estimation: assume 150 words per minute
    words = re.findall(r'\b\w+\b', script_text)
    total_words = len(words)
    duration = _get_voiceover_duration(voiceover_path)
    if duration == 0 or total_words == 0:
        return []
    
    words_per_sec = total_words / duration
    subtitles = []
    start_time = 0.0
    for i, word in enumerate(words):
        end_time = (i + 1) / words_per_sec
        subtitles.append({
            'text': word,
            'start': start_time,
            'end': end_time
        })
        start_time = end_time
    return subtitles

def run_assembly(script_result: Dict[str, Any], assets: Dict[str, Any]) -> str:
    """
    Assemble final video from script and assets.

    Returns: path to output .mp4
    """
    if MOVIEPY_IMPORT_ERROR is not None:
        raise RuntimeError(f"Assembly dependencies are missing: {MOVIEPY_IMPORT_ERROR}")

    out_dir = ASSETS_DIR / "assembly"
    out_dir.mkdir(exist_ok=True)
    output_path = str(out_dir / "final_video.mp4")

    visuals = assets.get("visuals", [])
    voiceover = assets.get("voiceover")
    music = assets.get("music")
    sfx = assets.get("sfx", [])

    if not visuals or not voiceover:
        raise ValueError("Missing visuals or voiceover")

    # Get voiceover duration
    vo_duration = _get_voiceover_duration(voiceover)

    # Load video clips, resize to 1080x1920
    video_clips = []
    for path in visuals:
        if Path(path).exists():
            clip = VideoFileClip(path).resize(height=1920, width=1080)
            video_clips.append(clip)

    if not video_clips:
        raise ValueError("No valid video clips")

    # Concatenate and adjust to match voiceover
    total_video_duration = sum(c.duration for c in video_clips)
    if total_video_duration < vo_duration:
        # Loop or slow down
        loops_needed = int(vo_duration / total_video_duration) + 1
        extended_clips = video_clips * loops_needed
        final_video = concatenate_videoclips(extended_clips).subclip(0, vo_duration)
    else:
        final_video = concatenate_videoclips(video_clips).subclip(0, vo_duration)

    # Audio layering
    vo_audio = AudioFileClip(voiceover)
    audio_layers = [vo_audio]

    if music and Path(music).exists():
        music_audio = AudioFileClip(music).fx(volumex, 0.1)  # -20dB
        music_audio = music_audio.subclip(0, vo_duration)
        audio_layers.append(music_audio)

    # SFX at visual cues (assume timestamps from script)
    script = script_result.get("script", {})
    visual_cues = script.get("visual_cues", [10.0, 20.0])  # Placeholder timestamps
    for i, cue_time in enumerate(visual_cues[:len(sfx)]):
        if i < len(sfx) and Path(sfx[i]).exists():
            sfx_clip = AudioFileClip(sfx[i]).set_start(cue_time)
            audio_layers.append(sfx_clip)

    final_audio = CompositeAudioClip(audio_layers)

    # Captions
    script_text = _build_script_text(script)
    subtitles = _generate_subtitles(script_text, voiceover)
    text_clips = []
    for sub in subtitles:
        txt_clip = TextClip(
            sub['text'],
            fontsize=70,
            color=style_profile.get('caption_color', '#FFD700'),
            font=style_profile.get('font', 'Montserrat-Bold'),
            bg_color='black',
            size=(1080, 100)
        ).set_position('center').set_duration(sub['end'] - sub['start']).set_start(sub['start'])
        text_clips.append(txt_clip)

    # Combine video, audio, captions
    final_video = final_video.set_audio(final_audio)
    final_composite = CompositeVideoClip([final_video] + text_clips)

    # Apply polish: vignette and contrast (simplified)
    # For vignette, add a mask or effect
    # For now, just export

    final_composite.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')

    return output_path

def _build_script_text(script: dict) -> str:
    """Rebuild script text from parts."""
    meat = script.get("meat", {})
    parts = [
        script.get("hook", ""),
        script.get("stakes", ""),
        meat.get("tip1", "") if isinstance(meat, dict) else "",
        meat.get("tip2", "") if isinstance(meat, dict) else "",
        meat.get("tip3", "") if isinstance(meat, dict) else "",
        script.get("cta", ""),
    ]
    return " ".join(p.strip() for p in parts if p.strip())