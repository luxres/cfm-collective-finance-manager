from django.urls import path

from ..views.pages import assets as asset_pages
from ..views.partials import assets as asset_htmx

urlpatterns = [
    # pages
    path("asset/", asset_pages.asset_management_page, name="asset_management_page"),
    path("asset/<int:asset_id>/overview/", asset_pages.asset_overview_page, name="asset_overview_page"),
    path("asset-pool/<int:asset_pool_id>/overview/", asset_pages.asset_pool_overview_page, name="asset_pool_overview_page"),

    # htmx: assets
    path("htmx/asset/<int:collective_id>/asset-table/", asset_htmx.asset_table_htmx, name="asset_table_htmx"),
    path("htmx/asset/<int:collective_id>/add/", asset_htmx.add_asset_htmx, name="add_asset_htmx"),
    path("htmx/asset/<int:asset_id>/edit/", asset_htmx.edit_asset_htmx, name="edit_asset_htmx"),
    path("htmx/asset/<int:asset_id>/delete/", asset_htmx.delete_asset_htmx, name="delete_asset_htmx"),

    # htmx: asset pools
    path("htmx/asset/<int:collective_id>/asset-pool-table/", asset_htmx.asset_pool_table_htmx, name="asset_pool_table_htmx"),
    path("htmx/asset-pool/<int:collective_id>/add/", asset_htmx.add_asset_pool_htmx, name="add_asset_pool_htmx"),
    path("htmx/asset-pool/<int:asset_pool_id>/edit/", asset_htmx.edit_asset_pool_htmx, name="edit_asset_pool_htmx"),
    path("htmx/asset-pool/<int:asset_pool_id>/delete/", asset_htmx.delete_asset_pool_htmx, name="delete_asset_pool_htmx"),
]
