"""
Module 1: Trend Research & Scripting
-------------------------------------
Uses pytrends to fetch real trending data, then feeds raw trend signals
into Groq (Llama 3.3 70B) to generate a viral-style video script.

4-Part Narrative Structure (60-second target, min 150 spoken words):
  1. Pattern Interrupt  — Hook that stops the scroll           (15–20 words)
  2. The Stakes         — Why this matters right now           (25–30 words)
  3. The Meat           — 3 sub-points × 2-3 sentences each   (80–95 words)
  4. Retention CTA      — Keeps them subscribed                (20–25 words)

Pacing cues ([Pause 1s], [Emphasis]) are embedded in the script text
to guide the voiceover engine and fill time naturally.

Validation: if the generated script is under 140 words, the LLM is
asked to rewrite it with more depth before returning to the user.

Every output reflects the centralized style_profile.

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
          (short punchy sentences that fit cleanly on one caption line)

        LIVE TREND DATA (analyze this before writing — do NOT guess):
        Top trending search queries for "{niche}" right now:
        {trends_block}

        Latest news headlines related to "{niche}":
        {news_block}

        TASK:
        Write a 60-second vertical video script (YouTube Shorts / TikTok)
        for viewers interested in {niche}.

        ══ STRICT WORD COUNT RULE ══
        The TOTAL spoken word count (ignoring pacing cues) MUST be at least 150 words.
        Standard pacing is 2.5 words/second × 60 seconds = 150 words minimum.
        Do NOT stop writing early. Expand each section with full storytelling depth.

        ══ PACING CUE RULE ══
        Embed these markers directly in the text where natural:
          [Pause 1s]  — after the hook opener, between major thoughts, before reveals
          [Emphasis]  — immediately before a key word or phrase the speaker should stress
        These markers are for the voiceover engine and do NOT count toward word totals.

        ══ 4-PART NARRATIVE STRUCTURE ══

        ── PART 1: PATTERN INTERRUPT (0–8 sec) ── Target: 15–20 spoken words
        Hook style: {hook_style}
        - Open with one unexpected, scroll-stopping line.
        - Reference the #1 trending query if it fits naturally.
        - End on a hard cliffhanger. Make skipping feel like a mistake.
        - Use [Pause 1s] after the opening line.
        - Example structure: "Most people think X. [Pause 1s] They're wrong."

        ── PART 2: THE STAKES (8–20 sec) ── Target: 25–30 spoken words
        - Answer immediately: "Why does this matter RIGHT NOW?"
        - Drop one specific stat, date, or real-world consequence from the trend data.
        - Use [Emphasis] before the key stat or number.
        - Build urgency without clickbait. Be precise.

        ── PART 3: THE MEAT (20–52 sec) ── Target: 80–95 spoken words
        Write exactly 3 sub-points. Each sub-point MUST have 2–3 full sentences of depth.
        Do NOT write one-liners. Explain, illustrate, give context.

        Sub-point 1 (tip1):
        - Lead with a bold statement grounded in the trend data.
        - Follow with 1–2 sentences that explain WHY or HOW.
        - End with [Pause 1s] before moving to sub-point 2.

        Sub-point 2 (tip2):
        - Introduce a contrasting or complementary angle.
        - Back it with a specific detail or consequence.
        - Use [Emphasis] on the most important word.
        - End with [Pause 1s].

        Sub-point 3 (tip3):
        - Deliver the most actionable, surprising insight last.
        - Make it feel like something they can do today.
        - Use [Emphasis] before the core action word.

        ── PART 4: RETENTION CTA (52–60 sec) ── Target: 20–25 spoken words
        CTA style: {cta_style}
        - Do NOT say just "like and subscribe."
        - Tease one specific thing they will miss if they don't follow.
        - Feel personal. Feel urgent. Feel like a kept promise.

        ══ OUTPUT FORMAT ══
        Return ONLY a valid JSON object — no markdown fences, no extra text:
        {{
          "hook": "...",
          "stakes": "...",
          "meat": {{
            "tip1": "...",
            "tip2": "...",
            "tip3": "..."
          }},
          "cta": "...",
          "keywords": ["...", "..."],
          "mood_tags": ["...", "..."],
          "thumbnail_text": "..."
        }}
    """).strip()

    return prompt


# ── Validation helpers ────────────────────────────────────────────────────────

PACING_CUE_PATTERN = ["[Pause 1s]", "[Emphasis]"]


def _extract_spoken_text(script: dict) -> str:
    """Concatenate all spoken parts into one string for word-count validation."""
    meat = script.get("meat", {})
    parts = [
        script.get("hook", ""),
        script.get("stakes", ""),
        meat.get("tip1", "") if isinstance(meat, dict) else "",
        meat.get("tip2", "") if isinstance(meat, dict) else "",
        meat.get("tip3", "") if isinstance(meat, dict) else "",
        script.get("cta", ""),
    ]
    return " ".join(parts)


def verify_script_length(script_text: str, target_seconds: int = 60) -> tuple[bool, str]:
    """
    Validate that the spoken script fills the target video duration.

    Pacing cues ([Pause 1s], [Emphasis]) are stripped before counting
    so they don't inflate the word total.

    Standard voiceover pacing: ~2.5 words/second.
    Pass threshold: 90% of target duration.

    Returns:
        (True,  "Length is perfect.")                        — passes
        (False, "Too short (N words). Need more detail.")    — fails
    """
    clean = script_text
    for cue in PACING_CUE_PATTERN:
        clean = clean.replace(cue, "")

    word_count = len(clean.split())
    estimated_seconds = word_count / 2.5

    if estimated_seconds < (target_seconds * 0.9):
        return False, f"Too short ({word_count} words). Need more detail."
    return True, "Length is perfect."


# ── Groq call + retry logic ───────────────────────────────────────────────────

def _call_groq(client: Groq, messages: list[dict]) -> str:
    """Raw Groq API call. Returns the stripped response text."""
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.8,
        max_tokens=2048,
    )
    raw = completion.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
    return raw


def _parse_json(raw: str) -> dict:
    """Parse JSON response, returning a safe fallback dict on failure."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "hook": raw,
            "stakes": "",
            "meat": {"tip1": "", "tip2": "", "tip3": ""},
            "cta": "",
            "keywords": [],
            "mood_tags": [],
            "thumbnail_text": "",
            "raw_response": raw,
        }


def generate_script(prompt: str, target_seconds: int = 60) -> dict:
    """
    Send the data-grounded prompt to Groq (Llama 3.3 70B).

    Validation loop:
      1. Generate the script.
      2. Count actual spoken words (pacing cues stripped).
      3. If under the 90%-of-target threshold, send one retry with an
         explicit expansion instruction appended to the conversation.
      4. Return whichever version passes (or the retry result regardless).

    Returns a dict with keys:
        hook, stakes, meat (tip1/tip2/tip3), cta,
        actual_word_count, length_ok,
        keywords, mood_tags, thumbnail_text
    """
    client = _init_groq()
    system_msg = {
        "role": "system",
        "content": (
            "You are an elite viral short-form video scriptwriter. "
            "Always respond with valid JSON only — no markdown fences, "
            "no preamble, no explanation. Just the raw JSON object."
        ),
    }

    # ── Attempt 1 ────────────────────────────────────────────────────────────
    messages = [system_msg, {"role": "user", "content": prompt}]
    raw = _call_groq(client, messages)
    script = _parse_json(raw)

    spoken = _extract_spoken_text(script)
    length_ok, verdict = verify_script_length(spoken, target_seconds)
    print(f"[Module 1] Script validation attempt 1: {verdict}")

    # ── Retry if too short ────────────────────────────────────────────────────
    if not length_ok:
        expansion_instruction = textwrap.dedent(f"""
            The script you just wrote is {verdict}

            Rewrite it now with significantly more depth and storytelling.
            Rules for the rewrite:
            - PART 1 (hook): keep it sharp but add one extra sentence of intrigue.
            - PART 2 (stakes): add a second specific stat or real-world consequence.
            - PART 3 (meat): each of tip1, tip2, tip3 MUST have 2–3 full sentences.
              Explain the WHY and the HOW — do not just state a fact and move on.
            - PART 4 (cta): expand to include a teaser of what's coming next.
            - Embed [Pause 1s] and [Emphasis] markers throughout.
            - Total spoken words (excluding pacing cues) MUST reach at least 150.

            Return ONLY the updated JSON object in the same format.
        """).strip()

        messages = [
            system_msg,
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": expansion_instruction},
        ]
        raw = _call_groq(client, messages)
        script = _parse_json(raw)

        spoken = _extract_spoken_text(script)
        length_ok, verdict = verify_script_length(spoken, target_seconds)
        print(f"[Module 1] Script validation attempt 2: {verdict}")

    # Attach our own verified word count — don't trust the LLM's self-report
    clean_spoken = spoken
    for cue in PACING_CUE_PATTERN:
        clean_spoken = clean_spoken.replace(cue, "")
    script["actual_word_count"] = len(clean_spoken.split())
    script["length_ok"] = length_ok

    return script


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
    word_count  = script.get("actual_word_count", "—")
    length_ok   = script.get("length_ok", True)
    length_badge = "✅ on target" if length_ok else "⚠️ short"

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
        f"_{word_count} spoken words — {length_badge}_\n\n"
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
