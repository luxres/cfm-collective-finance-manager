"""PAGES: external party management."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ...forms import ExternalPartyForm
from ...services import external_parties as external_party_services


@login_required
def external_parties_management_page(request):
    """PAGE: table of external parties (counterparties not part of any collective)."""
    parties = external_party_services.get_external_parties_with_accounts()

    return render(request, "ledger/external_party_management/external_party_main.html", {
        "parties": parties,
        "add_form": ExternalPartyForm(),
    })
