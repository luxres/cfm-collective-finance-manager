from django.urls import path

from ..views.pages import external_parties as external_party_pages
from ..views.partials import external_parties as external_party_htmx

urlpatterns = [
    # pages
    path("external-party/", external_party_pages.external_parties_management_page, name="external_parties_management_page"),

    # htmx
    path("htmx/external-party/add/", external_party_htmx.add_external_party_htmx, name="add_external_party_htmx"),
    path("htmx/external-party/<int:party_id>/delete/", external_party_htmx.delete_external_party_htmx, name="delete_external_party_htmx"),
    path("htmx/external-party/table/", external_party_htmx.external_party_table_htmx, name="external_party_table_htmx"),
]
