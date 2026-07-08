"""PAGES: category management & the single-category overview."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from ...models import Category
from ...services import access, categories as category_services, collectives


@login_required
def category_management_page(request):
    """PAGE: category tables (receipt/event tabs) for the active collective."""
    user_collectives = access.get_user_collectives(request.user)
    active_collective = collectives.resolve_active_collective(
        request.user, request.GET.get("collective"), user_collectives,
    )

    return render(request, "ledger/category_management/category_main.html", {
        "collectives": user_collectives,
        "active_collective": active_collective,
    })


@login_required
def category_overview_page(request, category_id):
    """PAGE: totals and charts for a single category."""
    category = get_object_or_404(Category, id=category_id)
    if not access.can_access_account_holder(request.user, category.collective):
        return HttpResponse("Not allowed", status=403)

    context = category_services.category_overview_context(category)

    return render(request, "ledger/category_management/category_overview.html", {
        "category": category,
        "collective": category.collective,
        **context,
    })
