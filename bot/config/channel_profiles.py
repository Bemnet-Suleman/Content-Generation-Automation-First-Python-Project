from __future__ import annotations

from typing import Any

CHANNEL_PROFILES: dict[str, dict[str, Any]] = {
    "gline": {
        "key": "gline",
        "display_name": "G-Line",
        "motto": "Where knowledge compounds faster than interest",
        "niche": "financial education",
        "tone": "motivational, practical, and grounded",
        "content_angle": "teach wealth habits, money discipline, and long-term thinking",
        "cta_style": "challenge the audience to take one simple action today",
        "visual_theme": "dark_cinematic",
        "font": "Montserrat-Bold",
        "caption_color": "#FFD700",
        "music_genre": "Lo-fi Suspense",
        "hashtags": ["#FinancialLiteracy", "#WealthHabits", "#MoneyMindset"],
    },
    "factum": {
        "key": "factum",
        "display_name": "Factum",
        "motto": "Facts, wisdom, and perspective",
        "niche": "philosophy and human truth",
        "tone": "calm, reflective, and intellectually sharp",
        "content_angle": "distill timeless ideas into short, memorable takeaways",
        "cta_style": "leave the audience with one perspective shift",
        "visual_theme": "minimal_cinematic",
        "font": "Montserrat-Bold",
        "caption_color": "#F4C542",
        "music_genre": "Ambient Reflection",
        "hashtags": ["#Philosophy", "#Wisdom", "#Mindset"],
    },
    "404circus": {
        "key": "404circus",
        "display_name": "404 Circus",
        "motto": "Bringing tomorrow's code into today's clarity",
        "niche": "tech, AI, and software clarity",
        "tone": "sharp, explanatory, and future-facing",
        "content_angle": "translate complex tech into simple, practical insight",
        "cta_style": "tease the next tool, trend, or shortcut",
        "visual_theme": "neon_synth",
        "font": "Montserrat-Bold",
        "caption_color": "#00E5FF",
        "music_genre": "Cyber Lo-fi",
        "hashtags": ["#Tech", "#AI", "#DeveloperTips"],
    },
}


def normalize_channel_key(value: str | None) -> str | None:
    if not value:
        return None
    raw = value.strip().lower().replace("-", "").replace(" ", "")
    if raw in {"gline", "finance", "financial"}:
        return "gline"
    if raw in {"factum", "philosophy", "wisdom", "facts"}:
        return "factum"
    if raw in {"404circus", "404circus", "404", "tech", "ai", "developer"}:
        return "404circus"
    return raw if raw in CHANNEL_PROFILES else None


def get_channel_profile(value: str | None = None) -> dict[str, Any]:
    key = normalize_channel_key(value) or "gline"
    profile = CHANNEL_PROFILES.get(key, CHANNEL_PROFILES["gline"]).copy()
    profile["key"] = key
    return profile


def build_channel_style_override(value: str | None = None) -> dict[str, str]:
    profile = get_channel_profile(value)
    return {
        "visual_theme": profile.get("visual_theme", "dark_cinematic"),
        "font": profile.get("font", "Montserrat-Bold"),
        "caption_color": profile.get("caption_color", "#FFD700"),
        "music_genre": profile.get("music_genre", "Lo-fi Suspense"),
    }


__all__ = ["CHANNEL_PROFILES", "get_channel_profile", "build_channel_style_override", "normalize_channel_key"]
