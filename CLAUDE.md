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

# backend tests (138+ tests, no live network needed — Claude/GitHub calls are mocked)
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

**Candidate comparison** lives inside the same `/recruiter` page, not a
separate route or endpoint: `CandidateSummary.skill_breakdown` (the same
per-skill rows `compute_readiness` already produces) rides along on the
existing dashboard payload, and the frontend just lets the recruiter check
2+ candidates to render them side by side. Don't add a `/compare` endpoint
— there's nothing it would compute that the dashboard call doesn't already
return.

## Skill evolution timeline (P3, backend + frontend)

`timeline_engine.py` / `POST /timeline/compute` reshapes `submission_history`
into a per-skill, per-attempt score history — the "Statistics 38.8% ->
70.8%" narrative (`docs/demo_script.md`) as a full sequence, not just a
before/after pair. `readiness_engine.py` already collapses the same history
to "latest wins" for the current score; this exposes every point instead.
Pure function, no AI call, no DB read — same "no DB yet, compute from
session state" contract as readiness/evidence/freshness.

Rendered as a "Skill Evolution" section on the Readiness screen
(`readiness/page.tsx`), fetched alongside readiness whenever
`submissionHistory` changes. Only shows skills with 2+ entries — a single
attempt isn't "evolution" yet, so the section stays hidden until a mutation
+ resubmission actually happened. If you add a new skill-name-keyed
aggregation like this, watch the same casing pitfall this one already hit:
`normalize_skill` only trims-and-returns an unrecognized (non-taxonomy)
skill rather than restoring its original case, so deriving a display name
from an already-lowercased dict key silently lowercases it — compute the
canonical display name once per skill and carry it alongside the key,
don't re-derive it from the key later (see the comment in
`compute_timeline`, and `test_skill_outside_the_taxonomy_keeps_its_
original_casing` in `tests/test_timeline_engine.py`).

## Demo rehearsal status

BLUEPRINT.md checklist item 35 ("full rehearsal of `docs/demo_script.md`
twice; kill network once mid-rehearsal") has been run and passed twice in
this environment:

- **Run 1** — a clean `scripts/smoke_test.py` pass against a normally
  started backend (`DATABASE_URL` configured, no live Claude/GitHub
  credentials). Readiness went 63.3% → 70.5%, matching the "without GitHub
  evidence" numbers in `docs/demo_script.md` exactly.
- **Run 2** — the same in-flight session (same `job_id`, first challenge,
  and evaluation carried forward) but with the network genuinely killed
  partway through, between the first readiness check and the mutation
  step: the backend was restarted with a fake-but-real-shaped
  `ANTHROPIC_API_KEY` (so `claude_client.py` actually attempts a live
  round-trip instead of short-circuiting on "no key configured") and every
  outbound route pointed at a proxy nothing listens on, `NO_PROXY` cleared
  too since this sandbox otherwise routes `api.anthropic.com` around the
  proxy directly. The rest of the demo — mutate, resubmit, readiness,
  history — completed with `demo_fallback: true` on every AI-touched
  response, no 500s, and the identical final readiness numbers as Run 1.
  Postgres (a local connection, not internet-routed) kept working
  throughout — worth distinguishing from the AI/GitHub fallback story if
  asked live.

The orchestration script for Run 2 was a one-off (scratchpad, not
committed) — to redo it, restart the backend mid-script with
`HTTPS_PROXY=http://127.0.0.1:1` (and `https_proxy`, `HTTP_PROXY`,
`http_proxy`, and empty `NO_PROXY`/`no_proxy`) plus a placeholder
`ANTHROPIC_API_KEY`, and confirm `demo_fallback: true` shows up on the
mutate/submit responses rather than a 500.

## Pitch deck

`docs/veridexa_pitch.pptx` (checklist item 36) — 13 slides built with
`pptxgenjs`, not a mockup: every product screenshot in it is a real
Playwright capture against a live backend + frontend + Postgres, cropped
to content bounds with Pillow. The recruiter-dashboard/comparison
screenshot needed two seeded candidates on the same job to actually show a
comparison, not a single row. Positioning language is pulled from
BLUEPRINT.md Section A/B and `docs/demo_script.md`'s pitch/closing lines —
there's no "Section 27–29" in this document (that checklist item referenced
stale numbering from the original draft spec, now corrected in the
checklist entry itself).

To rebuild it: recapture screenshots via Playwright (see this session's
approach — `next/dynamic` Monaco needs `.monaco-editor .view-lines` click
+ `keyboard.type`, and client-side `<Link>` navigation, not `page.goto`,
between screens or the Zustand session store resets), regenerate with a
pptxgenjs script, then run this skill's own QA loop: `validate.py`,
convert to PDF via `soffice.py`, `pdftoppm`, and actually look at every
slide — the first render had two real defects (a 7-column step row
bleeding text into itself, and screenshot images overlapping their own
2-line captions) that only visual QA caught, not the schema validator.
This sandbox needed `libreoffice-impress`, `libreoffice-draw`, and
`poppler-utils` installed (`apt-get install`) before conversion worked at
all — `libreoffice-core` alone has no presentation import filter.

## What's not built yet / deliberately out of scope

Auth is P3 per BLUEPRINT.md Section B — don't add it unless explicitly
asked. This is a 2-developer, 36-hour hackathon scope; resist gold-plating.
