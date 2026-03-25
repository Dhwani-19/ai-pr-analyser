"""GitHub REST API fetchers for web requests."""

from __future__ import annotations

import httpx

from models.pr_models import PRData


def fetch_pr_data_from_api(repo: str, owner: str, pr_number: int, token: str) -> PRData:
    """Fetch PR metadata and unified diff using the GitHub REST API."""

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    diff_headers = dict(headers)
    diff_headers["Accept"] = "application/vnd.github.v3.diff"

    pr_response = httpx.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=headers,
        timeout=30.0,
    )
    pr_response.raise_for_status()
    pr_payload = pr_response.json()

    files_response = httpx.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        headers=headers,
        timeout=30.0,
    )
    files_response.raise_for_status()
    files_payload = files_response.json()

    diff_response = httpx.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=diff_headers,
        timeout=30.0,
    )
    diff_response.raise_for_status()

    return PRData(
        repo=repo,
        owner=owner,
        pr_number=pr_number,
        files_changed=[item.get("filename", "") for item in files_payload],
        diff=diff_response.text,
        base_sha=(pr_payload.get("base") or {}).get("sha", ""),
        head_sha=(pr_payload.get("head") or {}).get("sha", ""),
    )
