# First-release verification

Use two consenting participants in a dedicated test group. Keep real group records intact. Do not send verification emails or create live records without arranging the test with the owner.

| Flow | Expected evidence | Current production status |
| --- | --- | --- |
| Sign-in, join, duel, lock | Two users see their own predictions only before deadline | Previously recorded as verified |
| Score notice | Both recipients receive the correct duel link; 72h clock begins after successful send | Unverified |
| Dispute and correction | Dispute pauses resolution; new revision preserves earlier values and resets review | Unverified |
| Void | Admin supplies reason; later submissions rejected; duel omitted from scored statistics | Unverified |
| Tie | Final equal scores void duel and do not alter Brier average | Unverified |
| 72-hour boundary | Pending before boundary, resolves on next read at/after boundary; late response refused | Unverified |
| Phone | Sign-in and duel controls usable on an actual phone | Unverified |

Automated API tests cover these rule boundaries with controlled time and a substituted mail sender. Local browser tests and a passing build are separate evidence from real production behavior. Do not mark a row verified without date, environment, and observed outcome. Capture screenshots only with test names/data and no email addresses or tokens.

A failed SMTP attempt must not save the score revision, participant confirmation, or notice; retrying after delivery recovers must create exactly one revision and one notice. A partially delivered attempt can send the first recipient a duplicate email on retry; the transaction rolls back database changes but cannot retract email.
