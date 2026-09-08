from app.github.selection import select_files_for_analysis


def _entry(path: str, size: int = 500) -> dict:
    return {"path": path, "size": size, "type": "blob"}


def test_relevant_extension_files_rank_above_irrelevant_ones():
    tree = [
        _entry("src/analysis.py"),
        _entry("src/scratch.rb"),
    ]
    source_files, _ = select_files_for_analysis(
        tree, claimed_skills=["Python"], required_skills=[], limit=10
    )

    paths = [f["path"] for f in source_files]
    assert paths.index("src/analysis.py") < paths.index("src/scratch.rb")


def test_excluded_and_non_source_files_are_never_selected():
    tree = [
        _entry("node_modules/lib/index.js"),
        _entry("README.md"),
        _entry("logo.png", size=10_000),
        _entry("src/main.py"),
    ]
    source_files, _ = select_files_for_analysis(tree, [], [], limit=10)

    paths = {f["path"] for f in source_files}
    assert paths == {"src/main.py"}


def test_dependency_files_are_returned_separately_from_source_files():
    tree = [
        _entry("requirements.txt", size=200),
        _entry("nested/requirements.txt", size=200),
        _entry("src/main.py"),
    ]
    source_files, dependency_files = select_files_for_analysis(tree, [], [], limit=10)

    assert {f["path"] for f in source_files} == {"src/main.py"}
    dep_paths = [f["path"] for f in dependency_files]
    assert "requirements.txt" in dep_paths
    # root-level manifest preferred over a nested one when capped
    assert dep_paths[0] == "requirements.txt"


def test_limit_is_respected():
    tree = [_entry(f"src/file_{i}.py") for i in range(30)]
    source_files, _ = select_files_for_analysis(tree, [], [], limit=5)

    assert len(source_files) == 5


def test_empty_or_oversized_files_are_deprioritized_not_excluded():
    tree = [
        _entry("src/tiny.py", size=1),
        _entry("src/normal.py", size=500),
        _entry("src/huge.py", size=50_000),
    ]
    source_files, _ = select_files_for_analysis(tree, [], [], limit=10)

    paths = [f["path"] for f in source_files]
    assert paths[0] == "src/normal.py"
    assert set(paths) == {"src/tiny.py", "src/normal.py", "src/huge.py"}


def test_test_directories_are_deprioritized_not_excluded():
    tree = [
        _entry("tests/test_main.py"),
        _entry("src/main.py"),
    ]
    source_files, _ = select_files_for_analysis(tree, [], [], limit=10)

    paths = [f["path"] for f in source_files]
    assert paths == ["src/main.py", "tests/test_main.py"]
