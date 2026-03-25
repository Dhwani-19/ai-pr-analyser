"""Repo context agent definitions and execution helper."""

from __future__ import annotations

from typing import Any

from models.pr_models import PRData
from models.signal_models import AnalyzerSignals

CRITICAL_MODULE_HINTS = ["auth", "payment", "billing", "middleware", "security"]

try:
    from crewai import Agent
except Exception:  # pragma: no cover - optional runtime dependency
    Agent = None


def create_repo_context_agent(tools: list[Any] | None = None, llm: Any | None = None) -> Any:
    """Create CrewAI agent or fallback descriptor."""

    if Agent is None:
        return {
            "role": "Repo Context Agent",
            "goal": "Understand repository architecture and critical module impact",
            "backstory": "A senior architect specializing in dependency boundaries and critical paths.",
            "tools": tools or [],
        }

    return Agent(
        role="Repo Context Agent",
        goal="Understand repository structure and identify critical modules impacted by this PR.",
        backstory=(
            "You are a staff-level architect focused on mapping code changes to architectural "
            "risk, especially around auth, billing, and security boundaries."
        ),
        llm=llm,
        tools=tools or [],
        verbose=False,
    )


def run_repo_context_analysis(pr_data: PRData) -> AnalyzerSignals:
    """Score architectural impact based on changed critical modules."""

    touched = []
    for file_path in pr_data.files_changed:
        lowered = file_path.lower()
        for keyword in CRITICAL_MODULE_HINTS:
            if keyword in lowered:
                touched.append(keyword)

    unique_touched = sorted(set(touched))
    impact = min(1.0, len(unique_touched) * 0.25)

    notes = (
        [f"Critical modules touched: {', '.join(unique_touched)}"]
        if unique_touched
        else ["No critical modules detected in changed files"]
    )

    return AnalyzerSignals(
        language="repo",
        security_score=0.0,
        complexity_delta=0.0,
        ai_pattern_score=0.0,
        architectural_impact=impact,
        notes=notes,
    )
