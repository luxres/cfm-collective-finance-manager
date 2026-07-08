from django.urls import path

from ..views.pages import mobile as mobile_pages
from ..views.api import pwa

urlpatterns = [
    # page
    path("m/add-receipt/", mobile_pages.mobile_add_receipt_page, name="mobile_add_receipt_page"),

    # PWA plumbing for the page above
    path("m/manifest.json", pwa.manifest_json, name="mobile_manifest_json"),
    path("m/icon.svg", pwa.pwa_icon, name="mobile_pwa_icon"),
]
