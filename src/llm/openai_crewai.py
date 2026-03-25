"""CrewAI LLM configuration helpers."""

from __future__ import annotations

import os
from typing import Any

from models.llm_models import LLMConfig

try:
    from crewai import LLM
except Exception:  # pragma: no cover - optional runtime dependency
    LLM = None


def _normalize_model_name(provider: str, model_name: str) -> str:
    normalized = model_name.strip()
    if not normalized:
        normalized = "gpt-5-mini"
    if "/" not in normalized:
        normalized = f"{provider}/{normalized}"
    return normalized


def build_crewai_llm(config: LLMConfig | None = None) -> Any:
    """Construct a CrewAI LLM configured for the selected provider."""

    if LLM is None:
        raise RuntimeError("CrewAI is not installed. Install dependencies from requirements.txt.")

    config = config or LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "openai"),
        model=os.getenv("OPENAI_MODEL_NAME", "gpt-5-mini"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
    )

    kwargs: dict[str, Any] = {
        "model": _normalize_model_name(config.provider, config.model),
        "api_key": config.api_key,
        "temperature": float(os.getenv("LLM_TEMPERATURE", os.getenv("OPENAI_TEMPERATURE", "0.1"))),
    }

    if config.provider == "openai":
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        organization = os.getenv("OPENAI_ORGANIZATION", "").strip()
        project = os.getenv("OPENAI_PROJECT", "").strip()
    else:
        base_url = os.getenv("ANTHROPIC_BASE_URL", "").strip()
        organization = ""
        project = ""

    if base_url:
        kwargs["base_url"] = base_url

    if organization:
        kwargs["organization"] = organization

    if project:
        kwargs["project"] = project

    max_tokens = os.getenv("LLM_MAX_TOKENS", os.getenv("OPENAI_MAX_TOKENS", "")).strip()
    if max_tokens:
        kwargs["max_tokens"] = int(max_tokens)

    timeout = os.getenv("LLM_TIMEOUT", os.getenv("OPENAI_TIMEOUT", "")).strip()
    if timeout:
        kwargs["timeout"] = float(timeout)

    return LLM(**kwargs)


def crewai_enabled() -> bool:
    """Return True when CrewAI execution is explicitly enabled."""

    return os.getenv("ENABLE_CREWAI", "").strip().lower() in {"1", "true", "yes", "on"}
