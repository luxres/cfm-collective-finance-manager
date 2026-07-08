from decimal import Decimal
import uuid
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import models

from .account_holders import AccountHolder
from .categories import Category
from .upload_sessions import UploadSession


class Receipt(models.Model):

    class Direction(models.TextChoices):
        INGOING = "in", "Ingoing (money received)"
        OUTGOING = "out", "Outgoing (money spent)"
        INTERNAL = "intern", "Internal Transfer"

    class TaxCategory(models.TextChoices):
        IDEEL = "ideel", "Ideeler Bereich"
        VERMOEGEN = "vermoegen", "Vermögensverwaltung"
        ZWECK = "zweck", "Zweckbereich"
        WIRTSCHAFT = "wirtschaftlich", "Wirtschaftlicher Bereich"

    class AddressStatus(models.TextChoices):
        ALIGNED = "ok", "ok"
        DIFFERS = "incorrect", "incorrect"
    
    class DocumentStatus(models.TextChoices):
        ATTACHED = "attached", "Attached"
        PENDING = "pending", "Missing receipt"
        NONE = "no", "No receipt"

    note = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    date = models.DateField()

    direction = models.CharField(
        max_length=10,
        choices=Direction.choices,
        default=Direction.OUTGOING,
    )

    tax_category = models.CharField(
        max_length=20,
        choices=TaxCategory.choices,
        null=True,
        blank=True,
    )

    address_status = models.CharField(
        max_length=10,
        choices=AddressStatus.choices,
        default=AddressStatus.ALIGNED,
    )

    document_status = models.CharField(
        choices=DocumentStatus.choices,
        default=DocumentStatus.NONE,
    )

    responsible_holder = models.ForeignKey(
        "AccountHolder",
        on_delete=models.PROTECT,
        related_name="responsible_receipts",
    )

    uploaded_by_holder = models.ForeignKey(
        "AccountHolder",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_receipts",
    )

    collective = models.ForeignKey(
        "AccountHolder",
        on_delete=models.PROTECT,
        related_name="collective_receipts",
        null=True,
        blank=True,
    )

    counterparty = models.ForeignKey(
        "AccountHolder",
        on_delete=models.PROTECT,
        related_name="counterparty_receipts",
        null=True,
        blank=True,
    )

    event = models.ForeignKey(
        "Event",
        on_delete=models.SET_NULL,
        related_name="receipts",
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="receipts",
    )

    upload_session = models.OneToOneField(
            UploadSession,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name="receipt",
        )
    
    uploaded_at = models.DateTimeField(auto_now_add=True)

   
    def collective_transaction_amount(self):
        """
        Returns the net amount that reached the collective
        through linked transactions.
        """

        if not self.collective:
            return Decimal("0")

        total = Decimal("0")

        for transaction in self.transactions.all():
            for line in transaction.lines.filter(
                account__account_holder=self.collective
            ):
                total += line.amount

        return total

    @property
    def is_closed(self):
        """
        Receipt is closed when the collective received/paid
        exactly the receipt amount.
        """

        if not self.collective:
            return False

        if self.direction == self.Direction.INTERNAL:
            # ensure all involved lines stay inside the same collective
            total = Decimal("0")

            for transaction in self.transactions.all():
                for line in transaction.lines.all():
                    if line.account.account_holder != self.collective:
                        return False  # external leakage → not valid internal transfer

                    total += line.amount

            return total == 0.0

        expected = self.amount

        if self.direction == self.Direction.OUTGOING:
            expected = -expected

        return self.collective_transaction_amount() == expected

    def clean(self):
        errors = {}

        if self.collective:
            if self.collective.holder_type != AccountHolder.HolderType.COLLECTIVE:
                errors["collective"] = (
                    "Collective must reference an AccountHolder of type COLLECTIVE."
                )

        if self.responsible_holder:
            if self.responsible_holder.holder_type != AccountHolder.HolderType.USER:
                errors["responsible_holder"] = (
                    "Responsible holder must reference an AccountHolder of type USER."
                )

        if self.uploaded_by_holder:
            if self.uploaded_by_holder.holder_type != AccountHolder.HolderType.USER:
                errors["uploaded_by_holder"] = (
                    "Uploaded-by holder must reference an AccountHolder of type USER."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"Receipt #{self.id}"
