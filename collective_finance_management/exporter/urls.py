from django.urls import path

from .views import htmx, pages

app_name = "exporter"

urlpatterns = [
    # pages
    path("", pages.source_list_page, name="source_list_page"),
    path("<str:source_key>/", pages.source_export_page, name="source_export_page"),

    # htmx
    path("htmx/<str:source_key>/completeness/", htmx.source_completeness_htmx, name="source_completeness_htmx"),
    path("htmx/<str:source_key>/download/", htmx.source_download_htmx, name="source_download_htmx"),
]
