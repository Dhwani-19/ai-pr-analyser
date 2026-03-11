"""Risk manager agent for aggregating analysis signals into final report."""

from __future__ import annotations

from typing import Any

from models.report_models import RiskReport
from models.signal_models import AnalyzerSignals
from tools.complexity_tools import average
from tools.risk_scoring_tool import score_risk

try:
    from crewai import Agent
except Exception:  # pragma: no cover
    Agent = None


def create_risk_manager_agent(tools: list[Any] | None = None) -> Any:
    """Create risk manager CrewAI agent."""

    if Agent is None:
        return {
            "role": "Risk Aggregator Agent",
            "goal": "Aggregate all signals and generate a PR Risk Intelligence Report",
            "backstory": "A pragmatic engineering manager focused on merge safety.",
            "tools": tools or [],
        }

    return Agent(
        role="Risk Aggregator Agent",
        goal="Aggregate analyzer signals, compute risk score, and produce final report.",
        backstory=(
            "You are an engineering risk manager who balances security, complexity, and "
            "architectural blast radius before approving production merges."
        ),
        tools=tools or [],
        verbose=False,
        allow_delegation=True,
    )


def aggregate_risk(signals: list[AnalyzerSignals]) -> RiskReport:
    """Aggregate signal vectors into the final RiskReport."""

    security_score = average([s.security_score for s in signals])
    complexity_score = average([s.complexity_delta for s in signals])
    ai_pattern_score = average([s.ai_pattern_score for s in signals])
    architectural_score = max([s.architectural_impact for s in signals], default=0.0)

    return score_risk(
        security_score=security_score,
        complexity_score=complexity_score,
        ai_pattern_score=ai_pattern_score,
        architectural_score=architectural_score,
    )
