# Progress

Last updated: 2026-10-08. Tests: API 7 passing, web 2 passing.

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
- [ ] Not yet clicked in the UI: dispute, corrected score, void duel, captain duel, tie, 72-hour auto-confirm
- [ ] Create-duel form resets its fields after any refresh (members list effect in `DuelCard.tsx`)
- [ ] UI white-screens if the API payload lacks `responses` (happened with a stale API container); consider an error boundary
- [ ] Mobile-first polish and empty/error states

## To verify / open items
- [ ] Captain-duel scoring: `rules.captain_slot_points` exists; confirm it is used for captain duels, with tests for vice promotion, chips, and empty slots
- [ ] Test gaps vs README list: exact deadline boundaries over HTTP, late submissions, correction notice windows
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
