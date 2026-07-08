"""Building blocks shared by more than one export source in this package."""
from __future__ import annotations

from datetime import date

from django import forms

from ledger.models import AccountHolder
from ledger.services import access


def year_choices():
    current_year = date.today().year
    return [(y, str(y)) for y in range(current_year, current_year - 8, -1)]


class CollectiveYearParamsForm(forms.Form):
    """
    Params shared by every per-Verein-per-year source (EÜR, AVEÜR, and
    whatever comes next): which collective, which tax year.
    """
    collective = forms.ModelChoiceField(
        queryset=AccountHolder.objects.none(),
        label="Verein",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    year = forms.ChoiceField(
        choices=year_choices,
        label="Jahr",
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Scoping the queryset to the user's own collectives is also the
        # permission check: a ModelChoiceField rejects any submitted value
        # that isn't in it, so a user can't export a collective they don't
        # belong to just by editing the URL's query string.
        self.fields["collective"].queryset = (
            access.get_user_collectives(user) if user else AccountHolder.objects.none()
        )

    def clean_year(self):
        return int(self.cleaned_data["year"])
