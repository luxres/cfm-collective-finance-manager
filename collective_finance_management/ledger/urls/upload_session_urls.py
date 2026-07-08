from django.urls import path

from ..views.pages import uploads as upload_pages
from ..views.components import upload_widget

urlpatterns = [
    # pages
    path("receipt/upload-file/mobile/<uuid:token>/", upload_pages.mobile_upload_page, name="mobile_upload_page"),

    # htmx (components)
    path("htmx/receipt/upload-file/standard/<uuid:token>/", upload_widget.upload_session_file_htmx, name="upload_session_file_htmx"),
    path("htmx/receipt/upload-file/status/<uuid:token>/", upload_widget.upload_session_status_htmx, name="upload_session_status_htmx"),
    path("htmx/receipt/upload-file/qr/mobile/<uuid:token>/", upload_widget.upload_session_qr_htmx, name="upload_session_qr_htmx"),
]
