from app.github.filters import extension_of, is_excluded


def test_source_files_are_not_excluded():
    for path in ["src/main.py", "queries/report.sql", "app/api.ts", "Model.java"]:
        assert is_excluded(path) is False, path


def test_excluded_directories_are_filtered():
    for path in [
        "node_modules/lodash/index.js",
        ".git/config",
        "dist/bundle.js",
        "build/output.py",
        "venv/lib/site-packages/x.py",
        "__pycache__/module.pyc",
        "coverage/report.html",
    ]:
        assert is_excluded(path) is True, path


def test_lockfiles_are_excluded():
    for path in ["package-lock.json", "backend/poetry.lock", "yarn.lock"]:
        assert is_excluded(path) is True, path


def test_binary_and_media_extensions_are_excluded():
    for path in ["logo.png", "video.mp4", "font.woff2", "archive.zip", "app.min.js"]:
        assert is_excluded(path) is True, path


def test_extension_of():
    assert extension_of("src/main.py") == ".py"
    assert extension_of("README") == ""
    assert extension_of("a/b/c.test.ts") == ".ts"
