"""skill_engine service — BLUEPRINT.md Feature 2.

Owns the canonical skill taxonomy (single source of truth — mirrors
supabase/migrations/002_seed_skills.sql) and a lightweight alias ->
canonical-name normalization map. ~40 skills, deliberately not a full
ontology: aliases map common synonyms (e.g. "PostgreSQL", "Postgres") onto
one of the taxonomy's own entries — they never invent a target that isn't
already in TAXONOMY.
"""

from dataclasses import dataclass

from app.schemas.common import SkillCategory
from app.schemas.job import JobRequiredSkill

_IMPORTANCE_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass(frozen=True)
class TaxonomySkill:
    name: str
    category: SkillCategory


TAXONOMY: list[TaxonomySkill] = [
    TaxonomySkill(name, category)
    for name, category in [
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
]

_CANONICAL_BY_LOWER = {skill.name.lower(): skill.name for skill in TAXONOMY}

# Free-text synonym (lowercase) -> canonical taxonomy name. Every target here
# must already exist in TAXONOMY above — this map only merges spellings and
# specific-implementation names onto an existing entry, it never introduces
# a new canonical skill.
_ALIASES: dict[str, str] = {
    # database
    "mysql": "SQL", "postgresql": "SQL", "postgres": "SQL", "sql server": "SQL",
    "sqlite": "SQL", "t-sql": "SQL", "tsql": "SQL", "pl/sql": "SQL", "mssql": "SQL",
    "oracle sql": "SQL", "oracle db": "SQL",
    "mongodb": "NoSQL", "dynamodb": "NoSQL", "cassandra": "NoSQL", "redis": "NoSQL",
    "nosql databases": "NoSQL",
    "data modeling": "Database Design", "database schema design": "Database Design",
    "db design": "Database Design",
    # programming
    "js": "JavaScript", "node": "JavaScript", "node.js": "JavaScript", "nodejs": "JavaScript",
    "es6": "JavaScript", "vanilla javascript": "JavaScript",
    "ts": "TypeScript",
    "golang": "Go",
    "c plus plus": "C++", "cpp": "C++",
    "python scripting": "Python", "python programming": "Python",
    # data
    "data analytics": "Data Analysis", "analytics": "Data Analysis",
    "dashboards": "Data Visualization", "data viz": "Data Visualization", "charts": "Data Visualization",
    "data wrangling": "Data Cleaning", "data munging": "Data Cleaning",
    "extract transform load": "ETL",
    "excel spreadsheets": "Excel", "microsoft excel": "Excel", "vlookup": "Excel",
    "powerbi": "Power BI", "power-bi": "Power BI",
    "ab testing": "A/B Testing", "a/b tests": "A/B Testing",
    "significance testing": "Hypothesis Testing", "statistical significance": "Hypothesis Testing",
    "pandas library": "Pandas",
    "numpy arrays": "NumPy",
    # ai/ml
    "ml": "Machine Learning",
    "dl": "Deep Learning", "neural networks": "Deep Learning",
    "nlp": "Natural Language Processing",
    "sklearn": "Scikit-learn", "scikit learn": "Scikit-learn",
    "tensorflow.js": "TensorFlow",
    "pytorch lightning": "PyTorch",
    # cloud
    "amazon web services": "AWS",
    "google cloud": "GCP", "google cloud platform": "GCP",
    "microsoft azure": "Azure",
    "containers": "Docker", "containerization": "Docker",
    "k8s": "Kubernetes",
    # tools
    "version control": "Git", "github": "Git", "gitlab": "Git",
    "rest api": "API Development", "restful api": "API Development", "api design": "API Development",
    "unit testing": "Testing/QA", "qa": "Testing/QA", "quality assurance": "Testing/QA",
    "test automation": "Testing/QA",
    # business / communication / problem solving
    "agile": "Project Management", "scrum": "Project Management", "project mgmt": "Project Management",
    "business requirements analysis": "Business Analysis",
    "stakeholder engagement": "Stakeholder Management",
    "communication skills": "Communication", "verbal communication": "Communication",
    "written communication": "Communication",
    "documentation": "Technical Writing",
    "presentations": "Presentation", "public speaking": "Presentation",
    "problem-solving": "Problem Solving", "analytical thinking": "Problem Solving",
    "critical-thinking": "Critical Thinking",
}


def get_taxonomy() -> list[TaxonomySkill]:
    return TAXONOMY


def normalize_skill(raw: str) -> str:
    """Best-effort normalize a free-text skill name to the taxonomy's
    canonical form (exact match first, then alias lookup). An unrecognized
    skill is returned trimmed but otherwise unchanged — still shown to the
    user, just not taxonomy-backed."""
    key = raw.strip().lower()
    if not key:
        return raw.strip()
    if key in _CANONICAL_BY_LOWER:
        return _CANONICAL_BY_LOWER[key]
    if key in _ALIASES:
        return _ALIASES[key]
    return raw.strip()


def normalize_required_skills(skills: list[JobRequiredSkill]) -> list[JobRequiredSkill]:
    """Normalizes each skill's name and merges duplicates that normalize to
    the same canonical skill (e.g. a JD mentioning both "MySQL" and
    "PostgreSQL" would otherwise produce two "SQL" rows). Keeps the highest
    importance and `required=True` if any instance required it; preserves
    first-seen order."""
    merged: dict[str, JobRequiredSkill] = {}
    order: list[str] = []

    for skill in skills:
        canonical = normalize_skill(skill.skill)
        key = canonical.lower()
        if key not in merged:
            merged[key] = JobRequiredSkill(skill=canonical, importance=skill.importance, required=skill.required)
            order.append(key)
            continue

        existing = merged[key]
        importance = (
            skill.importance
            if _IMPORTANCE_RANK[skill.importance] > _IMPORTANCE_RANK[existing.importance]
            else existing.importance
        )
        merged[key] = JobRequiredSkill(
            skill=canonical, importance=importance, required=existing.required or skill.required
        )

    return [merged[key] for key in order]
