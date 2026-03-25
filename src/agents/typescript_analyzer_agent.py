"""TypeScript analyzer agent factory and runner."""

from __future__ import annotations

from typing import Any

from models.signal_models import AnalyzerSignals
from tools.typescript_analysis_tools import analyze_typescript_files

try:
    from crewai import Agent
except Exception:  # pragma: no cover
    Agent = None


def create_typescript_analyzer_agent(tools: list[Any] | None = None, llm: Any | None = None) -> Any:
    """Create TypeScript analyzer CrewAI agent with role metadata."""

    if Agent is None:
        return {
            "role": "TypeScript Analyzer Agent",
            "goal": "Analyze TypeScript structure and unsafe patterns",
            "backstory": "A frontend security engineer expert in Node and API risk.",
            "tools": tools or [],
        }

    return Agent(
        role="TypeScript Analyzer Agent",
        goal="Analyze TypeScript files for complexity, unsafe patterns, and route changes.",
        backstory=(
            "You are a principal JavaScript/TypeScript engineer specializing in runtime safety "
            "and API edge-case resilience."
        ),
        llm=llm,
        tools=tools or [],
        verbose=False,
    )


def run_typescript_analysis(file_paths: list[str], diff: str = "") -> AnalyzerSignals:
    """Run deterministic TypeScript analysis for PR files."""

    return analyze_typescript_files(file_paths, diff=diff)
