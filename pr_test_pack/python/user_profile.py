"""Baseline user profile utilities for PR testing."""

from __future__ import annotations


def normalize_username(raw: str) -> str:
    value = raw.strip().lower()
    value = value.replace(" ", "_")
    return value


def merge_tags(existing: list[str], incoming: list[str]) -> list[str]:
    unique = set(existing)
    unique.update(incoming)
    return sorted(unique)
