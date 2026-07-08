from django import forms
from django.utils import timezone
from django.db import transaction as db_transaction
from decimal import Decimal



from .models import (
    AccountHolder,
    AccountHolderMembership,
    FinanceAccount,
    BankAccountDetails,
    Category,
    Event,
    Receipt,
    Transaction,
    TransactionLine,
    Asset,
    AssetPool,
)

from .services.access import (
    get_accessible_account_holders,
    get_all_user_account_holders,
    get_external_holders,
)
from .services.categories import (
    get_event_categories,
    category_choices,
)
from .services.assets import get_asset_pools
from .services.receipts import get_collective_receipts

# =========================================================
# ACCOUNT HOLDER
# =========================================================

class AccountHolderForm(forms.ModelForm):
    class Meta:
        model = AccountHolder
        fields = ["name", "description", "active", "holder_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "holder_type": forms.Select(attrs={"class": "form-select"}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.holder_type = AccountHolder.HolderType.USER
        if commit:
            obj.save()
        return obj

class ExternalPartyForm(forms.ModelForm):
    class Meta:
        model = AccountHolder
        fields = ["name", "description", "active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.holder_type = AccountHolder.HolderType.EXTERNAL
        if commit:
            obj.save()
        return obj


# =========================================================
# FINANCE ACCOUNT
# =========================================================

class FinanceAccountForm(forms.ModelForm):
    class Meta:
        model = FinanceAccount
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
        }

class BankAccountCommandForm(forms.Form):
    # FinanceAccount fields
    # account_holder = forms.ModelChoiceField(
    #     queryset=AccountHolder.objects.all(),
    #     widget=forms.Select(attrs={"class": "form-select"})
    # )

    account_name = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    # BankAccountDetails fields
    iban = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    bic = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    bank_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    account_holder_name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

# =========================================================
# CATEGORIES
# =========================================================
class CategoryForm(forms.ModelForm):
    # Plain ChoiceField (not the default ModelChoiceField a ForeignKey
    # would get) because the choices need to be in tree order with
    # indentation baked into the label - see services.categories.category_choices.
    parent = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Category
        fields = ["name", "description", "parent"]

        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, collective=None, category_type=None, **kwargs):
        instance = kwargs.get("instance")
        # Editing an existing category already carries its own
        # collective/type - no need to make every call site pass them.
        collective = collective or (instance.collective if instance else None)
        category_type = category_type or (instance.type if instance else None)

        super().__init__(*args, **kwargs)

        # Stamp these onto the instance *now*, not after save(commit=False)
        # in the view - Category.clean() (which checks parent's
        # collective/type match) runs automatically during is_valid(),
        # so it needs to already see the right values, not just at the
        # end once the view gets around to setting them.
        if collective is not None:
            self.instance.collective = collective
        if category_type is not None:
            self.instance.type = category_type

        self.fields["parent"].choices = category_choices(
            collective, category_type, excluding=instance,
        )

        if instance and instance.pk and instance.parent_id:
            self.initial["parent"] = str(instance.parent_id)

    def clean_parent(self):
        value = self.cleaned_data.get("parent")
        return Category.objects.get(pk=value) if value else None

# =========================================================
# EVENT
# =========================================================

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "start_date",
            "end_date",
            "responsible_holder",
            "category"
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "responsible_holder": forms.Select(attrs={"class": "form-select"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, collective=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["responsible_holder"].queryset = get_all_user_account_holders()

        if collective:
            self.fields["category"].queryset = get_event_categories(collective)

    def clean(self):
        cleaned = super().clean()

        start = cleaned.get("start_date")
        end = cleaned.get("end_date")

        if start and end and end < start:
            raise forms.ValidationError("End date cannot be before start date")

        return cleaned


# =========================================================
# RECEIPT
# =========================================================

class ReceiptForm(forms.ModelForm):
    # Plain ChoiceField, not the default ModelChoiceField, so the
    # options can be indented in tree order - see CategoryForm.parent
    # for the same pattern.
    category = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = Receipt
        fields = [
            "note",
            "counterparty",
            "direction",
            "date",
            "amount",
            "category",
            "tax_category",
            "address_status",
            "responsible_holder",
            "event",
            "document_status",
        ]
        widgets = {
            "note": forms.TextInput(attrs={"class": "form-control"}),
            "counterparty": forms.Select(attrs={"class": "form-select"}),
            "direction": forms.Select(attrs={"class": "form-select"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "tax_category": forms.Select(attrs={"class": "form-select"}),
            "address_status": forms.Select(attrs={"class": "form-select"}),
            "responsible_holder": forms.Select(attrs={"class": "form-select"}),
            "event": forms.Select(attrs={"class": "form-select"}),
            "document_status": forms.Select(attrs={"class": "form-select", "id": "id_document_status"}),
        }

    def __init__(self, *args, upload_session = None, django_user=None, collective=None, **kwargs):
        instance = kwargs.get("instance")

        super().__init__(*args, **kwargs)
        
        self.upload_session=upload_session
        self.fields["responsible_holder"].queryset = get_all_user_account_holders()
        
        if django_user:
            self.fields["counterparty"].queryset = get_external_holders(django_user)

        self.fields["category"].choices = category_choices(collective, Category.CategoryType.RECEIPT)

        if instance and instance.pk and instance.category_id:
            self.initial["category"] = str(instance.category_id)

    def clean_category(self):
        value = self.cleaned_data.get("category")
        return Category.objects.get(pk=value) if value else None

    def clean(self):
        cleaned = super().clean()

        if (
            cleaned.get("document_status") == "attached"
            and (
                self.upload_session is None
                or not self.upload_session.file
            )
        ):
            self.add_error(None, "Please upload a file or change Document Status.")

        return cleaned

# =========================================================
# MOBILE QUICK-ADD
# =========================================================
class QuickAddReceiptForm(forms.Form):
    """
    Deliberately minimal - see `services.receipts.quick_create_receipt`.
    Only what someone can realistically fill in one-handed, standing at
    a till with a paper receipt: direction, amount, date, and a photo
    taken on the spot. Everything else gets filled in properly later on
    desktop.
    """
    direction = forms.ChoiceField(
        choices=Receipt.Direction.choices,
        initial=Receipt.Direction.OUTGOING,
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg text-center",
            "step": "0.01",
            "inputmode": "decimal",
            "placeholder": "0.00",
        }),
    )
    date = forms.DateField(
        initial=timezone.localdate,
        widget=forms.DateInput(attrs={"class": "form-control form-control-lg", "type": "date"}),
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control form-control-lg",
            "accept": "image/*",
            "capture": "environment",
        }),
    )

# =========================================================
# TRANSACTION
# =========================================================

class TransactionForm(forms.ModelForm):

    from_holder = forms.ModelChoiceField(
        queryset=AccountHolder.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "from-holder"
        })
    )

    from_account = forms.ModelChoiceField(
        queryset=FinanceAccount.objects.none(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "from-account"
        })
    )

    to_holder = forms.ModelChoiceField(
        queryset=AccountHolder.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "to-holder"
        })
    )

    to_account = forms.ModelChoiceField(
        queryset=FinanceAccount.objects.none(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "to-account"
        })
    )

    amount = forms.DecimalField(
        min_value=Decimal("0.01"),
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "min": "0.01",
            "step": "0.01",
        }),
    )

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= 0:
            raise forms.ValidationError("Amount must be positive.")
        return amount
    
    class Meta:
        model = Transaction
        fields = [
            "description",
            "date",
        ]

        widgets = {
            "description": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter transaction description"
            }),

            "amount": forms.NumberInput(attrs={
                "class": "form-control form-control-lg text-center",
                "step": "0.01",
                "placeholder": "0.00",
            }),

            "date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }

class TransactionCommandForm(forms.Form):
    description = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter transaction description"
        })
    )

    date = forms.DateField(
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date"
        })
    )

    from_holder = forms.ModelChoiceField(
        queryset=AccountHolder.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "from-holder"
        })
    )

    to_holder = forms.ModelChoiceField(
        queryset=AccountHolder.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "to-holder"
        })
    )

    from_account = forms.ModelChoiceField(
        queryset=FinanceAccount.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "from-account"
        })
    )

    to_account = forms.ModelChoiceField(
        queryset=FinanceAccount.objects.all(),
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "to-account"
        })
    )

    amount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg text-center",
            "step": "0.01",
            "placeholder": "0.00"
        })
    )


# =========================================================
# ASSETS
# =========================================================

class AssetPoolForm(forms.ModelForm):
    class Meta:
        model = AssetPool
        fields = ["name", "acquisition_year", "depreciation_years"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "acquisition_year": forms.NumberInput(attrs={"class": "form-control"}),
            "depreciation_years": forms.NumberInput(attrs={"class": "form-control"}),
        }


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "purchase_date",
            "purchase_price",
            "useful_life",
            "depreciation_method",
            "asset_pool",
            "receipt",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "purchase_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "useful_life": forms.NumberInput(attrs={"class": "form-control"}),
            "depreciation_method": forms.Select(attrs={"class": "form-select"}),
            "asset_pool": forms.Select(attrs={"class": "form-select"}),
            "receipt": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, collective=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["asset_pool"].required = False
        self.fields["receipt"].required = False

        self.fields["asset_pool"].queryset = get_asset_pools(collective)
        self.fields["receipt"].queryset = get_collective_receipts(collective) if collective else Receipt.objects.none()