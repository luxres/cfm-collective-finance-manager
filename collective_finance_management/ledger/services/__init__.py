"""
Business logic for the ledger app, grouped one module per field/domain.

View functions (see ``ledger/views/``) must stay "dumb": read the request,
call into these services to do the actual work, and pick a template /
response to return. Anything that decides *what* happens (permissions,
computed totals, orchestrating multiple model writes, building chart /
header data, resolving "the active collective", etc.) belongs here
instead.

Modules:

- ``access``        -- account holder membership & permission checks
- ``collectives``   -- resolving "the active collective" for a request
- ``accounts``      -- finance accounts, bank account details, overviews
- ``categories``    -- category CRUD support + overview data
- ``events``         -- event CRUD support + overview data
- ``receipts``       -- receipt CRUD support + overview data
- ``transactions``   -- double-entry transaction creation/updates
- ``external_parties`` -- external party (AccountHolder) helpers
- ``upload_sessions`` -- receipt file upload session lifecycle
- ``dashboard``      -- balance timelines for the dashboard page
- ``overview``       -- shared "overview page" building blocks (timeline
                         chart data + header card), reused by every
                         `*_overview` page
- ``sorting``        -- shared HTMX table sort-link building
"""
