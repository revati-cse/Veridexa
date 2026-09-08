# Veridexa AI — Deploy Runbook

Closes BLUEPRINT.md checklist item 34. All the config referenced below
(`render.yaml`, `backend/Procfile`, `.env.example`, CORS wiring in
`backend/app/config.py`) has already been verified locally to behave
correctly — see CLAUDE.md's "Deployment config verification" section. This
runbook is what's left: the actual account setup and click-through, which
needs real Render/Vercel/Supabase credentials no prior session has had.
Follow it in order — each step's dependencies come before it.

## Prerequisites

- A Supabase account (or any reachable Postgres 14+ instance).
- A Render account (or Railway — see the alternative in Step 2).
- A Vercel account.
- An Anthropic API key (`ANTHROPIC_API_KEY`) — optional but strongly
  recommended for the live demo; without it every AI call runs on the
  fixture fallback (`demo_fallback: true`), which still works but isn't
  the live path.
- A GitHub PAT (`GITHUB_TOKEN`, `public_repo` read-only scope) — optional,
  only needed for `/github/analyze` to hit real repos instead of a 422.
- This repo cloned locally, or push access to trigger Render/Vercel's
  git-based deploys.

## Step 1 — Database (Supabase)

1. Create a new Supabase project. Note its Postgres connection string
   (**Project Settings → Database → Connection string**, use the
   `postgres://` URI, not the pooler URL, unless you configure `asyncpg`
   for pgbouncer) and its project URL + service role key
   (**Project Settings → API**).
2. Run both migrations against it, in order, via the Supabase SQL editor
   or `psql`:
   ```
   psql "$DATABASE_URL" -f supabase/migrations/001_init.sql
   psql "$DATABASE_URL" -f supabase/migrations/002_seed_skills.sql
   psql "$DATABASE_URL" -f supabase/migrations/003_candidate_claims.sql
   ```
3. Verify the seed landed:
   ```
   psql "$DATABASE_URL" -c "SELECT count(*) FROM skills;"   -- expect 44
   ```
4. Keep the connection string, project URL, and service role key handy —
   they're backend env vars in Step 2.

## Step 2 — Backend (Render)

This repo includes a Render Blueprint (`render.yaml`, repo root) that
provisions a single Python web service from `backend/`.

1. In the Render dashboard: **New → Blueprint**, connect this repo (branch
   `main`). Render reads `render.yaml` and creates the `veridexa-backend`
   service — `pip install -r requirements.txt`,
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check on
   `/health`.
2. Set the secret env vars `render.yaml` declares (`sync: false` means "set
   me in the dashboard" — Render never stores these in git):

   | Env var | Value |
   |---|---|
   | `ANTHROPIC_API_KEY` | your Anthropic key (optional — see Prerequisites) |
   | `GITHUB_TOKEN` | your read-only PAT (optional) |
   | `SUPABASE_URL` | from Step 1 |
   | `SUPABASE_SERVICE_ROLE_KEY` | from Step 1 |
   | `DATABASE_URL` | from Step 1 |
   | `ALLOWED_ORIGINS` | `http://localhost:3000` for now — you'll add the Vercel domain in Step 4 |

3. Deploy. Once live, confirm:
   ```
   curl https://<your-render-domain>/health
   ```
   should return `{"status":"ok"}`. If `ANTHROPIC_API_KEY`/`GITHUB_TOKEN`
   are unset, every AI call and GitHub read fall back to fixtures
   (`demo_fallback: true`) rather than 500ing — expected, not a failure.

### Backend (Railway, alternative to Render)

Railway auto-detects `backend/Procfile`
(`web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Create a service
from this repo, set **Root Directory** to `backend`, and set the same six
env vars as the table above.

## Step 3 — Frontend (Vercel)

1. **New Project**, import this repo, set **Root Directory** to `frontend`
   (Vercel auto-detects Next.js — no extra config needed).
2. Set `NEXT_PUBLIC_API_BASE_URL` to the backend URL from Step 2 (e.g.
   `https://veridexa-backend.onrender.com`).
3. Deploy. Note the resulting `*.vercel.app` domain (or your custom
   domain).

## Step 4 — Close the CORS loop

The backend was deployed in Step 2 with `ALLOWED_ORIGINS` only allowing
`localhost`. Now that the real frontend domain exists:

1. Back in Render: update `ALLOWED_ORIGINS` to include the Vercel domain
   from Step 3, comma-separated (e.g.
   `http://localhost:3000,https://veridexa.vercel.app`).
2. Redeploy the backend (Render redeploys automatically on an env var
   change, or trigger manually).
3. Verify CORS is actually enforcing the new list, not just present:
   ```
   curl -i -X OPTIONS https://<your-render-domain>/health \
     -H "Origin: https://<your-vercel-domain>" \
     -H "Access-Control-Request-Method: GET" | grep -i access-control-allow-origin
   ```
   should echo your Vercel origin back. A request with a stranger
   `Origin` header should get a 400 with no
   `access-control-allow-origin` header — that's the isolation working,
   not a bug.

## Step 5 — Post-deploy verification

Don't consider the deploy done until all of these pass against the *live*
URLs, not localhost:

1. **Smoke test against the live backend** — `scripts/smoke_test.py`
   already supports pointing at any base URL:
   ```
   cd backend
   SMOKE_TEST_BASE_URL=https://<your-render-domain> python scripts/smoke_test.py
   ```
   Expect `SMOKE TEST PASSED`. If `ANTHROPIC_API_KEY`/`DATABASE_URL` are
   both configured for real, the readiness numbers should match the
   "with GitHub evidence" / live-Claude path rather than the fixture
   numbers in `docs/demo_script.md` — that's expected once it's live,
   not a discrepancy to chase.
2. **Frontend smoke-click** — open the Vercel URL, paste the demo JD from
   `docs/demo_script.md`, and walk Screens 1–7 by hand once. Confirm no
   CORS errors in the browser console (would show as a fetch failure on
   `/jobs/parse` from Screen 2 specifically — that's the tell if Step 4
   was missed).
3. **Recruiter dashboard** — visit `/recruiter` on the Vercel URL, paste a
   `job_id` from a Screen 3 you just ran, confirm the candidate row loads
   (`db_available: true`).
4. **Rehearse `docs/demo_script.md` once for real**, live network, to
   confirm nothing about the deployed environment (cold starts, Render
   free-tier sleep, real Claude latency) breaks the rehearsed pacing —
   this is a different risk than the "kill the network" rehearsal
   (checklist item 35) already covered locally.

## Rollback / troubleshooting

- **Backend 500s on every request**: check Render's logs first — a
  missing `DATABASE_URL` should *not* cause this (writes no-op
  gracefully); a malformed `DATABASE_URL` (wrong host/port/credentials)
  will, since `asyncpg.connect` fails at startup. Fix the connection
  string and redeploy rather than unsetting it.
- **Frontend loads but every API call fails**: almost always
  `NEXT_PUBLIC_API_BASE_URL` pointing at the wrong backend, or Step 4's
  CORS update not yet redeployed. Check the browser Network tab for the
  actual failing request before guessing.
- **`/github/analyze` always 422s live**: either `GITHUB_TOKEN` is unset
  (fine — designed fallback, per BLUEPRINT.md Section V) or the token's
  scope doesn't cover the repo being analyzed (needs at least
  `public_repo` read).
- **Need to revert a bad deploy**: Render and Vercel both keep prior
  deploys — use their dashboard's "redeploy previous" rather than force-
  pushing or reverting commits in git.

## Reference — full env var list

Mirrors `.env.example` (repo root) exactly; keep both in sync if either
changes.

| Var | Where | Required? |
|---|---|---|
| `ANTHROPIC_API_KEY` | backend | optional (fixture fallback otherwise) |
| `GITHUB_TOKEN` | backend | optional (422 + continue otherwise) |
| `SUPABASE_URL` | backend | optional (DB features no-op otherwise) |
| `SUPABASE_SERVICE_ROLE_KEY` | backend | optional |
| `DATABASE_URL` | backend | optional |
| `ALLOWED_ORIGINS` | backend | yes — defaults to `localhost:3000` only |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | yes — defaults to `localhost:8000` only |
