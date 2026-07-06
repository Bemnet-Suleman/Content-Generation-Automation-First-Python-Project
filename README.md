# Style Profile Module

A Telegram bot for generating short-form content workflows from trend research to final video assembly. The project is organized into three modules:

- Module 1: research and draft a trend-based script
- Module 2: source visuals, voiceover, music, and sound effects
- Module 3: assemble the final vertical video with captions and export it

## Features

- `/start` to view the active style profile
- `/script [niche]` to generate a script from live trend research
- `/assets` to gather supporting media for the last generated script
- `/assemble` to build and send the finished video
- Custom style and niche overrides per chat
- `/channel` to switch between the three brand pipelines: G-Line, Factum, and 404 Circus

## Three-channel workflow

The backend is now aligned around three content brands so the Telegram workflow can cover most of the creator's production work:

1. G-Line — financial content with a motivational, money-mindset angle.
2. Factum — philosophy/facts/wisdom content with a reflective, high-signal tone.
3. 404 Circus — tech/AI content with a clear, future-facing explanation style.

When a channel is selected, the bot uses that brand context in Module 1 when drafting scripts, and it carries matching visual/audio defaults into Module 2 and Module 3. This gives the workflow a brand-aware backbone so the creator only needs to review and polish the final output instead of starting from scratch every time.

## Project structure

- `main.py` — application entry point
- `bot/bot.py` — Telegram command handlers
- `bot/modules/` — core workflow modules
- `bot/config/style_profile.py` — default visual and output profile
- `assets/` — generated output and media workspace
- `.env.example` — environment variable template

## Requirements

This project depends on:

- Python 3.10+
- `python-dotenv`
- `python-telegram-bot`
- `requests`
- `beautifulsoup4`
- `groq`
- `moviepy`
- `pydub`
- `pysubs2`

You will also need `ffmpeg` available on your system for video processing.

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install the Python dependencies.
4. Copy `.env.example` to `.env` and fill in your credentials.
5. Start the bot with:

```bash
python main.py
```

## Environment variables

Create a `.env` file using the provided `.env.example` as a template. At minimum, configure:

- `TELEGRAM_BOT_TOKEN`
- `GROQ_API_KEY`
- `PEXELS_API_KEY`
- `PIXABAY_API_KEY`
- `FREESOUND_API_KEY`
- `HF_TOKEN`

## Publishing to GitHub

Before pushing to GitHub:

- keep secrets out of version control
- commit `.env.example` but do not commit `.env`
- avoid committing generated media files or local cache folders

## Notes

The bot writes generated assets into the local `assets/` folder during execution. These files are generally intended to stay local unless you want to track them in a separate artifacts repository.
