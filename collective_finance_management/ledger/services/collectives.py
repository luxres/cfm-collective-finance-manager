"""
"Which collective is currently active" is asked, in the same way, by
every management page that has a collective switcher (categories,
events, receipts, assets). Centralised here instead of being
copy-pasted per view.
"""
from typing import Optional

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet

from ..models import AccountHolder
from . import access


def resolve_active_collective(
    user: AbstractBaseUser,
    requested_id: Optional[str],
    collectives: Optional[QuerySet[AccountHolder]] = None,
) -> Optional[AccountHolder]:
    """
    Picks the collective a management page should display:
    the one requested via `?collective=<id>` if the user has access to
    it, otherwise the user's first collective.
    """
    if collectives is None:
        collectives = access.get_user_collectives(user)

    active_collective = None
    if requested_id:
        active_collective = collectives.filter(id=requested_id).first()

    if not active_collective:
        active_collective = collectives.first()

    return active_collective
