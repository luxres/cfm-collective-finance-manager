"""
EÜR (Einnahmenüberschussrechnung) export for a single Verein (collective).

This lives in `exporter` (not `ledger`) and imports `ledger`'s models and
services directly - `exporter` is the place that knows how to turn domain
data into downloadable files, and EÜR is one of its export sources.
`ledger` has no knowledge of `exporter` at all.

Design notes
------------
* One row per relevant `TransactionLine`, not per `Receipt`. The EÜR follows
  the Zufluss-/Abflussprinzip (cash basis): what matters is the date money
  actually moved, not the date on the receipt. A single receipt can
  therefore produce zero, one, or several rows (e.g. a split payment paid
  partly in December and partly in January lands in two different tax
  years).
* A line is treated as an internal transfer (and excluded) when *every*
  line of its parent Transaction touches an account belonging to the same
  collective - e.g. moving cash from the till to the bank account. This is
  checked structurally rather than trusting `Receipt.direction`, since a
  transaction may have no receipt at all, or the receipt may be missing/
  mismarked.
* A receipt is "included" in a given year's EÜR - for both the exported
  rows *and* the completeness stats below - if it has at least one
  non-internal-transfer transaction line dated in that year. This follows
  the same Zufluss-/Abflussprinzip as the rows themselves: a receipt dated
  in December but paid in January belongs to January's export and
  January's completeness check, not December's, regardless of its own
  `Receipt.date` (Belegdatum).
* Depreciable fixed assets (§4 Abs. 3 Satz 3-5 EStG) are the one
  exception to pure cash-basis accounting: their purchase price isn't
  deductible in the year it's paid - it has to be capitalized and
  written off via AfA over the asset's useful life instead (see the
  companion `afa_anlagen.AfaAnlagenSource`). So if a receipt paid for
  one or more such assets, the *capitalized* portion of its amount is
  netted out of its cash-flow row(s) here - see `_capitalized_amount`.
  A receipt that also covered non-asset costs (e.g. an invoice for a
  laptop *and* a cable) still shows the non-asset portion as a normal
  deductible row. GWG assets that were immediately written off
  (Sofortabschreibung) are *not* netted out - they remain fully
  deductible in their purchase year, same as any other expense.
"""
from __future__ import annotations

from decimal import Decimal

from django.urls import reverse

from ledger.models import Receipt, TransactionLine

from ..interfaces import CompletenessReport, DataSourceProvider, ExportColumn
from ._shared import CollectiveYearParamsForm


class EuerVereinSource(DataSourceProvider):
    key = "euer_verein"
    label = "EÜR – Einnahmenüberschussrechnung (Verein)"
    description = (
        "Flat cash-flow export of everything that actually moved into or out "
        "of a Verein's finance accounts in a given year (Zufluss-/"
        "Abflussprinzip). One row per relevant transaction line, including "
        "the tax sphere (ideell / Vermögensverwaltung / Zweckbetrieb / "
        "wirtschaftlicher Geschäftsbetrieb). Capitalized asset purchases are "
        "netted out here - see the AVEÜR export for their AfA."
    )

    def get_param_form_class(self):
        return CollectiveYearParamsForm

    def get_columns(self, user, cleaned_params):
        return [
            ExportColumn("date", "Datum (Zahlung)", "date"),
            ExportColumn("amount", "Betrag", "decimal"),
            ExportColumn("income", "Einnahme", "decimal"),
            ExportColumn("expense", "Ausgabe", "decimal"),
            ExportColumn("capitalized_amount", "davon aktiviert (siehe AVEÜR)", "decimal"),
            ExportColumn("capitalized_assets", "Anlagegüter", "string"),
            ExportColumn("tax_category", "Sphäre", "string"),
            ExportColumn("category", "Kategorie", "string"),
            ExportColumn("description", "Verwendungszweck", "string"),
            ExportColumn("account", "Konto", "string"),
            ExportColumn("counterparty", "Gegenpartei", "string"),
            ExportColumn("event", "Veranstaltung", "string"),
            ExportColumn("responsible", "Verantwortlich", "string"),
            ExportColumn("receipt_id", "Beleg-Nr", "string"),
            ExportColumn("receipt_date", "Belegdatum", "date"),
            ExportColumn("receipt_closed", "Beleg abgeschlossen", "bool"),
            ExportColumn("note", "Notiz", "string"),
        ]

    # ------------------------------------------------------------------
    # shared: which transaction lines / receipts count for a given year
    # ------------------------------------------------------------------

    def _relevant_lines(self, collective, year):
        return (
            TransactionLine.objects
            .filter(
                account__account_holder=collective,
                transaction__date__year=year,
            )
            .select_related(
                "account",
                "transaction",
                "transaction__receipt",
                "transaction__receipt__category",
                "transaction__receipt__event",
                "transaction__receipt__counterparty",
                "transaction__receipt__responsible_holder",
            )
            .prefetch_related("transaction__receipt__assets")
            .order_by("transaction__date", "id")
        )

    def _is_internal_transfer(self, line, collective) -> bool:
        holder_ids = set(
            line.transaction.lines.values_list("account__account_holder_id", flat=True)
        )
        return holder_ids == {collective.id}

    def _included_receipt_ids(self, collective, year) -> set[int]:
        """
        Receipts that have at least one non-internal-transfer transaction
        line dated in `year` - i.e. exactly the receipts this year's EÜR
        rows are built from (Zufluss-/Abflussprinzip).
        """
        receipt_ids = set()

        for line in self._relevant_lines(collective, year):
            if self._is_internal_transfer(line, collective):
                continue
            if line.transaction.receipt_id:
                receipt_ids.add(line.transaction.receipt_id)

        return receipt_ids

    def _capitalized_assets(self, receipt):
        """The receipt's linked assets that are capitalized (not immediately written off)."""
        if not receipt:
            return []
        return [
            asset for asset in receipt.assets.all()
            if asset.depreciation_method != asset.DeprecationMethod.NONE
        ]

    def _capitalized_amount(self, receipt) -> Decimal:
        return sum((a.purchase_price for a in self._capitalized_assets(receipt)), Decimal("0"))

    # ------------------------------------------------------------------
    # rows
    # ------------------------------------------------------------------

    def get_rows(self, user, cleaned_params):
        collective = cleaned_params["collective"]
        year = cleaned_params["year"]

        # How much of each receipt's capitalized-asset amount still needs
        # netting out of upcoming rows *within this year's export*. Covers
        # the common case (one row per receipt) as well as same-year split
        # payments. A receipt whose asset purchase is itself split across
        # different tax years would need cross-year state this export
        # doesn't keep - rare enough that it isn't handled here.
        remaining_capitalized: dict[int, Decimal] = {}

        rows = []
        for line in self._relevant_lines(collective, year):
            if self._is_internal_transfer(line, collective):
                continue

            transaction = line.transaction
            receipt = transaction.receipt
            amount = line.amount

            capitalized_amount = Decimal("0")
            capitalized_assets_note = ""

            if receipt:
                if receipt.id not in remaining_capitalized:
                    remaining_capitalized[receipt.id] = self._capitalized_amount(receipt)

                remaining = remaining_capitalized[receipt.id]
                if remaining > 0:
                    capitalized_amount = min(remaining, abs(amount))
                    remaining_capitalized[receipt.id] -= capitalized_amount
                    amount = (
                        amount - capitalized_amount if amount > 0
                        else amount + capitalized_amount
                    )
                    capitalized_assets_note = ", ".join(
                        a.name for a in self._capitalized_assets(receipt)
                    )

            rows.append({
                "date": transaction.date,
                "amount": amount,
                "income": amount if amount > 0 else None,
                "expense": -amount if amount < 0 else None,
                "capitalized_amount": capitalized_amount if capitalized_amount > 0 else None,
                "capitalized_assets": capitalized_assets_note,
                "tax_category": (
                    receipt.get_tax_category_display()
                    if receipt and receipt.tax_category else ""
                ),
                "category": receipt.category.name if receipt and receipt.category else "",
                "description": transaction.description or (receipt.note if receipt else ""),
                "account": line.account.name,
                "counterparty": receipt.counterparty.name if receipt and receipt.counterparty else "",
                "event": receipt.event.name if receipt and receipt.event else "",
                "responsible": (
                    receipt.responsible_holder.name
                    if receipt and receipt.responsible_holder else ""
                ),
                "receipt_id": f"#{receipt.id}" if receipt else "",
                "receipt_date": receipt.date if receipt else None,
                "receipt_closed": receipt.is_closed if receipt else None,
                "note": line.note,
            })

        return rows

    # ------------------------------------------------------------------
    # completeness ("how many receipts are included, how many aren't
    # closed yet")
    # ------------------------------------------------------------------

    def get_completeness(self, user, cleaned_params):
        collective = cleaned_params["collective"]
        year = cleaned_params["year"]

        receipt_ids = self._included_receipt_ids(collective, year)
        receipts = (
            Receipt.objects
            .filter(id__in=receipt_ids)
            .select_related("responsible_holder")
            .order_by("date")
        )

        total = receipts.count()
        closed = 0
        open_items = []

        for receipt in receipts:
            if receipt.is_closed:
                closed += 1
            else:
                open_items.append({
                    "id": receipt.id,
                    "date": receipt.date,
                    "amount": receipt.amount,
                    "direction": receipt.get_direction_display(),
                    "note": receipt.note,
                    "detail_url": reverse("receipt_overview_page", args=[receipt.id]),
                })

        return CompletenessReport(
            label=f"Receipts with a transaction dated in {year}",
            total=total,
            complete=closed,
            incomplete_items=open_items,
        )
