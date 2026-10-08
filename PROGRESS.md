# Progress

Last updated: 2026-10-08. Tests: API 18 passing with PostgreSQL (17 passing and one PostgreSQL check skipped without it), web 12 passing.

## Done (first release backend)
- [x] Monorepo scaffold, docker compose, setup script, Makefile
- [x] Data model + initial Alembic migration
- [x] Auth: bearer JWT validation (audience `authenticated`), users created on first sight
- [x] Groups: create, join by invite code (hashed), list members
- [x] Group admins can replace a lost invite code; the previous code stops working
- [x] Duels: create (admin sets deadline), list, read with per-viewer privacy
- [x] Sealed probability submissions (0–100, 5-pt steps, append-only, deadline enforced)
- [x] Void duel; auto-void on missing submission or tie
- [x] Score entry by admin with source link, email notice to both players
- [x] Confirm / dispute with reason, repeat-dispute block, corrected revisions
- [x] 72-hour auto-confirm via `rules.resolution_state`
- [x] First sign-in survives simultaneous profile/group requests; a temporary API error has a Retry action in the web app
- [x] Group history: wins, losses, sample size, mean Brier
- [x] Tests: rules, private access, deadline revisions, no-show, dispute/correction, auto-confirm, tie

## Frontend
- [x] Magic-link sign-in (GoTrue + Mailpit) — verified end to end 2026-10-08: link email, verify, `/me` and group create work with the token; no token gives 401
- [x] Create/join group, group switcher, invite code shown once
- [x] Create duel (admin), duel cards, history and Brier stats (`App.tsx`, `DuelCard.tsx`)
- [x] Build, typecheck, lint and tests pass; login page renders at http://localhost:5173
- [x] Two-user click-through 2026-10-08: sign in, create group, join by code, create duel, sealed submissions (opponent hidden until deadline), reveal at deadline, admin posts score + both emailed, confirm, resolved, correct Brier (0.1225 / 0.160)
- [x] Dispute -> corrected score -> confirm -> resolved, clicked in UI as the non-admin participant (captain duel)
- [ ] Not yet clicked in the UI: void duel, tie, 72-hour auto-confirm
- [x] Fixed: create-duel form no longer resets on refresh
- [x] Added error boundary (`ErrorBoundary.tsx`) so a bad payload shows a reload screen, not a blank page
- [x] Phone layout checked at 375px: no horizontal overflow, tap targets at least 44px (was 18px for sign-out, section headers, source links)
- [ ] Visual review on a real phone

## To verify / open items
- [x] Captain-duel scoring: the admin enters FPL's official captain-slot points; `rules.captain_slot_points` documents and tests vice promotion, chip multipliers, and empty slots. Automatic FPL scoring is outside this release.
- [x] Test gaps closed: deadline boundary (1s before / at deadline), outsiders and non-participants, void duel, repeat-dispute guard, exact 72h boundary (API: 12 tests)
- [x] CI workflow written (`.github/workflows/ci.yml`: API ruff+pytest, web tsc+lint+test+build). API steps verified in a clean venv; not yet run on GitHub (repo not pushed)
- [x] Production config guard: app refuses to start with APP_ENV=production and a placeholder JWT secret/DB password or non-https WEB_URL (tests added)
- [x] Deploy prep: production web image (`apps/web/Dockerfile.prod` + nginx, built and served locally OK) and `DEPLOY.md` checklist. Nothing deployed yet

## FPL data source (researched October 2026)
- The FPL web API (`fantasy.premierleague.com/api`) is undocumented and unofficial, so it can change without notice.
- premierleague.com's terms restrict reusing site material, building databases from downloaded material, and commercial use. They do not mention APIs or scraping by name and do not address FPL data separately.
- Decision: keep manual score entry with a link to the FPL source. Do not build automatic import until permission is confirmed with the Premier League.

## Later (per README)
- Fork the gameweek (captain swap first, then transfers)
- AI opposing counsel (confidence before/after)
- AI manager
- Automatic FPL data import, once a permitted data source is confirmed

## Dev notes
- API container now runs uvicorn with `--reload` (it served stale code before and crashed the UI). Recreate with `docker-compose up -d api` after compose changes.
- `docker compose up -d --build` now works here using the installed Compose CLI plugin; all five services started and the API health check passed.
- Vitest was updated to 4.1.11; `npm audit` now reports zero advisories.
- Test data in local DB: users claude-test@ and claude-test2@example.com, groups "Claude smoke test" and "UI test court".
