"""
Business logic for Receipts: queries, the receipt overview page data,
and creating/saving a receipt together with its upload session.
"""
from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet
from django.urls import reverse

from ..models import AccountHolder, Receipt, UploadSession
from . import access, overview, upload_sessions


def get_collective_receipts(collective: AccountHolder) -> QuerySet[Receipt]:
    """Receipts for a collective."""
    return (
        Receipt.objects
        .filter(collective=collective)
        .select_related(
            "event",
            "responsible_holder",
            "uploaded_by_holder",
            "collective",
            "counterparty",
        )
        .order_by("-date")
    )


def get_user_receipt(user: AbstractBaseUser, receipt_id: int) -> Receipt:
    """Only returns a receipt if the user belongs to its collective."""
    return Receipt.objects.get(
        id=receipt_id,
        collective__memberships__django_user=user,
    )


def receipt_overview_context(receipt: Receipt) -> dict:
    """Header data for the receipt overview page."""
    direction_badge_class = {
        Receipt.Direction.INGOING: "bg-success",
        Receipt.Direction.OUTGOING: "bg-danger",
    }.get(receipt.direction, "bg-secondary")

    document_badge_class = {
        "attached": "bg-success",
        "pending": "bg-warning text-dark",
    }.get(receipt.document_status, "bg-secondary")

    amount_class = {
        Receipt.Direction.INGOING: "text-success",
        Receipt.Direction.OUTGOING: "text-danger",
    }.get(receipt.direction, "")

    header = overview.header_context(
        title=f"Receipt #{receipt.id}",
        type=receipt.direction,
        date=receipt.date.strftime("%d. %B %Y") if receipt.date else None,
        rows=[
            {"label": "Responsible", "value": receipt.responsible_holder.name if receipt.responsible_holder else None},
            {"label": "Collective", "value": receipt.collective.name if receipt.collective else None},
            {
                "label": "Event",
                "value": receipt.event.name if receipt.event else None,
                "url": reverse("event_overview_page", args=[receipt.event.id]) if receipt.event else None,
            },
            {"label": "Counterparty", "value": receipt.counterparty.name if receipt.counterparty else None},
            {
                "label": "Receipt File",
                "hx_get": reverse("upload_session_status_htmx", args=[receipt.upload_session.token]),
                "target_id": "upload-status-target",
            },
            {"label": "Number of associated assets", "value": receipt.assets.count()},
        ],
        stats=[
            {"label": "Amount", "value": receipt.amount, "class": amount_class},
            {"label": "Document Status", "type": "badge", "badge_text": receipt.document_status, "badge_class": document_badge_class},
            {
                "label": "Transaction Status",
                "type": "badge",
                "badge_text": "closed" if receipt.is_closed else "open",
                "badge_class": "bg-success" if receipt.is_closed else "bg-warning text-dark",
            },
        ],
    )

    return {"header": header}


def start_receipt_upload_session(upload_session_id) -> UploadSession:
    """
    Gets (or creates) the upload session for a new receipt and opens its
    upload window.
    """
    if upload_session_id:
        session = UploadSession.objects.get(id=upload_session_id)
    else:
        session = UploadSession.objects.create()

    session.start_timer()
    return session


def create_receipt(
    *,
    receipt: Receipt,
    collective: AccountHolder,
    user: AbstractBaseUser,
    upload_session: UploadSession,
) -> Receipt:
    """Stamps system fields on a new receipt and links its upload session."""
    receipt.collective = collective
    receipt.uploaded_by_holder = access.get_user_account_holder(user)

    upload_session.save()
    receipt.upload_session = upload_session
    receipt.save()

    return receipt


def save_edited_receipt(receipt: Receipt, upload_session: UploadSession) -> Receipt:
    """
    Saves an edited receipt, clearing the linked upload session's file
    if the receipt no longer claims to have a document attached.
    """
    if receipt.document_status != receipt.DocumentStatus.ATTACHED:
        upload_sessions.clear_file(upload_session)

    receipt.save()
    return receipt


def quick_create_receipt(
    *,
    collective: AccountHolder,
    user: AbstractBaseUser,
    direction: str,
    amount,
    date,
    photo=None,
) -> Receipt:
    """
    Minimal-field receipt creation for the mobile quick-add page: only
    the essentials are captured on the phone (direction, amount, date,
    optionally a photo taken on the spot). Category, event, tax sphere,
    and counterparty are deliberately left unset for a proper pass on
    desktop later - the point of this flow is speed, not completeness.
    """
    personal_holder = access.get_user_account_holder(user)

    upload_session = UploadSession.objects.create()
    if photo:
        upload_sessions.receive_uploaded_file(upload_session, photo)

    receipt = Receipt(
        collective=collective,
        direction=direction,
        amount=amount,
        date=date,
        responsible_holder=personal_holder,
        uploaded_by_holder=personal_holder,
        document_status=(
            Receipt.DocumentStatus.ATTACHED if photo else Receipt.DocumentStatus.PENDING
        ),
        upload_session=upload_session,
    )
    receipt.full_clean()
    receipt.save()

    return receipt