"""TypeScript analysis using tree-sitter-ready heuristics and pattern scanning."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from models.signal_models import AnalyzerSignals
from tools.complexity_tools import normalize_complexity_delta
from tools.diff_tools import extract_diff_chunks

try:
    from tree_sitter import Language, Parser  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency setup
    Language = None
    Parser = None

UNSAFE_PATTERNS = ["eval(", "new Function(", "as any", ": any", "@ts-ignore"]
ROUTE_PATTERN = re.compile(r"\b(app|router)\.(get|post|put|delete|patch|use)\(")
CONTROL_FLOW_PATTERN = re.compile(r"\b(if|for|while|switch|catch)\b")


def _read_files(file_paths: list[str]) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists() or path.suffix not in {".ts", ".tsx", ".mts", ".cts"}:
            continue
        try:
            files.append((file_path, path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return files


def _eslint_findings(file_paths: list[str]) -> tuple[int, list[str]]:
    """Run eslint in JSON mode when available and return issue count + notes."""

    if not file_paths:
        return 0, []

    command = [
        "npx",
        "eslint",
        "--format",
        "json",
        "--no-error-on-unmatched-pattern",
        *file_paths,
    ]
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode not in {0, 1}:
            return 0, []
        payload = json.loads(completed.stdout or "[]")
    except Exception:
        return 0, []

    issue_count = 0
    notes: list[str] = []
    for file_report in payload:
        messages = file_report.get("messages", [])
        if not messages:
            continue
        file_path = file_report.get("filePath", "unknown")
        issue_count += len(messages)
        notes.append(f"ESLint findings in {file_path}: {len(messages)}")
    return issue_count, notes


def _analyze_diff(diff: str, file_paths: list[str] | None = None) -> AnalyzerSignals:
    chunks = extract_diff_chunks(diff)
    target_files = set(file_paths or [])
    ts_suffixes = {".ts", ".tsx", ".mts", ".cts"}
    ts_chunks = [
        chunk
        for chunk in chunks
        if Path(chunk.file_path).suffix in ts_suffixes and (not target_files or chunk.file_path in target_files)
    ]

    if not ts_chunks:
        return AnalyzerSignals(language="typescript", notes=["No TypeScript files to analyze"])

    unsafe_hits = 0
    route_changes = 0
    raw_complexity = 0.0
    notes: list[str] = []

    for chunk in ts_chunks:
        added_content = "\n".join(chunk.added_lines)
        unsafe_in_file = sum(added_content.count(pattern) for pattern in UNSAFE_PATTERNS)
        routes_in_file = len(ROUTE_PATTERN.findall(added_content))
        complexity_in_file = len(CONTROL_FLOW_PATTERN.findall(added_content))

        unsafe_hits += unsafe_in_file
        route_changes += routes_in_file
        raw_complexity += complexity_in_file

        if unsafe_in_file:
            notes.append(f"Unsafe TypeScript constructs in {chunk.file_path}: {unsafe_in_file}")
        if routes_in_file:
            notes.append(f"Route handler changes in {chunk.file_path}: {routes_in_file}")

    security_score = min(1.0, unsafe_hits * 0.2)
    complexity_delta = normalize_complexity_delta(raw_complexity, baseline=max(len(ts_chunks), 1) * 8)
    architectural_impact = min(1.0, route_changes * 0.15)
    notes.append("Analyzed TypeScript diff hunks because local files were unavailable")

    return AnalyzerSignals(
        language="typescript",
        security_score=security_score,
        complexity_delta=complexity_delta,
        ai_pattern_score=0.0,
        architectural_impact=architectural_impact,
        notes=notes,
    )


def analyze_typescript_files(file_paths: list[str], diff: str = "") -> AnalyzerSignals:
    """Analyze TypeScript files for complexity and unsafe patterns."""

    files = _read_files(file_paths)
    if not files:
        if diff:
            return _analyze_diff(diff, file_paths)
        return AnalyzerSignals(language="typescript", notes=["No TypeScript files to analyze"])

    unsafe_hits = 0
    route_changes = 0
    raw_complexity = 0.0
    notes: list[str] = []
    eslint_issue_count, eslint_notes = _eslint_findings(file_paths)
    notes.extend(eslint_notes)

    for file_path, content in files:
        unsafe_in_file = sum(content.count(pattern) for pattern in UNSAFE_PATTERNS)
        routes_in_file = len(ROUTE_PATTERN.findall(content))
        complexity_in_file = len(CONTROL_FLOW_PATTERN.findall(content))

        unsafe_hits += unsafe_in_file
        route_changes += routes_in_file
        raw_complexity += complexity_in_file

        if unsafe_in_file:
            notes.append(f"Unsafe TypeScript constructs in {file_path}: {unsafe_in_file}")
        if routes_in_file:
            notes.append(f"Route handler changes in {file_path}: {routes_in_file}")

    security_score = min(1.0, (unsafe_hits * 0.2) + (eslint_issue_count * 0.01))
    complexity_delta = normalize_complexity_delta(raw_complexity, baseline=max(len(files), 1) * 8)
    architectural_impact = min(1.0, route_changes * 0.15)

    if Parser is None:
        notes.append("tree-sitter parser bindings not configured; used heuristic fallback")

    return AnalyzerSignals(
        language="typescript",
        security_score=security_score,
        complexity_delta=complexity_delta,
        ai_pattern_score=0.0,
        architectural_impact=architectural_impact,
        notes=notes or [f"Analyzed {len(files)} TypeScript file(s)"],
    )
