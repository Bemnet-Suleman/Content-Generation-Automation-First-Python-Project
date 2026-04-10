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
        f"🎬 *Content Creation Bot* — Active\n\n"
        f"Style Theme: `{theme}`\n"
        f"Font: `{style_profile['font']}`\n"
        f"Caption Color: `{style_profile['caption_color']}`\n"
        f"Music Genre: `{style_profile['music_genre']}`\n\n"
        f"*Available Commands:*\n"
        f"/script — Generate a viral script for the default niche\n"
        f"/script \\[niche\\] — Generate a script for your custom niche\n"
        f"  _Example: /script crypto investing_"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def cmd_script(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    niche_args = context.args
    niche = " ".join(niche_args).strip() if niche_args else None

    display_niche = niche or os.getenv("CONTENT_NICHE", "personal finance tips")
    await update.message.reply_text(
        f"⏳ Fetching live trends for *{display_niche}*...\n"
        f"_This may take 10–20 seconds._",
        parse_mode="Markdown",
    )

    try:
        result = run_trend_research(niche)
        message = result["telegram_message"]
        await update.message.reply_text(message, parse_mode="Markdown")
    except EnvironmentError as e:
        await update.message.reply_text(
            f"⚠️ *Configuration Error*\n`{e}`\n\n"
            f"Add your `GROQ_API_KEY` as a Replit secret.",
            parse_mode="Markdown",
        )
    except Exception as e:
        logger.exception("Module 1 error")
        await update.message.reply_text(
            f"❌ *Error in Module 1*\n`{str(e)}`",
            parse_mode="Markdown",
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
