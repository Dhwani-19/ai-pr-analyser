"""Crew definition for PR risk intelligence analysis."""

from __future__ import annotations

import multiprocessing
import os
from queue import Empty
from typing import Any

from agents.ai_pattern_agent import create_ai_pattern_agent, run_ai_pattern_analysis
from agents.python_analyzer_agent import create_python_analyzer_agent, run_python_analysis
from agents.repo_context_agent import create_repo_context_agent, run_repo_context_analysis
from agents.risk_manager_agent import aggregate_risk, create_risk_manager_agent
from agents.typescript_analyzer_agent import create_typescript_analyzer_agent, run_typescript_analysis
from llm.openai_crewai import build_crewai_llm, crewai_enabled
from models.llm_models import LLMConfig
from models.pr_models import PRData
from models.report_models import RiskReport

try:
    from crewai import Crew, Process, Task
except Exception:  # pragma: no cover - optional runtime dependency
    Crew = None
    Process = None
    Task = None


CREWAI_TIMEOUT_NOTE = (
    "Model-assisted analysis exceeded the configured time limit and was stopped. "
    "The report below uses the deterministic risk analyzers only."
)


def _crewai_timeout_seconds() -> int:
    raw_value = os.getenv("CREWAI_TIMEOUT_SECONDS", "90").strip()
    try:
        timeout = int(raw_value)
    except ValueError:
        timeout = 90
    return max(timeout, 10)


def _build_crewai_objects(llm_config: LLMConfig | None = None) -> tuple[Any, list[Any]]:
    llm = build_crewai_llm(llm_config)
    repo_context_agent = create_repo_context_agent(llm=llm)
    python_agent = create_python_analyzer_agent(llm=llm)
    ts_agent = create_typescript_analyzer_agent(llm=llm)
    ai_pattern_agent = create_ai_pattern_agent(llm=llm)
    manager_agent = create_risk_manager_agent(llm=llm)

    return manager_agent, [repo_context_agent, python_agent, ts_agent, ai_pattern_agent]


def _run_crewai_hierarchical(pr_data: PRData, llm_config: LLMConfig | None = None) -> str | None:
    """Run CrewAI orchestration when explicitly enabled."""

    if Crew is None or Task is None or Process is None:
        raise RuntimeError("CrewAI is required when ENABLE_CREWAI is enabled.")

    manager, agents = _build_crewai_objects(llm_config)

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

    crew = Crew(
        agents=agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_agent=manager,
        verbose=False,
    )
    result = crew.kickoff(
        inputs={
            "pr_number": pr_data.pr_number,
            "files_changed": pr_data.files_changed,
            "diff": pr_data.diff,
            "base_sha": pr_data.base_sha,
            "head_sha": pr_data.head_sha,
            "repo": pr_data.repo,
            "owner": pr_data.owner,
        }
    )
    return str(result).strip() or None


def _crewai_worker(
    result_queue: multiprocessing.Queue,
    pr_data_payload: dict[str, Any],
    llm_config_payload: dict[str, Any] | None,
) -> None:
    try:
        pr_data = PRData(**pr_data_payload)
        llm_config = LLMConfig(**llm_config_payload) if llm_config_payload else None
        result_queue.put(
            {
                "status": "ok",
                "result": _run_crewai_hierarchical(pr_data, llm_config),
            }
        )
    except Exception as exc:
        result_queue.put(
            {
                "status": "error",
                "error": str(exc),
            }
        )


def _run_crewai_with_timeout(pr_data: PRData, llm_config: LLMConfig | None = None) -> str | None:
    timeout_seconds = _crewai_timeout_seconds()
    context = multiprocessing.get_context("spawn")
    result_queue: multiprocessing.Queue = context.Queue()
    process = context.Process(
        target=_crewai_worker,
        args=(
            result_queue,
            pr_data.model_dump(),
            llm_config.model_dump() if llm_config else None,
        ),
    )
    process.start()

    try:
        message = result_queue.get(timeout=timeout_seconds)
    except Empty:
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
        return CREWAI_TIMEOUT_NOTE
    finally:
        result_queue.close()
        result_queue.join_thread()

    process.join(timeout=5)

    if message.get("status") == "error":
        raise RuntimeError(message.get("error", "CrewAI execution failed."))

    return message.get("result")


def run_pr_risk_analysis(
    pr_data: PRData,
    language_map: dict[str, list[str]] | None = None,
    llm_config: LLMConfig | None = None,
) -> RiskReport:
    """Run PR risk analysis via multi-agent orchestration and return RiskReport."""

    language_map = language_map or {"python": [], "typescript": []}
    llm_summary = _run_crewai_with_timeout(pr_data, llm_config) if crewai_enabled() else None
    llm_timed_out = llm_summary == CREWAI_TIMEOUT_NOTE

    signals = [
        run_repo_context_analysis(pr_data),
        run_python_analysis(language_map.get("python", []), diff=pr_data.diff),
        run_typescript_analysis(language_map.get("typescript", []), diff=pr_data.diff),
        run_ai_pattern_analysis(pr_data),
    ]
    report = aggregate_risk(signals)
    report.llm_summary = llm_summary
    report.llm_timed_out = llm_timed_out
    return report
