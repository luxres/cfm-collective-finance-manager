"""PAGE: the standalone mobile page opened by scanning a receipt's QR code."""
from django.shortcuts import get_object_or_404, render

from ...models import UploadSession


def mobile_upload_page(request, token):
    """PAGE: minimal, self-contained page for uploading a receipt file from a phone."""
    upload_session = get_object_or_404(UploadSession, token=token)

    return render(
        request,
        "ledger/upload_session_management/mobile_upload.html",
        {"upload_session": upload_session},
    )
