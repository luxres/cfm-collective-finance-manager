from django.urls import path

from ..views.pages import categories as category_pages
from ..views.partials import categories as category_htmx

urlpatterns = [
    # pages
    path("categories/", category_pages.category_management_page, name="category_management_page"),
    path("categories/<int:category_id>/overview/", category_pages.category_overview_page, name="category_overview_page"),

    # htmx
    path("htmx/categories/<int:collective_id>/<str:category_type>/add/", category_htmx.add_category_htmx, name="add_category_htmx"),
    path("htmx/categories/<int:category_id>/edit/", category_htmx.edit_category_htmx, name="edit_category_htmx"),
    path("htmx/categories/<int:category_id>/delete/", category_htmx.delete_category_htmx, name="delete_category_htmx"),
    path("htmx/categories/<int:collective_id>/<str:category_type>/category-table/", category_htmx.category_table_htmx, name="category_table_htmx"),
    path("htmx/categories/<int:category_id>/children/", category_htmx.category_children_htmx, name="category_children_htmx"),
]
