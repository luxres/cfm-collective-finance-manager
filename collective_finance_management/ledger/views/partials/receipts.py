"""HTMX ENDPOINTS: fragments used by the receipt management / overview pages."""
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, render

from ...forms import ReceiptForm
from ...models import AccountHolder, Receipt, Transaction
from ...services import access, receipts as receipt_services, sorting

SORTABLE_COLUMNS = [
    "id", "amount", "category", "event", "counterparty", "direction",
    "document_status", "tax_category", "address_status", "responsible_holder", "date",
]


@login_required
def receipt_table_htmx(request, collective_id):
    """HTMX endpoint: sortable, filterable receipt table."""
    collective = get_object_or_404(AccountHolder, id=collective_id)

    event_id = request.GET.get("event_id")
    category_id = request.GET.get("category_id")

    receipts = Receipt.objects.filter(collective=collective)
    if event_id:
        receipts = receipts.filter(event_id=event_id)
    if category_id:
        receipts = receipts.filter(category_id=category_id)

    sort_state = sorting.build_sort_state(
        request,
        url_name="receipt_table_htmx",
        url_args=[collective_id],
        sortable_columns=SORTABLE_COLUMNS,
        default_table_id="receipt-table",
    )
    receipts = receipts.order_by(sort_state.sort)

    return render(request, "ledger/receipt_management/partials/receipt_table.html", {
        "collective": collective,
        "receipts": receipts,
        "current_sort": sort_state.sort,
        "table_id": sort_state.table_id,
        "sort_links": sort_state.sort_links,
    })


@login_required
def receipt_details_htmx(request, receipt_id):
    """HTMX endpoint: linked transactions for a receipt."""
    receipt = get_object_or_404(Receipt, id=receipt_id)

    if not access.can_access_account_holder(request.user, receipt.collective):
        return HttpResponse("Not allowed", status=403)

    transactions = (
        Transaction.objects
        .filter(receipt=receipt)
        .select_related("created_by_holder")
        .prefetch_related("lines__account__account_holder")
        .order_by("-date", "-id")
    )

    return render(request, "ledger/receipt_management/partials/receipt_details.html", {
        "receipt": receipt,
        "transactions": transactions,
    })


@login_required
def add_receipt_htmx(request, collective_id):
    """HTMX endpoint: create-receipt modal form (with its upload widget)."""
    # TODO permission check
    user = request.user
    collective = get_object_or_404(AccountHolder, id=collective_id)

    upload_session = receipt_services.start_receipt_upload_session(
        request.GET.get("upload_session_id")
    )

    if request.method == "GET":
        form = ReceiptForm(
            upload_session=upload_session,
            django_user=user,
            collective=collective,
            initial={"collective": collective},
        )
        return render(request, "ledger/receipt_management/partials/receipt_form.html", {
            "form": form,
            "receipt": None,
            "collective": collective,
            "upload_session": upload_session,
        })

    form = ReceiptForm(
        request.POST,
        request.FILES,
        upload_session=upload_session,
        django_user=user,
        collective=collective,
    )

    if not form.is_valid():
        return render(request, "ledger/receipt_management/partials/receipt_form.html", {
            "form": form,
            "receipt": None,
            "collective": collective,
            "upload_session": upload_session,
        }, status=400)

    receipt = form.save(commit=False)

    # permission check (same safety as edit)
    if not access.can_access_account_holder(user, collective):
        return HttpResponse("Not allowed", status=403)

    receipt_services.create_receipt(
        receipt=receipt, collective=collective, user=user, upload_session=upload_session,
    )

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_receipt_htmx(request, receipt_id):
    """HTMX endpoint: edit-receipt modal form (with its upload widget)."""
    receipt = get_object_or_404(Receipt, id=receipt_id)

    if not access.can_access_account_holder(request.user, receipt.collective):
        return HttpResponse("Not allowed", status=403)

    upload_session = receipt.upload_session
    upload_session.start_timer()

    if request.method == "GET":
        form = ReceiptForm(
            instance=receipt,
            upload_session=upload_session,
            django_user=request.user,
            collective=receipt.collective,
        )
        return render(request, "ledger/receipt_management/partials/receipt_form.html", {
            "form": form,
            "receipt": receipt,
            "collective": receipt.collective,
            "upload_session": upload_session,
        })

    form = ReceiptForm(
        request.POST,
        request.FILES,
        upload_session=upload_session,
        instance=receipt,
        django_user=request.user,
        collective=receipt.collective,
    )

    if not form.is_valid():
        return render(request, "ledger/receipt_management/partials/receipt_form.html", {
            "form": form,
            "receipt": receipt,
            "collective": receipt.collective,
            "upload_session": upload_session,
        }, status=400)

    receipt_services.save_edited_receipt(form.save(commit=False), upload_session)

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def receipt_file_htmx(request, receipt_id):
    """HTMX endpoint (action): streams the receipt's attached file."""
    # TODO permissions
    receipt = get_object_or_404(Receipt, id=receipt_id)
    return FileResponse(receipt.upload_session.file.open("rb"))
