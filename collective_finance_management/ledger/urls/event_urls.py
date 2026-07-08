from django.urls import path

from ..views.pages import events as event_pages
from ..views.partials import events as event_htmx

urlpatterns = [
    # pages
    path("event/", event_pages.event_management_page, name="event_management_page"),
    path("event/<int:event_id>/overview", event_pages.event_overview_page, name="event_overview_page"),

    # htmx
    path("htmx/event/<int:collective_id>/add/", event_htmx.add_event_htmx, name="add_event_htmx"),
    path("htmx/event/<int:event_id>/edit/", event_htmx.edit_event_htmx, name="edit_event_htmx"),
    path("htmx/event/<int:event_id>/delete/", event_htmx.delete_event_htmx, name="delete_event_htmx"),
    path("htmx/event/<int:collective_id>/event-table/", event_htmx.event_table_htmx, name="event_table_htmx"),
]
