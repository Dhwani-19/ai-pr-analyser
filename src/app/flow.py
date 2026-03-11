"""Flow controller for PR risk analysis orchestration."""

from __future__ import annotations

from crews.pr_risk_crew import run_pr_risk_analysis
from models.pr_models import PRData
from models.report_models import RiskReport
from tools.diff_tools import extract_diff_chunks
from tools.github_tools import fetch_pr_data
from tools.language_detector import detect_languages


class PRRiskFlow:
    """Coordinates PR data intake, analysis, and report generation."""

    def run(self, repo: str, owner: str, pr_number: int) -> RiskReport:
        """Execute full PR risk flow and return final report."""

        pr_data = self.fetch_pr_metadata(repo=repo, owner=owner, pr_number=pr_number)
        language_map = self.detect_language(pr_data)
        self.parse_diff(pr_data)
        return self.run_crew(pr_data, language_map)

    def fetch_pr_metadata(self, repo: str, owner: str, pr_number: int) -> PRData:
        """Fetch PR metadata and unified diff."""

        return fetch_pr_data(repo=repo, owner=owner, pr_number=pr_number)

    def detect_language(self, pr_data: PRData) -> dict[str, list[str]]:
        """Detect changed files by language."""

        return detect_languages(pr_data.files_changed)

    def parse_diff(self, pr_data: PRData) -> None:
        """Parse diff chunks for future tool extension."""

        _ = extract_diff_chunks(pr_data.diff)

    def run_crew(self, pr_data: PRData, language_map: dict[str, list[str]]) -> RiskReport:
        """Run CrewAI orchestration layer and return report."""

        return run_pr_risk_analysis(pr_data=pr_data, language_map=language_map)
