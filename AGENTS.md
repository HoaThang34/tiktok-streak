# AGENTS.md

TikTok Streak Manager: a local Python HTTP dashboard + Selenium/Chrome automation tool for sending TikTok streak messages across multiple accounts.

## Run & verify
- Install deps: `pip install -r requirements.txt` (selenium>=4.20.0, python-dotenv>=1.0.0). System Python 3.8+ or the bundled `python_embed/` (Windows, via `run.bat`).
- Start: `python app.py` (or double-click `run.bat`). Requires Google Chrome installed.
- Server binds the first free port from 5000 upward, serves `web/index.html`, and auto-opens Chrome.
- No test/lint/typecheck commands or CI exist; verify changes by running `python app.py` and exercising the UI/API. Treat `python app.py` as the smoke check.

## Architecture
- `app.py`: `ThreadingHTTPServer` + `DashboardHandler`; routes 17 GET/POST endpoints; runs work in a single background thread via `run_background_task` (`CURRENT_TASK`, `STOP_EVENT`, `TASK_THREAD`).
- `utils.py`: account/cookie/config/friends persistence and all Selenium automation (`init_browser`, `login_with_cookies`, `scan_friends`, `send_messages_to_selected`).
- `web/index.html`: entire frontend (single file, vanilla HTML/CSS/JS; Shadcn Light Mode). No bundler.
- Data: `accounts.json` (ignored) plus per-account `accounts/<id>/` with `cookies.json`, `config.json`, `friends.json`, `friends.csv`. Legacy root-level files are migrated by `ensure_data_migration()`.
- Multi-account execution is strictly sequential: open Chrome → send → `browser.quit()` → 3s pause → next account. No concurrent sessions.
- `task_send_messages_sequential` checks each account's sent-vs-selected friends progress before running and reruns only accounts that are still incomplete; it keeps retrying (respecting `STOP_EVENT`) until every selected account has sent == selected.

## Critical constraints
- Backend uses Python standard library only; frontend is a single static file. Do not add Flask/FastAPI/Django/React/Vue/Tailwind/CDNs unless explicitly requested.
- Selenium loops must check `STOP_EVENT.is_set()` / `should_stop()` and `browser.quit()` must be in `finally`.
- `save_accounts()` in `utils.py` filters computed fields (`has_cookies`, `cookies_count`, `friends_count`, `selected_friends_count`). New account fields must be added there and given defaults in `load_accounts()` (and in create/reset paths), or they are dropped on save.
- Keep account data isolated by `accounts/<id>/`; never share cookies/config/friends across accounts.
- Sensitive data (`cookies.json`, `accounts.json`, `accounts/`, `.env`, etc.) is gitignored; do not commit real credentials.

## Detailed docs (`.agents/`)
- `.agents/README.md` — navigation and fast task lookup.
- `.agents/FEATURE_MODIFICATION_GUIDE.md` — where to change things (account/config/message/task/Selenium/UI).
- `.agents/ARCHITECTURE_AND_STORAGE.md` — schemas and threading model.
- `.agents/API_REFERENCE.md` — all endpoints and payloads.
- `.agents/rules/tiktok_streak_rules.md` — repo coding rules.