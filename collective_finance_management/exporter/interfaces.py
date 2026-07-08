"""
Export framework interfaces.

`exporter` is this project's export app: it owns every `DataSourceProvider`
itself (see `exporter/sources/`) and is free to depend on `ledger`'s models
directly - `ledger` has no knowledge of `exporter`. What *is* meant to stay
generic and pluggable is the output *format* (`exporter/formats.py`): today
it's CSV, tomorrow XLSX/PDF/JSON, without touching a source's row/column
logic.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class ExportColumn:
    """Describes a single column of an export dataset."""

    key: str
    label: str
    # "string" | "decimal" | "date" | "bool" | "int"
    type: str = "string"


@dataclass
class ExportDataset:
    """The generic, format-agnostic result of running a data source."""

    columns: list[ExportColumn]
    rows: list[dict[str, Any]]
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompletenessReport:
    """
    Optional "is this data ready to be exported" summary a data source can
    provide. Rendered by the UI as a status panel before download, e.g.
    "42 of 45 receipts closed" with links to the open ones.
    """

    label: str
    total: int
    complete: int
    incomplete_items: list[dict[str, Any]] = field(default_factory=list)

    @property
    def incomplete(self) -> int:
        return self.total - self.complete

    @property
    def is_complete(self) -> bool:
        return self.total > 0 and self.complete == self.total

    @property
    def has_data(self) -> bool:
        return self.total > 0


class DataSourceProvider(abc.ABC):
    """
    One export purpose, e.g. "EÜR for a Verein" or "member list". Implemented
    inside `exporter/sources/` against `ledger`'s models directly and
    registered in `exporter/apps.py`.
    """

    key: str
    label: str
    description: str = ""

    @abc.abstractmethod
    def get_param_form_class(self):
        """Return a Django Form *class* used to collect this source's params.
        Must accept a `user=` kwarg in __init__ (used to scope querysets to
        what the requesting user may access)."""

    @abc.abstractmethod
    def get_columns(self, user, cleaned_params: dict) -> list[ExportColumn]:
        ...

    @abc.abstractmethod
    def get_rows(self, user, cleaned_params: dict) -> list[dict[str, Any]]:
        ...

    def get_completeness(self, user, cleaned_params: dict) -> Optional[CompletenessReport]:
        """Optional. Return None if this source has no notion of completeness."""
        return None

    def get_dataset(self, user, cleaned_params: dict) -> ExportDataset:
        return ExportDataset(
            columns=self.get_columns(user, cleaned_params),
            rows=self.get_rows(user, cleaned_params),
        )
