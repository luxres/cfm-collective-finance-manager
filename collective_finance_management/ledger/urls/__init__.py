"""
URL configuration for the ledger app.

Each feature owns its own url module under this package. Within every
module, routes are grouped and named by what they return:

- ``*_page``  -- full HTML documents (clean, bookmarkable paths)
- ``*_htmx``  -- HTMX fragments, all served under the ``htmx/`` prefix
- ``*_api``   -- plain JSON endpoints, all served under the ``api/`` prefix

This file just stitches the per-feature modules together so
`collective_finance_management/urls.py` can keep doing a single
`include('ledger.urls')`.
"""

from . import (
    dashboard_urls,
    account_urls,
    receipt_urls,
    transaction_urls,
    event_urls,
    external_urls,
    api_endpoint_urls,
    category_urls,
    upload_session_urls,
    asset_urls,
    mobile_urls,
)

urlpatterns = [
    *dashboard_urls.urlpatterns,
    # finance account management urls
    *account_urls.urlpatterns,
    # finance receipt management urls
    *receipt_urls.urlpatterns,
    # transaction management
    *transaction_urls.urlpatterns,
    # event management
    *event_urls.urlpatterns,
    # external parties management
    *external_urls.urlpatterns,
    # api endpoints
    *api_endpoint_urls.urlpatterns,
    # category_management
    *category_urls.urlpatterns,
    #update session
    *upload_session_urls.urlpatterns,
    #assets
    *asset_urls.urlpatterns,
    #mobile
    *mobile_urls.urlpatterns,
]
