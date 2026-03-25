"""Session helpers for the web UI."""

from __future__ import annotations

from typing import Any

from fastapi import Request


SESSION_USER_TOKEN = "github_user_token"
SESSION_USER_LOGIN = "github_user_login"
SESSION_SELECTED_INSTALLATION = "github_installation_id"
SESSION_LLM_PROVIDER = "llm_provider"
SESSION_LLM_MODEL = "llm_model"
SESSION_LLM_API_KEY = "llm_api_key"


def get_session_value(request: Request, key: str, default: Any = None) -> Any:
    """Read a value from session storage."""

    return request.session.get(key, default)


def set_session_value(request: Request, key: str, value: Any) -> None:
    """Write a value into the current session."""

    request.session[key] = value


def clear_auth_session(request: Request) -> None:
    """Remove GitHub authentication state from the session."""

    for key in list(request.session.keys()):
        if key.startswith("github_"):
            request.session.pop(key, None)
