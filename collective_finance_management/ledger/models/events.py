from decimal import Decimal
from django.db.models import Sum
from django.db import models
from django.core.exceptions import ValidationError
from .receipts import Receipt



class Event(models.Model):
    name = models.CharField(max_length=255)

    start_date = models.DateField()
    end_date = models.DateField()

    responsible_holder = models.ForeignKey(
        "AccountHolder",
        on_delete=models.PROTECT,
        related_name="responsible_events",
    )

    collective = models.ForeignKey(
        "AccountHolder",
        on_delete=models.PROTECT,
        related_name="events",
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        "Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def can_delete(self):
        return not self.receipts.exists()

    def __str__(self):
        return self.name

    def clean(self):
        if self.end_date < self.start_date:
            raise ValidationError("end_date cannot be before start_date")

    def incoming_total(self):
        """
        Sum of all INGOING receipts linked to this event.
        """
        return (
            self.receipts
            .filter(direction=Receipt.Direction.INGOING)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    def outgoing_total(self):
        """
        Sum of all OUTGOING receipts linked to this event.
        """
        return (
            self.receipts
            .filter(direction=Receipt.Direction.OUTGOING)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )

    def balance_total(self):
        """
        Net balance = incoming - outgoing
        (internal transfers ignored)
        """
        return self.incoming_total() - self.outgoing_total()