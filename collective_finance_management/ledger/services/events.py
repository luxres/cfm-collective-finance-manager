"""Business logic for Events."""
from django.db.models import QuerySet

from ..models import Event
from . import overview


def get_events(collective=None) -> QuerySet[Event]:
    if not collective:
        return Event.objects.none()
    return Event.objects.filter(collective=collective).order_by("-start_date")


def event_overview_context(event: Event) -> dict:
    """Header + timeline data for the event overview page."""
    receipts = event.receipts.all()
    timeline = overview.build_timeline(overview.receipt_direction_entries(receipts))

    header = overview.header_context(
        title=event.name,
        type="Event",
        date=f"{event.start_date:%d. %B %Y} → {event.end_date:%d. %B %Y}",
        rows=[
            {"label": "Responsible", "value": event.responsible_holder.name if event.responsible_holder else None},
            {"label": "Collective", "value": event.collective.name if event.collective else None},
        ],
        stats=[
            {"label": "Net", "value": event.balance_total, "class": ""},
            {"label": "Incoming", "value": event.incoming_total, "class": "text-success fw-bold"},
            {"label": "Outgoing", "value": event.outgoing_total, "class": "text-danger fw-bold"},
        ],
    )

    return {
        "header": header,
        "charts_empty_message": "No receipts yet for this event — charts will appear once there is data.",
        **timeline,
    }
