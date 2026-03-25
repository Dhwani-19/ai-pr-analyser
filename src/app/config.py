"""Application configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    return value in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class AppSettings:
    """Configuration required for the GitHub App web flow."""

    session_secret: str
    github_app_id: str
    github_client_id: str
    github_client_secret: str
    github_app_private_key: str
    github_app_name: str
    github_app_install_url: str
    session_https_only: bool = False
    allow_user_supplied_llm_keys: bool = True
    github_api_url: str = "https://api.github.com"
    github_web_url: str = "https://github.com"


def load_settings() -> AppSettings:
    """Load required settings from environment variables."""

    app_name = os.getenv("GITHUB_APP_NAME", "").strip()
    install_url = os.getenv("GITHUB_APP_INSTALL_URL", "").strip()
    if not app_name and not install_url:
        raise RuntimeError(
            "Set GITHUB_APP_NAME or GITHUB_APP_INSTALL_URL to support GitHub App installation."
        )

    if not install_url and app_name:
        install_url = f"https://github.com/apps/{app_name}/installations/new"

    return AppSettings(
        session_secret=_required("SESSION_SECRET"),
        github_app_id=_required("GITHUB_APP_ID"),
        github_client_id=_required("GITHUB_CLIENT_ID"),
        github_client_secret=_required("GITHUB_CLIENT_SECRET"),
        github_app_private_key=_required("GITHUB_APP_PRIVATE_KEY").replace("\\n", "\n"),
        github_app_name=app_name or install_url.rstrip("/").split("/")[-3],
        github_app_install_url=install_url,
        session_https_only=_bool_env("SESSION_HTTPS_ONLY", False),
        allow_user_supplied_llm_keys=_bool_env("ALLOW_USER_SUPPLIED_LLM_KEYS", True),
        github_api_url=os.getenv("GITHUB_API_URL", "https://api.github.com").strip(),
        github_web_url=os.getenv("GITHUB_WEB_URL", "https://github.com").strip(),
    )
