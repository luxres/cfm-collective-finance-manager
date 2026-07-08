"""
EÜR (Einnahmenüberschussrechnung) export for a single Verein (collective).

This module plugs `ledger` into the generic `exporter` app - see
`exporter/interfaces.py` for the contract. It is registered from
`LedgerConfig.ready()`.

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
* The "closed" completeness check is based on `Receipt.date` (Belegdatum),
  per product decision - i.e. "did every receipt *dated* in year Y end up
  fully settled", not "did every payment that landed in year Y have a
  receipt". A receipt dated in December but paid in January will show as
  open in December's check even though its cash-flow row (if any) belongs
  to January's export - that's intentional, it flags exactly the kind of
  item a bookkeeper needs to sanity check before closing the year.
"""
from __future__ import annotations

from datetime import date

from django import forms
from django.urls import reverse

from exporter.interfaces import CompletenessReport, DataSourceProvider, ExportColumn

from .models import AccountHolder, TransactionLine
from .services import access, receipts as receipt_services


def _year_choices():
    current_year = date.today().year
    return [(y, str(y)) for y in range(current_year, current_year - 8, -1)]


class EuerExportParamsForm(forms.Form):
    collective = forms.ModelChoiceField(
        queryset=AccountHolder.objects.none(),
        label="Verein",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    year = forms.ChoiceField(
        choices=_year_choices,
        label="Jahr",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["collective"].queryset = (
            access.get_user_collectives(user) if user else AccountHolder.objects.none()
        )

    def clean_year(self):
        return int(self.cleaned_data["year"])


class EuerVereinSource(DataSourceProvider):
    key = "euer_verein"
    label = "EÜR – Einnahmenüberschussrechnung (Verein)"
    description = (
        "Flat cash-flow export of everything that actually moved into or out "
        "of a Verein's finance accounts in a given year (Zufluss-/"
        "Abflussprinzip). One row per relevant transaction line, including "
        "the tax sphere (ideell / Vermögensverwaltung / Zweckbetrieb / "
        "wirtschaftlicher Geschäftsbetrieb)."
    )

    def get_param_form_class(self):
        return EuerExportParamsForm

    def get_columns(self, user, cleaned_params):
        return [
            ExportColumn("date", "Datum (Zahlung)", "date"),
            ExportColumn("amount", "Betrag", "decimal"),
            ExportColumn("income", "Einnahme", "decimal"),
            ExportColumn("expense", "Ausgabe", "decimal"),
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
    # rows
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
            .order_by("transaction__date", "id")
        )

    def _is_internal_transfer(self, line, collective) -> bool:
        holder_ids = set(
            line.transaction.lines.values_list("account__account_holder_id", flat=True)
        )
        return holder_ids == {collective.id}

    def get_rows(self, user, cleaned_params):
        collective = cleaned_params["collective"]
        year = cleaned_params["year"]

        rows = []
        for line in self._relevant_lines(collective, year):
            if self._is_internal_transfer(line, collective):
                continue

            transaction = line.transaction
            receipt = transaction.receipt
            amount = line.amount

            rows.append({
                "date": transaction.date,
                "amount": amount,
                "income": amount if amount > 0 else None,
                "expense": -amount if amount < 0 else None,
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
    # completeness ("are all receipts closed?")
    # ------------------------------------------------------------------

    def get_completeness(self, user, cleaned_params):
        collective = cleaned_params["collective"]
        year = cleaned_params["year"]

        receipts = receipt_services.get_collective_receipts(collective).filter(date__year=year)

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
            label=f"Receipts dated in {year}",
            total=total,
            complete=closed,
            incomplete_items=open_items,
        )
