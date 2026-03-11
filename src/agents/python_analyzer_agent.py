"""Python analyzer agent factory and runner."""

from __future__ import annotations

from typing import Any

from models.signal_models import AnalyzerSignals
from tools.python_analysis_tools import analyze_python_files

try:
    from crewai import Agent
except Exception:  # pragma: no cover
    Agent = None


def create_python_analyzer_agent(tools: list[Any] | None = None) -> Any:
    """Create Python analyzer CrewAI agent with role metadata."""

    if Agent is None:
        return {
            "role": "Python Analyzer Agent",
            "goal": "Analyze Python AST structure, complexity, and security heuristics",
            "backstory": "A Python static-analysis specialist who flags risk signals quickly.",
            "tools": tools or [],
        }

    return Agent(
        role="Python Analyzer Agent",
        goal="Analyze Python files using AST, complexity heuristics, and security signals.",
        backstory=(
            "You are an experienced Python platform engineer focused on readability, "
            "maintainability, and common exploit patterns in backend services."
        ),
        tools=tools or [],
        verbose=False,
    )


def run_python_analysis(file_paths: list[str], diff: str = "") -> AnalyzerSignals:
    """Run deterministic Python analysis for PR files."""

    return analyze_python_files(file_paths, diff=diff)
