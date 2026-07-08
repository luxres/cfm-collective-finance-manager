"""API: plain JSON endpoints (not tied to any template) used by JS on the frontend."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404

from ...models import AccountHolder, FinanceAccount
from ...services import access


@login_required
def finance_accounts_by_holder_api(request, account_holder_id):
    """API: finance accounts belonging to one account holder."""
    holder = get_object_or_404(AccountHolder, id=account_holder_id)

    if not access.get_accessible_account_holders(request.user).filter(id=holder.id).exists():
        return HttpResponseForbidden("Not allowed")

    accounts = (
        FinanceAccount.objects
        .filter(account_holder=holder)
        .values("id", "name", "type")
        .order_by("name")
    )

    return JsonResponse({"accounts": list(accounts)})


@login_required
def finance_account_holders_by_type_api(request):
    """API: account holders of a given `?type=` the user can access."""
    holder_type = request.GET.get("type")

    if not holder_type:
        return JsonResponse({"holders": []})

    holders = access.get_accessible_account_holders(request.user).filter(holder_type=holder_type)

    return JsonResponse({
        "holders": [{"id": h.id, "name": h.name} for h in holders]
    })
