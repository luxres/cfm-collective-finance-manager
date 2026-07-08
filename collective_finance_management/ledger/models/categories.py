from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal
from django.db.models import Sum


class Category(models.Model):

    class CategoryType(models.TextChoices):
        RECEIPT = "receipt", "Receipt"
        EVENT = "event", "Event"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    type = models.CharField(
        max_length=20,
        choices=CategoryType.choices
    )

    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
    )

    collective = models.ForeignKey(
        "AccountHolder",
        on_delete=models.CASCADE,
        related_name="categories"
    )

    def clean(self):
        if not self.parent:
            return

        errors = {}

        if self.parent_id == self.id:
            errors["parent"] = "A category cannot be its own parent."
        elif self.collective_id and self.parent.collective_id != self.collective_id:
            errors["parent"] = "Parent category must belong to the same collective."
        elif self.parent.type != self.type:
            errors["parent"] = "Parent category must be of the same type (receipt/event)."
        else:
            # Walking up from the proposed parent must never reach `self` -
            # if it does, `self` is an ancestor of its own proposed parent,
            # i.e. assigning it would create a cycle.
            ancestor = self.parent
            seen = set()
            while ancestor is not None:
                if self.pk and ancestor.pk == self.pk:
                    errors["parent"] = "This would create a circular category hierarchy."
                    break
                if ancestor.pk in seen:
                    break  # already-broken data elsewhere; don't loop forever
                seen.add(ancestor.pk)
                ancestor = ancestor.parent

        if errors:
            raise ValidationError(errors)

    @property
    def can_delete(self):
        if self.children.exists():
            return False

        if self.type == self.CategoryType.RECEIPT:
            return not self.receipts.exists()

        if self.type == self.CategoryType.EVENT:
            return not self.events.exists()

    def __str__(self):
        return f"{self.name} ({self.type})"

    def get_descendant_ids(self):
        """All descendant category ids (not including self), recursively."""
        ids = []
        for child in self.children.all():
            ids.append(child.id)
            ids.extend(child.get_descendant_ids())
        return ids

    def _category_ids_for_totals(self):
        """Self + every descendant - totals roll up the whole subtree."""
        return [self.id] + self.get_descendant_ids()

    def incoming_total(self):
        from .receipts import Receipt
        category_ids = self._category_ids_for_totals()

        if self.type == self.CategoryType.RECEIPT:
            return (
                Receipt.objects
                .filter(category_id__in=category_ids, direction=Receipt.Direction.INGOING)
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

        if self.type == self.CategoryType.EVENT:
            from .events import Event
            return sum(
                (event.incoming_total() for event in Event.objects.filter(category_id__in=category_ids)),
                Decimal("0.00"),
            )

        return Decimal("0.00")

    def outgoing_total(self):
        from .receipts import Receipt
        category_ids = self._category_ids_for_totals()

        if self.type == self.CategoryType.RECEIPT:
            return (
                Receipt.objects
                .filter(category_id__in=category_ids, direction=Receipt.Direction.OUTGOING)
                .aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )

        if self.type == self.CategoryType.EVENT:
            from .events import Event
            return sum(
                (event.outgoing_total() for event in Event.objects.filter(category_id__in=category_ids)),
                Decimal("0.00"),
            )

        return Decimal("0.00")

    def balance_total(self):
        return self.incoming_total() - self.outgoing_total()