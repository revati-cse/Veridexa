# CLAUDE.md

Guidance for Claude Code sessions working in this repo.

## What this is

Veridexa AI — an evidence-based skill verification and job readiness
platform (tagline: *"From claimed skills to proven capability."*), built
for the IIC 3.0 hackathon at Manipal University Jaipur. Core loop: paste a
job description → claim skills + optionally a GitHub repo → Veridexa
generates a real SQL/data challenge targeting the job's top skills →
candidate solves it in Monaco → backend runs the query for real and scores
it → computes a Job Readiness % (backend formula, never the LLM) → surfaces
skill gaps → "Improve My Readiness" mutates a new challenge targeting the
weakest skill → resubmit → readiness updates live.

**`BLUEPRINT.md` (repo root) is the single source of truth for the design.**
Read the relevant lettered section (A–Z) before touching a feature — it
covers the DB schema, every API endpoint, the AI prompt architecture,
scoring formulas, and the security/testing requirements. If you deliberately
deviate from it, update it — don't let it silently drift out of date.

## Repo layout

```
backend/    FastAPI (Python 3.11) — app/{routers,services,schemas,db,ai,github,sandbox,fixtures}/
frontend/   Next.js 16 (App Router) + React 18 + TypeScript + Tailwind, Zustand for session state
supabase/migrations/   Postgres schema (001_init.sql) + skill taxonomy seed (002_seed_skills.sql)
docs/       demo_script.md and similar reference docs
```

Backend routers are thin: each just calls a pure `services/*.py` function
and (where wired) a best-effort `db/*.py` write. Business logic lives in
`services/`, not in routers.

## Running it locally

```
# backend
cd backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # http://localhost:8000, /health

# backend tests (130+ tests, no live network needed — Claude/GitHub calls are mocked)
cd backend && source venv/bin/activate && python -m pytest -q

# end-to-end smoke test against a *running* backend (see docs/demo_script.md)
uvicorn app.main:app &
python scripts/smoke_test.py

# frontend
cd frontend && npm install && npm run dev   # http://localhost:3000
```

See `.env.example` (repo root) for every env var; all of them are optional
locally — see "Graceful degradation" below.

Tests use plain `asyncio.run(...)` inside sync `def test_*` functions, not
`pytest-asyncio` (no plugin dependency for that). Follow the same pattern
for new async tests.

## Key architectural conventions

- **Claim vs. Evidence vs. Performance.** Never trust a claim. Evidence
  rows only ever come from GitHub analysis or challenge submissions — never
  from what the candidate typed about themselves. See BLUEPRINT.md Section 2/L.
- **Backend computes every score.** Claude is asked for rubric sub-scores,
  strengths/weaknesses, and evidence observations — it never computes
  `overall_score`, `difficulty`, or `readiness %` itself. Those are
  deterministic backend formulas (Section K/N).
- **Demo fallback.** Every Claude-calling service (`job_parser`,
  `github_analyzer`, `challenge_generator`, `evaluation_engine`,
  `challenge_mutation_engine`) retries once on failure, then falls back to
  a hand-checked fixture in `backend/app/fixtures/`, flagging
  `demo_fallback: true` on the response. This means the API never 500s
  from a missing `ANTHROPIC_API_KEY` or a flaky connection — useful both
  for local dev without a key and for demo-day reliability.
- **Best-effort DB writes.** `backend/app/db/*.py` is a Postgres
  persistence layer wired in as a write-through, not the primary data
  path — every function no-ops when `DATABASE_URL` is unset
  (`is_available()`), and every router call wraps writes in
  `app.db.safe_write(...)`, which logs and swallows failures rather than
  breaking the response. Reads (`get_taxonomy`, `get_job`,
  `get_challenge_chain`, ...) return `None`/`[]` on no-DB, and callers fall
  back to the in-memory/session-passed contract. **The one write you must
  not skip when adding a new `db/*.py` insert**: check whether the row's
  FK targets something that might not exist yet (e.g. `challenges.user_id`,
  `challenges.job_id`) — `save_challenge` degrades a missing `job_id` link
  rather than losing the row; match that pattern rather than letting a raw
  `ForeignKeyViolationError` bubble up through `safe_write`'s catch-all.
- **"No DB yet" request contracts.** Several endpoints still take full
  context in the request body instead of looking up by id (e.g.
  `SubmissionCreate` carries the whole `Challenge`, `ChallengeMutateRequest`
  carries the whole previous `SubmissionRecord`). This was a deliberate,
  documented choice before persistence existed and has been *kept* even
  after DB wiring landed — DB writes were added as a side-effect, not a
  contract change. Don't "clean this up" into DB-lookup-by-id without
  discussing it; the frontend session store is still the primary path.
- **Prompt-injection delimiters.** Every prompt that interpolates
  candidate- or web-sourced text (JD text, repo file contents, candidate
  explanations, job titles, weaknesses fed into the mutation prompt) wraps
  it in an explicit `<tag>` with a matching system-prompt instruction to
  treat it strictly as data. Follow this exactly when adding a new prompt —
  never string-concatenate untrusted text into an instruction-bearing part.
- **SQL sandbox isolation.** `sandbox/sql_runner.py` runs candidate SQL
  against a fresh in-memory SQLite instance with a statement-type denylist,
  row caps, and a timeout. If you touch the denylist, check it against
  table-valued-function forms too (e.g. `pragma_table_info()` bypassed a
  naive `\bPRAGMA\b` regex — it's `PRAGMA\w*` now for a reason).
- **Pydantic schemas are the source of truth**, mirrored by hand into
  `frontend/lib/types.ts`. Keep both in sync when changing a schema.

## Known gotchas (already solved — don't reintroduce)

- Monaco is self-hosted (`import * as monaco from "monaco-editor"` +
  `loader.config({ monaco })`), not loaded from the jsdelivr CDN — the CDN
  is unreachable in some sandboxed environments. The worker is
  `"monaco-editor/editor/editor.worker.js"` (not the `esm/vs/...` path —
  `monaco-editor`'s own `exports` map already prepends that).
- The Monaco editor page is wrapped in `next/dynamic(..., { ssr: false })`
  — a plain `"use client"` import still crashes `next build` prerendering
  with `window is not defined`.
- `dompurify` is pinned by `monaco-editor`'s own `package.json` (not a
  range) — bump it via the root `overrides` field in `frontend/package.json`,
  not `npm audit fix`.

## Freshness (P2, backend-only)

`freshness_engine.py` / `POST /freshness/compute` flags whether the
evidence behind each skill is recent or stale (`fresh`/`aging`/`stale`/
`not_assessed`), based on `GithubAnalyzeResponse.analyzed_at` and
`SubmissionEvaluationResponse.evaluated_at`. It is **informational only** —
deliberately not blended into `readiness_engine`'s score, so the numbers
verified in `docs/demo_script.md` stay reproducible. No frontend screen
calls it yet (`api.computeFreshness` exists in `lib/api.ts` but is unused) —
add one only if asked; it wasn't part of the original 7-screen flow
(Section Q).

## Recruiter dashboard (P3, backend + frontend)

`GET /recruiter/jobs/{job_id}/dashboard` (`recruiter_dashboard.py`,
`frontend/app/recruiter/page.tsx`) ranks candidates for a job by
`readiness_score` — computed via the exact same `readiness_engine.
compute_readiness` the candidate's own dashboard uses, never a separate
recruiter-side formula. This is the **one endpoint in the API that requires
a database** — there's no way to know "which candidates applied to this
job" from a single session's state, so `db_available: false` (empty
`candidates`) is the response whenever `DATABASE_URL` isn't configured.

Two deliberate simplifications, both because the data isn't persisted
anywhere yet: `claims=[]` (no `claims` table exists — `POST /candidates/
claims` is still a stub) and `github_evidence=None` (GitHub analysis is
never written to storage) for every candidate. The score reflects challenge
performance only. There's also no recruiter/candidate role or auth of any
kind — the `/recruiter` page is just another unauthenticated route; the job
ID it needs is shown on the Skills screen after a candidate parses a JD
(`skills/page.tsx`).

If you add a new `db/*.py` write, keep `app.db.challenges.
get_candidate_ids_for_job` and `app.db.submissions.
get_submission_history_for_job` in mind — they reconstruct `Challenge`/
`SubmissionEvaluationResponse` objects from persisted rows, and
`evaluations` doesn't have an `evidence` column (only the separate
`evidence` table does), so reconstructed evaluations always have
`evidence=[]`. That's fine today: neither `readiness_engine` nor
`skill_gap_engine` reads that field.

## What's not built yet / deliberately out of scope

Auth, candidate comparison, and timeline views are P3 per BLUEPRINT.md
Section B — don't add them unless explicitly asked. This is a
2-developer, 36-hour hackathon scope; resist gold-plating.
