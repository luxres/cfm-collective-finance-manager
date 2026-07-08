"""
Concrete export sources.

Unlike a "bring your own domain" plugin system, `exporter` is the
collective-finance-management project's export app: it is allowed to (and
does) depend on `ledger` directly. Each module in this package implements
one `DataSourceProvider` against `ledger`'s models. New export purposes
(e.g. a member list, a cash book / Kassenbuch, ...) get their own module
here and get registered in `apps.py`.

Only the *format* a dataset is written out as (CSV today, XLSX/PDF/JSON
later) is meant to be pluggable/generic - see `exporter/formats.py`.
"""
