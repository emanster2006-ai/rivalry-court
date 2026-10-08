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

## Frontend (basic)
- [x] `App`, `DuelCard`, API client, 2 tests
- [ ] Sign-in flow (magic link) in the UI
- [ ] Create/join group screens
- [ ] Create duel, submit probability, enter/confirm/dispute scores
- [ ] History and Brier view
- [ ] Mobile-first polish

## To verify / open items
- [ ] Magic-link sign-in: backend only validates a JWT from an external auth service (`scripts/init-auth-db.sql`); confirm that service is wired up in compose and works end to end
- [ ] Captain-duel scoring: `rules.captain_slot_points` exists; confirm it is used for captain duels, with tests for vice promotion, chips, and empty slots
- [ ] Test gaps vs README list: exact deadline boundaries over HTTP, late submissions, correction notice windows
- [ ] CI (not set up)
- [ ] Deploy plan

## Later (per README)
- Fork the gameweek (captain swap first, then transfers)
- AI opposing counsel (confidence before/after)
- AI manager
- Automatic FPL data import, once a permitted data source is confirmed
