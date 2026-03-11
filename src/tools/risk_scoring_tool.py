"""Risk score aggregation logic."""

from models.report_models import RiskReport


def build_recommendation(score: int) -> str:
    """Provide recommendation text by risk bucket."""

    if score <= 30:
        return "Standard review is sufficient before merge."
    if score <= 70:
        return "Require focused review on affected critical paths before merge."
    return "Senior engineer review required before merge."


def score_risk(
    security_score: float,
    complexity_score: float,
    ai_pattern_score: float,
    architectural_score: float,
) -> RiskReport:
    """Compute weighted risk score and construct final report model."""

    weighted = (
        0.3 * security_score
        + 0.25 * complexity_score
        + 0.25 * ai_pattern_score
        + 0.2 * architectural_score
    )
    overall_score = int(round(weighted * 100))
    risk_level = RiskReport.level_from_score(overall_score)

    summary = (
        f"Risk level is {risk_level} with strongest signals in security ({security_score:.2f}) "
        f"and complexity ({complexity_score:.2f})."
    )

    return RiskReport(
        overall_score=overall_score,
        risk_level=risk_level,
        security_score=security_score,
        complexity_score=complexity_score,
        ai_pattern_score=ai_pattern_score,
        architectural_score=architectural_score,
        recommendation=build_recommendation(overall_score),
        summary=summary,
    )
