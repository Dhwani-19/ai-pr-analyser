"""AI-generated code pattern detection agent."""

from __future__ import annotations

import re
from typing import Any

from models.pr_models import PRData
from models.signal_models import AnalyzerSignals

try:
    from crewai import Agent
except Exception:  # pragma: no cover
    Agent = None

GENERIC_VAR_PATTERN = re.compile(r"\b(data|temp|value|result|item|obj|foo|bar)\b")
VERBOSE_COMMENT_PATTERN = re.compile(r"^\s*(#|//).{90,}$", re.MULTILINE)
REPETITIVE_BLOCK_PATTERN = re.compile(r"(if\s*\(.+\)\s*\{[^}]+\}){2,}", re.DOTALL)
EDGE_CASE_SIGNAL_PATTERN = re.compile(r"\b(None|null|undefined|except|catch)\b")


def create_ai_pattern_agent(tools: list[Any] | None = None) -> Any:
    """Create AI pattern detection CrewAI agent."""

    if Agent is None:
        return {
            "role": "AI Pattern Detection Agent",
            "goal": "Detect signs of AI-generated code and missing edge-case handling",
            "backstory": "A reviewer who can spot synthetic coding patterns quickly.",
            "tools": tools or [],
        }

    return Agent(
        role="AI Pattern Detection Agent",
        goal=(
            "Detect AI-generated code patterns like repetitive structures, generic naming, "
            "overly verbose comments, and missing edge-case handling."
        ),
        backstory=(
            "You are an engineer who studies AI-assisted coding output quality and consistently "
            "flags low-context changes that require deeper human scrutiny."
        ),
        tools=tools or [],
        verbose=False,
    )


def run_ai_pattern_analysis(pr_data: PRData) -> AnalyzerSignals:
    """Heuristic AI pattern analysis over PR diff text."""

    diff = pr_data.diff or ""
    generic_var_hits = len(GENERIC_VAR_PATTERN.findall(diff))
    verbose_comment_hits = len(VERBOSE_COMMENT_PATTERN.findall(diff))
    repetitive_hits = len(REPETITIVE_BLOCK_PATTERN.findall(diff))

    edge_case_tokens = len(EDGE_CASE_SIGNAL_PATTERN.findall(diff))
    missing_edge_case_penalty = 0.25 if edge_case_tokens == 0 and len(diff) > 300 else 0.0

    score = min(
        1.0,
        generic_var_hits * 0.02 + verbose_comment_hits * 0.08 + repetitive_hits * 0.2 + missing_edge_case_penalty,
    )

    notes = [
        f"Generic variable usage hits: {generic_var_hits}",
        f"Verbose comment hits: {verbose_comment_hits}",
        f"Repetitive structure hits: {repetitive_hits}",
    ]
    if missing_edge_case_penalty > 0:
        notes.append("Potential missing edge-case checks detected")

    return AnalyzerSignals(
        language="ai-pattern",
        security_score=0.0,
        complexity_delta=0.0,
        ai_pattern_score=score,
        architectural_impact=0.0,
        notes=notes,
    )
