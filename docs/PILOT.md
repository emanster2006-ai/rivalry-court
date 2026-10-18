# Rivalry Court pilot: three gameweeks with friends

Status: ready to recruit; this is a plan, not completed user research. Earlier project notes record a two-user production sign-in/join/lock trial on October 8–9, 2026. No multi-gameweek results are claimed.

## Before inviting participants

Complete `RELEASE_VERIFICATION.md`, especially delivery of score notices to both inboxes. Use a dedicated group with consenting participants. Confirm the official FPL deadline and finalized scores manually. Explain that usernames are permanent, predictions become visible to group members after lock, and this is an experimental friend-group app. Do not collect passwords, tokens, inbox screenshots, or FPL account credentials.

Start with 2–4 friends over three gameweeks. Let people stop at any point. No invitations or emails have been sent by this change.

## Run each gameweek

1. Admin creates one gameweek-points duel with the official deadline; both people verify the deadline before submitting.
2. Each person signs in, joins, and submits without coaching. Note whether they finish and where they need help. Ask what “65%” means to them before revealing the opponent's prediction.
3. After lock, check that predictions are visible and revisions are refused. Wait for FPL to finalize scores before entering them with the official source link.
4. Verify both score emails arrive, then have participants review and confirm. Record any delivery delay or confusion. Exercise dispute/correction in a separate arranged verification duel.
5. Ask: “What did you expect here?”, “What was hardest?”, “Would you use this next gameweek, and why?” Record observations, not names or email addresses.

## Record one row per attempt

Copy this table into a private pilot log. Use anonymous labels such as P1/P2; don't publish participant-level predictions or quotes without consent.

| Date / gameweek | App commit | Device / browser | Anonymous participant | Task | Completed unaided? | Time / delay | Observed problem | Severity | Issue / fix | Retest outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Count invitations, participants who opt in, attempts at each task, completed tasks, score notices actually received, and people who return the following week. Keep denominators and exclusions. With a tiny sample, report counts rather than broad claims about usability.

## Turn feedback into engineering evidence

Open one issue per observed problem: task, expected behavior, actual behavior, reproduction steps, anonymized evidence, and acceptance criteria. Prioritize blocked tasks and privacy/correctness errors before convenience improvements. Link each fix PR and retest the original task. Publish an aggregate three-gameweek report with sample size, dropouts, issues fixed, and remaining limits. Do not fill this report with simulated observations.

## Invitation draft (owner sends)

> I'm testing Rivalry Court, a small app where friends lock FPL win predictions and review the results afterward. Would you like to try it for three gameweeks and tell me where it gets confusing? It uses email sign-in and a private group; your prediction becomes visible in the group after the deadline. It's experimental and you can stop whenever you want. I'll arrange the first run with you and won't publish your details or comments without permission.
