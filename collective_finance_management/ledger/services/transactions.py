"""
Double-entry Transaction/TransactionLine business logic.

This is the single place that knows how to turn "move X from A to B"
into a balanced pair of TransactionLines. Both the receipt-linked
transaction form and the standalone JSON transfer API funnel through
here so the bookkeeping rule only exists once.
"""
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction as db_transaction

from ..models import FinanceAccount, Transaction, TransactionLine
from . import access


@db_transaction.atomic
def create_transfer(
    *,
    description: str,
    date,
    amount,
    from_account: FinanceAccount,
    to_account: FinanceAccount,
    user: AbstractBaseUser,
    receipt_id=None,
) -> Transaction:
    """Creates a Transaction plus its two balanced TransactionLines."""
    transaction = Transaction.objects.create(
        description=description,
        date=date,
        created_by_holder=access.get_user_account_holder(user),
        receipt_id=receipt_id,
    )

    TransactionLine.objects.create(
        transaction=transaction,
        account=from_account,
        amount=-amount,
        note=f"To {to_account.account_holder.name} - (Account: {to_account.name})",
    )

    TransactionLine.objects.create(
        transaction=transaction,
        account=to_account,
        amount=amount,
        note=f"From {from_account.account_holder.name} - (Account: {from_account.name})",
    )

    return transaction


@db_transaction.atomic
def update_transfer(transaction: Transaction, *, description: str, date, amount,
                     from_account: FinanceAccount, to_account: FinanceAccount) -> Transaction:
    """Updates a Transaction and rebuilds its two lines from scratch."""
    transaction.description = description
    transaction.date = date
    transaction.save()

    transaction.lines.all().delete()

    TransactionLine.objects.create(
        transaction=transaction,
        account=from_account,
        amount=-amount,
        note=f"To {to_account.account_holder.name} - (Account: {to_account.name})",
    )
    TransactionLine.objects.create(
        transaction=transaction,
        account=to_account,
        amount=amount,
        note=f"From {from_account.account_holder.name} - (Account: {from_account.name})",
    )

    return transaction


# ---------------------------------------------------------------------
# Thin wrappers matching the shapes the two current call sites already
# use (cleaned_data dicts from Django forms), kept so views only ever
# have to unpack `form.cleaned_data` and hand it over.
# ---------------------------------------------------------------------

def create_transaction(data: dict, user: AbstractBaseUser, receipt_id) -> Transaction:
    return create_transfer(
        description=data["description"],
        date=data["date"],
        amount=data["amount"],
        from_account=data["from_account"],
        to_account=data["to_account"],
        user=user,
        receipt_id=receipt_id,
    )


def update_transaction(transaction: Transaction, data: dict, user: AbstractBaseUser) -> Transaction:
    return update_transfer(
        transaction,
        description=data["description"],
        date=data["date"],
        amount=data["amount"],
        from_account=data["from_account"],
        to_account=data["to_account"],
    )
