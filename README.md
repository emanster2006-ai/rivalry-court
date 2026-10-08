# Rivalry Court

Rivalry Court is a social game played alongside Fantasy Premier League (FPL). Friends lock predictions before an FPL deadline, challenge each other's reasoning, and revisit the results after each gameweek. FPL remains the source of truth for teams and points; this project focuses on the decisions and rivalries around them.

## Agreed scope

1. **Sealed rivalry duels — first playable release.** Two friends compare either final gameweek scores after transfer penalties or points awarded to their captain slots. Each privately submits only a probability that their own side wins; the duel type and participants determine the sides. Predictions reveal at the FPL deadline, and resolved predictions contribute to a Brier-score history.
2. **Fork the gameweek.** Start with a captain swap where both players appeared and no chip, vice-captain, or auto-substitution complicates scoring. Then add transfers and the remaining FPL rules with explicit tests. A fork compares outcomes after the gameweek; it does not prove which choice was better beforehand.
3. **AI opposing counsel.** Before a prediction locks, AI asks a short, evidence-grounded question that challenges an assumption. Record confidence before and after the question so its effect can be studied across many predictions. AI never determines FPL points or adjudicates the winner.
4. **AI manager — later release.** A virtual competitor makes deadline-locked decisions using only information available at that time. Its inputs, decisions, and results remain visible for fair comparison with human players.

## First release: definition of done

- Members sign in by email magic link, choose a unique username for public display, and join a private group by invite code.
- A group admin creates a duel for two members using one of the two fixed claim types and enters the official FPL gameweek deadline before submissions open. The server enforces it in UTC and rejects late submissions. An incorrect deadline voids the duel rather than being moved after a submission.
- Each member submits only a 0–100% probability, in 5-point steps, that their own side wins. Revisions before the deadline are preserved; only the latest counts. Probabilities stay hidden until the deadline and are locked afterward.
- A missing submission or tied result voids the duel. Voided duels remain in activity history but do not affect wins, losses, or Brier scores.
- Resolution waits until FPL finalizes that gameweek's scores, including its treatment of postponed fixtures. Captain duels use the points officially awarded to each captain slot, including vice-captain promotion and chip multipliers; a slot with no eligible player scores zero.
- After FPL finalizes the gameweek, a group admin enters both final values with an official FPL source link. Each participant can confirm or dispute with a reason; an admin who is also a participant confirms at entry. After both participants are emailed the score entry, an unanswered confirmation auto-confirms in 72 hours. A dispute pauses the timer until the admin posts corrected or reaffirmed values with a source; this creates a group-visible revision, resets confirmations, and starts a new notice window. The same participant cannot repeat an unchanged dispute to stall resolution.
- The app shows the result, each member's history and sample size, and mean Brier score (`(p − outcome)²`, with `p` from 0 to 1) for resolved predictions.
- Tests cover deadline boundaries, private access, missing and late submissions, ties, captain substitution, scoring, confirmations, disputes, the 72-hour rule, and corrections.

The first release uses manually entered results. Automatic FPL data import is a separate step after confirming a dependable, permitted data source.

## Engineering approach

- **Frontend:** React and TypeScript, designed for quick use on a phone before a deadline.
- **Backend:** Python and FastAPI for duels, deadlines, resolution, and later AI/data workflows; Supabase Auth/GoTrue magic links and invite-code group membership. The same GoTrue service runs locally with Mailpit, so development works offline after the images and packages are installed; production can use managed Supabase Auth.
- **Database:** PostgreSQL for users, groups, duels, append-only probability submissions, score entries, confirmations, and corrections. Store and compare all timestamps in UTC.
- **Tests and delivery:** Unit tests for rules and access control, API tests for the core flow, CI, and a one-command local development setup.

We will ship the first playable flow before adding FPL counterfactual rules or AI. A salted commit-reveal protocol is not planned: private access control and append-only records are enough for the first friend group. Each later phase should be usable with a real group and measured against actual gameweeks.

## Run locally

Install Docker and Docker Compose, then run `make setup` from this directory. It creates `.env` with random local secrets and starts PostgreSQL, GoTrue, Mailpit, the API, and the web app. Open [Rivalry Court](http://localhost:5173) and use [Mailpit](http://localhost:8025) to open your magic link. The API is at [localhost:8001](http://localhost:8001/docs). After setup, `docker compose up --build` restarts the stack; `docker-compose up --build` also works when Compose is installed as a standalone command. Run `make test` for API and web tests. No external FPL or AI key is needed for this release. See [PROGRESS.md](PROGRESS.md) for verification notes and [DEPLOY.md](DEPLOY.md) for deployment considerations.

After signing in, choose a username in **Your name in court**. Usernames are unique, can be chosen **only once** (they cannot be changed afterwards), use 3–24 letters, numbers, or underscores, and appear on duels and group history. Until set, a member appears as a temporary `Player-xxxxxxxx` label. Other group members do not receive your email address from the group API. Local sign-in links and score notices go to Mailpit because `.env` points SMTP to the local test inbox. To deliver to Gmail or another real inbox, deploy the app with a real SMTP provider and verified sender; changing the email typed into the login form does not change local delivery.

For a local two-person trial, sign in as the second member in an incognito window on the same computer and use the invite code. `localhost` is not reachable from a friend's computer; hosting is needed for remote friends.

`.env.example` documents every local variable. The setup script generates `POSTGRES_PASSWORD` and `AUTH_JWT_SECRET`; the remaining defaults are ready for local use. For a deployed app, set real public URLs, SMTP credentials, a strong JWT secret shared by GoTrue and the API, and a managed PostgreSQL/Auth service. Do not reuse local secrets. The app assumes HTTPS at deployment.

## Architecture and decisions

`apps/web` is a mobile-first React/TypeScript app. It calls GoTrue directly for magic-link sessions and sends the resulting bearer token to `apps/api`. FastAPI verifies its signature and audience and enforces membership, admin rights, sealed probabilities, and deadlines. PostgreSQL stores groups, duels, and append-only submission, score, notice, confirmation, and void events. Alembic applies the schema and triggers that reject event updates and deletes. Pure functions in `apps/api/rivalry/rules.py` determine deadline, void, resolution, captain-slot, and Brier behavior.

The admin creates a duel because they must supply its official deadline. Invite codes are random and stored as hashes; each code is shown once, and an admin can generate a replacement that invalidates the old code. Score notices go to both participants, and the 72-hour clock begins only after delivery succeeds. Corrections are new score entries, with earlier values and dispute reasons visible to the group. An admin must verify that FPL has finalized the gameweek before entering a score. The server accepts only `fantasy.premierleague.com` source links. Sealed picks need no separate selection because each player always backs their own side. Commit-reveal was skipped because authenticated private access plus immutable records is proportionate for a friend group.

## Tests

Run `cd apps/api && python3 -m venv .venv && .venv/bin/pip install -e '.[dev]' && .venv/bin/pytest && .venv/bin/ruff check .` for API tests and lint. Run `cd apps/web && npm ci && npm test && npm run lint && npm run build` for web tests, lint, and strict TypeScript build. CI runs these on every push and pull request, applying Alembic migrations to PostgreSQL and checking the immutable-table triggers and database constraints. API tests cover access, deadline boundaries, sealed revisions, no-shows, ties, captain substitution, Brier scores, disputes, corrections, and the 72-hour rule.

## Next

The roadmap is captain-only gameweek forks, then transfer forks and remaining FPL rules, followed by AI opposing counsel and later an AI manager. Automatic FPL import depends on a dependable, permitted source. This first release relies on an admin to enter correct deadlines and finalized official scores; it has no background worker, so auto-confirmation is computed when a duel or history is read after 72 hours. Magic-link and score email delivery need working SMTP outside local development.
