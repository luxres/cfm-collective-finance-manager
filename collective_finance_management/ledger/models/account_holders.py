from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AccountHolder(models.Model):
    class HolderType(models.TextChoices):
        USER = "user", "User"
        COLLECTIVE = "collective", "Collective"
        EXTERNAL = "external", "External"

    name = models.CharField(max_length=255)

    holder_type = models.CharField(
        max_length=20,
        choices=HolderType.choices,
    )

    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def can_delete(self):
        return True

    def __str__(self):
        return self.name

    def clean(self):
        if self.holder_type == self.HolderType.USER:
            # Unsaved instances cannot use reverse relations
            if self.pk and self.memberships.count() > 1:
                raise ValidationError(
                    "USER account holders can only have one member."
                )


class AccountHolderMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        MEMBER = "member", "Member"

    django_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="account_memberships",
    )

    account_holder = models.ForeignKey(
        "AccountHolder",
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.MEMBER,
    )

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("django_user", "account_holder")

    def clean(self):
        # enforce business rules
        if self.account_holder.holder_type == "user":
            # only ONE membership allowed for user-type accounts
            if AccountHolderMembership.objects.filter(
                account_holder=self.account_holder
            ).exclude(pk=self.pk).exists():
                raise ValidationError("User-type AccountHolder can only have one member.")
