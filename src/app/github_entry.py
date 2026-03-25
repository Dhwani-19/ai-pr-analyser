"""CLI entry point used by GitHub Actions to run PR risk analysis."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure `src` is on path when executed as `python src/app/github_entry.py`.
CURRENT_FILE = Path(__file__).resolve()
SRC_DIR = CURRENT_FILE.parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.flow import PRRiskFlow  # noqa: E402


def _read_event_pr_number() -> int | None:
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path:
        return None

    path = Path(event_path)
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    pr = payload.get("pull_request", {})
    pr_number = pr.get("number")
    return int(pr_number) if pr_number else None


def _resolve_repo_owner() -> tuple[str, str]:
    repository = os.getenv("GITHUB_REPOSITORY", "")
    owner = os.getenv("PR_OWNER", "")
    repo = os.getenv("PR_REPO", "")

    if repository and "/" in repository:
        derived_owner, derived_repo = repository.split("/", 1)
        owner = owner or derived_owner
        repo = repo or derived_repo

    return owner, repo


def _format_security_bucket(score: float) -> str:
    if score <= 0.3:
        return "Low"
    if score <= 0.7:
        return "Medium"
    return "High"


def main() -> int:
    load_dotenv()
    owner, repo = _resolve_repo_owner()
    pr_number_env = os.getenv("PR_NUMBER", "")
    pr_number = int(pr_number_env) if pr_number_env.isdigit() else _read_event_pr_number()

    if not owner or not repo or not pr_number:
        print("Missing PR context. Set GITHUB_REPOSITORY and PR_NUMBER (or GITHUB_EVENT_PATH).")
        return 1

    flow = PRRiskFlow()
    report = flow.run(repo=repo, owner=owner, pr_number=pr_number)

    print("PR Risk Intelligence Report")
    print()
    print(f"Overall Risk Score: {report.overall_score} ({report.risk_level})")
    print()
    print(f"Security Risk: {_format_security_bucket(report.security_score)}")
    print(f"Complexity Drift: +{int(round(report.complexity_score * 100))}%")
    print(f"AI Pattern Score: {report.ai_pattern_score:.2f}")
    print()
    print("Recommendation:")
    print(report.recommendation)
    if report.llm_summary:
        print()
        print("CrewAI / OpenAI Summary:")
        print(report.llm_summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
