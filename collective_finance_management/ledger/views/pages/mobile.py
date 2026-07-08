"""PAGE: the mobile "quick add receipt" page - installable to the home screen."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ...forms import QuickAddReceiptForm
from ...services import access, collectives, receipts as receipt_services


@login_required
def mobile_add_receipt_page(request):
    """
    PAGE: standalone, mobile-first page for capturing a receipt in a
    few taps - meant to be added to the home screen and reopened
    repeatedly, not navigated to from the desktop UI. Collective is
    switchable via `?collective=`, same mechanism as the desktop pages.
    """
    user_collectives = access.get_user_collectives(request.user)
    active_collective = collectives.resolve_active_collective(
        request.user, request.GET.get("collective"), user_collectives,
    )

    saved_receipt = None

    if request.method == "POST":
        form = QuickAddReceiptForm(request.POST, request.FILES)

        if form.is_valid() and active_collective:
            saved_receipt = receipt_services.quick_create_receipt(
                collective=active_collective,
                user=request.user,
                direction=form.cleaned_data["direction"],
                amount=form.cleaned_data["amount"],
                date=form.cleaned_data["date"],
                photo=form.cleaned_data.get("photo"),
            )
            # Fresh empty form for the next capture, keeping the same
            # collective selected - this page is meant to be reopened
            # and used again immediately, not navigated away from.
            form = QuickAddReceiptForm()
    else:
        form = QuickAddReceiptForm()

    return render(request, "ledger/mobile/add_receipt.html", {
        "collectives": user_collectives,
        "active_collective": active_collective,
        "form": form,
        "saved_receipt": saved_receipt,
    })
