"""
COMPONENTS: the receipt file-upload widget (QR code + polling status +
file receiver). Embedded into the receipt form (desktop) and the
mobile upload page, so it's a shared component rather than a
one-feature partial.
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from ...models import UploadSession
from ...services import upload_sessions as upload_session_services


def upload_session_file_htmx(request, token):
    """COMPONENT (htmx action): receives the uploaded file from the mobile page."""
    session = get_object_or_404(UploadSession, token=token)

    if session.upload_blocked():
        return HttpResponse("Upload not allowed", status=403)

    file = request.FILES.get("file")
    if not file:
        return HttpResponse("No file", status=400)

    upload_session_services.receive_uploaded_file(session, file)

    return HttpResponse("Uploaded")


@login_required
def upload_session_status_htmx(request, token):
    """COMPONENT (htmx): polled fragment showing whether a file has been uploaded yet."""
    upload_session = get_object_or_404(UploadSession, token=token)

    return render(request, "ledger/upload_session_management/partials/upload_status.html", {
        "upload_session": upload_session,
        "uploaded": bool(upload_session.file),
    })


@login_required
def upload_session_qr_htmx(request, token):
    """COMPONENT (htmx): QR code image linking to the mobile upload page."""
    session = get_object_or_404(UploadSession, token=token)

    upload_url = request.build_absolute_uri(
        reverse("mobile_upload_page", args=[session.token])
    )

    png_bytes = upload_session_services.build_qr_code_png(upload_url)

    return HttpResponse(png_bytes, content_type="image/png")
