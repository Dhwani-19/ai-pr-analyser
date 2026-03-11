"""Pydantic models for analyzer outputs."""

from pydantic import BaseModel, Field


class AnalyzerSignals(BaseModel):
    """Signals emitted by language-specific and heuristic analyzers."""

    language: str
    security_score: float = Field(default=0.0, ge=0.0, le=1.0)
    complexity_delta: float = Field(default=0.0, ge=0.0, le=1.0)
    ai_pattern_score: float = Field(default=0.0, ge=0.0, le=1.0)
    architectural_impact: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: list[str] = Field(default_factory=list)
