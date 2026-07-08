"""
Business logic for AccountHolders / FinanceAccounts / bank account
details: building the accounts management page sections, creating and
updating cash & bank accounts, and the account overview data.
"""
from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction as db_transaction
from django.db.models import Exists, OuterRef, Sum, QuerySet

from ..models import AccountHolder, BankAccountDetails, FinanceAccount, TransactionLine
from . import access, overview


def annotated_accounts_for_holder(holder: AccountHolder) -> QuerySet[FinanceAccount]:
    """Accounts for a holder, annotated with whether they have transactions."""
    return FinanceAccount.objects.filter(
        account_holder=holder
    ).annotate(
        has_transactions=Exists(
            TransactionLine.objects.filter(account=OuterRef("pk"))
        )
    )


def build_account_management_sections(user: AbstractBaseUser) -> list[dict]:
    """
    Builds the list of sections (personal holder + every collective the
    user can see) shown on the accounts management page, each with its
    accounts and the permissions the current user has over it.
    """
    sections = []

    personal_holder = access.get_user_account_holder(user)
    sections.append({
        "holder": personal_holder,
        "accounts": annotated_accounts_for_holder(personal_holder) if personal_holder else FinanceAccount.objects.none(),
        "can_add": True,
        "is_personal": True,
        "can_manage": True,
    })

    for holder in access.get_user_collectives(user):
        sections.append({
            "holder": holder,
            "accounts": annotated_accounts_for_holder(holder),
            "can_add": access.can_manage_account_holder(user, holder),
            "can_manage": access.can_manage_account_holder(user, holder),
            "is_personal": False,
        })

    return sections


def account_overview_context(account: FinanceAccount) -> dict:
    """Header + timeline data for the account overview page."""
    lines = account.transaction_lines.select_related("transaction")
    entries = (
        (
            line.transaction.date,
            "in" if (line.amount or 0) >= 0 else "out",
            abs(float(line.amount or 0)),
        )
        for line in lines
    )
    timeline = overview.build_timeline(entries)

    header = overview.header_context(
        title=account.name,
        type="Bank Account" if account.type == "bank" else "Cash",
        date=account.created_at.strftime("%d. %B %Y") if account.created_at else None,
        rows=[
            {"label": "Holder", "value": account.account_holder.name if account.account_holder else None},
            *([
                {"label": "IBAN", "value": account.bank_details.iban},
                {"label": "BIC", "value": account.bank_details.bic},
                {"label": "Bank", "value": account.bank_details.bank_name},
                {"label": "Account Holder Name", "value": account.bank_details.account_holder_name},
            ] if account.type == "bank" and account.bank_details else []),
        ],
        stats=[
            {
                "label": "Balance",
                "value": account.balance,
                "currency": account.currency,
                "class": "text-success" if account.balance >= 0 else "text-danger",
            },
        ],
    )

    return {
        "header": header,
        "charts_empty_message": "No transactions yet for this account — charts will appear once there is data.",
        **timeline,
    }


def get_account_transaction_lines(account: FinanceAccount):
    """
    Transaction lines for an account, each annotated with its
    counterparty line (the other leg of the same double-entry
    transaction), plus the running saldo.
    """
    lines = (
        account.transaction_lines
        .select_related("transaction", "transaction__created_by_holder")
        .prefetch_related("transaction__receipt__counterparty")
        .order_by("-transaction__date")
    )

    for line in lines:
        other_lines = [l for l in line.transaction.lines.all() if l.pk != line.pk]
        line.counterparty_line = other_lines[0] if other_lines else None

    saldo = lines.aggregate(total=Sum("amount"))["total"] or 0

    return lines, saldo


def finalize_cash_account(account: FinanceAccount, holder: AccountHolder) -> FinanceAccount:
    """Stamps the system fields a cash account needs and saves it."""
    account.account_holder = holder
    account.type = FinanceAccount.Type.CASH
    account.save()
    return account


@db_transaction.atomic
def create_bank_account(holder: AccountHolder, cleaned_data: dict) -> FinanceAccount:
    finance_account = FinanceAccount.objects.create(
        account_holder=holder,
        name=cleaned_data["account_name"],
        currency="EUR",
        type=FinanceAccount.Type.BANK,
    )

    BankAccountDetails.objects.create(
        finance_account=finance_account,
        iban=cleaned_data["iban"],
        bic=cleaned_data.get("bic", ""),
        bank_name=cleaned_data.get("bank_name", ""),
        account_holder_name=cleaned_data["account_holder_name"],
    )

    return finance_account


@db_transaction.atomic
def update_bank_account(account: FinanceAccount, cleaned_data: dict) -> FinanceAccount:
    account.account_holder = cleaned_data["account_holder"]
    account.name = cleaned_data["account_name"]
    account.currency = cleaned_data.get("currency", "EUR")
    account.save()

    BankAccountDetails.objects.update_or_create(
        finance_account=account,
        defaults={
            "iban": cleaned_data["iban"],
            "bic": cleaned_data.get("bic", ""),
            "bank_name": cleaned_data.get("bank_name", ""),
            "account_holder_name": cleaned_data["account_holder_name"],
        },
    )

    return account
