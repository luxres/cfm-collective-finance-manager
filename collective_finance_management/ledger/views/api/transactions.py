"""API: standalone JSON endpoint for creating a transfer directly (no receipt)."""
from datetime import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from ...models import FinanceAccount
from ...services import transactions as transaction_services


@login_required
@require_POST
def create_transaction_api(request):
    """API: creates a standalone double-entry transfer between two accounts."""
    date = request.POST.get("date")
    date = timezone.make_aware(datetime.fromisoformat(date)) if date else timezone.now()

    from_account = get_object_or_404(FinanceAccount, id=request.POST.get("from_account"))
    to_account = get_object_or_404(FinanceAccount, id=request.POST.get("to_account"))

    transaction = transaction_services.create_transfer(
        description=request.POST.get("description"),
        date=date,
        amount=Decimal(request.POST.get("amount")),
        from_account=from_account,
        to_account=to_account,
        user=request.user,
        receipt_id=request.POST.get("receipt_id"),
    )

    return JsonResponse({
        "success": True,
        "transaction_id": transaction.id,
    })
