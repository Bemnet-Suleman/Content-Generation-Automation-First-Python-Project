"""
Telegram Bot — Content Creation Agent
Module 1: Trend Research & Scripting

Commands:
  /start   — Welcome message + available commands
  /script  — Run Module 1 for the default niche
  /script [niche] — Run Module 1 for a custom niche
"""

import os
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from bot.modules.module1_trend_research import run_trend_research
from bot.config import style_profile

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


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
        f"  <i>Example: /script crypto investing</i>"
    )
    await update.message.reply_text(welcome, parse_mode="HTML")


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
        message = result["telegram_message"]
        await update.message.reply_text(message, parse_mode="HTML")
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


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN is not set. Add it as a Replit secret."
        )

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("script", cmd_script))

    logger.info("Bot is running. Waiting for commands...")
    app.run_polling()


if __name__ == "__main__":
    main()
