# Rivalry Court

Rivalry Court is a social game played alongside Fantasy Premier League (FPL). Friends lock predictions before an FPL deadline, challenge each other's reasoning, and revisit the results after each gameweek. FPL remains the source of truth for teams and points; this project focuses on the decisions and rivalries around them.

## Agreed scope

1. **Sealed rivalry duels — first playable release.** Two friends compare either final gameweek scores after transfer penalties or points awarded to their captain slots. Each privately submits only a probability that their own side wins; the duel type and participants determine the sides. Predictions reveal at the FPL deadline, and resolved predictions contribute to a Brier-score history.
2. **Fork the gameweek.** Start with a captain swap where both players appeared and no chip, vice-captain, or auto-substitution complicates scoring. Then add transfers and the remaining FPL rules with explicit tests. A fork compares outcomes after the gameweek; it does not prove which choice was better beforehand.
3. **AI opposing counsel.** Before a prediction locks, AI asks a short, evidence-grounded question that challenges an assumption. Record confidence before and after the question so its effect can be studied across many predictions. AI never determines FPL points or adjudicates the winner.
4. **AI manager — later release.** A virtual competitor makes deadline-locked decisions using only information available at that time. Its inputs, decisions, and results remain visible for fair comparison with human players.

## First release: definition of done

- Members sign in by email magic link and join a private group by invite code.
- Two members create a duel using one of the two fixed claim types. A group admin enters the official FPL gameweek deadline before submissions open; the server enforces it in UTC and rejects late submissions. An incorrect deadline voids the duel rather than being moved after a submission.
- Each member submits only a 0–100% probability, in 5-point steps, that their own side wins. Revisions before the deadline are preserved; only the latest counts. Probabilities stay hidden until the deadline and are locked afterward.
- A missing submission or tied result voids the duel. Voided duels remain in activity history but do not affect wins, losses, or Brier scores.
- Resolution waits until FPL finalizes that gameweek's scores, including its treatment of postponed fixtures. Captain duels use the points officially awarded to each captain slot, including vice-captain promotion and chip multipliers; a slot with no eligible player scores zero.
- A group admin enters both final values with a link to their FPL source. Each participant can confirm or dispute with a reason; an admin who is also a participant confirms at entry. After both participants are emailed the score entry, an unanswered confirmation auto-confirms in 72 hours. A dispute pauses the timer until the admin posts corrected or reaffirmed values with a source; this creates a group-visible revision, resets confirmations, and starts a new notice window. The same participant cannot repeat an unchanged dispute to stall resolution.
- The app shows the result, each member's history and sample size, and mean Brier score (`(p − outcome)²`, with `p` from 0 to 1) for resolved predictions.
- Tests cover deadline boundaries, private access, missing and late submissions, ties, captain substitution, scoring, confirmations, disputes, the 72-hour rule, and corrections.

The first release uses manually entered results. Automatic FPL data import is a separate step after confirming a dependable, permitted data source.

## Engineering approach

- **Frontend:** React and TypeScript, designed for quick use on a phone before a deadline.
- **Backend:** Python and FastAPI for duels, deadlines, resolution, and later AI/data workflows; managed magic-link authentication and invite-code group membership.
- **Database:** PostgreSQL for users, groups, duels, append-only probability submissions, score entries, confirmations, and corrections. Store and compare all timestamps in UTC.
- **Tests and delivery:** Unit tests for rules and access control, API tests for the core flow, CI, and a one-command local development setup.

We will ship the first playable flow before adding FPL counterfactual rules or AI. A salted commit-reveal protocol is not planned: private access control and append-only records are enough for the first friend group. Each later phase should be usable with a real group and measured against actual gameweeks.
