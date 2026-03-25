"""Pydantic models for GitHub App web integration."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GitHubInstallation(BaseModel):
    """A GitHub App installation visible to the current user."""

    installation_id: int = Field(..., alias="id")
    account_login: str
    account_type: str


class GitHubRepository(BaseModel):
    """Repository accessible through a selected installation."""

    full_name: str
    owner: str
    name: str
    private: bool = False


class GitHubPullRequest(BaseModel):
    """Lightweight pull request list item for the UI."""

    number: int
    title: str
    state: str
    author_login: str
    head_ref: str
    updated_at: str
