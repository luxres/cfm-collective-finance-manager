"""HTMX ENDPOINTS: fragments used by the account management / overview pages."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from ...forms import BankAccountCommandForm, FinanceAccountForm
from ...models import AccountHolder, FinanceAccount
from ...services import access, accounts as account_services


@login_required
def accounts_by_holder_htmx(request, account_holder_id):
    """HTMX endpoint: accounts card for one holder, used inside the accounts page."""
    account_holder = get_object_or_404(AccountHolder, id=account_holder_id)
    all_accounts = FinanceAccount.objects.filter(account_holder=account_holder)

    membership = access.get_membership(request.user, account_holder)

    return render(request, "ledger/account_management/partials/account_holder_card.html", {
        "holder": account_holder,
        "accounts": all_accounts,
        "cash_accounts": all_accounts.filter(type=FinanceAccount.Type.CASH),
        "bank_accounts": all_accounts.filter(type=FinanceAccount.Type.BANK),
        "membership": membership,
    })


@login_required
def account_transactions_htmx(request, account_id):
    """HTMX endpoint: transaction line table for one account."""
    account = get_object_or_404(FinanceAccount, pk=account_id)
    lines, saldo = account_services.get_account_transaction_lines(account)

    return render(request, "ledger/account_management/partials/transaction_line_table.html", {
        "account": account,
        "lines": lines,
        "saldo": saldo,
    })


@login_required
def add_cash_account_htmx(request, account_holder_id):
    """HTMX endpoint: create-cash-account modal form."""
    # TODO add permissions
    holder = get_object_or_404(AccountHolder, pk=account_holder_id)

    if request.method == "GET":
        form = FinanceAccountForm(initial={"account_holder": holder})
        return render(request, "ledger/account_management/partials/cash_account_form.html", {
            "form": form,
            "holder": holder,
            "account": None,
        })

    form = FinanceAccountForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/account_management/partials/cash_account_form.html", {
            "form": form,
            "holder": holder,
            "account": None,
        }, status=400)

    account_services.finalize_cash_account(form.save(commit=False), holder)

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_cash_account_htmx(request, account_id):
    """HTMX endpoint: edit-cash-account modal form."""
    # TODO add permissions
    account = get_object_or_404(FinanceAccount, pk=account_id)

    if request.method == "GET":
        form = FinanceAccountForm(initial={
            "account_holder": account.account_holder,
            "name": account.name,
        })
        return render(request, "ledger/account_management/partials/cash_account_form.html", {
            "form": form,
            "holder": account.account_holder,
            "account": account,
        })

    form = FinanceAccountForm(request.POST, instance=account)

    if not form.is_valid():
        return render(request, "ledger/account_management/partials/cash_account_form.html", {
            "form": form,
            "holder": account.account_holder,
            "account": account,
        }, status=400)

    account_services.finalize_cash_account(form.save(commit=False), account.account_holder)

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def add_bank_account_htmx(request, account_holder_id):
    """HTMX endpoint: create-bank-account modal form."""
    holder = get_object_or_404(AccountHolder, pk=account_holder_id)

    if request.method == "GET":
        form = BankAccountCommandForm(initial={"account_holder": holder})
        return render(request, "ledger/account_management/partials/bank_account_form.html", {
            "form": form,
            "holder": holder,
        })

    form = BankAccountCommandForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/account_management/partials/bank_account_form.html", {
            "form": form,
            "holder": holder,
        }, status=400)

    account_services.create_bank_account(holder, form.cleaned_data)

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_bank_account_htmx(request, account_id):
    """HTMX endpoint: edit-bank-account modal form."""
    account = get_object_or_404(FinanceAccount, pk=account_id, type=FinanceAccount.Type.BANK)
    bank_details = getattr(account, "bank_details", None)

    if request.method == "GET":
        form = BankAccountCommandForm(initial={
            "account_holder": account.account_holder,
            "account_name": account.name,
            "currency": account.currency,
            "iban": bank_details.iban if bank_details else "",
            "bic": bank_details.bic if bank_details else "",
            "bank_name": bank_details.bank_name if bank_details else "",
            "account_holder_name": bank_details.account_holder_name if bank_details else "",
        })
        return render(request, "ledger/account_management/partials/bank_account_form.html", {
            "form": form,
            "account": account,
            "holder": account.account_holder,
        })

    form = BankAccountCommandForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/account_management/partials/bank_account_form.html", {
            "form": form,
            "account": account,
            "holder": account.account_holder,
        }, status=400)

    account_services.update_bank_account(account, form.cleaned_data)

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@require_http_methods(["DELETE"])
@login_required
def delete_account_htmx(request, account_id):
    """HTMX endpoint (action): deletes an account, refused if it has transactions."""
    account = get_object_or_404(FinanceAccount, id=account_id)

    # TODO check permissions

    if not account.can_delete:
        return HttpResponseBadRequest(
            "This account cannot be deleted because it has transactions."
        )

    account.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
