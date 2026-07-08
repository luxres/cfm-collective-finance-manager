"""PAGES: asset management, and the single-asset / single-pool overviews."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...models import Asset, AssetPool
from ...services import access, assets as asset_services, collectives


@login_required
def asset_management_page(request):
    """PAGE: asset & asset-pool tabs for the active collective."""
    user_collectives = access.get_user_collectives(request.user)
    active_collective = collectives.resolve_active_collective(
        request.user, request.GET.get("collective"), user_collectives,
    )

    return render(request, "ledger/asset_management/asset_main.html", {
        "collectives": user_collectives,
        "active_collective": active_collective,
    })


@login_required
def asset_overview_page(request, asset_id):
    """PAGE: purchase details and depreciation schedule for a single asset."""
    asset = get_object_or_404(Asset, id=asset_id)
    if not access.can_access_account_holder(request.user, asset.collective):
        return HttpResponse("Not allowed", status=403)

    context = asset_services.asset_overview_context(asset)

    return render(request, "ledger/asset_management/asset_overview.html", {
        "asset": asset,
        **context,
    })


@login_required
def asset_pool_overview_page(request, asset_pool_id):
    """PAGE: pooled assets and depreciation schedule for a single asset pool."""
    asset_pool = get_object_or_404(AssetPool, id=asset_pool_id)
    if not access.can_access_account_holder(request.user, asset_pool.collective):
        return HttpResponse("Not allowed", status=403)

    context = asset_services.asset_pool_overview_context(asset_pool)

    return render(request, "ledger/asset_management/asset_pool_overview.html", {
        "asset_pool": asset_pool,
        **context,
    })
