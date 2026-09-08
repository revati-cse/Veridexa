"""Shared literal types reused across schema modules.

Keep this file the single place these vocabularies are defined — every
other schema imports from here instead of redeclaring the same Literal.
"""

from typing import Literal

Importance = Literal["high", "medium", "low"]

SkillCategory = Literal[
    "programming",
    "database",
    "data",
    "ai_ml",
    "cloud",
    "business",
    "communication",
    "problem_solving",
    "tools",
]

EvidenceStrength = Literal["none", "weak", "moderate", "strong"]

EvidenceSourceType = Literal["resume", "project", "github", "challenge", "submission"]

ClaimLevel = Literal["beginner", "intermediate", "advanced"]

Difficulty = Literal[1, 2, 3]
