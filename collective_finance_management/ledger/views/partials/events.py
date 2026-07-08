"""HTMX ENDPOINTS: fragments used by the event management page."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from ...forms import EventForm
from ...models import AccountHolder, Event
from ...services import access, sorting

SORTABLE_COLUMNS = ["id", "name", "start_date", "end_date"]


@login_required
def event_table_htmx(request, collective_id):
    """HTMX endpoint: sortable, optionally category-filtered event table."""
    # TODO permission checks
    collective = get_object_or_404(AccountHolder, id=collective_id)

    events = Event.objects.filter(collective=collective)

    category_id = request.GET.get("category_id")
    if category_id:
        events = events.filter(category_id=category_id)

    sort_state = sorting.build_sort_state(
        request,
        url_name="event_table_htmx",
        url_args=[collective_id],
        sortable_columns=SORTABLE_COLUMNS,
        default_table_id="event-table",
    )
    events = events.order_by(sort_state.sort)

    return render(request, "ledger/event_management/partials/event_table.html", {
        "collective": collective,
        "events": events,
        "current_sort": sort_state.sort,
        "table_id": sort_state.table_id,
        "sort_links": sort_state.sort_links,
    })


@login_required
def add_event_htmx(request, collective_id):
    """HTMX endpoint: create-event modal form."""
    collective = get_object_or_404(AccountHolder, id=collective_id)

    if request.method == "GET":
        form = EventForm(collective=collective, initial={"collective": collective})
        return render(request, "ledger/event_management/partials/event_form.html", {
            "form": form,
            "event": None,
            "collective": collective,
        })

    form = EventForm(request.POST, collective=collective)

    if not form.is_valid():
        return render(request, "ledger/event_management/partials/event_form.html", {
            "form": form,
            "event": None,
            "collective": collective,
        }, status=400)

    event = form.save(commit=False)
    event.collective = collective  # system field
    event.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_event_htmx(request, event_id):
    """HTMX endpoint: edit-event modal form."""
    event = get_object_or_404(Event, id=event_id)

    if not access.can_access_account_holder(request.user, event.collective):
        return HttpResponse("Not allowed", status=403)

    if request.method == "GET":
        form = EventForm(instance=event, collective=event.collective)
        return render(request, "ledger/event_management/partials/event_form.html", {
            "form": form,
            "event": event,
            "collective": event.collective,
        })

    form = EventForm(request.POST, instance=event, collective=event.collective)

    if not form.is_valid():
        return render(request, "ledger/event_management/partials/event_form.html", {
            "form": form,
            "event": event,
            "collective": event.collective,
        }, status=400)

    form.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@require_http_methods(["DELETE"])
@login_required
def delete_event_htmx(request, event_id):
    """HTMX endpoint (action): deletes an event, refused if it has transactions."""
    event = get_object_or_404(Event, id=event_id)

    # TODO check permissions

    if not event.can_delete:
        return HttpResponseBadRequest(
            "This event cannot be deleted because it has transactions."
        )

    event.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
