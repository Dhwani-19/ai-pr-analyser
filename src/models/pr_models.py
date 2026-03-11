"""Pydantic models for pull request input data."""

from pydantic import BaseModel, Field


class PRData(BaseModel):
    """Normalized pull request data consumed by the orchestration flow."""

    repo: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    pr_number: int = Field(..., ge=1, description="Pull request number")
    files_changed: list[str] = Field(default_factory=list)
    diff: str = Field(default="")
    base_sha: str = Field(default="")
    head_sha: str = Field(default="")
