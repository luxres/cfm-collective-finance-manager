"""Business logic for receipt/event Categories."""
from django.db.models import QuerySet

from ..models import AccountHolder, Category, Event, Receipt
from . import overview


def get_events_categories(collective=None) -> QuerySet[Category]:
    if not collective:
        return Category.objects.none()
    return Category.objects.filter(collective=collective, type="event")


def get_event_categories(collective=None) -> QuerySet[Category]:
    # kept as a separate name for backwards compatibility with forms.py
    return get_events_categories(collective)


def get_receipt_categories(collective=None) -> QuerySet[Category]:
    if not collective:
        return Category.objects.none()
    return Category.objects.filter(collective=collective, type="receipt")


def get_top_level_categories(collective, category_type) -> QuerySet[Category]:
    """Categories with no parent - the root rows shown in the management table."""
    if not collective:
        return Category.objects.none()
    return (
        Category.objects
        .filter(collective=collective, type=category_type, parent__isnull=True)
        .order_by("name")
    )


def get_direct_category_receipts(category: Category):
    """
    Receipts tagged directly to *this exact* category - not rolled up
    through its children. This is what the per-node drill-down (the
    expandable "Details" section) shows for one layer of the tree, as
    opposed to `get_category_receipts` (rolled up through the whole
    subtree), which powers the overview page's header stats.
    """
    if category.type == Category.CategoryType.RECEIPT:
        return Receipt.objects.filter(category=category).order_by("-date")

    if category.type == Category.CategoryType.EVENT:
        events = Event.objects.filter(category=category)
        return Receipt.objects.filter(event__in=events).order_by("-date")

    return Receipt.objects.none()


def get_category_receipts(category: Category):
    """
    Receipts belonging to a category *and all of its sub-categories*
    (direct receipts for receipt categories, or receipts of every event
    in that subtree for event categories) - matches the rollup used by
    `Category.incoming_total`/`outgoing_total`, so the overview page's
    chart always agrees with its own header stats.
    """
    category_ids = category._category_ids_for_totals()

    if category.type == Category.CategoryType.RECEIPT:
        return Receipt.objects.filter(category_id__in=category_ids)

    if category.type == Category.CategoryType.EVENT:
        events = Event.objects.filter(category_id__in=category_ids)
        return Receipt.objects.filter(event__in=events)

    return Receipt.objects.none()


def get_category_tree(collective, category_type, *, excluding=None) -> list[dict]:
    """
    Every category of this type for the collective, in depth-first
    order, each entry annotated with its `depth` (0 = top-level). This
    is the ordering an indented flat `<select>` needs to represent the
    tree without any JS/tree-widget.

    `excluding`: pass a `Category` instance (e.g. the one being edited)
    to leave it and its whole subtree out - used for building `parent`
    choices, since picking itself or a descendant as its own parent
    would create a cycle.
    """
    categories = list(
        Category.objects
        .filter(collective=collective, type=category_type)
        .select_related("parent")
    )

    blocked_ids = set()
    if excluding is not None and excluding.pk:
        blocked_ids = {excluding.pk} | set(excluding.get_descendant_ids())
        categories = [c for c in categories if c.id not in blocked_ids]

    children_by_parent = {}
    for c in categories:
        children_by_parent.setdefault(c.parent_id, []).append(c)

    for siblings in children_by_parent.values():
        siblings.sort(key=lambda c: c.name.lower())

    ordered = []

    def walk(parent_id, depth):
        for c in children_by_parent.get(parent_id, []):
            ordered.append({"category": c, "depth": depth})
            walk(c.id, depth + 1)

    walk(None, 0)

    # Any category whose parent got excluded (e.g. it was a child of the
    # thing we're excluding) already got filtered out above along with
    # its whole subtree, so nothing is orphaned in `ordered`.
    return ordered


def category_choices(collective, category_type, *, excluding=None, include_blank=True) -> list[tuple]:
    """
    (value, label) choices for a plain `forms.ChoiceField` representing
    the category tree as an indented flat list - e.g. "Transport",
    "— Taxi", "— Train". The simplest way to pick from a tree with an
    ordinary dropdown, no JS required.
    """
    if not collective or not category_type:
        return [("", "—")] if include_blank else []

    tree = get_category_tree(collective, category_type, excluding=excluding)

    choices = [("", "—")] if include_blank else []
    choices += [
        (str(node["category"].id), ("— " * node["depth"]) + node["category"].name)
        for node in tree
    ]
    return choices


def category_overview_context(category: Category) -> dict:
    """Header + timeline data for the category overview page."""
    receipts = get_category_receipts(category)
    timeline = overview.build_timeline(overview.receipt_direction_entries(receipts))

    type_label = (
        "Receipt Category" if category.type == Category.CategoryType.RECEIPT
        else "Event Category"
    )

    header = overview.header_context(
        title=category.name,
        type=type_label,
        rows=[
            {"label": "Description", "value": category.description},
            {"label": "Collective", "value": category.collective.name if category.collective else None},
            {"label": "Parent category", "value": category.parent.name if category.parent else None},
        ],
        stats=[
            {"label": "Net", "value": category.balance_total, "class": "fw-bold"},
            {"label": "Incoming", "value": category.incoming_total, "class": "text-success fw-bold"},
            {"label": "Outgoing", "value": category.outgoing_total, "class": "text-danger fw-bold"},
        ],
    )

    return {
        "header": header,
        "charts_empty_message": "No data available yet.",
        **timeline,
    }
