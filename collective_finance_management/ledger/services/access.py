"""
Membership & permission logic for AccountHolders.

Anything that answers "is this user allowed to ..." or "which account
holders can this user see/manage" lives here so it has a single home
instead of being re-implemented per feature.
"""
from typing import Optional, Literal

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Q, QuerySet

from ..models import AccountHolder, AccountHolderMembership

RoleType = Literal["admin", "member"]


def get_membership(
    user: AbstractBaseUser,
    account_holder: AccountHolder,
) -> Optional[AccountHolderMembership]:
    """Returns the membership object for a user in an account holder."""
    return (
        AccountHolderMembership.objects
        .filter(django_user=user, account_holder=account_holder)
        .only("role", "id")
        .first()
    )


def get_user_role_in_account_holder(
    user: AbstractBaseUser,
    account_holder: AccountHolder,
) -> Optional[RoleType]:
    """Returns the role of a user in an account holder (if any)."""
    membership = get_membership(user, account_holder)
    return membership.role if membership else None


def is_member(user: AbstractBaseUser, account_holder: AccountHolder) -> bool:
    return get_membership(user, account_holder) is not None


def is_admin(user: AbstractBaseUser, account_holder: AccountHolder) -> bool:
    return get_user_role_in_account_holder(user, account_holder) == "admin"


def get_user_account_holder(user: AbstractBaseUser) -> Optional[AccountHolder]:
    """Returns the USER-type AccountHolder linked to this user."""
    membership = (
        AccountHolderMembership.objects
        .select_related("account_holder")
        .filter(
            django_user=user,
            account_holder__holder_type=AccountHolder.HolderType.USER,
        )
        .first()
    )
    return membership.account_holder if membership else None


def get_all_user_account_holders() -> QuerySet[AccountHolder]:
    """Returns all USER-type AccountHolders."""
    return AccountHolder.objects.filter(
        holder_type=AccountHolder.HolderType.USER
    )


def get_user_collectives(
    user: AbstractBaseUser,
    role: Optional[RoleType] = None,
) -> QuerySet[AccountHolder]:
    """Collectives the user belongs to. Optionally filter by role."""
    qs = AccountHolder.objects.filter(
        holder_type=AccountHolder.HolderType.COLLECTIVE,
        memberships__django_user=user,
    )

    if role:
        qs = qs.filter(memberships__role=role)

    return qs.distinct()


def get_external_holders(
    user: AbstractBaseUser,
) -> QuerySet[AccountHolder]:
    """
    All EXTERNAL account holders
    """
    return AccountHolder.objects.filter(holder_type=AccountHolder.HolderType.EXTERNAL).distinct()


def get_accessible_account_holders(
    user: AbstractBaseUser,
) -> QuerySet[AccountHolder]:
    """
    All account holders the user can access (member or admin), plus all
    personal and external-party holders.
    """
    return AccountHolder.objects.filter(
        Q(memberships__django_user=user) |
        Q(holder_type=AccountHolder.HolderType.USER) |
        Q(holder_type=AccountHolder.HolderType.EXTERNAL)
    ).distinct()


def get_manageable_account_holders(
    user: AbstractBaseUser,
) -> QuerySet[AccountHolder]:
    """Account holders the user can manage (admin only)."""
    return AccountHolder.objects.filter(
        memberships__django_user=user,
        memberships__role="admin",
    ).distinct()


def can_access_account_holder(
    user: AbstractBaseUser,
    account_holder: AccountHolder,
) -> bool:
    """User has any membership (member or admin), or it's their own personal holder."""
    return AccountHolderMembership.objects.filter(
        django_user=user,
        account_holder=account_holder,
    ).exists() or account_holder.holder_type == AccountHolder.HolderType.USER


def can_manage_account_holder(
    user: AbstractBaseUser,
    account_holder: AccountHolder,
) -> bool:
    """User must be admin in that account holder."""
    return AccountHolderMembership.objects.filter(
        django_user=user,
        account_holder=account_holder,
        role="admin",
    ).exists()
