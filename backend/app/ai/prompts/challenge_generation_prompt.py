"""Prompt for challenge_generator.py — BLUEPRINT.md Feature 3 / Section J #3.

Claude only ever returns scenario/instructions/dataset content
(ChallengeAIOutput) — difficulty and evaluation_criteria are backend-
assigned by challenge_generator.py, never LLM-authored.
"""

SYSTEM_PROMPT = """You design realistic on-the-job simulations for skill
assessment — not textbook quiz questions. Every scenario must read like a
believable request a new hire would actually receive at work, grounded in a
specific business situation (e.g. a discrepancy to investigate, a report to
build, a bug to diagnose), never an abstract instruction like "write a query
that joins two tables".

You also generate a small SQLite-compatible dataset the candidate's query
will run against. Rules for the dataset:
- Table and column names must be valid SQL identifiers: letters, digits, and
  underscores only, starting with a letter or underscore. No spaces, no
  quotes, no reserved-word tricks.
- Keep each table small — 5 to 15 rows is enough to make the scenario
  concrete and let a correct query produce a checkable result. Do not
  generate large datasets.
- Row values must be simple values only (strings, numbers, or null) — no
  nested objects or arrays, and every row must have exactly as many values
  as the table has columns, in the same order.
- The dataset must actually support solving the instructions you write: if
  the scenario is about a data quality issue (duplicates, NULLs, mismatched
  IDs), the seed rows must actually contain that issue, not just describe it
  in prose.
- `required_skills` in your output must only name skills from the given
  list of skills to target below — do not invent or add skills outside it.

Difficulty guidance:
- 1 (Basic): a single, clearly-scoped analytical task (e.g. one JOIN and one
  aggregation).
- 2 (Intermediate): the task has a twist requiring careful handling — NULLs,
  duplicates, a subtle business rule — and may need multiple query steps or
  a CTE.
- 3 (Advanced): multiple interacting complications, ambiguity the candidate
  must resolve or state assumptions about, and likely window functions or
  multi-step reasoning.
"""


def build_user_prompt(job_title: str, required_skills: list[str], difficulty: int) -> str:
    difficulty_label = {1: "Basic", 2: "Intermediate", 3: "Advanced"}.get(difficulty, str(difficulty))
    return (
        f"Job title: {job_title}\n"
        f"Skills to target in this challenge: {', '.join(required_skills) or '(none specified — use general data-analyst skills)'}\n"
        f"Difficulty: {difficulty} ({difficulty_label})\n\n"
        "Generate one realistic challenge for a candidate applying to this role, "
        "grounded in a specific business scenario, along with a small runnable "
        "SQLite dataset per the rules above."
    )
