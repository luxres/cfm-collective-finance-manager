"""HTMX ENDPOINTS: fragments used by the asset management page (assets & asset pools)."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from ...forms import AssetForm, AssetPoolForm
from ...models import AccountHolder, Asset, AssetPool
from ...services import assets as asset_services, sorting

ASSET_SORTABLE_COLUMNS = ["id", "name", "purchase_date", "purchase_price", "receipt_id", "useful_life"]
ASSET_POOL_SORTABLE_COLUMNS = ["id", "name", "acquisition_year", "depreciation_years"]


# ---------------------------------------------------------------------
# ASSETS
# ---------------------------------------------------------------------

@login_required
def asset_table_htmx(request, collective_id):
    """HTMX endpoint: sortable asset table for one collective."""
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    assets = asset_services.get_assets(collective)

    sort_state = sorting.build_sort_state(
        request,
        url_name="asset_table_htmx",
        url_args=[collective_id],
        sortable_columns=ASSET_SORTABLE_COLUMNS,
        default_table_id="asset-table",
    )
    assets = assets.order_by(sort_state.sort)

    return render(request, "ledger/asset_management/partials/asset_table.html", {
        "collective": collective,
        "assets": assets,
        "current_sort": sort_state.sort,
        "table_id": sort_state.table_id,
        "sort_links": sort_state.sort_links,
    })


@login_required
def add_asset_htmx(request, collective_id):
    """HTMX endpoint: create-asset modal form."""
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    if request.method == "GET":
        return render(request, "ledger/asset_management/partials/asset_form.html", {
            "form": AssetForm(collective=collective),
            "asset": None,
            "active_collective": collective,
        })

    form = AssetForm(request.POST, collective=collective)

    if not form.is_valid():
        return render(request, "ledger/asset_management/partials/asset_form.html", {
            "form": form,
            "asset": None,
            "active_collective": collective,
        }, status=400)

    asset = form.save(commit=False)
    asset.collective = collective  # system field
    asset.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_asset_htmx(request, asset_id):
    """HTMX endpoint: edit-asset modal form."""
    # TODO permissions
    asset = get_object_or_404(Asset, id=asset_id)

    if request.method == "GET":
        return render(request, "ledger/asset_management/partials/asset_form.html", {
            "form": AssetForm(instance=asset, collective=asset.collective),
            "asset": asset,
            "active_collective": asset.collective,
        })

    form = AssetForm(request.POST, instance=asset, collective=asset.collective)

    if not form.is_valid():
        return render(request, "ledger/asset_management/partials/asset_form.html", {
            "form": form,
            "asset": asset,
            "active_collective": asset.collective,
        }, status=400)

    form.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@require_http_methods(["DELETE"])
@login_required
def delete_asset_htmx(request, asset_id):
    """HTMX endpoint (action): deletes an asset."""
    # TODO check permissions
    asset = get_object_or_404(Asset, id=asset_id)
    asset.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response


# ---------------------------------------------------------------------
# ASSET POOLS
# ---------------------------------------------------------------------

@login_required
def asset_pool_table_htmx(request, collective_id):
    """HTMX endpoint: sortable asset-pool table for one collective."""
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    asset_pools = asset_services.get_asset_pools(collective)

    sort_state = sorting.build_sort_state(
        request,
        url_name="asset_pool_table_htmx",
        url_args=[collective_id],
        sortable_columns=ASSET_POOL_SORTABLE_COLUMNS,
        default_table_id="asset-pool-table",
    )
    asset_pools = asset_pools.order_by(sort_state.sort)

    return render(request, "ledger/asset_management/partials/asset_pool_table.html", {
        "collective": collective,
        "asset_pools": asset_pools,
        "current_sort": sort_state.sort,
        "table_id": sort_state.table_id,
        "sort_links": sort_state.sort_links,
    })


@login_required
def add_asset_pool_htmx(request, collective_id):
    """HTMX endpoint: create-asset-pool modal form."""
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    if request.method == "GET":
        return render(request, "ledger/asset_management/partials/asset_pool_form.html", {
            "form": AssetPoolForm(),
            "asset_pool": None,
            "active_collective": collective,
        })

    form = AssetPoolForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/asset_management/partials/asset_pool_form.html", {
            "form": form,
            "asset_pool": None,
            "active_collective": collective,
        }, status=400)

    asset_pool = form.save(commit=False)
    asset_pool.collective = collective  # system field
    asset_pool.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_asset_pool_htmx(request, asset_pool_id):
    """HTMX endpoint: edit-asset-pool modal form."""
    # TODO permissions
    asset_pool = get_object_or_404(AssetPool, id=asset_pool_id)

    if request.method == "GET":
        return render(request, "ledger/asset_management/partials/asset_pool_form.html", {
            "form": AssetPoolForm(instance=asset_pool),
            "asset_pool": asset_pool,
            "active_collective": asset_pool.collective,
        })

    form = AssetPoolForm(request.POST, instance=asset_pool)

    if not form.is_valid():
        return render(request, "ledger/asset_management/partials/asset_pool_form.html", {
            "form": form,
            "asset_pool": asset_pool,
            "active_collective": asset_pool.collective,
        }, status=400)

    form.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@require_http_methods(["DELETE"])
@login_required
def delete_asset_pool_htmx(request, asset_pool_id):
    """HTMX endpoint (action): deletes an asset pool (its assets are kept, unpooled)."""
    # TODO check permissions
    asset_pool = get_object_or_404(AssetPool, id=asset_pool_id)
    asset_pool.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
