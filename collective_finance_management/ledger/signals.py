from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import AccountHolder, AccountHolderMembership, FinanceAccount

User = get_user_model()


@receiver(post_save, sender=User)
def create_personal_account_holder(sender, instance, created, **kwargs):
    if not created:
        return

    # 1. Create personal AccountHolder
    holder = AccountHolder.objects.create(
        name=instance.username,
        holder_type=AccountHolder.HolderType.USER,
        description="Personal account holder",
        active=True,
    )

    # 2. Link user via membership
    AccountHolderMembership.objects.create(
        django_user=instance,
        account_holder=holder,
        role=AccountHolderMembership.Role.ADMIN,
    )

        # 3. Create default finance account
    FinanceAccount.objects.create(
        account_holder=holder,
        name="Default Account",
    )

@receiver(post_save, sender=AccountHolder)
def create_default_account_for_external_party(sender, instance, created, **kwargs):
    if not created:
        return

    if instance.holder_type != AccountHolder.HolderType.EXTERNAL:
        return

    FinanceAccount.objects.create(
        account_holder=instance,
        name="Default Account",
    )