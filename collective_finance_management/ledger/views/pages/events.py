"""PAGES: event management & the single-event overview."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...models import Event
from ...services import access, collectives, events as event_services


@login_required
def event_management_page(request):
    """PAGE: event table for the active collective, with a collective switcher."""
    user_collectives = access.get_user_collectives(request.user)
    active_collective = collectives.resolve_active_collective(
        request.user, request.GET.get("collective"), user_collectives,
    )

    return render(request, "ledger/event_management/event_main.html", {
        "collectives": user_collectives,
        "active_collective": active_collective,
    })


@login_required
def event_overview_page(request, event_id):
    """PAGE: totals, dates and charts for a single event."""
    event = get_object_or_404(Event, id=event_id)
    if not access.can_access_account_holder(request.user, event.collective):
        return HttpResponse("Not allowed", status=403)

    context = event_services.event_overview_context(event)

    return render(request, "ledger/event_management/event_overview.html", {
        "event": event,
        **context,
    })
