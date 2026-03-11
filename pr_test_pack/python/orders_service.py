"""Baseline service module for PR risk testing."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Order:
    id: str
    amount_cents: int
    status: str


def calculate_total(orders: list[Order]) -> int:
    """Return total amount for active orders."""

    return sum(order.amount_cents for order in orders if order.status == "active")


def mark_shipped(order: Order) -> Order:
    """Update order status and return the new object."""

    return Order(id=order.id, amount_cents=order.amount_cents, status="shipped")
