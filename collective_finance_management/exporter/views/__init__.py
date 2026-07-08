"""
View functions, split the same way as `ledger`'s: by what they return,
not by feature.

- ``pages`` -- full HTML documents: the source picker and the
  export/preview screen for one source. Function & URL name suffix:
  ``_page``.
- ``htmx``  -- HTMX fragments/actions used inside the export page: the
  live-updating completeness panel, and the file download itself
  (triggered by a plain link rather than an `hx-get`, but - like
  `receipt_file_htmx` in `ledger` - it's still a feature-scoped action
  that only makes sense from within that page, not a standalone
  document). Function & URL name suffix: ``_htmx``, URL path prefix
  ``htmx/``.

Neither should contain business logic - `get_dataset`/`get_completeness`
on the relevant `DataSourceProvider` (see `exporter/sources/`) already
own that.
"""
