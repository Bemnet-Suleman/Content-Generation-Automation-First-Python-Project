"""
Telegram Bot — Content Creation Agent

Commands:
  /start          — Welcome message + style profile summary
  /script [niche] — Module 1: generate trend-researched viral script
  /assets         — Module 2: source visuals, voiceover, music & SFX
                    (uses the script from the last /script call in this chat)
"""

import os
import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from bot.modules.module1_trend_research import run_trend_research
from bot.modules.module2_asset_sourcing import run_asset_sourcing, PexelsAuthError
from bot.config import style_profile

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# In-memory cache: chat_id → last script_result from Module 1
_script_cache: dict[int, dict] = {}


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
    niche_args = context.args
    niche = " ".join(niche_args).strip() if niche_args else None
    display_niche = niche or os.getenv("CONTENT_NICHE", "personal finance tips")

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
            f"Add your <code>GROQ_API_KEY</code> as a Replit secret.",
            parse_mode="HTML",
        )
    except Exception as e:
        logger.exception("Module 1 error")
        await update.message.reply_text(
            f"❌ <b>Error in Module 1</b>\n<code>{str(e)}</code>",
            parse_mode="HTML",
        )


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
        assets = run_asset_sourcing(script_result)
    except PexelsAuthError:
        await update.message.reply_text(
            "❌ <b>Pexels API Key Invalid.</b> Check your Secrets.\n"
            "Go to the Secrets tab and verify <code>PEXELS_API_KEY</code> is correct.",
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
        try:
            await update.message.reply_video(
                p.open("rb"),
                caption=f"🎥 <b>Visual {i}</b> — {p.name}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send visual {path}: {e}")
            await update.message.reply_text(
                f"⚠️ Visual {i} (<code>{p.name}</code>) could not be sent — file may exceed Telegram's 50 MB limit.",
                parse_mode="HTML",
            )

    # ── Voiceover ────────────────────────────────────────────────────────────
    vo = assets.get("voiceover")
    if vo and Path(vo).exists():
        try:
            await update.message.reply_audio(
                Path(vo).open("rb"),
                caption=f"🎙 <b>Voiceover</b> — {vo_engine}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send voiceover: {e}")

    # ── Mixed audio (voice + ducked music) ───────────────────────────────────
    mixed = assets.get("music_mixed")
    if mixed and Path(mixed).exists():
        try:
            await update.message.reply_audio(
                Path(mixed).open("rb"),
                caption="🎚 <b>Mixed audio</b> — voiceover + music ducked –20 dB",
                parse_mode="HTML",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send mixed audio: {e}")
    else:
        # Fall back to sending raw music if mixing failed
        music = assets.get("music")
        if music and Path(music).exists():
            try:
                await update.message.reply_audio(
                    Path(music).open("rb"),
                    caption="🎵 <b>Background music</b> (raw — mixing unavailable)",
                    parse_mode="HTML",
                )
                sent += 1
            except Exception as e:
                logger.warning(f"Failed to send music: {e}")

    # ── SFX ──────────────────────────────────────────────────────────────────
    for i, path in enumerate(assets.get("sfx", []), 1):
        p = Path(path)
        if not p.exists():
            continue
        try:
            await update.message.reply_audio(
                p.open("rb"),
                caption=f"💨 <b>SFX {i}</b> — {p.name}",
                parse_mode="HTML",
            )
            sent += 1
        except Exception as e:
            logger.warning(f"Failed to send SFX {path}: {e}")

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


# ── App ────────────────────────────────────────────────────────────────────────

def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN is not set. Add it as a Replit secret."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("script", cmd_script))
    app.add_handler(CommandHandler("assets", cmd_assets))

    logger.info("Bot is running. Waiting for commands...")
    app.run_polling()


if __name__ == "__main__":
    main()
