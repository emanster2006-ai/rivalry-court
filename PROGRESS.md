# Progress

Last updated: 2026-10-08. Tests: API 19 passing with PostgreSQL (18 passing and one PostgreSQL check skipped without it), web 14 passing.

## Done (first release backend)
- [x] Monorepo scaffold, docker compose, setup script, Makefile
- [x] Data model + initial Alembic migration
- [x] Auth: bearer JWT validation (audience `authenticated`), users created on first sight
- [x] Groups: create, join by invite code (hashed), list members
- [x] Group admins can replace a lost invite code; the previous code stops working
- [x] Unique usernames (chosen once, not editable) replace emails in group member lists, duels, and history; email stays private for login and score notices
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
- [x] Saved probability now sets the slider value; a refresh with unchanged data keeps an unsaved edit
- [x] Added error boundary (`ErrorBoundary.tsx`) so a bad payload shows a reload screen, not a blank page
- [x] Phone layout checked at 375px: no horizontal overflow, tap targets at least 44px (was 18px for sign-out, section headers, source links)
- [ ] Visual review on a real phone

## To verify / open items
- [x] Captain-duel scoring: the admin enters FPL's official captain-slot points; `rules.captain_slot_points` documents and tests vice promotion, chip multipliers, and empty slots. Automatic FPL scoring is outside this release.
- [x] Test gaps closed: deadline boundary (1s before / at deadline), outsiders and non-participants, void duel, repeat-dispute guard, exact 72h boundary (API: 12 tests)
- [x] CI workflow written (`.github/workflows/ci.yml`: API ruff+pytest, web tsc+lint+test+build). **Passed on GitHub 2026-10-08** (both jobs green) at https://github.com/emanster2006-ai/rivalry-court (private)
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
- Test data in local DB: two test users and two test groups ("smoke test" and "UI test court").

## Live deployment (2026-10-08)
- Web: https://rivalry-court-web.onrender.com (Render static, free)
- API: https://rivalry-court-api.onrender.com (Render Docker, free; sleeps after 15 idle minutes, ~50s to wake)
- Database + sign-in: Supabase project `gfgbawwuwacaduneaxaa` (free); email via Brevo SMTP
- Verified from outside: API health 200, no-token and forged-token requests get 401, CORS allows only the web origin, website bundle points at the right API/Supabase/key. API reached Live only after migrations (incl. row-level security) ran on Supabase.
- Verified 2026-10-08/09: real magic-link sign-in on the live site via Brevo (first email landed in spam), a friend joined by invite code, a duel was created and predictions locked.
- Not yet verified on production: the score-notice email sent by the API (Render → Brevo port 2525 + STARTTLS), dispute/correction/void/tie/72-hour flows, a real phone. A one-off `Database error saving new user` appeared once at sign-in (account still created); check Supabase Auth logs.
- Render fix history: `dockerCommand: sh -c "..."` failed with exit 127; replaced by `apps/api/start.sh`.



## Portfolio review — 2026-10-18 UTC

Added demo/ownership overview, production release checklist, and a regression test for SMTP failure rollback and successful retry. Production email and two-user flows have not been exercised in this review. Source visibility is unchanged. Changes are prepared on a review branch to avoid triggering the main-branch deployment.

Validation in this review: API 24 passed, 2 PostgreSQL checks skipped locally; frontend 14 passed; API/web lint and frontend build passed. GitHub CI also passed both API (Python 3.13 with PostgreSQL) and web jobs for the review branch.

## Ownership credit — 2026-10-28

Added a discreet bottom-right footer in the static HTML: `© 2026 Emmanuel Ezedinma Onwuka · Rivalry Court`, plus author and description metadata. The credit is public before sign-in and readable without JavaScript; private game data and access controls are unchanged. Google indexing remains unverified and is not guaranteed. Static HTML parsing verified the exact credit and author metadata. Full local suites could not run because the executor network proxy was unreachable; check the ownership-credit PR's GitHub CI for API/web tests, lint, and build results. Live deployment verification is pending.

## Weekly duel flow — 2026-11-26

- The dashboard highlights the first action due, starting with an unsubmitted prediction nearest its deadline. Saved predictions show their edit window.
- Duels show the latest official score and source, and resolved duels show the winner and a copyable link. Score-notice links open the indicated duel in its group.
- Admins can start a rematch with the same players and claim type, then supply a new gameweek and official deadline.
- Local verification passed for 19 web tests, frontend lint and production build, and API lint. Of the 26 API tests, 24 passed and the two PostgreSQL-only tests were skipped locally. Chrome with test data exercised prediction, result links, and rematch at 1,200px and 375px wide.
- A separate local run with PostgreSQL, GoTrue, and Mailpit exercised real email delivery to two test addresses. At 375px, a signed-out participant followed the score email, signed in by magic link, and landed in the linked duel in a non-default group. The participant disputed, the admin corrected the score, and the participant confirmed the revised result.
- On 2026-11-26, the production API returned a healthy status. A mailbox review found two score notices addressed to different recipients with the same production duel link on 2026-10-09. A fresh live delivery check, the hosted signed-out redirect, and a two-player phone pilot are still open.
