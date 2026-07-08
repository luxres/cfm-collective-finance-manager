"""Business logic for external parties (AccountHolders of type EXTERNAL)."""
from django.db.models import QuerySet

from ..models import AccountHolder


def get_external_parties() -> QuerySet[AccountHolder]:
    return AccountHolder.objects.filter(
        holder_type=AccountHolder.HolderType.EXTERNAL
    )


def get_external_parties_with_accounts() -> QuerySet[AccountHolder]:
    return get_external_parties().prefetch_related("finance_accounts")
