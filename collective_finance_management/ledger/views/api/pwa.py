"""
API: PWA plumbing for the mobile quick-add page - the manifest and its
icon, so the page can be "Added to Home Screen" and open full-screen
like a native app.

NOTE: `pwa_icon` below is a plain placeholder (a colored square with a
monogram) generated on the fly, not a real asset. Swap it for a proper
branded PNG (served as a static file) before shipping this to real
users - browsers are picky about icon quality/format for the install
prompt, and a static file will always be simpler/faster than generating
one per request.
"""
from django.http import HttpResponse, JsonResponse


def manifest_json(request):
    """API: the Web App Manifest for the mobile quick-add page."""
    manifest = {
        "name": "Add Receipt",
        "short_name": "Add Receipt",
        "description": "Quickly capture a receipt for your Collective.",
        "start_url": "/m/add-receipt/",
        "scope": "/m/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#198754",
        "icons": [
            {"src": "/m/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"},
        ],
    }
    return JsonResponse(manifest, content_type="application/manifest+json")


def pwa_icon(request):
    """API: placeholder home-screen icon - replace with a real static asset."""
    svg = """
        <svg width="50" height="50" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <!-- connections -->
        <line x1="100" y1="100" x2="100" y2="40" stroke="#4f4f63" stroke-width="6"/>
        <line x1="100" y1="100" x2="100" y2="160" stroke="#4f4f63" stroke-width="6"/>
        <line x1="100" y1="100" x2="40" y2="100" stroke="#4f4f63" stroke-width="6"/>
        <line x1="100" y1="100" x2="160" y2="100" stroke="#4f4f63" stroke-width="6"/>

        <!-- nodes (bigger) -->
        <circle cx="100" cy="100" r="16" fill="#4f4f63"/>
        <circle cx="100" cy="40" r="16" fill="#1f7a5a"/>
        <circle cx="100" cy="160" r="16" fill="#1f7a5a"/>
        <circle cx="40" cy="100" r="16" fill="#1f7a5a"/>
        <circle cx="160" cy="100" r="16" fill="#1f7a5a"/>
    </svg>
    """
    return HttpResponse(svg, content_type="image/svg+xml")
