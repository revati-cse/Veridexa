"""File-tree filtering rules for github_analyzer.py — BLUEPRINT.md Section I
"File filtering strategy". Keep this list small and obvious; it's a
hackathon-scale allowlist/denylist, not a general-purpose gitignore engine.
"""

EXCLUDED_DIR_SEGMENTS = {
    ".git", "node_modules", "dist", "build", "venv", ".venv", "env",
    "__pycache__", ".next", "target", "vendor", "coverage",
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode", "site-packages",
}

EXCLUDED_FILENAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Cargo.lock",
}

EXCLUDED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp", ".webp",
    ".pdf", ".zip", ".tar", ".gz", ".rar", ".7z",
    ".exe", ".so", ".dll", ".dylib", ".bin", ".class", ".jar",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".mp4", ".mov", ".avi", ".mp3", ".wav",
    ".min.js", ".min.css", ".map", ".lock",
}

# Files worth reading in full for skill evidence.
SOURCE_EXTENSIONS = {
    ".py", ".sql", ".js", ".jsx", ".ts", ".tsx", ".java", ".ipynb",
    ".r", ".go", ".rb", ".php", ".c", ".cpp", ".cs", ".kt", ".scala", ".swift",
}

# Manifest files parsed for dependency-name evidence (app/github/dependencies.py)
# rather than sent to Claude as source code.
DEPENDENCY_FILENAMES = {"requirements.txt", "package.json", "pyproject.toml"}

MIN_FILE_SIZE_BYTES = 50
MAX_FILE_SIZE_BYTES = 15_000
MAX_TREE_ENTRIES = 3000


def extension_of(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    if "." not in name:
        return ""
    return "." + name.rsplit(".", 1)[-1].lower()


def is_excluded(path: str) -> bool:
    segments = path.split("/")
    if any(segment in EXCLUDED_DIR_SEGMENTS for segment in segments[:-1]):
        return True
    filename = segments[-1]
    if filename in EXCLUDED_FILENAMES:
        return True
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in EXCLUDED_EXTENSIONS)
