"""Pydantic models for runtime LLM configuration."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


SUPPORTED_LLM_PROVIDERS = {"openai", "anthropic"}


class LLMConfig(BaseModel):
    """Runtime LLM configuration passed from the web UI into CrewAI."""

    provider: str = Field(..., description="LLM provider slug")
    model: str = Field(..., min_length=1, description="Provider model name")
    api_key: str = Field(..., min_length=1, description="Provider API key")

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_LLM_PROVIDERS:
            raise ValueError(f"Unsupported LLM provider: {value}")
        return normalized

    @field_validator("model", "api_key")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("This field is required.")
        return normalized
