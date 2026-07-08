from django.core.exceptions import ValidationError
from django.db import models

from .account_holders import AccountHolder


class FinanceAccount(models.Model):
    class Type(models.TextChoices):
        CASH = "cash", "Cash"
        BANK = "bank", "Bank Account"

    account_holder = models.ForeignKey(
        AccountHolder,
        on_delete=models.CASCADE,
        related_name="finance_accounts",
    )

    name = models.CharField(max_length=255)

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.CASH,
    )

    currency = models.CharField(max_length=10, default="EUR")

    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def can_delete(self):
        return not self.transaction_lines.exists()

    @property
    def balance(self):
        return self.transaction_lines.aggregate(
            total=models.Sum("amount")
        )["total"] or 0

    def __str__(self):
        return f"{self.account_holder.name} - {self.name} ({self.type})"

    def clean(self):
        if self.type == FinanceAccount.Type.BANK and not hasattr(self, "bank_details"):
            raise ValidationError("Bank accounts must have bank details.")


class BankAccountDetails(models.Model):
    finance_account = models.OneToOneField(
        "FinanceAccount",
        on_delete=models.CASCADE,
        related_name="bank_details",
    )

    iban = models.CharField(max_length=34)
    bic = models.CharField(max_length=11, blank=True)

    bank_name = models.CharField(max_length=255, blank=True)

    account_holder_name = models.CharField(max_length=255)

    def clean(self):
        if self.finance_account.type != FinanceAccount.Type.BANK:
            raise ValidationError("Bank details only allowed for BANK finance accounts.")
