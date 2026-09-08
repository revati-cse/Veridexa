from app.github.dependencies import (
    extract_dependencies,
    parse_package_json,
    parse_pyproject_toml,
    parse_requirements_txt,
)


def test_parse_requirements_txt():
    content = """
        # comment
        pandas==2.2.0
        numpy>=1.26
        -e git+https://example.com/x.git
        requests
    """
    assert parse_requirements_txt(content) == ["pandas", "numpy", "requests"]


def test_parse_package_json():
    content = '{"dependencies": {"react": "^18.0.0"}, "devDependencies": {"typescript": "^5.0.0"}}'
    assert set(parse_package_json(content)) == {"react", "typescript"}


def test_parse_package_json_handles_malformed_json():
    assert parse_package_json("{not valid json") == []


def test_parse_pyproject_toml_pep621():
    content = """
        [project]
        name = "veridexa"
        dependencies = ["pandas>=2.0", "fastapi"]
    """
    assert parse_pyproject_toml(content) == ["pandas", "fastapi"]


def test_parse_pyproject_toml_poetry_excludes_python():
    content = """
        [tool.poetry.dependencies]
        python = "^3.11"
        requests = "^2.31"
    """
    assert parse_pyproject_toml(content) == ["requests"]


def test_extract_dependencies_deduplicates_across_files():
    files = {
        "requirements.txt": "pandas\nrequests\n",
        "sub/requirements.txt": "pandas\nnumpy\n",
        "irrelevant.py": "import pandas",
    }
    assert extract_dependencies(files) == ["pandas", "requests", "numpy"]
