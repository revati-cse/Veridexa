"""Prompt for challenge_mutation_engine.py — BLUEPRINT.md Feature 8 / Section
J #5. THE core product differentiator: this is what distinguishes Veridexa
from a difficulty slider — the next scenario is written to specifically
probe what the candidate actually got wrong, not just "harder" or "easier".

Claude only returns scenario/instructions/dataset/mutation_reason
(MutatedChallengeAIOutput) — difficulty is backend-assigned by
challenge_mutation_engine.py's adapt_difficulty(), same principle as
challenge_generator.py.
"""

_DIFFICULTY_LABEL = {1: "Basic", 2: "Intermediate", 3: "Advanced"}

SYSTEM_PROMPT = """You mutate the next challenge in a skill-assessment sequence
to specifically probe a candidate's demonstrated weaknesses, while staying
realistic and connected to the same job and business domain as the previous
challenge.

You are given the previous challenge's scenario and required skills, the
candidate's weaknesses from that attempt, and — if one was identified — a
specific skill gap to target along with the concrete concepts the candidate
appears to be missing.

Rules:
- The new scenario must be a DIFFERENT, believable business situation for
  the same job — not a cosmetic reword of the previous one — that
  specifically exercises the target skill gap. If a target skill and
  missing concepts are given, the new dataset must actually contain the
  data issue those concepts require (e.g. if "NULL handling" is a missing
  concept, the new dataset must include rows with NULL values relevant to
  the task, not just mention NULLs in prose).
- If no specific skill gap was identified, design the mutation directly
  around the weaknesses listed, still producing a genuinely different
  scenario rather than a trivial variation.
- `mutation_reason` must be short, specific, and written for the candidate
  to read — reference their actual weaknesses from the previous attempt
  (e.g. "Targeted because your previous submission didn't handle NULL
  customer IDs and didn't deduplicate repeated transactions."). Never
  generic phrasing like "to test your skills further".
- Same dataset rules as challenge generation: valid SQL identifiers
  (letters, digits, underscores only), 5-15 rows per table, simple values
  only (strings, numbers, or null), each row matching its table's column
  count, and the dataset must actually support solving the instructions.
- `required_skills` in your output must only name skills from the given
  list of skills to target — do not invent skills.
"""


def build_user_prompt(
    previous_scenario: str,
    previous_required_skills: list[str],
    weaknesses: list[str],
    target_skill: str | None,
    missing_concepts: list[str],
    job_title: str,
    required_skills: list[str],
    difficulty: int,
) -> str:
    difficulty_label = _DIFFICULTY_LABEL.get(difficulty, str(difficulty))
    lines = [
        f"Job title: {job_title}",
        f"Skills to target in this challenge: {', '.join(required_skills) or '(none specified)'}",
        f"Difficulty: {difficulty} ({difficulty_label})",
        "",
        f"Previous challenge scenario: {previous_scenario}",
        f"Previous challenge's required skills: {', '.join(previous_required_skills) or '(none recorded)'}",
        f"Candidate's weaknesses from that attempt: {'; '.join(weaknesses) if weaknesses else '(none recorded)'}",
    ]

    if target_skill:
        lines.append(f"Specifically target this skill gap: {target_skill}")
        concepts = ", ".join(missing_concepts) if missing_concepts else "(unspecified — infer from the weaknesses above)"
        lines.append(f"Missing concepts to probe: {concepts}")
    else:
        lines.append("No specific skill gap was identified — design the mutation around the weaknesses listed above.")

    lines.append("")
    lines.append(
        "Generate a mutated challenge: a different, realistic business scenario for "
        "the same job that specifically probes the weaknesses above, along with a "
        "runnable SQLite dataset and a mutation_reason explaining why this scenario "
        "was chosen."
    )
    return "\n".join(lines)
