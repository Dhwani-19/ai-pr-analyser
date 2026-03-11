"""Python PR analysis using AST and lightweight heuristics."""

from __future__ import annotations

import ast
import re
from pathlib import Path

from radon.complexity import cc_visit

from models.signal_models import AnalyzerSignals
from tools.complexity_tools import normalize_complexity_delta
from tools.diff_tools import extract_diff_chunks

SUSPICIOUS_IMPORTS = {
    "subprocess",
    "pickle",
    "marshal",
    "os",
    "requests",
}

SECURITY_PATTERNS = ["eval(", "exec(", "shell=True", "yaml.load("]
PYTHON_CONTROL_FLOW_PATTERN = re.compile(r"\b(if|for|while|try|except|with|match|elif)\b")


class _PythonStats(ast.NodeVisitor):
    def __init__(self) -> None:
        self.functions = 0
        self.classes = 0
        self.try_blocks = 0
        self.imports: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self.functions += 1
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self.functions += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:  # noqa: N802
        self.classes += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:  # noqa: N802
        self.try_blocks += 1
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:  # noqa: N802
        for item in node.names:
            self.imports.add(item.name.split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # noqa: N802
        if node.module:
            self.imports.add(node.module.split(".")[0])


def _read_files(file_paths: list[str]) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists() or path.suffix != ".py":
            continue
        try:
            files.append((file_path, path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return files


def _analyze_diff(diff: str, file_paths: list[str] | None = None) -> AnalyzerSignals:
    chunks = extract_diff_chunks(diff)
    target_files = set(file_paths or [])
    python_chunks = [
        chunk
        for chunk in chunks
        if chunk.file_path.endswith(".py") and (not target_files or chunk.file_path in target_files)
    ]

    if not python_chunks:
        return AnalyzerSignals(language="python", notes=["No Python files to analyze"])

    suspicious_import_hits = 0
    security_pattern_hits = 0
    raw_complexity = 0.0
    notes: list[str] = []

    for chunk in python_chunks:
        added_content = "\n".join(chunk.added_lines)
        suspicious_import_hits += len(
            re.findall(r"^\s*(?:from\s+(subprocess|pickle|marshal|os|requests)\b|import\s+(subprocess|pickle|marshal|os|requests)\b)", added_content, re.MULTILINE)
        )
        security_pattern_hits += sum(added_content.count(pattern) for pattern in SECURITY_PATTERNS)
        raw_complexity += len(PYTHON_CONTROL_FLOW_PATTERN.findall(added_content))

    security_score = min(1.0, (suspicious_import_hits * 0.15) + (security_pattern_hits * 0.2))
    complexity_delta = normalize_complexity_delta(raw_complexity, baseline=max(len(python_chunks), 1) * 5)
    notes.append("Analyzed Python diff hunks because local files were unavailable")

    return AnalyzerSignals(
        language="python",
        security_score=security_score,
        complexity_delta=complexity_delta,
        ai_pattern_score=0.0,
        architectural_impact=0.0,
        notes=notes,
    )


def analyze_python_files(file_paths: list[str], diff: str = "") -> AnalyzerSignals:
    """Analyze Python files and produce normalized risk signals."""

    files = _read_files(file_paths)
    if not files:
        if diff:
            return _analyze_diff(diff, file_paths)
        return AnalyzerSignals(language="python", notes=["No Python files to analyze"])

    total_functions = 0
    raw_complexity = 0.0
    suspicious_import_hits = 0
    security_pattern_hits = 0
    notes: list[str] = []

    for file_path, content in files:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            notes.append(f"Syntax issue while parsing {file_path}")
            continue

        stats = _PythonStats()
        stats.visit(tree)

        total_functions += stats.functions
        suspicious = sorted(stats.imports.intersection(SUSPICIOUS_IMPORTS))
        suspicious_import_hits += len(suspicious)
        if suspicious:
            notes.append(f"Suspicious imports in {file_path}: {', '.join(suspicious)}")

        raw_complexity += sum(block.complexity for block in cc_visit(content))
        security_pattern_hits += sum(content.count(pattern) for pattern in SECURITY_PATTERNS)

    security_score = min(1.0, (suspicious_import_hits * 0.15) + (security_pattern_hits * 0.2))
    complexity_delta = normalize_complexity_delta(raw_complexity, baseline=max(total_functions, 1) * 5)

    return AnalyzerSignals(
        language="python",
        security_score=security_score,
        complexity_delta=complexity_delta,
        ai_pattern_score=0.0,
        architectural_impact=0.0,
        notes=notes or [f"Analyzed {len(files)} Python file(s)"],
    )
