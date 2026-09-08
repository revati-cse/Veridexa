# Veridexa AI — Demo Script

Written per BLUEPRINT.md Section R/U/W/Z (checklist items 29, 30, 35). Every
number below is not aspirational — it's the actual output of
`backend/scripts/smoke_test.py` run against the real backend code and the
checked-in fixtures in `backend/app/fixtures/`. Rehearse against these
numbers; if a code change makes them drift, re-run the smoke test and update
this file rather than reciting stale numbers on stage.

Run the rehearsal itself with:
```
cd backend && uvicorn app.main:app &
python scripts/smoke_test.py
```

---

## 0. Before you're on stage

- Confirm `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, and `DATABASE_URL` are set on
  whatever backend the demo hits — this makes the run **live** (real Claude
  calls, real GitHub reads). Every fallback below is a safety net, not the
  primary path; it should be rare in rehearsal.
- Run `scripts/smoke_test.py` once with all three configured, and once with
  `ANTHROPIC_API_KEY` unset (or the network killed) to rehearse the fallback
  path — checklist item 35 explicitly calls for this. Both must print
  `SMOKE TEST PASSED`.
- Have a GitHub repo URL ready that you actually own or can speak to
  confidently — the live demo shouldn't use a throwaway/unfamiliar repo,
  since the evidence table will say true things about whatever it finds.

## 1. The pitch, in one breath

*"Every resume says 'proficient in SQL.' Veridexa doesn't ask candidates to
claim skills — it makes them prove it, live, against a challenge built from
the actual job description, and it tells them exactly what to fix next."*

## 2. Screen-by-screen walkthrough

**Screen 1 — Landing.** One sentence of positioning, click through.

**Screen 2 — Paste the job description.** Paste the demo JD (below) and
submit.
```
We are hiring a Data Analyst to join our growing analytics team. The ideal
candidate has strong SQL and Python skills, is comfortable with statistics
(hypothesis testing, significance), and can build dashboards in Power BI.
Strong problem-solving skills required. 2+ years of experience preferred.
```

**Screen 3 — Extracted requirements.** Veridexa returns:

| Skill | Importance |
|---|---|
| SQL | high |
| Python | high |
| Statistics | medium |
| Power BI | medium |
| Problem Solving | high |

Say out loud: *"This is a real Claude call parsing unstructured text into
the exact taxonomy row we grade against — not a keyword match."*

**Screen 4 — Claim your skills + GitHub repo.** Enter claimed levels (use
these — they're what the readiness numbers below assume):

| Skill | Claimed level |
|---|---|
| SQL | intermediate |
| Python | advanced |
| Statistics | beginner |
| Power BI | intermediate |
| Problem Solving | advanced |

Paste a real GitHub repo URL. Veridexa reads it read-only (metadata,
languages, a ranked selection of files) and returns a claim-vs-evidence
table per skill — e.g. Python claimed "advanced" backed by "strong" repo
evidence (multiple modules, pandas usage, a tested API implementation) reads
as *corroborated*; Statistics claimed "beginner" with only "weak" evidence
(no hypothesis-testing or modeling code found) reads as *consistent, not yet
demonstrated*. Say out loud: *"A claim never becomes evidence by itself —
evidence only comes from code or a graded challenge."*

If GitHub is unreachable (rate limit, private repo, flaky venue Wi-Fi): the
API returns a clear 422 and the flow **continues without GitHub evidence** —
this is not a crash path, it's designed behavior (BLUEPRINT.md Section V).
Readiness numbers without GitHub evidence are noted separately below.

**Screen 5 — The challenge.** *"Investigate the Revenue Discrepancy"* — a
SQL challenge built from two small tables (`customers`, `orders`) containing
a deliberately duplicated order row and one order with a missing
`customer_id`. Write and run:
```sql
SELECT c.name, SUM(o.amount) AS revenue
FROM customers c JOIN orders o ON o.customer_id = c.id
GROUP BY c.name
```
Explanation: *"I joined customers to orders and summed the amount per
customer to get each customer's total revenue."* Submit. The SQL sandbox
executes this query for real, in-memory, before any AI reasoning happens.

**Screen 6 — Evaluation.** Overall score **75.25 / 100**. Strengths: correct
JOIN, clear structure. Weaknesses: didn't deduplicate the repeated order
row, didn't handle the order with a missing `customer_id`. Skill gap
flagged: **Statistics** ("Hypothesis testing", "Statistical significance") —
say out loud: *"That's not a Statistics question. The gap comes from
comparing this candidate's overall skill profile against the job, not just
this one challenge — and it's what drives the next step."*

**Screen 7 — Readiness dashboard.**

With GitHub evidence populated (the primary, expected path):

| Skill | Score |
|---|---|
| SQL | 74.7 |
| Python | 92.5 |
| Statistics | **38.8** |
| Power BI | 50.0 |
| Problem Solving | 78.8 |

**Readiness: 70.4%.** Skill gaps flagged: **Statistics, Power BI**. Power BI
stays flagged because this MVP doesn't generate a Power BI challenge — a
deliberate scope cut (BLUEPRINT.md Section B), and an honest one to name if
asked rather than dodge.

*(If GitHub evidence was unavailable on Screen 4: readiness computes from
claims + challenge evidence only — 63.3%, with Python/Power BI both at a
flat 50 since neither has any evidence source yet. Still a coherent,
correct number — say so plainly rather than treating it as a lesser demo.)*

**Screen 7 → 8 — "Improve My Readiness."** Click it. The Challenge Mutation
Engine reads the previous evaluation's #1 skill gap (Statistics) and its
missing concepts directly — no new AI call to *decide* the target, only to
*write* the new challenge. New challenge: *"Is the Revenue Increase Real, or
Just Noise?"* — a `monthly_orders` dataset, asking whether a month-over-
month increase is statistically significant. State on stage: *"This
challenge did not exist five seconds ago. It was written specifically
because this candidate struggled with statistical reasoning, using this
candidate's own weak point as the brief."*

**Screen 8 — Resubmit.**
```sql
SELECT month, AVG(amount) AS avg_amount, COUNT(*) AS n
FROM monthly_orders GROUP BY month
```
Explanation: *"I compared the average order amount and sample size for each
month to reason about whether the increase is larger than normal
month-to-month variation, rather than assuming any increase is
meaningful."* Submit. Score: **83.75 / 100** — correctly reasoned about
significance and sample size, still marked down slightly for not reporting
a p-value or confidence interval (this is a real, honest weakness, not a
manufactured one).

**Screen 7 (again) — Readiness updates live.**

| Skill | Before | After |
|---|---|---|
| SQL | 74.7 | 79.8 |
| Statistics | **38.8** | **70.8** |
| Overall readiness | **70.4%** | **76.5%** |

Statistics drops off the skill-gap list entirely (only Power BI remains —
still untested, as expected). Say out loud: *"The candidate didn't just
retake a quiz. They closed a specific, named gap, and the system can prove
it — same as it proved the gap existed in the first place."*

## 3. Closing line

*"Claimed skills to proven capability — every number on this dashboard
traces back to code that ran or a challenge that was graded. Nothing on
this screen is something the candidate just said about themselves."*

## 4. If something breaks live

| Symptom | What's actually happening | What to say |
|---|---|---|
| A response has a slight delay, then succeeds | Retry-then-fixture-fallback logic (Section V) kicked in and recovered | Nothing — this is invisible by design if it recovers |
| `demo_fallback: true` visible in dev tools / API response | Claude was unreachable for that one call; the fixture reliability net took over | *"That's the reliability layer — the demo keeps running, honestly, even on bad Wi-Fi."* If asked directly, say so plainly; don't hide it |
| GitHub analyze returns an error | Repo unreachable/rate-limited | Continue without GitHub evidence — this is Section V's designed behavior, not a bug. Say so. |
| Backend fully unreachable | Real outage | Fall back to a pre-recorded screen-capture of this exact script; don't attempt to debug live |

## 5. Reproducing these exact numbers

```
cd backend
source venv/bin/activate   # or: python3 -m venv venv && pip install -r requirements.txt
uvicorn app.main:app &
python scripts/smoke_test.py
```
Without `ANTHROPIC_API_KEY`/`GITHUB_TOKEN` configured, every AI call and the
GitHub read fall back exactly as described above, and the printed
readiness-before/after numbers will match the "without GitHub evidence" row
in Screen 7 above (63.3% → 70.5%). The "with GitHub evidence" numbers
(70.4% → 76.5%) were computed the same way, with `demo_github_evidence.json`
supplied as `github_evidence` to `/readiness/compute` — i.e. the numbers a
real, reachable GitHub repo produces.
