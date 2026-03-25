"""GitHub App OAuth and installation token helpers."""

from __future__ import annotations

import time
from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
import jwt

from app.config import AppSettings
from models.github_models import GitHubInstallation, GitHubPullRequest, GitHubRepository


def create_oauth_state() -> str:
    """Generate a CSRF-resistant OAuth state token."""

    return token_urlsafe(24)


def build_user_oauth_url(settings: AppSettings, state: str) -> str:
    """Create the GitHub authorization URL for the app user flow."""

    query = urlencode(
        {
            "client_id": settings.github_client_id,
            "state": state,
        }
    )
    return f"{settings.github_web_url}/login/oauth/authorize?{query}"


def _build_app_jwt(settings: AppSettings) -> str:
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 540,
        "iss": settings.github_app_id,
    }
    return jwt.encode(payload, settings.github_app_private_key, algorithm="RS256")


def _request(
    method: str,
    url: str,
    *,
    bearer_token: str | None = None,
    json_body: dict | None = None,
    accept: str = "application/vnd.github+json",
) -> dict | list:
    headers = {
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    response = httpx.request(method, url, headers=headers, json=json_body, timeout=30.0)
    response.raise_for_status()
    if not response.content:
        return {}
    return response.json()


def exchange_code_for_user_token(settings: AppSettings, code: str) -> str:
    """Exchange the OAuth callback code for a user access token."""

    response = httpx.post(
        f"{settings.github_web_url}/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token", "").strip()
    if not token:
        raise RuntimeError("GitHub OAuth exchange did not return an access token.")
    return token


def fetch_authenticated_user(settings: AppSettings, user_token: str) -> str:
    """Fetch the current GitHub user login."""

    payload = _request("GET", f"{settings.github_api_url}/user", bearer_token=user_token)
    login = str(payload.get("login", "")).strip()
    if not login:
        raise RuntimeError("Unable to resolve the authenticated GitHub user.")
    return login


def list_user_installations(settings: AppSettings, user_token: str) -> list[GitHubInstallation]:
    """List app installations the current user can access."""

    payload = _request(
        "GET",
        f"{settings.github_api_url}/user/installations",
        bearer_token=user_token,
    )
    installations = []
    for item in payload.get("installations", []):
        account = item.get("account") or {}
        installations.append(
            GitHubInstallation(
                id=item["id"],
                account_login=account.get("login", ""),
                account_type=account.get("type", ""),
            )
        )
    return installations


def create_installation_token(settings: AppSettings, installation_id: int) -> str:
    """Mint a short-lived installation token for repository API calls."""

    app_jwt = _build_app_jwt(settings)
    payload = _request(
        "POST",
        f"{settings.github_api_url}/app/installations/{installation_id}/access_tokens",
        bearer_token=app_jwt,
        json_body={},
    )
    token = str(payload.get("token", "")).strip()
    if not token:
        raise RuntimeError("Failed to create a GitHub installation token.")
    return token


def list_installation_repositories(
    settings: AppSettings,
    installation_token: str,
) -> list[GitHubRepository]:
    """List repositories available to the selected installation."""

    payload = _request(
        "GET",
        f"{settings.github_api_url}/installation/repositories",
        bearer_token=installation_token,
    )
    repos = []
    for item in payload.get("repositories", []):
        owner = (item.get("owner") or {}).get("login", "")
        repos.append(
            GitHubRepository(
                full_name=item.get("full_name", ""),
                owner=owner,
                name=item.get("name", ""),
                private=bool(item.get("private", False)),
            )
        )
    return repos


def list_repository_pull_requests(
    settings: AppSettings,
    installation_token: str,
    owner: str,
    repo: str,
) -> list[GitHubPullRequest]:
    """List open pull requests for a repository."""

    payload = _request(
        "GET",
        f"{settings.github_api_url}/repos/{owner}/{repo}/pulls",
        bearer_token=installation_token,
    )
    pulls = []
    for item in payload:
        user = item.get("user") or {}
        head = item.get("head") or {}
        pulls.append(
            GitHubPullRequest(
                number=item["number"],
                title=item.get("title", ""),
                state=item.get("state", ""),
                author_login=user.get("login", ""),
                head_ref=head.get("ref", ""),
                updated_at=item.get("updated_at", ""),
            )
        )
    return pulls
