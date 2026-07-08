"""
Anlagenverzeichnis / AVEÜR (AfA schedule) export for a single Verein.

Companion to `euer.py`: depreciable fixed assets (`Asset`/`AssetPool`)
have their purchase amount excluded from the EÜR's cash-flow rows for
the year they're bought (see `EuerVereinSource._capitalized_amount`)
and are deducted via AfA instead, spread over their useful life. This
source produces that AfA schedule for one collective/year - one row
per asset (or per pool, for pooled assets) that has depreciation
activity in that year.

GWG assets that were immediately written off (Sofortabschreibung) are
still listed here, for their purchase year only, purely for the
Anlagenverzeichnis's record-keeping convention - they have no further
AfA after that, since their full cost was already deducted as a normal
expense in `euer.py`'s cash-flow rows, not here.
"""
from __future__ import annotations

from ledger.models import Asset, AssetPool

from ..interfaces import DataSourceProvider, ExportColumn
from ._shared import CollectiveYearParamsForm


class AfaAnlagenSource(DataSourceProvider):
    key = "afa_anlagen_verein"
    label = "Anlagenverzeichnis / AVEÜR – AfA (Verein)"
    description = (
        "AfA (Absetzung für Abnutzung) schedule for one Verein and year: "
        "one row per asset or asset pool with depreciation activity that "
        "year - the deductions that replace the capitalized purchase "
        "amounts excluded from the EÜR cash-flow export."
    )

    def get_param_form_class(self):
        return CollectiveYearParamsForm

    def get_columns(self, user, cleaned_params):
        return [
            ExportColumn("type", "Art", "string"),
            ExportColumn("name", "Bezeichnung", "string"),
            ExportColumn("acquisition_date", "Anschaffungsdatum", "date"),
            ExportColumn("acquisition_cost", "Anschaffungskosten", "decimal"),
            ExportColumn("depreciation_method", "Abschreibungsmethode", "string"),
            ExportColumn("useful_life", "Nutzungsdauer (Jahre)", "string"),
            ExportColumn("annual_depreciation", "AfA (Jahr)", "decimal"),
            ExportColumn("accumulated_depreciation", "AfA kumuliert", "decimal"),
            ExportColumn("book_value", "Restbuchwert (Jahresende)", "decimal"),
            ExportColumn("receipt_id", "Beleg-Nr", "string"),
        ]

    def _asset_rows(self, collective, year):
        rows = []

        # Individually-depreciated assets only - pooled assets are
        # reported once per pool below instead (their own AfA fields
        # all read zero once assigned to a pool).
        assets = (
            Asset.objects
            .filter(collective=collective, asset_pool__isnull=True)
            .select_related("receipt")
        )

        for asset in assets:
            is_immediate = asset.depreciation_method == Asset.DeprecationMethod.NONE

            if is_immediate:
                # Sofortabschreibung: listed only in the purchase year.
                if asset.purchase_date.year != year:
                    continue
            else:
                first_year = asset.purchase_date.year
                last_year = first_year + asset.useful_life - 1
                if not (first_year <= year <= last_year):
                    continue

            rows.append({
                "type": "GWG (Sofortabschreibung)" if is_immediate else "Anlagegut",
                "name": asset.name,
                "acquisition_date": asset.purchase_date,
                "acquisition_cost": asset.purchase_price,
                "depreciation_method": asset.get_depreciation_method_display(),
                "useful_life": str(asset.useful_life),
                "annual_depreciation": asset.annual_depreciation,
                "accumulated_depreciation": asset.accumulated_depreciation(year),
                "book_value": asset.book_value(year),
                "receipt_id": f"#{asset.receipt.id}" if asset.receipt else "",
                "_sort_key": (asset.purchase_date, asset.name),
            })

        return rows

    def _asset_pool_rows(self, collective, year):
        rows = []

        for pool in AssetPool.objects.filter(collective=collective):
            first_year = pool.acquisition_year
            last_year = first_year + pool.depreciation_years - 1
            if not (first_year <= year <= last_year):
                continue

            rows.append({
                "type": "Sammelposten",
                "name": pool.name,
                "acquisition_date": None,
                "acquisition_cost": pool.acquisition_cost,
                "depreciation_method": f"Linear über {pool.depreciation_years} Jahre",
                "useful_life": str(pool.depreciation_years),
                "annual_depreciation": pool.annual_depreciation,
                "accumulated_depreciation": pool.accumulated_depreciation(year),
                "book_value": pool.remaining_value(year),
                "receipt_id": "",
                # Sammelposten sort right after the acquisition year starts,
                # by name; there's no single acquisition date to sort by.
                "_sort_key": (None, pool.name),
            })

        return rows

    def get_rows(self, user, cleaned_params):
        collective = cleaned_params["collective"]
        year = cleaned_params["year"]

        rows = self._asset_rows(collective, year) + self._asset_pool_rows(collective, year)
        rows.sort(key=lambda r: (r["_sort_key"][0] is None, r["_sort_key"]))

        for row in rows:
            del row["_sort_key"]

        return rows
