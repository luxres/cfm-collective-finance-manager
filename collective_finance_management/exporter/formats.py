"""
Output format writers. Each writer turns a generic ExportDataset into bytes
for download. Adding a new format later (XLSX, PDF, JSON, ...) means adding
one class here and registering it in `registry.py` - no changes needed to
any data source, and no changes needed in `ledger`.
"""
from __future__ import annotations

import abc
import csv
import io
from typing import Any, Optional

from django import forms

from .interfaces import ExportDataset


class BaseFormatWriter(abc.ABC):
    key: str
    label: str
    content_type: str = "application/octet-stream"
    file_extension: str = "bin"

    def get_option_form_class(self) -> Optional[type]:
        """Optional Django Form class for format-specific options
        (e.g. CSV delimiter/decimal style). Return None if the format has
        no configurable options."""
        return None

    @abc.abstractmethod
    def write(self, dataset: ExportDataset, options: dict[str, Any]) -> bytes:
        ...


class CsvStyleForm(forms.Form):
    STYLE_CHOICES = [
        ("de", "Deutsch / Excel (Semikolon-getrennt, Komma als Dezimaltrennzeichen)"),
        ("intl", "International (Komma-getrennt, Punkt als Dezimaltrennzeichen)"),
    ]

    csv_style = forms.ChoiceField(
        choices=STYLE_CHOICES,
        initial="de",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="CSV format",
    )


class CsvFormatWriter(BaseFormatWriter):
    """
    Generic CSV writer. Knows nothing about EUR, receipts, or ledger - it
    just serializes whatever ExportDataset it is handed, according to the
    chosen locale style.
    """

    key = "csv"
    label = "CSV"
    content_type = "text/csv"
    file_extension = "csv"

    STYLES = {
        "de": dict(delimiter=";", decimal_sep=",", date_fmt="%d.%m.%Y",
                   bom=True, bool_labels=("Ja", "Nein")),
        "intl": dict(delimiter=",", decimal_sep=".", date_fmt="%Y-%m-%d",
                     bom=False, bool_labels=("Yes", "No")),
    }

    def get_option_form_class(self):
        return CsvStyleForm

    def _format_value(self, value: Any, col_type: str, style: dict) -> str:
        if value is None or value == "":
            return ""

        if col_type == "decimal":
            text = f"{value:.2f}"
            if style["decimal_sep"] != ".":
                text = text.replace(".", style["decimal_sep"])
            return text

        if col_type == "date" and hasattr(value, "strftime"):
            return value.strftime(style["date_fmt"])

        if col_type == "bool":
            yes, no = style["bool_labels"]
            return yes if value else no

        return str(value)

    def write(self, dataset: ExportDataset, options: dict[str, Any]) -> bytes:
        style = self.STYLES[options.get("csv_style", "de")]

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=style["delimiter"], lineterminator="\r\n")

        writer.writerow([col.label for col in dataset.columns])
        for row in dataset.rows:
            writer.writerow([
                self._format_value(row.get(col.key), col.type, style)
                for col in dataset.columns
            ])

        text = buffer.getvalue()
        return text.encode("utf-8-sig" if style["bom"] else "utf-8")
