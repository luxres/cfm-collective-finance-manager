from decimal import Decimal
from django.db import models
from django.utils import timezone

from .receipts import Receipt


class AssetPool(models.Model):
    """
    Collective depreciation pool (Sammelposten).
    """

    name = models.CharField(max_length=30)

    acquisition_year = models.PositiveSmallIntegerField(
        default=timezone.now().year
    )

    depreciation_years = models.PositiveSmallIntegerField(
        default=5,
        help_text="Normally 5 years according to German GWG Sammelposten."
    )

    collective = models.ForeignKey(
        "AccountHolder",
        on_delete=models.CASCADE,
        related_name="asset_pools",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.acquisition_year})"

    @property
    def acquisition_cost(self):
        return sum(a.purchase_price for a in self.assets.all())

    @property
    def annual_depreciation(self):
        if self.depreciation_years == 0:
            return Decimal("0.00")

        return self.acquisition_cost / Decimal(self.depreciation_years)

    def accumulated_depreciation(self, year=None):
        if year is None:
            year = timezone.now().year

        years = max(0, year - self.acquisition_year + 1)
        years = min(years, self.depreciation_years)

        return self.annual_depreciation * years

    def remaining_value(self, year=None):
        return max(
            Decimal("0.00"),
            self.acquisition_cost - self.accumulated_depreciation(year),
        )


class Asset(models.Model):

    class DeprecationMethod(models.TextChoices):
        LINEAR = "linear", "Linear"
        NONE = "none", "Immediate Expense"

    name = models.CharField(max_length=255)

    collective = models.ForeignKey(
        "AccountHolder",
        on_delete=models.CASCADE,
        related_name="assets",
    )

    receipt = models.ForeignKey(
        Receipt,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
    )

    purchase_date = models.DateField()

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    useful_life = models.PositiveSmallIntegerField(
        default=3,
        help_text="Useful life in years according to AfA table.",
    )

    depreciation_method = models.CharField(
        max_length=20,
        choices=DeprecationMethod.choices,
        default=DeprecationMethod.LINEAR,
    )

    depreciation_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal("33.33"),
        help_text="Annual depreciation percentage.",
    )

    asset_pool = models.ForeignKey(
        AssetPool,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assets",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    @property
    def is_gwg(self):
        """
        GWG threshold according to current German tax law.
        """
        return self.purchase_price <= Decimal("800.00")

    @property
    def annual_depreciation(self):
        if self.asset_pool:
            return Decimal("0.00")

        if self.depreciation_method == self.DeprecationMethod.NONE:
            return self.purchase_price

        return self.purchase_price / Decimal(self.useful_life)

    def accumulated_depreciation(self, year=None):
        if self.asset_pool:
            return Decimal("0.00")

        if year is None:
            year = timezone.now().year

        years = max(0, year - self.purchase_date.year + 1)
        years = min(years, self.useful_life)

        if self.depreciation_method == self.DeprecationMethod.NONE:
            return self.purchase_price

        return self.annual_depreciation * years

    def book_value(self, year=None):
        if self.asset_pool:
            return Decimal("0.00")

        return max(
            Decimal("0.00"),
            self.purchase_price - self.accumulated_depreciation(year),
        )

    @property
    def fully_depreciated(self):
        return self.book_value() <= Decimal("0.00")

    def save(self, *args, **kwargs):
        if self.useful_life:
            self.depreciation_rate = (
                Decimal("100.00") / Decimal(self.useful_life)
            ).quantize(Decimal("0.01"))

        super().save(*args, **kwargs)