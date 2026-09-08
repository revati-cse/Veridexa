from app.schemas.job import JobRequiredSkill
from app.services.skill_engine import (
    TAXONOMY,
    get_taxonomy,
    normalize_required_skills,
    normalize_skill,
)


def test_exact_canonical_name_passes_through():
    assert normalize_skill("SQL") == "SQL"
    assert normalize_skill("Python") == "Python"


def test_exact_match_is_case_insensitive():
    assert normalize_skill("python") == "Python"
    assert normalize_skill("sql") == "SQL"


def test_known_aliases_map_to_canonical_taxonomy_entries():
    assert normalize_skill("PostgreSQL") == "SQL"
    assert normalize_skill("MySQL") == "SQL"
    assert normalize_skill("mongodb") == "NoSQL"
    assert normalize_skill("Node.js") == "JavaScript"
    assert normalize_skill("scikit learn") == "Scikit-learn"


def test_pandas_and_numpy_are_distinct_taxonomy_entries_not_aliased_to_python():
    # The taxonomy deliberately lists Pandas/NumPy as their own skills, not
    # merged into "Python" — normalization must respect that, not invent a
    # different grouping than what /skills/taxonomy actually serves.
    assert normalize_skill("Pandas") == "Pandas"
    assert normalize_skill("pandas library") == "Pandas"
    assert normalize_skill("NumPy") == "NumPy"


def test_unrecognized_skill_is_returned_trimmed_not_dropped():
    assert normalize_skill("  Some Made Up Skill  ") == "Some Made Up Skill"


def test_every_alias_target_exists_in_the_taxonomy():
    from app.services.skill_engine import _ALIASES

    canonical_names = {skill.name for skill in TAXONOMY}
    for alias, target in _ALIASES.items():
        assert target in canonical_names, f"alias '{alias}' points to '{target}', which is not in TAXONOMY"


def test_get_taxonomy_returns_all_entries():
    assert len(get_taxonomy()) == len(TAXONOMY)
    assert all(skill.category for skill in get_taxonomy())


def test_normalize_required_skills_merges_aliased_duplicates_keeping_highest_importance():
    skills = [
        JobRequiredSkill(skill="MySQL", importance="medium"),
        JobRequiredSkill(skill="PostgreSQL", importance="high"),
        JobRequiredSkill(skill="Python", importance="high"),
    ]
    result = normalize_required_skills(skills)

    assert len(result) == 2
    sql_row = next(s for s in result if s.skill == "SQL")
    assert sql_row.importance == "high"


def test_normalize_required_skills_preserves_first_seen_order():
    skills = [
        JobRequiredSkill(skill="Python", importance="high"),
        JobRequiredSkill(skill="SQL", importance="high"),
        JobRequiredSkill(skill="mysql", importance="low"),
    ]
    result = normalize_required_skills(skills)

    assert [s.skill for s in result] == ["Python", "SQL"]


def test_normalize_required_skills_required_flag_is_true_if_any_instance_required_it():
    skills = [
        JobRequiredSkill(skill="MySQL", importance="low", required=False),
        JobRequiredSkill(skill="PostgreSQL", importance="low", required=True),
    ]
    result = normalize_required_skills(skills)

    assert result[0].required is True
