# Deploying Rivalry Court

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
- `DATABASE_URL`, `POSTGRES_*`, `AUTH_DB_PASSWORD` — real passwords, never the `change-me` defaults.
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
