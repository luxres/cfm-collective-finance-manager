"""
Shared logic for the sortable HTMX tables (category, event, receipt
tables): reading the requested sort column and building the
"click this header to sort by it" links.
"""
from dataclasses import dataclass
from typing import Iterable

from django.http import HttpRequest
from django.urls import reverse


@dataclass
class TableSortState:
    sort: str
    table_id: str
    sort_links: dict


def build_sort_state(
    request: HttpRequest,
    *,
    url_name: str,
    url_args: Iterable,
    sortable_columns: Iterable[str],
    default_sort: str = "id",
    default_table_id: str = "table",
) -> TableSortState:
    """
    Reads `sort` / `table_id` from the query string and returns both the
    resolved values plus a `{column: url}` map the template can use for
    clickable column headers (toggling ascending/descending).
    """
    table_id = request.GET.get("table_id", default_table_id)
    sort = request.GET.get("sort", default_sort)

    base_url = reverse(url_name, args=list(url_args))
    sort_links = {}

    for column in sortable_columns:
        params = request.GET.copy()
        params["sort"] = f"-{column}" if sort == column else column
        params["table_id"] = table_id
        sort_links[column] = f"{base_url}?{params.urlencode()}"

    return TableSortState(sort=sort, table_id=table_id, sort_links=sort_links)
