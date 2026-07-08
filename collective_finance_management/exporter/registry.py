"""
Simple in-memory registries for export data sources and format writers.

`exporter` registers its own sources (see `exporter/sources/`) from
`ExporterConfig.ready()` - there is no cross-app plugin step, `ledger` does
not know `exporter` exists.

Built-in format writers (currently just CSV) register themselves below.
"""
from __future__ import annotations

from typing import Optional

from .formats import BaseFormatWriter, CsvFormatWriter
from .interfaces import DataSourceProvider

_sources: dict[str, DataSourceProvider] = {}
_formats: dict[str, BaseFormatWriter] = {}


def register_source(provider: DataSourceProvider) -> None:
    _sources[provider.key] = provider


def get_source(key: str) -> Optional[DataSourceProvider]:
    return _sources.get(key)


def all_sources() -> list[DataSourceProvider]:
    return list(_sources.values())


def register_format(writer: BaseFormatWriter) -> None:
    _formats[writer.key] = writer


def get_format(key: str) -> Optional[BaseFormatWriter]:
    return _formats.get(key)


def all_formats() -> list[BaseFormatWriter]:
    return list(_formats.values())


# Built-in formats are always available.
register_format(CsvFormatWriter())
