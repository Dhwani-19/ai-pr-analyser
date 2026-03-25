"""GitHub PR data fetchers for local CLI and Actions runtime."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from models.pr_models import PRData
from tools.github_api import fetch_pr_data_from_api


def _run_gh_command(args: list[str]) -> str:
    """Run a GitHub CLI command and return stdout."""

    completed = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _load_event_payload() -> dict:
    """Load GitHub event payload when running in GitHub Actions."""

    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path:
        return {}
    path = Path(event_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_pr_data(
    repo: str,
    owner: str,
    pr_number: int,
    github_token: str | None = None,
) -> PRData:
    """Fetch PR metadata and unified diff for CLI, Actions, or web execution."""

    if github_token:
        return fetch_pr_data_from_api(repo=repo, owner=owner, pr_number=pr_number, token=github_token)

    fallback_diff = os.getenv("PR_DIFF", "")
    fallback_files = os.getenv("PR_FILES", "")

    try:
        json_out = _run_gh_command(
            [
                "pr",
                "view",
                str(pr_number),
                "--repo",
                f"{owner}/{repo}",
                "--json",
                "files,baseRefOid,headRefOid",
            ]
        )
        pr_payload = json.loads(json_out)
        diff = _run_gh_command(["pr", "diff", str(pr_number), "--repo", f"{owner}/{repo}"])

        return PRData(
            repo=repo,
            owner=owner,
            pr_number=pr_number,
            files_changed=[f.get("path", "") for f in pr_payload.get("files", [])],
            diff=diff,
            base_sha=pr_payload.get("baseRefOid", ""),
            head_sha=pr_payload.get("headRefOid", ""),
        )
    except Exception:
        payload = _load_event_payload()
        pull_request = payload.get("pull_request", {})
        files = [item.strip() for item in fallback_files.split(",") if item.strip()]
        return PRData(
            repo=repo,
            owner=owner,
            pr_number=pr_number,
            files_changed=files,
            diff=fallback_diff,
            base_sha=pull_request.get("base", {}).get("sha", ""),
            head_sha=pull_request.get("head", {}).get("sha", ""),
        )
