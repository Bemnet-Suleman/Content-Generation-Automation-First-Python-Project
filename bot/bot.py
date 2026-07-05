"""
Telegram Bot — Content Creation Agent

Commands:
  /start          — Welcome message + style profile summary
  /niche [niche]  — Set default niche for scripts
  /script [niche] — Module 1: generate trend-researched viral script
                    (uses cached niche if no arg provided)
  /assets         — Module 2: source visuals, voiceover, music & SFX
                    (uses the script from the last /script call in this chat)
  /assemble       — Module 3: assemble final vertical video and send it
"""

import os
import logging
from pathlib import Path

from dotenv import load_dotenv, find_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

load_dotenv(find_dotenv())

from bot.modules.module1_trend_research import run_trend_research
from bot.modules.module2_asset_sourcing import run_asset_sourcing, PexelsAuthError
from bot.modules.module3_assembly import run_assembly
from bot.config import style_profile

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory cache: chat_id → last script_result from Module 1
_script_cache: dict[int, dict] = {}

# Custom style override: chat_id → style dict
_custom_style_cache: dict[int, dict] = {}

# Custom niche override: chat_id → niche string
_niche_cache: dict[int, str] = {}


# ── /start ─────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    theme = style_profile["visual_theme"].upper().replace("_", " ")
    welcome = (
        f"🎬 <b>Content Creation Bot</b> — Active\n\n"
        f"Style Theme: <code>{theme}</code>\n"
        f"Font: <code>{style_profile['font']}</code>\n"
        f"Caption Color: <code>{style_profile['caption_color']}</code>\n"
        f"Music Genre: <code>{style_profile['music_genre']}</code>\n\n"
        f"<b>Available Commands:</b>\n"
        f"/script — Generate a viral script for the default niche\n"
        f"/script [niche] — Generate a script for your custom niche\n"
        f"  <i>Example: /script crypto investing</i>\n\n"
        f"/assets — Source visuals, voiceover, music &amp; SFX for the last script"
    )
    await update.message.reply_text(welcome, parse_mode="HTML")


# ── /script ────────────────────────────────────────────────────────────────────

async def cmd_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    niche_args = context.args
    niche = " ".join(niche_args).strip() if niche_args else _niche_cache.get(chat_id)
    if not niche:
        await update.message.reply_text(
            "⚠️ No niche provided.\n"
            "Use <b>/script [niche]</b> or set a niche with <b>/niche [niche]</b> first.",
            parse_mode="HTML",
        )
        return
    display_niche = niche

    await update.message.reply_text(
        f"⏳ Fetching live trends for <b>{display_niche}</b>...\n"
        f"<i>This may take 10–20 seconds.</i>",
        parse_mode="HTML",
    )

    try:
        result = run_trend_research(niche)
        # Cache for /assets
        _script_cache[update.effective_chat.id] = result
        await update.message.reply_text(result["telegram_message"], parse_mode="HTML")
    except EnvironmentError as e:
        await update.message.reply_text(
            f"⚠️ <b>Configuration Error</b>\n<code>{e}</code>\n\n"
            f"Add <code>GROQ_API_KEY</code> to your .env file or environment.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Module 1 error")
        await update.message.reply_text(
            f"❌ <b>Error in Module 1</b>\n<code>{str(e)}</code>",
            parse_mode="HTML",
        )


# ── /style ─────────────────────────────────────────────────────────────────────

async def cmd_style(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    chat_id = update.effective_chat.id

    if not args:
        current = _custom_style_cache.get(chat_id, {})
        if current:
            msg = "Current custom style:\n" + "\n".join(f"{k}: {v}" for k, v in current.items())
        else:
            msg = "No custom style set. Using AI-generated styles."
        await update.message.reply_text(f"<code>{msg}</code>\n\nUse /style theme font color music_genre\nOr /style reset", parse_mode="HTML")
        return

    if args[0].lower() == "reset":
        _custom_style_cache.pop(chat_id, None)
        await update.message.reply_text("✅ Custom style reset. Next scripts will use AI-generated styles.", parse_mode="HTML")
        return

    if len(args) < 4:
        await update.message.reply_text("Usage: /style theme font color music_genre\nExample: /style dark_cinematic Montserrat-Bold #FFD700 Lo-fi_Suspense", parse_mode="HTML")
        return

    theme, font, color, music = args[0], args[1], args[2], " ".join(args[3:])
    style = {
        "visual_theme": theme,
        "font": font,
        "caption_color": color,
        "music_genre": music,
    }
    _custom_style_cache[chat_id] = style
    await update.message.reply_text(f"✅ Custom style set for next scripts:\n<code>{style}</code>", parse_mode="HTML")


# ── /niche ─────────────────────────────────────────────────────────────────────

async def cmd_niche(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    chat_id = update.effective_chat.id

    if not args:
        current = _niche_cache.get(chat_id, "")
        if current:
            msg = f"Current niche: {current}"
        else:
            msg = "No niche set. Use /niche [niche] to set one."
        await update.message.reply_text(f"<code>{msg}</code>", parse_mode="HTML")
        return

    if args[0].lower() == "reset":
        _niche_cache.pop(chat_id, None)
        await update.message.reply_text("✅ Niche reset.", parse_mode="HTML")
        return

    niche = " ".join(args)
    _niche_cache[chat_id] = niche
    await update.message.reply_text(f"✅ Niche set to: <code>{niche}</code>\nUse /script to generate a script for this niche.", parse_mode="HTML")


# ── /assets ────────────────────────────────────────────────────────────────────

async def cmd_assets(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    script_result = _script_cache.get(chat_id)

    if not script_result:
        await update.message.reply_text(
            "⚠️ No script found for this chat.\n"
            "Run <b>/script [niche]</b> first to generate one.",
            parse_mode="HTML",
        )
        return

    niche = script_result.get("niche", "your niche")
    await update.message.reply_text(
        f"🔍 Sourcing assets for <b>{niche}</b>...\n"
        f"<i>This may take 30–60 seconds. Each file will arrive separately.</i>",
        parse_mode="HTML",
    )

    try:
        custom_style = _custom_style_cache.get(chat_id)
        assets = run_asset_sourcing(script_result, chat_id, custom_style)
    except PexelsAuthError:
        await update.message.reply_text(
            "❌ <b>Pexels API Key Invalid.</b> Check your .env or environment.\n"
            "Verify <code>PEXELS_API_KEY</code> is set correctly.",
            parse_mode="HTML",
        )
        return
    except Exception as e:
        logger.exception("Module 2 error")
        await update.message.reply_text(
            f"❌ <b>Error in Module 2</b>\n<code>{str(e)}</code>",
            parse_mode="HTML",
        )
        return

    sent = 0
    vo_engine = assets.get("voiceover_engine", "")

    # ── Video clips ──────────────────────────────────────────────────────────
    for i, path in enumerate(assets.get("visuals", []), 1):
        p = Path(path)
        if not p.exists():
            continue
        for attempt in range(2):  # Retry once
            try:
                with p.open("rb") as video_file:
                    await update.message.reply_video(
                        video_file,
                        caption=f"🎥 <b>Visual {i}</b> — {p.name}",
                        parse_mode="HTML",
                    )
                sent += 1
                break  # Success
            except Exception as e:
                logger.warning(f"Failed to send visual {path} attempt {attempt+1}: {e}")
                if attempt == 1:  # After second attempt, fail silently
                    pass

    # ── Voiceover ────────────────────────────────────────────────────────────
    vo = assets.get("voiceover")
    if vo and Path(vo).exists():
        for attempt in range(2):
            try:
                with Path(vo).open("rb") as audio_file:
                    await update.message.reply_audio(
                        audio_file,
                        caption=f"🎙 <b>Voiceover</b> — {vo_engine}",
                        parse_mode="HTML",
                    )
                sent += 1
                break
            except Exception as e:
                logger.warning(f"Failed to send voiceover attempt {attempt+1}: {e}")

    # ── Mixed audio (voice + ducked music) ───────────────────────────────────
    mixed = assets.get("music_mixed")
    if mixed and Path(mixed).exists():
        for attempt in range(2):
            try:
                with Path(mixed).open("rb") as audio_file:
                    await update.message.reply_audio(
                        audio_file,
                        caption="🎚 <b>Mixed audio</b> — voiceover + music ducked –20 dB",
                        parse_mode="HTML",
                    )
                sent += 1
                break
            except Exception as e:
                logger.warning(f"Failed to send mixed audio attempt {attempt+1}: {e}")
    else:
        # Fall back to sending raw music if mixing failed
        music = assets.get("music")
        if music and Path(music).exists():
            for attempt in range(2):
                try:
                    with Path(music).open("rb") as audio_file:
                        await update.message.reply_audio(
                            audio_file,
                            caption="🎵 <b>Background music</b> (raw — mixing unavailable)",
                            parse_mode="HTML",
                        )
                    sent += 1
                    break
                except Exception as e:
                    logger.warning(f"Failed to send music attempt {attempt+1}: {e}")

    # ── SFX ──────────────────────────────────────────────────────────────────
    for i, path in enumerate(assets.get("sfx", []), 1):
        p = Path(path)
        if not p.exists():
            continue
        for attempt in range(2):
            try:
                with p.open("rb") as audio_file:
                    await update.message.reply_audio(
                        audio_file,
                        caption=f"💨 <b>SFX {i}</b> — {p.name}",
                        parse_mode="HTML",
                    )
                sent += 1
                break
            except Exception as e:
                logger.warning(f"Failed to send SFX {path} attempt {attempt+1}: {e}")

    # ── Summary ──────────────────────────────────────────────────────────────
    failures = assets.get("failures", [])
    summary_lines = [f"✅ <b>Module 2 complete</b> — {sent} file(s) delivered"]
    if failures:
        summary_lines.append(f"\n⚠️ <b>{len(failures)} issue(s):</b>")
        for f in failures:
            summary_lines.append(f"  • {f}")
    if sent == 0:
        summary_lines.insert(0, "❌ <b>No files could be sent.</b>\n")
    summary_lines.append("\n<i>Review quality, then run /assemble when ready.</i>")
    await update.message.reply_text("\n".join(summary_lines), parse_mode="HTML")


# ── /assemble ─────────────────────────────────────────────────────────────────

async def cmd_assemble(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    script_result = _script_cache.get(chat_id)
    assets = {}  # In a real implementation, cache assets too, but for now assume run again

    if not script_result:
        await update.message.reply_text(
            "⚠️ No script found for this chat.\n"
            "Run <b>/script [niche]</b> first to generate one.",
            parse_mode="HTML",
        )
        return

    await update.message.reply_text(
        f"🔨 Assembling final video...\n"
        f"<i>This may take 2–5 minutes depending on clip lengths.</i>",
        parse_mode="HTML",
    )

    try:
        # Re-run asset sourcing if needed
        custom_style = _custom_style_cache.get(chat_id)
        assets = run_asset_sourcing(script_result, chat_id, custom_style)
        output_path = run_assembly(script_result, assets)
        
        with Path(output_path).open("rb") as video_file:
            await update.message.reply_video(
                video_file,
                caption="🎬 <b>Final Assembled Video</b>",
                parse_mode="HTML",
            )
    except Exception as e:
        logger.exception("Module 3 error")
        await update.message.reply_text(
            f"❌ <b>Error in Assembly</b>\n<code>{str(e)}</code>",
            parse_mode="HTML",
        )


# ── App ────────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN is not set. Add it to your .env file or environment."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).connect_timeout(20).read_timeout(120).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("script", cmd_script))
    app.add_handler(CommandHandler("assets", cmd_assets))
    app.add_handler(CommandHandler("style", cmd_style))
    app.add_handler(CommandHandler("niche", cmd_niche))
    app.add_handler(CommandHandler("assemble", cmd_assemble))

    logger.info("Bot is running. Waiting for commands...")
    app.run_polling()


if __name__ == "__main__":
    main()
