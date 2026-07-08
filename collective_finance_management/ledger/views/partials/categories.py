"""HTMX ENDPOINTS: fragments used by the category management page."""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render

from ...forms import CategoryForm
from ...models import AccountHolder, Category
from ...services import access, sorting

SORTABLE_COLUMNS = ["id", "name"]


@login_required
def category_table_htmx(request, collective_id, category_type):
    """
    HTMX endpoint: sortable category table for one collective/type.
    Shows top-level categories by default; pass `?parent_id=<id>` to
    show that category's direct children instead - this is exactly how
    the "Details" drill-down recurses (see `category_children_htmx`):
    it nests this same table/endpoint filtered by parent, so every
    level of the tree gets the real table (Add/Edit/Delete/Details and
    all) rather than a stripped-down copy.
    """
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    parent_id = request.GET.get("parent_id")
    if parent_id:
        categories = Category.objects.filter(
            collective=collective, type=category_type, parent_id=parent_id,
        )
    else:
        categories = Category.objects.filter(
            collective=collective, type=category_type, parent__isnull=True,
        )

    sort_state = sorting.build_sort_state(
        request,
        url_name="category_table_htmx",
        url_args=[collective_id, category_type],
        sortable_columns=SORTABLE_COLUMNS,
        default_table_id="category-table",
    )
    categories = categories.order_by(sort_state.sort)

    return render(request, "ledger/category_management/partials/category_table.html", {
        "collective": collective,
        "categories": categories,
        "category_type": category_type,
        "current_sort": sort_state.sort,
        "table_id": sort_state.table_id,
        "sort_links": sort_state.sort_links,
    })


@login_required
def category_children_htmx(request, category_id):
    """
    HTMX endpoint: one layer of the drill-down for a category. The
    template nests two real, reused tables via their own `hx-get`s -
    no stripped-down copies:

    - the sub-categories: `category_table_htmx` itself, filtered by
      `?parent_id=<this category>` - which is how the recursion
      happens, since that table's own "Details" buttons call this same
      endpoint again for each child.
    - the receipts/events tagged directly to this category:
      `receipt_table_htmx` / `event_table_htmx`, filtered by
      `?category_id=<this category>`.
    """
    category = get_object_or_404(Category, id=category_id)

    if not access.can_access_account_holder(request.user, category.collective):
        return HttpResponse("Not allowed", status=403)

    return render(request, "ledger/category_management/partials/category_children.html", {
        "category": category,
    })


@login_required
def add_category_htmx(request, collective_id, category_type):
    """HTMX endpoint: create-category modal form."""
    # TODO permissions
    collective = get_object_or_404(AccountHolder, id=collective_id)

    if request.method == "GET":
        return render(request, "ledger/category_management/partials/category_form.html", {
            "form": CategoryForm(collective=collective, category_type=category_type),
            "category": None,
            "category_type": category_type,
            "active_collective": collective,
        })

    form = CategoryForm(request.POST, collective=collective, category_type=category_type)

    if not form.is_valid():
        return render(request, "ledger/category_management/partials/category_form.html", {
            "form": form,
            "category": None,
            "category_type": category_type,
            "active_collective": collective,
        }, status=400)

    category = form.save(commit=False)
    category.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def edit_category_htmx(request, category_id):
    """HTMX endpoint: edit-category modal form."""
    # TODO permissions
    category = get_object_or_404(Category, id=category_id)

    if not access.can_access_account_holder(request.user, category.collective):
        return HttpResponse("Not allowed", status=403)

    if request.method == "GET":
        return render(request, "ledger/category_management/partials/category_form.html", {
            "form": CategoryForm(instance=category),
            "category": category,
            "category_type": category.type,
            "active_collective": category.collective,
        })

    form = CategoryForm(request.POST, instance=category)

    if not form.is_valid():
        return render(request, "ledger/category_management/partials/category_form.html", {
            "form": form,
            "category": category,
            "category_type": category.type,
            "active_collective": category.collective,
        }, status=400)

    form.save()

    return HttpResponse("", headers={"HX-Trigger": "modalClose"})


@login_required
def delete_category_htmx(request, category_id):
    """HTMX endpoint (action): deletes a category, refused if it's in use or has sub-categories."""
    # TODO permissions
    category = get_object_or_404(Category, id=category_id)

    if not category.can_delete:
        return HttpResponseBadRequest(
            "This category cannot be deleted: it either has Receipts/Events tagged to it, "
            "or has sub-categories of its own (delete or re-parent those first)."
        )

    category.delete()

    response = HttpResponse(status=204)
    response["HX-Trigger"] = "modalClose"
    return response
