"""Crew definition for PR risk intelligence analysis."""

from __future__ import annotations

import os
from typing import Any

from agents.ai_pattern_agent import create_ai_pattern_agent, run_ai_pattern_analysis
from agents.python_analyzer_agent import create_python_analyzer_agent, run_python_analysis
from agents.repo_context_agent import create_repo_context_agent, run_repo_context_analysis
from agents.risk_manager_agent import aggregate_risk, create_risk_manager_agent
from agents.typescript_analyzer_agent import create_typescript_analyzer_agent, run_typescript_analysis
from models.pr_models import PRData
from models.report_models import RiskReport

try:
    from crewai import Crew, Process, Task
except Exception:  # pragma: no cover - optional runtime dependency
    Crew = None
    Process = None
    Task = None


def _build_crewai_objects() -> tuple[Any, list[Any]]:
    repo_context_agent = create_repo_context_agent()
    python_agent = create_python_analyzer_agent()
    ts_agent = create_typescript_analyzer_agent()
    ai_pattern_agent = create_ai_pattern_agent()
    manager_agent = create_risk_manager_agent()

    return manager_agent, [repo_context_agent, python_agent, ts_agent, ai_pattern_agent]


def _run_crewai_hierarchical(pr_data: PRData) -> None:
    """Optional CrewAI run for orchestration visibility.

    This run is intentionally non-blocking for report generation; deterministic analyzers
    still compute report signals regardless of LLM availability.
    """

    if Crew is None or Task is None or Process is None:
        return
    if not os.getenv("ENABLE_CREWAI"):
        return

    manager, agents = _build_crewai_objects()

    tasks = [
        Task(
            description=(
                "Analyze repository context and identify critical-module changes for PR "
                f"#{pr_data.pr_number}."
            ),
            expected_output="Architectural risk summary with critical modules and impact level.",
            agent=agents[0],
        ),
        Task(
            description="Analyze Python changes for complexity and security risk signals.",
            expected_output="Python analyzer signal summary with key concerns.",
            agent=agents[1],
        ),
        Task(
            description="Analyze TypeScript changes for unsafe patterns and route impacts.",
            expected_output="TypeScript analyzer signal summary with key concerns.",
            agent=agents[2],
        ),
        Task(
            description="Assess AI-generated code pattern likelihood using PR diff patterns.",
            expected_output="AI pattern likelihood summary and confidence.",
            agent=agents[3],
        ),
    ]

    try:
        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=False,
        )
        crew.kickoff(inputs={"pr_number": pr_data.pr_number, "files_changed": pr_data.files_changed})
    except Exception:
        # CrewAI execution is best-effort for open-source portability.
        return


def run_pr_risk_analysis(pr_data: PRData, language_map: dict[str, list[str]] | None = None) -> RiskReport:
    """Run PR risk analysis via multi-agent orchestration and return RiskReport."""

    language_map = language_map or {"python": [], "typescript": []}

    _run_crewai_hierarchical(pr_data)

    signals = [
        run_repo_context_analysis(pr_data),
        run_python_analysis(language_map.get("python", []), diff=pr_data.diff),
        run_typescript_analysis(language_map.get("typescript", []), diff=pr_data.diff),
        run_ai_pattern_analysis(pr_data),
    ]

    return aggregate_risk(signals)
