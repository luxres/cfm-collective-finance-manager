"""
Shared building blocks for the "*_overview" pages (account, category,
event, receipt): the income/expense/net timeline behind the charts tab,
and the header card (title/type/date/rows/stats).
"""
from collections import defaultdict
from typing import Iterable, Optional, Tuple

Entry = Tuple[object, Optional[str], object]  # (date, "in"|"out"|None, amount)


def build_timeline(entries: Iterable[Entry]) -> dict:
    """
    entries: iterable of (date, direction, amount) where direction is
    'in' or 'out'. Returns the dict every overview view needs for its
    charts tab.
    """
    income_map = defaultdict(float)
    expense_map = defaultdict(float)

    for date, direction, amount in entries:
        if not date:
            continue
        day = date.strftime("%Y-%m-%d")
        amount = float(amount or 0)
        if direction == "in":
            income_map[day] += amount
        elif direction == "out":
            expense_map[day] += amount

    labels = sorted(set(income_map.keys()) | set(expense_map.keys()))
    income_data = [income_map[d] for d in labels]
    expense_data = [expense_map[d] for d in labels]
    net_data = [income_map[d] - expense_map[d] for d in labels]

    return {
        "chart_labels": labels,
        "income_data": income_data,
        "expense_data": expense_data,
        "net_data": net_data,
        "total_income": sum(income_data),
        "total_expense": sum(expense_data),
    }


def header_context(*, title, type=None, date=None, rows=None, stats=None) -> dict:
    return {
        "title": title,
        "type": type,
        "date": date,
        "rows": rows or [],
        "stats": stats or [],
    }


def receipt_direction_entries(receipts) -> Iterable[Entry]:
    """
    Shared (date, in/out, amount) mapping for anything built from a
    Receipt queryset (category & event overviews both need this).
    """
    from ..models import Receipt

    return (
        (
            r.date,
            "in" if r.direction == Receipt.Direction.INGOING
            else "out" if r.direction == Receipt.Direction.OUTGOING
            else None,
            r.amount,
        )
        for r in receipts
    )
