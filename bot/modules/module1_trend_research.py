"""
Module 1: Trend Research & Scripting
-------------------------------------
Uses pytrends to fetch real trending data, then feeds raw trend signals
into Google Gemini (free tier) to generate a viral-style video script.

Every output reflects the centralized style_profile — tone, hook style,
CTA style, and formatting all come from that single dictionary so that
every module reads from the same cloth.

Entry points (called by the Telegram bot handler):
    run_trend_research(niche: str) -> dict
"""

import os
import json
import time
import textwrap
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq

import google.generativeai as genai

from bot.config import style_profile


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
NICHE_DEFAULT = os.getenv("CONTENT_NICHE", "personal finance tips")
TRENDS_GEO = os.getenv("TRENDS_GEO", "US")
TRENDS_TIMEFRAME = os.getenv("TRENDS_TIMEFRAME", "now 7-d")


def _init_gemini():
    if not GEMINI_API_KEY:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Add it as a Replit secret."
        )
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel("gemini-1.5-flash")


def fetch_pytrends(niche: str) -> list[dict]:
    """
    Pull the top trending related queries for the niche from Google Trends.
    Returns a list of {"query": str, "value": int} dicts sorted by value desc.
    """
    pytrends = TrendReq(hl="en-US", tz=360)
    kw_list = [niche]
    pytrends.build_payload(kw_list, timeframe=TRENDS_TIMEFRAME, geo=TRENDS_GEO)

    related = pytrends.related_queries()
    trending_items = []

    for kw, data in related.items():
        if data and data.get("top") is not None:
            df = data["top"]
            for _, row in df.iterrows():
                trending_items.append(
                    {"query": str(row["query"]), "value": int(row["value"])}
                )

    trending_items.sort(key=lambda x: x["value"], reverse=True)
    return trending_items[:15]


def fetch_google_news_snippets(query: str) -> list[str]:
    """
    Scrape Google News for top headlines matching the query.
    Provides fresh context so the LLM doesn't have to guess trends.
    Returns up to 10 headline strings.
    """
    url = f"https://news.google.com/search?q={requests.utils.quote(query)}&hl=en-US&gl=US"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        headlines = []
        for tag in soup.find_all(["h3", "h4"], limit=20):
            text = tag.get_text(strip=True)
            if len(text) > 15:
                headlines.append(text)
        return headlines[:10]
    except Exception:
        return []


def build_script_prompt(
    niche: str,
    trending_queries: list[dict],
    news_headlines: list[str],
) -> str:
    """
    Construct the LLM prompt from real trend data.
    The prompt bakes in the style_profile so the script matches the theme.
    """
    tone = style_profile["script_tone"]
    hook_style = style_profile["script_hook_style"]
    cta_style = style_profile["script_cta_style"]
    music_genre = style_profile["music_genre"]
    visual_theme = style_profile["visual_theme"]

    trends_block = "\n".join(
        [f"  - {item['query']} (interest score: {item['value']})"
         for item in trending_queries]
    ) or "  (No trend data returned — use general knowledge)"

    news_block = "\n".join(
        [f"  - {h}" for h in news_headlines]
    ) or "  (No live headlines retrieved)"

    prompt = textwrap.dedent(f"""
        You are a viral short-form video scriptwriter for {niche}.

        STYLE PROFILE (follow precisely):
        - Visual Theme : {visual_theme}
        - Music Genre  : {music_genre}
        - Script Tone  : {tone}
        - Hook Style   : {hook_style}  (create an open loop that compels the viewer to keep watching)
        - CTA Style    : {cta_style}

        LIVE TREND DATA (analyze this before writing — do NOT guess):
        Top trending search queries for "{niche}" right now:
        {trends_block}

        Latest news headlines related to "{niche}":
        {news_block}

        TASK:
        Using the trend data above as your foundation, write a tight 60-second
        vertical video script (YouTube Shorts / TikTok) targeting viewers
        interested in {niche}.

        The script MUST have exactly these three sections:

        [HOOK] (0-5 sec)
        - Open loop hook in the {hook_style} style.
        - Reference the #1 trending query if it fits naturally.
        - Must make the viewer say "wait, what?" and keep watching.

        [BODY] (5-50 sec)
        - Deliver 3-5 punchy, fact-backed insights derived from the trend data.
        - Each insight should feel revelatory, not generic.
        - Write in short, staccato sentences — optimized for captions
          rendered in {style_profile["font"]} at {style_profile["caption_font_size"]}px.
        - Do NOT pad. Every word earns its screen time.

        [CTA] (50-60 sec)
        - One sharp call-to-action in the {cta_style} style.
        - Feel urgent. Feel personal.

        After the script, provide:
        KEYWORDS: comma-separated list of 8-10 keywords for asset sourcing
        MOOD_TAGS: comma-separated mood words for music & B-roll selection
        SUGGESTED_THUMBNAIL_TEXT: one punchy phrase (max 6 words) in CAPS

        Format your response as valid JSON with keys:
        "hook", "body", "cta", "keywords", "mood_tags", "thumbnail_text"
    """).strip()

    return prompt


def generate_script(prompt: str) -> dict:
    """
    Send the data-grounded prompt to Gemini and parse the JSON response.
    Returns a dict with keys: hook, body, cta, keywords, mood_tags, thumbnail_text
    """
    model = _init_gemini()
    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "hook": raw,
            "body": "",
            "cta": "",
            "keywords": [],
            "mood_tags": [],
            "thumbnail_text": "",
            "raw_response": raw,
        }


def format_telegram_message(niche: str, script: dict, trending: list[dict]) -> str:
    """
    Build the Telegram message using the style_profile visual identity.
    Uses the profile's caption color (shown as emoji stand-in in text),
    label conventions, and tone to present the script to the user.
    """
    sep = "─" * 36
    label_color = style_profile["caption_color"]
    theme = style_profile["visual_theme"].upper().replace("_", " ")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    top_trends = "\n".join(
        [f"  {i+1}. {t['query']} ({t['value']})"
         for i, t in enumerate(trending[:5])]
    ) or "  (unavailable)"

    body_text = script.get("body", "").strip()
    cta_text = script.get("cta", "").strip()
    hook_text = script.get("hook", "").strip()
    keywords = script.get("keywords", [])
    mood_tags = script.get("mood_tags", [])
    thumbnail = script.get("thumbnail_text", "")

    if isinstance(keywords, list):
        keywords_str = ", ".join(keywords)
    else:
        keywords_str = str(keywords)

    if isinstance(mood_tags, list):
        mood_str = ", ".join(mood_tags)
    else:
        mood_str = str(mood_tags)

    message = (
        f"🎬 *MODULE 1 — TREND RESEARCH & SCRIPT*\n"
        f"`{sep}`\n"
        f"*Theme:* {theme}\n"
        f"*Niche:* {niche}\n"
        f"*Generated:* {timestamp}\n\n"
        f"📊 *TOP TRENDING QUERIES*\n{top_trends}\n\n"
        f"`{sep}`\n"
        f"📝 *GENERATED SCRIPT*\n\n"
        f"🔴 *\\[HOOK\\]* _(0–5 sec)_\n{hook_text}\n\n"
        f"▶ *\\[BODY\\]* _(5–50 sec)_\n{body_text}\n\n"
        f"🎯 *\\[CTA\\]* _(50–60 sec)_\n{cta_text}\n\n"
        f"`{sep}`\n"
        f"🔑 *ASSET KEYWORDS:* {keywords_str}\n"
        f"🎵 *MOOD TAGS:* {mood_str}\n"
        f"🖼 *THUMBNAIL TEXT:* `{thumbnail}`\n\n"
        f"_Style: {label_color} captions · {style_profile['font']} · {style_profile['music_genre']}_"
    )

    return message


def run_trend_research(niche: str | None = None) -> dict:
    """
    Main entry point for Module 1.

    Steps:
      1. Fetch real trending queries via pytrends
      2. Scrape live news headlines for context
      3. Build a data-grounded prompt (no LLM guessing)
      4. Generate the script via Gemini
      5. Return a dict with script data + Telegram message

    Args:
        niche: Content niche (e.g. "personal finance", "crypto news").
               Falls back to CONTENT_NICHE env var or default.

    Returns:
        {
          "niche": str,
          "trending_queries": list[dict],
          "script": dict,          # hook / body / cta / keywords / mood_tags / thumbnail_text
          "telegram_message": str, # Ready to send via bot.send_message(..., parse_mode="Markdown")
          "style_profile": dict,   # Snapshot of the profile used
        }
    """
    niche = niche or NICHE_DEFAULT

    print(f"[Module 1] Fetching trends for niche: '{niche}'")
    trending = fetch_pytrends(niche)

    top_query = trending[0]["query"] if trending else niche
    print(f"[Module 1] Top trending query: '{top_query}' — fetching news headlines...")
    headlines = fetch_google_news_snippets(top_query)

    print(f"[Module 1] Building grounded prompt and calling Gemini...")
    prompt = build_script_prompt(niche, trending, headlines)
    script = generate_script(prompt)

    tg_message = format_telegram_message(niche, script, trending)

    return {
        "niche": niche,
        "trending_queries": trending,
        "script": script,
        "telegram_message": tg_message,
        "style_profile": style_profile,
    }
