# Deploying Rivalry Court

## Free-hosting research (October 2026)
Checked against the providers' own pages where possible; blog comparisons disagreed with each other, so re-check pricing pages before signing up.

| Option | What it gives | Problems |
|---|---|---|
| Render free web service | 750 instance hours/month, 1 instance, sleeps after 15 idle minutes (about 1 minute to wake) | **Outbound SMTP ports 25, 465, 587 are blocked**, so the API cannot send score emails on them; files vanish on restart |
| Render free Postgres | 1 GB | **Expires after 30 days, deleted after a 14-day grace period.** Not usable for real history |
| Supabase Free | Auth + Postgres, 500 MB, 50,000 monthly users, two free projects | Built-in email sender only allows 2 messages/hour and only to team members, so custom SMTP is required; inactivity pausing is not stated on the pages I read (check) |
| Brevo free SMTP | About 300 emails/day (from search results; the official page could not be read) | Needs an account; confirm which SMTP ports it supports |
| Oracle Cloud always-free VM | Runs the whole Docker Compose stack as-is | Needs a card for sign-up; you manage the server and its security |

**Best fit for "free and safe" at friend-group scale (not yet built or tested):**
Supabase Free (sign-in + database) + Render free web service (API) + a free static host for the web app + Brevo free SMTP for emails.
Open items before this works:
1. The API verifies sign-in tokens with a shared HS256 secret. Check which signing method the hosted Supabase project uses and adapt `rivalry/auth.py` if it uses public keys instead.
2. The API sends score notices over SMTP from Render. Use a provider port that Render does not block (2525 if offered) or switch to the provider's web API.
3. Keep Supabase's database from pausing, and expect about a minute of delay on the first request after the API sleeps.

**Not recommended:** hosting everything on Render's free tier (the database disappears), or Fly.io (no real free tier now).

**Accounts:** signing up for these services has to be done by you; I cannot create accounts.

Nothing here has been run against a real host yet. It is a checklist for the first deployment.

## What has to run
| Piece | Image / command | Notes |
|---|---|---|
| Postgres 17 | managed database preferred | Create the app database, plus an `auth` schema for GoTrue (see `scripts/init-auth-db.sql`) |
| GoTrue (sign-in) | `supabase/gotrue:v2.196.0` | Same settings as the `auth` service in `compose.yaml`, with real SMTP |
| API | `apps/api/Dockerfile` | Run `alembic upgrade head` before `uvicorn rivalry.api:app --host 0.0.0.0 --port 8000` (no `--reload`) |
| Web | `apps/web/Dockerfile.prod` | Static files via nginx. Build args `VITE_API_URL` and `VITE_AUTH_URL` are baked in at build time |

## Environment (production)
- `APP_ENV=production` — the API refuses to start with placeholder secrets or a non-https `WEB_URL`.
- `AUTH_JWT_SECRET` — random, 32+ characters, **identical** for GoTrue (`GOTRUE_JWT_SECRET`) and the API.
- `DATABASE_URL`, `POSTGRES_*` — real passwords, never the `change-me` defaults.
- `WEB_URL` — the public https address of the web app. Used for CORS and magic-link redirects (`GOTRUE_SITE_URL`, `GOTRUE_URI_ALLOW_LIST`).
- `AUTH_URL` / `API_URL` — public https addresses the browser calls.
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM` — a real mail provider. Used by GoTrue (magic links) and the API (score notices). Mailpit is local only.
- Set `GOTRUE_MAILER_AUTOCONFIRM=false` and consider `GOTRUE_DISABLE_SIGNUP=true` after friends have joined.

## First-deploy checklist
1. Create the database and run the migrations.
2. Start GoTrue, then the API, then build and publish the web image.
3. Sign in with your own email; confirm the magic link arrives and lands on the site.
4. Create a group, invite one friend, create a duel with a deadline a few minutes ahead, and run it through reveal, score entry and confirmation (see "Two-user click-through" in `PROGRESS.md`).
5. Check the API logs for errors and that score-notice emails arrive.

## Risks to keep in mind
- The 72-hour auto-confirm is computed when someone reads the duel; it does not need a background job, but no reminder email is sent when it expires.
- All times are stored in UTC; the deadline is entered in the admin's local time and converted in the browser.
- Back up the Postgres database; predictions and score history live only there.
