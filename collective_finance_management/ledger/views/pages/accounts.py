"""PAGES: finance account management & the single-account overview."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...models import FinanceAccount
from ...services import access, accounts as account_services


@login_required
def account_management_page(request):
    """PAGE: personal + collective account sections with add/manage actions."""
    sections = account_services.build_account_management_sections(request.user)
    return render(request, "ledger/account_management/account_holder_main.html", {
        "sections": sections,
    })


@login_required
def account_overview_page(request, account_id):
    """PAGE: balance, details and charts for a single finance account."""
    account = get_object_or_404(FinanceAccount, id=account_id)
    if not access.can_access_account_holder(request.user, account.account_holder):
        return HttpResponse("Not allowed", status=403)

    context = account_services.account_overview_context(account)

    return render(request, "ledger/account_management/account_overview.html", {
        "account": account,
        **context,
    })
