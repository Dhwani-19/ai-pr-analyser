"""Complexity normalization helpers."""


def normalize_complexity_delta(raw_delta: float, baseline: float = 10.0) -> float:
    """Normalize complexity drift to a 0..1 range."""

    if baseline <= 0:
        baseline = 10.0
    normalized = raw_delta / baseline
    return max(0.0, min(1.0, normalized))


def average(values: list[float]) -> float:
    """Compute average and safely handle empty lists."""

    if not values:
        return 0.0
    return sum(values) / len(values)
