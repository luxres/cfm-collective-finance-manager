"""HTMX ENDPOINTS: the transaction form embedded in the receipt overview page."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from ...forms import TransactionCommandForm
from ...models import Receipt, Transaction
from ...services import transactions as transaction_services


@login_required
def add_transaction_htmx(request, receipt_id):
    """HTMX endpoint: create-transaction modal form, linked to a receipt."""
    receipt = get_object_or_404(Receipt, id=receipt_id)

    if request.method == "GET":
        return render(request, "ledger/receipt_management/partials/transaction_form.html", {
            "form": TransactionCommandForm(),
            "receipt": receipt,
            "transaction": None,
        })

    form = TransactionCommandForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/receipt_management/partials/transaction_form.html", {
            "form": form,
            "receipt": receipt,
            "transaction": None,
        }, status=400)

    transaction_services.create_transaction(
        data=form.cleaned_data, user=request.user, receipt_id=receipt_id,
    )

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_transaction_htmx(request, transaction_id):
    """HTMX endpoint: edit-transaction modal form."""
    transaction = get_object_or_404(Transaction, id=transaction_id)

    debit_line = transaction.lines.filter(amount__lt=0).first()
    credit_line = transaction.lines.filter(amount__gt=0).first()

    if request.method == "GET":
        initial = {
            "description": transaction.description,
            "date": transaction.date,
            "amount": abs(transaction.lines.first().amount) if transaction.lines.exists() else None,
            "from_account": debit_line.account if debit_line else None,
            "to_account": credit_line.account if credit_line else None,
            "from_holder": debit_line.account.account_holder if debit_line else None,
            "to_holder": credit_line.account.account_holder if credit_line else None,
        }

        return render(request, "ledger/receipt_management/partials/transaction_form.html", {
            "form": TransactionCommandForm(initial=initial),
            "transaction": transaction,
        })

    form = TransactionCommandForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/receipt_management/partials/transaction_form.html", {
            "form": form,
            "transaction": transaction,
        }, status=400)

    transaction_services.update_transaction(
        transaction=transaction, data=form.cleaned_data, user=request.user,
    )

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@require_http_methods(["DELETE"])
@login_required
def delete_transaction_htmx(request, transaction_id):
    """HTMX endpoint (action): deletes a transaction, refused if not allowed."""
    transaction = get_object_or_404(Transaction, id=transaction_id)

    # TODO check permissions

    if not transaction.can_delete:
        return HttpResponseBadRequest(
            "This transaction cannot be deleted."
        )

    transaction.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
