# Kook — Savage Hinglish Telegram Bot

Kook is a Telegram group companion with configurable personalities, contextual AI replies, SQLite conversation memory, welcome messages, moderation, warnings, chat locks, group utilities, and Tic-Tac-Toe. **AI image generation is intentionally excluded.**

## Run locally
1. Create a Telegram bot with @BotFather.
2. Copy `.env.example` to `.env` and set `BOT_TOKEN` and your numeric `OWNER_ID`.
3. Add at least one provider key for AI replies. Supported providers (automatic fallback order): OpenAI, Anthropic Claude, Gemini, DeepSeek, GLM, xAI Grok, Groq, and OpenRouter. Set the matching `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `DEEPSEEK_API_KEY`, `GLM_API_KEY`, `XAI_API_KEY`, `GROQ_API_KEY`, or `OPENROUTER_API_KEY`. Each provider is optional; failed providers are skipped and the next configured provider is tried. Model names can be overridden with the corresponding `*_MODEL` environment variable.
4. Install Python 3.11+: `pip install -r requirements.txt`
5. Start: `python main.py`

## Deploy to Render
Use the repository's `render.yaml` as a Background Worker blueprint, then add secrets in Render Environment settings. Never commit `.env` or API keys. Confirm current Render free-plan and persistent-disk eligibility before deployment because plan rules can change.

## Commands
`/start`, `/help`, `/personality`, `/welcome`, `/setwelcome`, `/ban`, `/kick`, `/mute`, `/unmute`, `/warn`, `/warns`, `/purge`, `/pin`, `/unpin`, `/id`, `/groupinfo`, `/admins`, `/lock`, `/unlock`, `/game`, `/panel`, `/health`.

**Permissions:** give the bot administrator rights for moderation commands. `/panel` and `/health` are owner-only based on `OWNER_ID`. This initial implementation does not yet expose a full per-command permission editor.

**Privacy and Telegram limits:** group AI replies require mentioning the bot or replying to it. For general group message visibility, adjust Telegram BotFather privacy settings if appropriate. Whisper-style messages are not end-to-end encrypted. Voice-chat participation and automatic voice-chat join events are not implemented in this initial repo version.


### Render start-command troubleshooting
The bot must run as a **Background Worker**, not a web service. The repository blueprint uses `python -u main.py` and the root `Procfile` declares `worker: python -u main.py`. If Render logs still show `gunicorn your_application.wsgi`, the existing Render service has a dashboard-level Start Command override or was created as a Web Service. Update that service's Start Command to `python -u main.py`, or create/sync a Background Worker from this repository's `render.yaml`; a repository commit cannot override a manually configured dashboard command by itself.
