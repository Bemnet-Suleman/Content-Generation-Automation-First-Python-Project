"""
Module 1: Trend Research & Scripting
-------------------------------------
Uses pytrends to fetch real trending data, then feeds raw trend signals
into Groq (Llama 3.3 70B) to generate a viral-style video script.

4-Part Narrative Structure (min 180 spoken words):
  1. Pattern Interrupt  — Hook that stops the scroll
  2. The Stakes         — Why this matters right now
  3. The Meat           — 3 distinct, fact-backed tips or insights
  4. Retention CTA      — Keeps them subscribed and coming back

Every output reflects the centralized style_profile — tone, hook style,
CTA style, and formatting all come from that single dictionary so that
every module reads from the same cloth.

Entry points (called by the Telegram bot handler):
    run_trend_research(niche: str) -> dict
"""

import os
import json
import textwrap
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pytrends.request import TrendReq
from groq import Groq

from bot.config import style_profile


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
NICHE_DEFAULT = os.getenv("CONTENT_NICHE", "personal finance tips")
TRENDS_GEO = os.getenv("TRENDS_GEO", "US")
TRENDS_TIMEFRAME = os.getenv("TRENDS_TIMEFRAME", "now 7-d")


def _init_groq() -> Groq:
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it as a Replit secret."
        )
    return Groq(api_key=GROQ_API_KEY)


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
        You are an elite viral short-form video scriptwriter for {niche}.

        STYLE PROFILE (follow precisely):
        - Visual Theme : {visual_theme}
        - Music Genre  : {music_genre}
        - Script Tone  : {tone}
        - Hook Style   : {hook_style}
        - CTA Style    : {cta_style}
        - Caption Font : {style_profile["font"]} at {style_profile["caption_font_size"]}px
          (write short, punchy sentences that fit cleanly on screen)

        LIVE TREND DATA (analyze this before writing — do NOT guess):
        Top trending search queries for "{niche}" right now:
        {trends_block}

        Latest news headlines related to "{niche}":
        {news_block}

        TASK:
        Using the trend data above as your foundation, write a 90-second
        vertical video script (YouTube Shorts / TikTok) for viewers interested
        in {niche}.

        The script MUST follow this exact 4-part narrative structure.
        The TOTAL spoken word count across all four parts MUST be at least 180 words.

        ── PART 1: PATTERN INTERRUPT (0–8 sec) ──
        Hook style: {hook_style}
        - Shatter the viewer's autopilot with one line they did NOT expect.
        - Reference the #1 trending query if it fits naturally.
        - End on a cliffhanger that makes skipping feel like a mistake.
        - Target: 20–30 words.

        ── PART 2: THE STAKES (8–25 sec) ──
        - Immediately answer: "Why does this matter RIGHT NOW?"
        - Use a specific stat, date, or real-world consequence drawn from the trend data.
        - Build urgency without sounding clickbait.
        - Target: 35–45 words.

        ── PART 3: THE MEAT (25–75 sec) ──
        - Deliver exactly 3 distinct, numbered tips or facts — each grounded in the trend data.
        - Each tip must feel like something the viewer could act on today.
        - Separate each tip clearly (Tip 1 / Tip 2 / Tip 3).
        - Write in short, staccato sentences optimized for caption display.
        - Do NOT pad. Do NOT repeat. Every word earns its screen time.
        - Target: 90–110 words across all 3 tips.

        ── PART 4: RETENTION CTA (75–90 sec) ──
        CTA style: {cta_style}
        - Do NOT just say "like and subscribe." Give them a specific reason to come back.
        - Tease what they'll miss if they don't follow.
        - Feel urgent. Feel personal. Feel like a promise.
        - Target: 25–35 words.

        After the script, provide supporting metadata.

        Return ONLY a valid JSON object with these exact keys — no markdown, no extra text:
        {{
          "hook": "...",
          "stakes": "...",
          "meat": {{
            "tip1": "...",
            "tip2": "...",
            "tip3": "..."
          }},
          "cta": "...",
          "word_count": <integer — total spoken words across all 4 parts>,
          "keywords": ["...", "..."],
          "mood_tags": ["...", "..."],
          "thumbnail_text": "..."
        }}
    """).strip()

    return prompt


def generate_script(prompt: str) -> dict:
    """
    Send the data-grounded prompt to Groq (Llama 3.3 70B) and parse the JSON response.
    Returns a dict with keys:
        hook, stakes, meat (tip1/tip2/tip3), cta,
        word_count, keywords, mood_tags, thumbnail_text
    """
    client = _init_groq()

    chat_completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an elite viral short-form video scriptwriter. "
                    "Always respond with valid JSON only — no markdown fences, "
                    "no preamble, no explanation. Just the raw JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.8,
        max_tokens=2048,
    )

    raw = chat_completion.choices[0].message.content.strip()

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "hook": raw,
            "stakes": "",
            "meat": {"tip1": "", "tip2": "", "tip3": ""},
            "cta": "",
            "word_count": 0,
            "keywords": [],
            "mood_tags": [],
            "thumbnail_text": "",
            "raw_response": raw,
        }


def format_telegram_message(niche: str, script: dict, trending: list[dict]) -> str:
    """
    Build the Telegram message using the style_profile visual identity.
    Renders the 4-part narrative structure with clear section labels.
    """
    sep = "─" * 36
    label_color = style_profile["caption_color"]
    theme = style_profile["visual_theme"].upper().replace("_", " ")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    top_trends = "\n".join(
        [f"  {i+1}. {t['query']} ({t['value']})"
         for i, t in enumerate(trending[:5])]
    ) or "  (unavailable)"

    hook_text   = script.get("hook", "").strip()
    stakes_text = script.get("stakes", "").strip()
    cta_text    = script.get("cta", "").strip()
    thumbnail   = script.get("thumbnail_text", "")
    word_count  = script.get("word_count", "—")

    meat = script.get("meat", {})
    if isinstance(meat, dict):
        tip1 = meat.get("tip1", "").strip()
        tip2 = meat.get("tip2", "").strip()
        tip3 = meat.get("tip3", "").strip()
    else:
        tip1 = tip2 = tip3 = ""

    keywords = script.get("keywords", [])
    mood_tags = script.get("mood_tags", [])
    keywords_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
    mood_str     = ", ".join(mood_tags) if isinstance(mood_tags, list) else str(mood_tags)

    message = (
        f"🎬 *MODULE 1 — TREND RESEARCH & SCRIPT*\n"
        f"`{sep}`\n"
        f"*Theme:* {theme}\n"
        f"*Niche:* {niche}\n"
        f"*Generated:* {timestamp}\n\n"
        f"📊 *TOP TRENDING QUERIES*\n{top_trends}\n\n"
        f"`{sep}`\n"
        f"📝 *SCRIPT — 4\\-PART NARRATIVE*\n"
        f"_~{word_count} spoken words_\n\n"
        f"⚡ *PART 1 — PATTERN INTERRUPT* _(0–8 sec)_\n"
        f"{hook_text}\n\n"
        f"🔥 *PART 2 — THE STAKES* _(8–25 sec)_\n"
        f"{stakes_text}\n\n"
        f"🧠 *PART 3 — THE MEAT* _(25–75 sec)_\n"
        f"*Tip 1:* {tip1}\n\n"
        f"*Tip 2:* {tip2}\n\n"
        f"*Tip 3:* {tip3}\n\n"
        f"🎯 *PART 4 — RETENTION CTA* _(75–90 sec)_\n"
        f"{cta_text}\n\n"
        f"`{sep}`\n"
        f"🔑 *ASSET KEYWORDS:* {keywords_str}\n"
        f"🎵 *MOOD TAGS:* {mood_str}\n"
        f"🖼 *THUMBNAIL TEXT:* `{thumbnail}`\n\n"
        f"_Style: {label_color} captions · {style_profile['font']} · {style_profile['music_genre']}_\n"
        f"_Model: Llama 3.3 70B via Groq_"
    )

    return message


def run_trend_research(niche: str | None = None) -> dict:
    """
    Main entry point for Module 1.

    Steps:
      1. Fetch real trending queries via pytrends
      2. Scrape live news headlines for context
      3. Build a data-grounded prompt (no LLM guessing)
      4. Generate the script via Groq / Llama 3.3 70B
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

    print(f"[Module 1] Building grounded prompt and calling Groq (Llama 3.3 70B)...")
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
