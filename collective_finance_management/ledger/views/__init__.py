"""
View functions, split by what they return rather than by feature, so
it's obvious at a glance what kind of endpoint you're looking at. This
is mirrored in the function names, the URL names, and the URL paths:

- ``pages``      -- full HTML documents (extend ``base.html`` or ship
                     their own ``<html>``). These are what a user
                     navigates to directly: /receipt/, /event/,
                     /finance-account/<id>/overview/, etc.
                     Function & URL name suffix: ``_page``.

- ``partials``   -- HTML fragments returned to an HTMX request that
                     swaps part of a *page*: tables, forms, and the
                     empty "204 + HX-Trigger" responses used after a
                     create/update/delete. Feature-specific; each one
                     only makes sense inside the page that requests it.
                     Function & URL name suffix: ``_htmx``. URL path
                     prefix: ``htmx/``.

- ``components`` -- small, reusable pieces embedded into more than one
                     feature's forms/pages (currently: the
                     upload-widget used by both the receipt form and
                     the mobile upload flow: status polling, QR code,
                     and the file-receiving endpoint). Still HTMX
                     endpoints, so they follow the same ``_htmx`` /
                     ``htmx/`` convention as ``partials``.

- ``api``        -- plain JSON endpoints, not tied to any template.
                     Function & URL name suffix: ``_api``. URL path
                     prefix: ``api/``.

None of these should contain business logic - that lives in
``ledger/services/``. A view function's job is: read the request,
resolve/authorize the objects involved, delegate to a service, and
render/return the result.
"""
