# Rivalry Court: decisions and tradeoffs

## Preserve the record when people change their minds

A prediction revision or score correction adds a new event instead of replacing the old value. PostgreSQL triggers reject updates and deletes on event tables. The API selects the latest relevant revision. This makes “what was known before kickoff?” inspectable and keeps disputes attached to the score they challenged.

The cost is more complicated reads and migrations. Append-only tables do not make the entire system tamper-proof: database administrators and deployment access remain trusted. See `apps/api/rivalry/models.py` and the Alembic migrations.

## Enforce privacy and deadlines on the server

The API checks group membership and hides the opponent's probability before the deadline. UTC comparisons determine whether a submission is accepted; the browser slider is only an input. Hiding a value in React would still expose it through network responses. Tests exercise outsiders, non-participants, and exact deadline boundaries.

## Keep official scoring manual for the first release

An admin enters finalized scores with an official FPL URL. This keeps the first release independent of an unofficial data feed, but trusts the admin to enter correct values and deadlines. Participants can dispute the entry, and corrections remain visible. Automatic import and AI adjudication are outside this release.

## Start the review window after a score notice succeeds

A failed SMTP attempt rolls back the score revision, confirmation, and notice in the database. A retry can then save one consistent revision and notice. This avoids a 72-hour clock starting when delivery failed. SMTP acceptance still does not prove inbox delivery, and sending to one person before the second fails can cause a duplicate email on retry. A transactional outbox would be a future option if delivery/retry complexity warrants it.

Auto-confirmation is evaluated when a duel/history is read after 72 hours; there is no background worker promising an exact-time update. See `rivalry/rules.py` and the failure-recovery API test.

## Separate evidence from presentation

The public case study contains the actual React interface rendered against synthetic browser fixtures. It demonstrates layout and the intended flow; it does not validate backend privacy, SMTP, production authentication, or real user behavior. Automated API tests and live pilot observations are separate evidence. The capture script blocks all nonlocal network requests and labels every frame.
