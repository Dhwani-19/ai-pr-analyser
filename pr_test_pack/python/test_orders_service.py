"""Basic tests for PR workflow validation."""

from pr_test_pack.python.orders_service import Order, calculate_total, mark_shipped


def test_calculate_total_only_active_orders() -> None:
    orders = [
        Order(id="a1", amount_cents=100, status="active"),
        Order(id="a2", amount_cents=250, status="draft"),
        Order(id="a3", amount_cents=300, status="active"),
    ]
    assert calculate_total(orders) == 400


def test_mark_shipped_changes_status() -> None:
    shipped = mark_shipped(Order(id="a1", amount_cents=100, status="active"))
    assert shipped.status == "shipped"
