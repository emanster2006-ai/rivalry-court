# Rivalry Court handoff — 2026-10-08

This is a snapshot for the next coding session. `README.md` is the product scope and engineering source of truth; `PROGRESS.md` tracks verification and remaining work. `CLAUDE.md` has the repo conventions. No application change is requested by this handoff itself.

## What we finished

- Built the first playable release: email magic-link sign-in, private invite-code groups, two fixed FPL duel types, sealed probability submissions, score entry and correction, participant confirmation or dispute, 72-hour auto-confirmation, history, and Brier stats. The frontend is React/TypeScript; the API is FastAPI/PostgreSQL with Alembic. See `README.md` for exact rules.
- Fixed the initial signed-in `Failed to fetch` problem and verified a real two-user local flow: group creation and join, duel creation, sealed predictions and reveal, score email, confirmation and resolution. Also clicked through a dispute and corrected captain-duel score. See `PROGRESS.md` for unclicked cases.
- Added recovery for a lost group invite code, preserved create-duel form values on refresh, initialized each duel slider from the saved prediction, and improved error recovery and phone-sized layout.
- Added editable, globally unique usernames. A signed-in member sets one under **Your name in court**. Usernames are 3–24 letters, numbers, or underscores; the API normalizes to lowercase and returns 409 when taken. Duel cards, member selectors, score responses, and history display usernames. Existing accounts use a temporary `Player-xxxxxxxx` label until they choose one. Group member and history responses no longer expose email addresses; the owner's `/me` response retains email for their own account. Emails still power login and score notices. Migration: `0002_usernames`.
- Updated `README.md` and `PROGRESS.md` and committed the username work as `fe34378` and `4240e01`. The earlier work is in the preceding commits; inspect `git log --oneline` for details.

## Local app and email

The five local services are PostgreSQL, GoTrue auth, API, Vite web, and Mailpit. At the last check, all were running, API was healthy, and Alembic was at `0002_usernames (head)`.

| Address | Purpose |
| --- | --- |
| `http://localhost:5173` | App |
| `http://localhost:8025` | Mailpit inbox for magic links and score notices |
| `http://localhost:8001/docs` | API docs |

Mailpit catches local outgoing mail because `.env` sets `SMTP_HOST=mailpit`; typing a Gmail address into sign-in does **not** send to Gmail. Real delivery requires deploying/configuring a real SMTP provider and verified sender, as described in `DEPLOY.md`. Localhost only works on the user's computer unless the app is hosted. Do not commit `.env` or print its secrets.

## Resume and verify

1. Check `git status --short` and read `README.md`, `PROGRESS.md`, and `CLAUDE.md` before editing. At handoff, the worktree was clean after the username commits.
2. If the local stack is stopped, run `docker compose up -d --build` (or `make setup` for a fresh checkout). Docker uses Colima on this machine. Refresh the app browser tab after changes.
3. Run API tests and lint with `cd apps/api && .venv/bin/pytest -q && .venv/bin/ruff check .`. Run web tests, lint, and build with `cd apps/web && npm test && npm run lint && npm run build`.
4. The last full verification was **19 API tests passing with PostgreSQL**, **14 web tests passing**, backend and frontend lint passing, and the production web build passing. The API health endpoint returned `{"status":"ok"}`. Without a PostgreSQL test URL, one schema test skips.

## Remaining items and next decisions

- The username flow has API and web tests, and the updated containers were started; a fresh manual click-through of setting names in both browser sessions was not done. Refresh the app, set a username in each account, and check the `who vs who` display if the user wants a UI check.
- Void, tie, and 72-hour auto-confirmation have automated coverage but have not been clicked through in the browser. A real-phone visual review is still open.
- CI exists but has not run on GitHub because the repo has not been pushed. Nothing is deployed. The user asked whether friends need to be on their laptop: for now, yes, because all URLs are localhost. Deployment is the separate next step; see `DEPLOY.md`.
- FPL score and deadline entry remain manual. AI opposing counsel and gameweek forks are roadmap items, not part of this release. Do not silently expand scope or scrape/import FPL data; `README.md` and `PROGRESS.md` record the data-source decision.

The user is a third-year software-engineering student building this with an assistant for internship portfolio value and enjoyment. They prefer the assistant to implement changes rather than asking them to type code. Explain product behavior plainly, and distinguish what was verified from what is only planned.
