from uuid import uuid4

from fastapi import APIRouter

from app.schemas import SkillTaxonomyItem
from app.schemas.common import SkillCategory

router = APIRouter(prefix="/skills", tags=["skills"])

# STUB: mirrors supabase/migrations/002_seed_skills.sql so the frontend claim
# picker has real category groupings to render before the DB is wired up in
# Phase 6. Once skill_engine.py reads from Supabase, delete this list and
# query the `skills` table instead — do not let the two fall out of sync
# in the meantime.
_TAXONOMY: list[tuple[str, SkillCategory]] = [
    ("Python", "programming"), ("JavaScript", "programming"), ("TypeScript", "programming"),
    ("Java", "programming"), ("R", "programming"), ("Go", "programming"), ("C++", "programming"),
    ("SQL", "database"), ("NoSQL", "database"), ("Database Design", "database"),
    ("Data Analysis", "data"), ("Data Visualization", "data"), ("Data Cleaning", "data"),
    ("ETL", "data"), ("Excel", "data"), ("Power BI", "data"), ("Tableau", "data"),
    ("Pandas", "data"), ("NumPy", "data"), ("Statistics", "data"), ("A/B Testing", "data"),
    ("Hypothesis Testing", "data"),
    ("Machine Learning", "ai_ml"), ("Deep Learning", "ai_ml"),
    ("Natural Language Processing", "ai_ml"), ("TensorFlow", "ai_ml"),
    ("PyTorch", "ai_ml"), ("Scikit-learn", "ai_ml"),
    ("AWS", "cloud"), ("Azure", "cloud"), ("GCP", "cloud"), ("Docker", "cloud"), ("Kubernetes", "cloud"),
    ("Business Analysis", "business"), ("Project Management", "business"),
    ("Stakeholder Management", "business"),
    ("Communication", "communication"), ("Technical Writing", "communication"),
    ("Presentation", "communication"),
    ("Problem Solving", "problem_solving"), ("Critical Thinking", "problem_solving"),
    ("Git", "tools"), ("API Development", "tools"), ("Testing/QA", "tools"),
]

_STUB_TAXONOMY = [
    SkillTaxonomyItem(id=uuid4(), name=name, category=category) for name, category in _TAXONOMY
]


@router.get("/taxonomy", response_model=list[SkillTaxonomyItem])
async def get_taxonomy() -> list[SkillTaxonomyItem]:
    return _STUB_TAXONOMY
