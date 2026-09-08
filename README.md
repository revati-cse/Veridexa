# Veridexa AI
Evidence-Based Skill Verification and Personalized Job Readiness Platform
*"From claimed skills to proven capability."*

See [`BLUEPRINT.md`](./BLUEPRINT.md) for the full technical design.

## Project status

Built for the IIC 3.0 hackathon at Manipal University Jaipur — the full
9-engine backend, all 7 candidate screens plus a recruiter dashboard, and
DB persistence are implemented and tested (140+ backend tests). 37 of
[BLUEPRINT.md's 38 checklist items](./BLUEPRINT.md#numbered-implementation-checklist)
are checked off. The one open item is **live deployment** (item 34):
the deployment config itself — `render.yaml`, `backend/Procfile`,
`.env.example`, CORS wiring — is written and verified (see CLAUDE.md's
"Deployment config verification"), but actually deploying to Render/
Railway/Vercel/Supabase needs real account credentials, so no live URL
exists yet. Follow "Deployment" below whenever those credentials are
available.

## Local development

**Backend** (FastAPI, Python 3.11):
```
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # fill in the Backend block; all vars are optional — missing ones just fall back to demo fixtures
uvicorn app.main:app --reload
```

**Frontend** (Next.js):
```
cd frontend
npm install
cp ../.env.example .env.local   # keep only NEXT_PUBLIC_API_BASE_URL
npm run dev
```

**Database** (optional locally — the API runs fine with `DATABASE_URL` unset; every write silently no-ops and every read falls back to in-memory/session data, per `backend/app/db/__init__.py`):
```
psql "$DATABASE_URL" -f supabase/migrations/001_init.sql
psql "$DATABASE_URL" -f supabase/migrations/002_seed_skills.sql
```

## Deployment

Backend → Render or Railway. Frontend → Vercel. Database → Supabase (Postgres).
For the full step-by-step (including post-deploy verification and
troubleshooting), see [`docs/deploy_runbook.md`](./docs/deploy_runbook.md).

### Backend (Render)

This repo includes a Render Blueprint (`render.yaml`, repo root) that provisions
a single Python web service from `backend/`:
1. In the Render dashboard: **New → Blueprint**, connect this repo. Render
   reads `render.yaml` and creates the `veridexa-backend` service
   (`pip install -r requirements.txt`; `uvicorn app.main:app --host 0.0.0.0 --port $PORT`;
   health check on `/health`).
2. Set the secret env vars it declares (`sync: false` in `render.yaml` means
   "set me in the dashboard"): `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`,
   `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `DATABASE_URL`,
   `ALLOWED_ORIGINS` (include the deployed Vercel domain, comma-separated).
3. Every var is optional — job parsing, evaluation, and challenge
   generation all fall back to demo fixtures if `ANTHROPIC_API_KEY` is
   missing (`demo_fallback: true` on the response), and persistence
   silently no-ops if `DATABASE_URL` is missing. Nothing 500s from a
   missing key.

### Backend (Railway, alternative)

Railway auto-detects `backend/Procfile` (`web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
Create a service from this repo, set **Root Directory** to `backend` in the
service settings, and set the same env vars as above.

### Frontend (Vercel)

1. **New Project**, import this repo, set **Root Directory** to `frontend`
   (Vercel auto-detects Next.js from there — no extra config needed).
2. Set `NEXT_PUBLIC_API_BASE_URL` to the deployed backend URL (e.g.
   `https://veridexa-backend.onrender.com`).
3. Redeploy the backend with `ALLOWED_ORIGINS` including the resulting
   `*.vercel.app` domain (or a custom domain) — CORS is locked to exactly
   what's listed there (`backend/app/config.py`).

### Database (Supabase)

1. Create a Supabase project, copy its Postgres connection string into
   `DATABASE_URL` and its project URL / service role key into
   `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` on the backend.
2. Run both migrations against it, in order, via the Supabase SQL editor or
   `psql`: `supabase/migrations/001_init.sql` then `002_seed_skills.sql`.
3. No further setup — `backend/app/db/pool.py` connects lazily on startup
   and the API degrades gracefully (see above) if this step is skipped.
