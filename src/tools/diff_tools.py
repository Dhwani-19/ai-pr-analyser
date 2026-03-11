"""Utilities for parsing unified git diffs."""

from dataclasses import dataclass, field


@dataclass
class DiffChunk:
    """Represents a single file's change section in a unified diff."""

    file_path: str
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    hunks: list[str] = field(default_factory=list)


def extract_diff_chunks(diff: str) -> list[DiffChunk]:
    """Parse unified diff text into file-level chunks."""

    chunks: list[DiffChunk] = []
    current: DiffChunk | None = None

    for line in diff.splitlines():
        if line.startswith("diff --git"):
            if current is not None:
                chunks.append(current)
            parts = line.split()
            file_path = parts[3].removeprefix("b/") if len(parts) >= 4 else "unknown"
            current = DiffChunk(file_path=file_path)
            continue

        if current is None:
            continue

        if line.startswith("@@"):
            current.hunks.append(line)
            continue

        if line.startswith("+") and not line.startswith("+++"):
            current.added_lines.append(line[1:])
            continue

        if line.startswith("-") and not line.startswith("---"):
            current.removed_lines.append(line[1:])

    if current is not None:
        chunks.append(current)

    return chunks
