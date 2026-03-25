"""Pydantic models for final risk report output."""

from pydantic import BaseModel, Field


class RiskReport(BaseModel):
    """Top-level pull request risk report."""

    overall_score: int = Field(..., ge=0, le=100)
    risk_level: str
    security_score: float = Field(..., ge=0.0, le=1.0)
    complexity_score: float = Field(..., ge=0.0, le=1.0)
    ai_pattern_score: float = Field(..., ge=0.0, le=1.0)
    architectural_score: float = Field(..., ge=0.0, le=1.0)
    recommendation: str
    summary: str
    llm_summary: str | None = None

    @staticmethod
    def level_from_score(score: int) -> str:
        """Map 0..100 score to LOW/MEDIUM/HIGH."""

        if score <= 30:
            return "LOW"
        if score <= 70:
            return "MEDIUM"
        return "HIGH"
