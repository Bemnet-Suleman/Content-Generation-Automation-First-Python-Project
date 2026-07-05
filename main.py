"""
Entry point for the Telegram Content Creation Bot.
Run: python main.py
"""

from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
assets_root = Path(__file__).resolve().parent / "assets"
assets_root.mkdir(parents=True, exist_ok=True)

from bot.bot import main

if __name__ == "__main__":
    main()
