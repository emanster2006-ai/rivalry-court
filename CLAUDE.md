# Rivalry Court

Full current context for any coding agent is in `AGENTS.md` (live URLs, architecture, deployment gotchas, decisions, open items). Read it first.

Social game played alongside Fantasy Premier League: friends lock sealed win-probabilities for head-to-head duels, then resolve them from FPL scores. See `README.md` for the agreed scope and the first-release definition of done. See `PROGRESS.md` for what is built and what is next — read it first and update it when you finish work.

For the 2026-10-08 takeover snapshot, read `SESSION_HANDOFF.md` after `PROGRESS.md`.

## Layout
- `apps/api` — Python / FastAPI / SQLAlchemy / Alembic. Code in `rivalry/` (`api.py` routes, `rules.py` pure rules, `models.py`, `auth.py` JWT bearer, `mail.py` SMTP score notices). Tests in `tests/`.
- `apps/web` — React + TypeScript + Vite + Vitest (`src/App.tsx`, `DuelCard.tsx`, `client.ts`).
- `compose.yaml`, `scripts/` — local Postgres/services and setup.

## Commands
- `make setup` — one-time local setup; `make up` / `make down` — docker compose.
- `make test` — API (`apps/api/.venv/bin/python -m pytest`) and web (`npm test -- --run`).

## Rules to keep
- All timestamps are UTC; deadline checks go through `rules.before_deadline`.
- Submissions are append-only; only the latest counts. Probabilities are hidden from the opponent until the deadline.
- Missing submission or tied score voids a duel; voided duels never affect wins/losses/Brier.
- Resolution logic lives in `rules.resolution_state`; the 72-hour auto-confirm is computed from the score notice time.
- First release uses manually entered results. No FPL import, AI features or commit-reveal yet.
- Never commit `.env` or backups of it.
