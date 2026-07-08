"""HTMX ENDPOINTS: fragments used by the external party management page."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...forms import ExternalPartyForm
from ...models import AccountHolder
from ...services import external_parties as external_party_services


@login_required
def external_party_table_htmx(request):
    """HTMX endpoint: external party table."""
    return render(request, "ledger/external_party_management/partials/external_party_table.html", {
        "parties": external_party_services.get_external_parties(),
    })


@login_required
def add_external_party_htmx(request):
    """HTMX endpoint: create-external-party modal form."""
    if request.method == "GET":
        return render(request, "ledger/external_party_management/partials/external_party_form.html", {
            "form": ExternalPartyForm(),
        })

    form = ExternalPartyForm(request.POST)

    if not form.is_valid():
        return render(request, "ledger/external_party_management/partials/external_party_form.html", {
            "form": form,
        }, status=400)

    form.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def delete_external_party_htmx(request, party_id):
    """HTMX endpoint (action): deletes an external party, refused if it's in use."""
    if request.method != "DELETE":
        return HttpResponse(status=405)

    party = get_object_or_404(AccountHolder, id=party_id)

    # TODO check if AccountHolder is in fact of type EXTERNAL

    if not party.can_delete:
        return HttpResponse("Cannot delete party", status=400)

    party.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
