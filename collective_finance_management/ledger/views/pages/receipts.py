"""PAGES: receipt management & the single-receipt overview."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...models import Receipt
from ...services import access, collectives, receipts as receipt_services


@login_required
def receipt_management_page(request):
    """PAGE: receipt table for the active collective, with a collective switcher."""
    user = request.user
    user_collectives = access.get_user_collectives(user)

    active_collective = collectives.resolve_active_collective(
        user, request.GET.get("collective"), user_collectives,
    )

    receipts = (
        receipt_services.get_collective_receipts(active_collective)
        if active_collective else Receipt.objects.none()
    )

    return render(request, "ledger/receipt_management/receipt_main.html", {
        "active_collective": active_collective,
        "receipts": receipts,
        "collectives": user_collectives,
    })


@login_required
def receipt_overview_page(request, receipt_id):
    """PAGE: details, status badges and linked transactions for a receipt."""
    receipt = get_object_or_404(Receipt, id=receipt_id)
    if not access.can_access_account_holder(request.user, receipt.collective):
        return HttpResponse("Not allowed", status=403)

    context = receipt_services.receipt_overview_context(receipt)

    return render(request, "ledger/receipt_management/receipt_overview.html", {
        "receipt": receipt,
        **context,
    })
