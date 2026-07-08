"""Business logic backing the top-level dashboard page."""
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser

from ..models import FinanceAccount
from . import access


def build_account_balance_timeline(account: FinanceAccount) -> dict:
    """Running balance over time for a single account (for its sparkline)."""
    lines = (
        account.transaction_lines
        .select_related("transaction")
        .order_by("transaction__date")
    )

    balance = Decimal("0")
    labels = []
    data = []

    for line in lines:
        balance += line.amount
        labels.append(line.transaction.date.strftime("%Y-%m-%d"))
        data.append(float(balance))

    return {"labels": labels, "data": data}


def build_accounts_timeline(accounts) -> dict:
    return {account.id: build_account_balance_timeline(account) for account in accounts}


def build_dashboard_context(user: AbstractBaseUser) -> dict:
    personal_holder = access.get_user_account_holder(user)
    collective_holders = access.get_user_collectives(user)

    personal_accounts = (
        FinanceAccount.objects.filter(
            account_holder=personal_holder
        ).prefetch_related("transaction_lines__transaction")
        if personal_holder else FinanceAccount.objects.none()
    )

    collective_accounts = FinanceAccount.objects.filter(
        account_holder__in=collective_holders
    ).prefetch_related("transaction_lines__transaction")

    memberships = user.account_memberships.select_related("account_holder")

    return {
        "user_memberships": memberships,
        "personal_accounts": personal_accounts,
        "collective_accounts": collective_accounts,
        "personal_timeline": build_accounts_timeline(personal_accounts),
        "collective_timeline": build_accounts_timeline(collective_accounts),
    }
