"""Business logic around the receipt file-upload session lifecycle."""
import io

from django.utils import timezone

from ..models import UploadSession


def clear_file(upload_session: UploadSession) -> None:
    """Removes the currently attached file from an upload session."""
    if upload_session.file:
        upload_session.file.delete(save=False)
    upload_session.file = None
    upload_session.save(update_fields=["file"])


def receive_uploaded_file(upload_session: UploadSession, file) -> UploadSession:
    """Attaches an uploaded file (from the mobile upload page) to a session."""
    upload_session.file = file
    upload_session.uploaded_at = timezone.now()
    upload_session.save()
    return upload_session


def build_qr_code_png(url: str) -> bytes:
    """Renders a QR code pointing at `url` as PNG bytes."""
    import qrcode

    image = qrcode.make(url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
