# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.
Also contains a Python Telegram Bot for automated YouTube/TikTok content creation.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)
- **Python**: 3.11 (Telegram bot, content automation)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally
- `python main.py` — run the Telegram bot (requires secrets below)

## Telegram Bot — Content Creation Agent

### Architecture

```
bot/
├── config/
│   ├── style_profile.py      # ← Single source of truth for ALL visual/style decisions
│   └── __init__.py
├── modules/
│   ├── module1_trend_research.py  # Trend Research & Scripting
│   └── __init__.py
└── bot.py                    # Telegram bot handlers
main.py                       # Entry point
```

### style_profile (Central Design Dictionary)

Every module reads from `bot/config/style_profile.py`. Keys include:
- `visual_theme`, `font`, `caption_color`, `music_genre`, `color_filter`
- `script_tone`, `script_hook_style`, `script_cta_style`
- Caption, video, watermark, transition, and output settings

### Module 1 — Trend Research & Scripting

- **Tools**: pytrends, BeautifulSoup, Google Gemini (free tier via google-generativeai)
- **Flow**: Fetch live Google Trends data → scrape news headlines → build data-grounded prompt → generate viral script (Hook/Body/CTA) → send formatted Telegram message
- **Bot commands**: `/start`, `/script`, `/script [niche]`

### Required Secrets

| Secret | Description |
|--------|-------------|
| `TELEGRAM_BOT_TOKEN` | From @BotFather on Telegram |
| `GEMINI_API_KEY` | From Google AI Studio (free tier) |

### Optional Env Vars

| Variable | Default | Description |
|----------|---------|-------------|
| `CONTENT_NICHE` | `personal finance tips` | Default niche |
| `TRENDS_GEO` | `US` | Google Trends geography |
| `TRENDS_TIMEFRAME` | `now 7-d` | Trends timeframe |

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.
