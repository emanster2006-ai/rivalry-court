# Progress

Last updated: 2026-10-08. Tests: API 12 passing, web 3 passing.

## Done (first release backend)
- [x] Monorepo scaffold, docker compose, setup script, Makefile
- [x] Data model + initial Alembic migration
- [x] Auth: bearer JWT validation (audience `authenticated`), users created on first sight
- [x] Groups: create, join by invite code (hashed), list members
- [x] Duels: create (admin sets deadline), list, read with per-viewer privacy
- [x] Sealed probability submissions (0–100, 5-pt steps, append-only, deadline enforced)
- [x] Void duel; auto-void on missing submission or tie
- [x] Score entry by admin with source link, email notice to both players
- [x] Confirm / dispute with reason, repeat-dispute block, corrected revisions
- [x] 72-hour auto-confirm via `rules.resolution_state`
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
- [ ] Captain-duel scoring: `rules.captain_slot_points` exists; confirm it is used for captain duels, with tests for vice promotion, chips, and empty slots
- [x] Test gaps closed: deadline boundary (1s before / at deadline), outsiders and non-participants, void duel, repeat-dispute guard, exact 72h boundary (API: 12 tests)
- [ ] CI (not set up)
- [ ] Deploy plan

## Later (per README)
- Fork the gameweek (captain swap first, then transfers)
- AI opposing counsel (confidence before/after)
- AI manager
- Automatic FPL data import, once a permitted data source is confirmed

## Dev notes
- API container now runs uvicorn with `--reload` (it served stale code before and crashed the UI). Recreate with `docker-compose up -d api` after compose changes.
- Docker here has no `docker compose` plugin; use `docker-compose`.
- Test data in local DB: users claude-test@ and claude-test2@example.com, groups "Claude smoke test" and "UI test court".
