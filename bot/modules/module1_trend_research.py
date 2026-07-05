"""
Module 1: Trend Research & Scripting
-------------------------------------
Trend source  : pytrends (Google Trends) → LLM Topic Brainstormer fallback
Script engine : Groq / Llama 3.3 70B

4-Part Narrative Structure (60-second target, min 150 spoken words):
  1. Pattern Interrupt  — Hook that stops the scroll           (15–20 words)
  2. The Stakes         — Why this matters right now           (25–30 words)
  3. The Meat           — 3 sub-points × 2-3 sentences each   (80–95 words)
  4. Retention CTA      — Keeps them subscribed                (20–25 words)

Pacing cues embedded in script text (visually distinct from spoken words):
  <<PAUSE>>  — 1-second beat for the voiceover engine
  <<STRESS>> — stress the next word/phrase

Validation: if spoken word count < 135, the LLM is asked to expand
before the result is returned to the user.

Every output reflects the centralized style_profile.

Entry points (called by the Telegram bot handler):
    run_trend_research(niche: str) -> dict
"""

import os
import re
import json
import textwrap
from datetime import datetime

import requests
from bs4 import BeautifulSoup
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
            "GROQ_API_KEY is not set. Add it to your .env file or environment."
        )
    return Groq(api_key=GROQ_API_KEY)


def _fetch_pytrends(niche: str) -> list[dict]:
    """
    Pytrends is disabled due to CPU compatibility issues.
    Always raises ValueError to force LLM fallback.
    """
    raise ValueError("Pytrends disabled — using LLM brainstormer instead")

    related = pt.related_queries()
    trending_items = []

    for kw, data in related.items():
        if data and data.get("top") is not None:
            df = data["top"]
            for _, row in df.iterrows():
                trending_items.append({
                    "query": str(row["query"]),
                    "value": int(row["value"]),
                    "source": "google_trends",
                })

    if not trending_items:
        raise ValueError("pytrends returned no results")

    trending_items.sort(key=lambda x: x["value"], reverse=True)
    return trending_items[:15]


def _brainstorm_trends_llm(niche: str, client: Groq) -> list[dict]:
    """
    LLM fallback: generate plausible trending sub-topics for the niche
    using the style_profile as context. Called only when Google Trends fails.

    Returns list of {"query": str, "value": int, "source": "llm_brainstormed"}.
    Values are synthetic interest scores (100 → lowest) for ranking purposes.
    """
    tone = style_profile["script_tone"]
    visual_theme = style_profile["visual_theme"]

    brainstorm_prompt = textwrap.dedent(f"""
        You are a content strategist specializing in viral {niche} content.

        Style context:
        - Visual theme : {visual_theme}
        - Script tone  : {tone}

        Task: Generate 10 specific, realistic sub-topics that are currently
        trending or highly searched within the "{niche}" niche.

        Rules:
        - Each sub-topic must be a realistic search query (2-6 words).
        - Order them from highest to lowest estimated search interest.
        - Do NOT use generic phrases like "tips" or "how to" alone.
        - Base them on realistic audience curiosity in the niche.

        Return ONLY a valid JSON array of objects, no extra text:
        [
          {{"query": "...", "value": 100}},
          {{"query": "...", "value": 90}},
          ...
        ]
    """).strip()

    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": "Respond with valid JSON only."},
            {"role": "user", "content": brainstorm_prompt},
        ],
        temperature=0.7,
        max_tokens=512,
    )
    raw = completion.choices[0].message.content.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

    items = json.loads(raw)
    for item in items:
        item["source"] = "llm_brainstormed"
    return items[:15]


def fetch_trends(niche: str, groq_client: Groq) -> tuple[list[dict], str]:
    """
    Two-layer trend fetcher:
      Layer 1 — pytrends-modern (live Google Trends data)
      Layer 2 — LLM Topic Brainstormer (style-profile-aware fallback)

    Returns:
        (trending_items, source_label)
        source_label is "📡 Live Google Trends" or "🧠 AI Brainstormed Topics"
    """
    try:
        items = _fetch_pytrends(niche)
        print(f"[Module 1] Trends source: Google Trends ({len(items)} queries)")
        return items, "📡 Live Google Trends"
    except Exception as e:
        print(f"[Module 1] Google Trends failed ({e}). Falling back to LLM brainstormer.")
        try:
            items = _brainstorm_trends_llm(niche, groq_client)
            print(f"[Module 1] LLM brainstormed {len(items)} topics")
            return items, "🧠 AI Brainstormed Topics"
        except Exception as e2:
            print(f"[Module 1] LLM brainstormer also failed ({e2}). Returning empty list.")
            return [], "⚠️ No Trend Data"


def fetch_google_news_snippets(query: str) -> list[str]:
    """
    Scrape Google News for top headlines matching the query.
    Provides fresh context so the LLM doesn't have to guess trends.
    Returns up to 10 headline strings.
    """
    url = (
        f"https://news.google.com/search?q={requests.utils.quote(query)}&hl=en-US&gl=US"
    )
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

    news_block = (
        "\n".join([f"  - {h}" for h in news_headlines])
        or "  (No live headlines retrieved)"
    )

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

        LATEST NEWS HEADLINES for "{niche}" (use these for facts and context only):
        {news_block}

        TASK:
        Write a 60-second vertical video script (YouTube Shorts / TikTok)
        for viewers interested in {niche}.

        ══ STRICT WORD COUNT RULE ══
        The TOTAL spoken word count (ignoring pacing cues) MUST be at least 150 words.
        Standard pacing is 2.5 words/second × 60 seconds = 150 words minimum.
        Do NOT stop writing early. Expand each section with full storytelling depth.

        ══ PACING CUE RULE ══
        You MUST embed these exact markers inside the spoken text where natural.
        They are NOT spoken aloud — they are director cues for the voiceover engine.
        They use double angle-brackets so they are visually unmistakable from dialogue.

          <<PAUSE>>  — insert a 1-second silent beat (after opener, before reveals,
                       between tips). Placed between sentences, never mid-sentence.
          <<STRESS>> — placed immediately before a single key word or short phrase
                       the speaker should emphasize (e.g. "the <<STRESS>> worst thing").

        IMPORTANT: These markers must look NOTHING like normal prose. Always use
        exactly <<PAUSE>> or <<STRESS>> — no brackets, no quotes, no variations.

        ══ 4-PART NARRATIVE STRUCTURE ══

        ── PART 1: PATTERN INTERRUPT (0–8 sec) ── Target: 15–20 spoken words
        Hook style: {hook_style}
        - Open with one unexpected, scroll-stopping line.
        - Reference the #1 trending query if it fits naturally.
        - End on a hard cliffhanger. Make skipping feel like a mistake.
        - Place <<PAUSE>> after the opening line.
        - Example: "Most people think saving 10% is enough. <<PAUSE>> It's not even close."

        ── PART 2: THE STAKES (8–20 sec) ── Target: 25–30 spoken words
        - Answer immediately: "Why does this matter RIGHT NOW?"
        - Drop one specific stat, date, or real-world consequence from the trend data.
        - Use <<STRESS>> directly before the key stat or number.
        - Build urgency without clickbait. Be precise.

        ── PART 3: THE MEAT (20–52 sec) ── Target: 80–95 spoken words
        Write exactly 3 sub-points. Each sub-point MUST have 2–3 full sentences of depth.
        Do NOT write one-liners. Explain, illustrate, give context.

        Sub-point 1 (tip1):
        - Lead with a bold statement grounded in the trend data.
        - Follow with 1–2 sentences that explain WHY or HOW.
        - End with <<PAUSE>> before moving to sub-point 2.

        Sub-point 2 (tip2):
        - Introduce a contrasting or complementary angle.
        - Back it with a specific detail or consequence.
        - Use <<STRESS>> on the single most important word.
        - End with <<PAUSE>>.

        Sub-point 3 (tip3):
        - Deliver the most actionable, surprising insight last.
        - Make it feel like something they can do today.
        - Use <<STRESS>> before the core action word.

        ── PART 4: RETENTION CTA (52–60 sec) ── Target: 20–25 spoken words
        CTA style: {cta_style}
        - Do NOT say just "like and subscribe."
        - Tease one specific thing they will miss if they don't follow.
        - Feel personal. Feel urgent. Feel like a kept promise.

        ── VISUAL CUES ──
        Provide 2 timestamps (in seconds) where SFX should be placed for emphasis.
        For example, at key moments in the script.

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
          "thumbnail_text": "...",
          "visual_cues": [10.0, 20.0]
        }}
    """).strip()

    return prompt


# ── Validation helpers ────────────────────────────────────────────────────────

PACING_CUE_PATTERN = ["<<PAUSE>>", "<<STRESS>>"]


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


def verify_script_length(
    script_text: str, target_seconds: int = 60
) -> tuple[bool, str]:
    """
    Validate that the spoken script fills the target video duration.

    Pacing cues ('[Pause 1s]','[Emphasis]') are stripped before counting
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
        raw = (
            "\n".join(lines[1:-1])
            if lines[-1].strip() == "```"
            else "\n".join(lines[1:])
        )
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
            "visual_cues": [10.0, 20.0],
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
            - Embed <<PAUSE>> and <<STRESS>> markers throughout.
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


def _esc_html(text: str) -> str:
    """
    Prepare LLM-generated text for Telegram HTML mode:
      1. Replace pacing cues with plain emoji (before HTML escaping).
      2. Escape & < > so nothing in the prose can open an HTML tag.
    """
    text = text.replace("<<PAUSE>>", " ⏸ ")
    text = text.replace("<<STRESS>>", "🔊")
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text


def format_telegram_message(
    niche: str,
    script: dict,
    trending: list[dict],
    trends_source: str = "📡 Live Google Trends",
) -> str:
    """
    Build the Telegram message in HTML parse mode.
    All LLM-generated content passes through _esc_html() so that
    special characters never break the parser, and pacing cues are
    rendered as inline badges rather than raw marker strings.
    """
    sep = "─" * 36
    label_color = style_profile["caption_color"]
    theme = style_profile["visual_theme"].upper().replace("_", " ")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    top_trends = (
        "\n".join(
            [f"  {i + 1}. {t['query']} ({t['value']})"
             for i, t in enumerate(trending[:5])]
        )
        or "  (unavailable)"
    )

    hook_text   = _esc_html(script.get("hook", "").strip())
    stakes_text = _esc_html(script.get("stakes", "").strip())
    cta_text    = _esc_html(script.get("cta", "").strip())
    thumbnail   = _esc_html(script.get("thumbnail_text", ""))
    word_count  = script.get("actual_word_count", "—")
    length_ok   = script.get("length_ok", True)
    length_badge = "✅ on target" if length_ok else "⚠️ short"

    meat = script.get("meat", {})
    if isinstance(meat, dict):
        meat_body = " ".join(
            _esc_html(meat.get(k, "").strip())
            for k in ("tip1", "tip2", "tip3")
            if meat.get(k, "").strip()
        )
    else:
        meat_body = ""

    keywords = script.get("keywords", [])
    mood_tags = script.get("mood_tags", [])
    keywords_str = _esc_html(", ".join(keywords) if isinstance(keywords, list) else str(keywords))
    mood_str     = _esc_html(", ".join(mood_tags) if isinstance(mood_tags, list) else str(mood_tags))

    message = (
        f"🎬 <b>MODULE 1 — TREND RESEARCH &amp; SCRIPT</b>\n"
        f"<code>{sep}</code>\n"
        f"<b>Theme:</b> {theme}\n"
        f"<b>Niche:</b> {niche}\n"
        f"<b>Generated:</b> {timestamp}\n\n"
        f"📊 <b>TOP TRENDING QUERIES</b> — <i>{trends_source}</i>\n{top_trends}\n\n"
        f"<code>{sep}</code>\n"
        f"📝 <b>SCRIPT — 4-PART NARRATIVE</b>\n"
        f"<i>{word_count} spoken words — {length_badge}</i>\n\n"
        f"⚡ <b>PART 1 — PATTERN INTERRUPT</b> <i>(0–8 sec)</i>\n"
        f"{hook_text}\n\n"
        f"🔥 <b>PART 2 — THE STAKES</b> <i>(8–20 sec)</i>\n"
        f"{stakes_text}\n\n"
        f"🧠 <b>PART 3 — THE MEAT</b> <i>(20–52 sec)</i>\n"
        f"{meat_body}\n\n"
        f"🎯 <b>PART 4 — RETENTION CTA</b> <i>(52–60 sec)</i>\n"
        f"{cta_text}\n\n"
        f"<code>{sep}</code>\n"
        f"🔑 <b>ASSET KEYWORDS:</b> {keywords_str}\n"
        f"🎵 <b>MOOD TAGS:</b> {mood_str}\n"
        f"🖼 <b>THUMBNAIL TEXT:</b> <code>{thumbnail}</code>\n\n"
        f"<i>Style: {label_color} captions · {style_profile['font']} · {style_profile['music_genre']}</i>\n"
        f"<i>Model: Llama 3.3 70B via Groq</i>"
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

    client = _init_groq()

    print(f"[Module 1] Fetching trends for niche: '{niche}'")
    trending, trends_source = fetch_trends(niche, client)

    top_query = trending[0]["query"] if trending else niche
    print(f"[Module 1] Top query: '{top_query}' — fetching news headlines...")
    headlines = fetch_google_news_snippets(top_query)

    print(f"[Module 1] Building prompt and calling Groq (Llama 3.3 70B)...")
    prompt = build_script_prompt(niche, trending, headlines)
    script = generate_script(prompt)

    tg_message = format_telegram_message(niche, script, trending, trends_source)

    return {
        "niche": niche,
        "trending_queries": trending,
        "script": script,
        "telegram_message": tg_message,
        "style_profile": style_profile,
    }
