"""
Business logic for Assets and AssetPools (fixed-asset depreciation
tracking): queries scoped to a collective, and the year-by-year
depreciation schedule shown on both overview pages.
"""
from django.db.models import QuerySet
from django.urls import reverse

from ..models import Asset, AssetPool
from . import overview


def get_assets(collective=None) -> QuerySet[Asset]:
    if not collective:
        return Asset.objects.none()
    return Asset.objects.filter(collective=collective).select_related("asset_pool", "receipt")


def get_asset_pools(collective=None) -> QuerySet[AssetPool]:
    if not collective:
        return AssetPool.objects.none()
    return AssetPool.objects.filter(collective=collective)


def asset_depreciation_schedule(asset: Asset) -> list[dict]:
    """
    Year-by-year depreciation for a single asset. Empty for assets
    inside a pool - the pool is depreciated as a whole instead (see
    `asset_pool_depreciation_schedule`).

    Immediate-write-off assets (Sofortabschreibung) are fully expensed
    in their purchase year regardless of `useful_life`, so their
    schedule is always a single row rather than one row per year.
    """
    if asset.asset_pool or not asset.purchase_date:
        return []

    start_year = asset.purchase_date.year

    if asset.depreciation_method == asset.DeprecationMethod.NONE:
        return [{
            "year": start_year,
            "annual_depreciation": asset.annual_depreciation,
            "accumulated_depreciation": asset.accumulated_depreciation(start_year),
            "book_value": asset.book_value(start_year),
        }]

    return [
        {
            "year": start_year + offset,
            "annual_depreciation": asset.annual_depreciation,
            "accumulated_depreciation": asset.accumulated_depreciation(start_year + offset),
            "book_value": asset.book_value(start_year + offset),
        }
        for offset in range(asset.useful_life)
    ]


def asset_pool_depreciation_schedule(pool: AssetPool) -> list[dict]:
    """Year-by-year depreciation for a whole asset pool (Sammelposten)."""
    return [
        {
            "year": pool.acquisition_year + offset,
            "annual_depreciation": pool.annual_depreciation,
            "accumulated_depreciation": pool.accumulated_depreciation(pool.acquisition_year + offset),
            "remaining_value": pool.remaining_value(pool.acquisition_year + offset),
        }
        for offset in range(pool.depreciation_years)
    ]


def asset_overview_context(asset: Asset) -> dict:
    """Header + depreciation schedule for the single-asset overview page."""
    header = overview.header_context(
        title=asset.name,
        type="Asset (GWG)" if asset.is_gwg else "Asset",
        date=asset.purchase_date.strftime("%d. %B %Y") if asset.purchase_date else None,
        rows=[
            {"label": "Collective", "value": asset.collective.name if asset.collective else None},
            {
                "label": "Asset Pool",
                "value": asset.asset_pool.name if asset.asset_pool else "—",
                "url": reverse("asset_pool_overview_page", args=[asset.asset_pool.id]) if asset.asset_pool else None,
            },
            {
                "label": "Receipt",
                "value": f"Receipt #{asset.receipt.id}" if asset.receipt else "—",
                "url": reverse("receipt_overview_page", args=[asset.receipt.id]) if asset.receipt else None,
            },
            {"label": "Depreciation Method", "value": asset.get_depreciation_method_display()},
            {"label": "Useful Life", "value": f"{asset.useful_life} years"},
        ],
        stats=[
            {"label": "Purchase Price", "value": asset.purchase_price, "class": "fw-bold"},
            {
                "label": "Book Value",
                "value": asset.book_value(),
                "class": "text-danger" if asset.fully_depreciated else "text-success",
            },
            {"label": "Annual Depreciation", "value": asset.annual_depreciation, "class": ""},
        ],
    )

    return {
        "header": header,
        "schedule": asset_depreciation_schedule(asset),
    }


def asset_pool_overview_context(pool: AssetPool) -> dict:
    """Header + depreciation schedule + pooled assets for the asset-pool overview page."""
    remaining_value = pool.remaining_value()

    header = overview.header_context(
        title=pool.name,
        type="Asset Pool (Sammelposten)",
        date=str(pool.acquisition_year),
        rows=[
            {"label": "Collective", "value": pool.collective.name if pool.collective else None},
            {"label": "Depreciation Period", "value": f"{pool.depreciation_years} years"},
            {"label": "Assets in Pool", "value": pool.assets.count()},
        ],
        stats=[
            {"label": "Acquisition Cost", "value": pool.acquisition_cost, "class": "fw-bold"},
            {"label": "Annual Depreciation", "value": pool.annual_depreciation, "class": ""},
            {
                "label": "Remaining Value",
                "value": remaining_value,
                "class": "text-success" if remaining_value > 0 else "text-danger",
            },
        ],
    )

    return {
        "header": header,
        "schedule": asset_pool_depreciation_schedule(pool),
        "assets": pool.assets.all(),
    }