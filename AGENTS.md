# Rivalry Court — instructions and context for coding agents (Codex, Claude Code, etc.)

Read this file first, then `PROGRESS.md` (checklist and verification), then `SESSION_HANDOFF.md` (history). `README.md` is the product scope and source of truth for rules. `DEPLOY.md` covers hosting. `CLAUDE.md` has repo conventions.

## What this is
A social game played alongside Fantasy Premier League. Two friends in a private group each privately lock a probability (0–100 in steps of 5) that *they* beat the other in a gameweek (total points after penalties, or captain-slot points). Predictions reveal at the FPL deadline and become immutable. The group admin then enters the official scores with a source link; participants confirm or dispute; no response for 72 hours auto-confirms. Resolved duels feed a per-member Brier score `(p - outcome)^2`, lower is better. FPL data is entered manually on purpose (see "Decisions").

The owner (Emmanuel) is a third-year software-engineering student building this for fun and for internship-portfolio value. Prefers that the agent implements changes rather than asking them to type code, plain-language explanations of product behavior, and a clear split between what was *verified* and what is only *planned*.

## Current status (2026-10-09)
- **Live and in use.** Emmanuel and a friend ran a real two-user duel on production on 2026-10-08/09: sign-in email → join by invite code → duel created → predictions locked.
- Web: https://rivalry-court-web.onrender.com (Render static site, free)
- API: https://rivalry-court-api.onrender.com (Render Docker web service, free; sleeps after ~15 idle minutes, ~50 s cold start)
- Auth + database: Supabase project `gfgbawwuwacaduneaxaa` (free). Email: Brevo SMTP (free). Repo: private, `emanster2006-ai/rivalry-court`, branch `main`.
- Tests: API 25 (23 pass + 2 Postgres-only that need `TEST_DATABASE_URL`), web 14. Lint, typecheck, build clean. CI (GitHub Actions) green with a Postgres service.
- **Not yet verified in production:** the "score needs your review" email sent *by the API* through Brevo on port 2525 from Render (sign-in emails sent by Supabase are verified), disputes/corrections/void/tie/72-hour on the live site, a real FPL gameweek with friends, a real phone.

## Architecture
```
Browser (React/Vite static)  ──magic link──▶  Supabase Auth (GoTrue)  ── emails via Brevo SMTP
        │                                              │ signs ES256 JWT (public key at /auth/v1/.well-known/jwks.json)
        └── Bearer JWT ──▶ FastAPI (Render) ──SQL──▶ Supabase Postgres (session pooler, port 5432)
                               └── score notices via Brevo SMTP (port 2525 + STARTTLS)
```
- `apps/api/rivalry/`: `api.py` (routes), `rules.py` (pure rules: deadline, Brier, resolution state machine), `auth.py` (JWT verify: JWKS/ES256 when `AUTH_JWKS_URL` set, else HS256 shared secret for local GoTrue), `models.py`, `schemas.py`, `mail.py`, `config.py` (refuses weak/placeholder values when `APP_ENV=production`).
- `apps/api/alembic/versions/`: `0001_initial` (schema + immutability triggers on event tables), `0002_usernames`, `0003_row_level_security` (RLS on every public table so Supabase's public REST API exposes nothing; the API connects as table owner).
- `apps/web/src/`: `App.tsx`, `DuelCard.tsx`, `client.ts` (Supabase auth-js client, sends publishable key), `ErrorBoundary.tsx`.
- Event tables (submissions, score revisions, notices, confirmations, void events) are append-only and protected by DB triggers. The latest submission/revision wins.
- Local stack: `docker compose up` (or `docker-compose`): Postgres, GoTrue, Mailpit (fake inbox at :8025), API (:8001, `--reload`), web (:5173). Local sign-in links appear in Mailpit.

## Commands
```sh
make setup                      # first-time local setup (.env with random secrets) + start stack
make test                       # API + web tests
cd apps/api && .venv/bin/python -m pytest -q && .venv/bin/ruff check .
cd apps/web && npm test && npm run lint && npm run build
# Postgres-only tests: TEST_DATABASE_URL=postgresql+psycopg://USER:PASS@localhost:5432/DB pytest
```

## Deployment facts and gotchas (learned the hard way)
- Render deploys from `render.yaml` (Blueprint, syncs from `main`). Secrets (`DATABASE_URL`, `SMTP_USER`, `SMTP_PASSWORD`) are `sync: false`, entered in the Render dashboard — never in git.
- **Do not use `dockerCommand: sh -c "..."`** on Render (exit 127). The image starts via `apps/api/start.sh` (migrate, then uvicorn on `$PORT`). Clear any leftover Docker Command in Render settings if it reappears.
- `DATABASE_URL` must use the Supabase **session pooler** (port 5432), start with `postgresql+psycopg://`, and URL-encode special characters in the password.
- Render's free plan blocks outbound SMTP ports 25/465/587, hence `SMTP_PORT=2525` with `SMTP_STARTTLS=true` (Brevo). Without STARTTLS Brevo rejects login.
- Supabase signs tokens with public keys; the shared-secret path is only for local GoTrue. Supabase's built-in email sender only mails team members (2/hour), so custom SMTP (Brevo) must stay enabled in Supabase → Authentication → Emails.
- Free Render Postgres is deleted after ~44 days — do not use it; the database lives in Supabase (free; confirm its inactivity-pause policy).
- The sender is Gmail via Brevo's shared domain; first emails to new recipients often land in spam. A custom domain fixes this (costs money).
- Docker here may expose `docker-compose` (standalone) and/or `docker compose` plugin; both have been used.
- The Claude Code auto-mode classifier blocked an agent from creating the GitHub remote and pushing once; the owner pushes manually (`git push`). `gh` is logged in as `emanster2006-ai` with the `workflow` scope.

## Decisions already made (do not silently reverse)
- First release uses **manual score entry** with a source link. No FPL scraping/import: the FPL API is undocumented/unofficial and premierleague.com terms restrict reuse and database-building; get permission first.
- Usernames are unique and **can be set only once**; group APIs never expose emails.
- No salted commit–reveal protocol; private access control + append-only records are enough for a friend group.
- Scope order: finish and exercise the first release with real friends → (later) fork-the-gameweek, AI opposing counsel, AI manager. Do not expand scope without asking.

## Open items / suggested next steps
1. Finish the live two-user run: reveal at deadline → admin posts score → confirm. **Check the score-notice email arrives** (Brevo → Transactional → Logs if not). If it fails, suspect port 2525/STARTTLS or an unverified Brevo sender (`emanster2006@gmail.com`).
2. Investigate the one-off "Database error saving new user" shown once on sign-in (check Supabase → Logs → Auth); account creation still succeeded.
3. UI click-through still missing for void, tie, and 72-hour auto-confirm; real-phone visual check; consider custom sending domain.
4. Consider a keep-alive/cold-start notice for the sleeping free API, a reminder email near deadlines, and ES256 key-fetch failure returning 503 instead of 401 (`auth.py`).
5. Update `PROGRESS.md` and this file when you finish work.

## Working rules for agents
- Never commit `.env`, API keys, DB passwords or SMTP keys; never print them in chat. Local `.env` is git-ignored.
- Do not sign up for services, spend money, or send email/messages without asking. Do not push to `main` unless the owner asks.
- Prefer small commits with clear messages; run API + web tests and lint before committing.
- Report plainly what was verified versus assumed.



## Portfolio review — 2026-10-18 UTC

Added demo/ownership overview, production release checklist, and a regression test for SMTP failure rollback and successful retry. Production email and two-user flows have not been exercised in this review. Source visibility is unchanged. Changes are prepared on a review branch to avoid triggering the main-branch deployment.

## Portfolio evidence update — 2026-10-18 UTC

Added a reproducible synthetic UI capture script, a public case study/media link, engineering tradeoffs, and a three-gameweek pilot protocol. Capture uses the real React UI with substituted auth/API responses and blocks external network requests; it does not verify production behavior or real user adoption. No invitations, emails, or live group records were created.

Local checks: API 24 passed, two PostgreSQL-only tests skipped; frontend 14 passed; API/web lint and frontend production build passed. Browser capture reported no page errors and no horizontal overflow at 390px. A real-phone check and multi-gameweek pilot are still pending.
