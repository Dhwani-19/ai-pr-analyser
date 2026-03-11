"""Language detection based on file extensions."""

from collections import defaultdict

PYTHON_EXTENSIONS = {".py"}
TYPESCRIPT_EXTENSIONS = {".ts", ".tsx", ".mts", ".cts"}


def detect_languages(files_changed: list[str]) -> dict[str, list[str]]:
    """Group changed files by supported language."""

    result: dict[str, list[str]] = defaultdict(list)

    for file_path in files_changed:
        lower = file_path.lower()
        if any(lower.endswith(ext) for ext in PYTHON_EXTENSIONS):
            result["python"].append(file_path)
        elif any(lower.endswith(ext) for ext in TYPESCRIPT_EXTENSIONS):
            result["typescript"].append(file_path)

    return {"python": result.get("python", []), "typescript": result.get("typescript", [])}
