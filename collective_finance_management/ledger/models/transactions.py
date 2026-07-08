from django.core.exceptions import ValidationError
from django.db import models

from .finance_accounts import FinanceAccount


class Transaction(models.Model):
    description = models.CharField(max_length=255)
    date = models.DateField()

    receipt = models.ForeignKey(
        "Receipt",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    created_by_holder = models.ForeignKey(
        "AccountHolder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_transactions",
    )

    @property
    def can_delete(self):
        return True

    def __str__(self):
        return f"{self.id}: {self.description}"

    def clean(self):
        if not self.pk:
            return
        
        total = self.lines.aggregate(
            total=models.Sum("amount")
        )["total"] or 0

        if total != 0:
            raise ValidationError(f"Transaction not balanced: {total}")


class TransactionLine(models.Model):
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.CASCADE,
        related_name="lines",
    )

    account = models.ForeignKey(
        FinanceAccount,
        on_delete=models.PROTECT,
        related_name="transaction_lines",
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    note = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["account"]),
            models.Index(fields=["transaction"]),
        ]  # increase database performance

    def __str__(self):
        return f"{self.account}: {self.amount}"
