from django.urls import path

from ..views.pages import receipts as receipt_pages
from ..views.partials import receipts as receipt_htmx
from ..views.partials import transactions as transaction_htmx

urlpatterns = [
    # pages
    path("receipt/", receipt_pages.receipt_management_page, name="receipt_management_page"),
    path("receipt/<int:receipt_id>/receipt-overview/", receipt_pages.receipt_overview_page, name="receipt_overview_page"),

    # htmx
    path("htmx/receipt/<int:collective_id>/receipt-table/", receipt_htmx.receipt_table_htmx, name="receipt_table_htmx"),
    path("htmx/receipt/<int:collective_id>/add/", receipt_htmx.add_receipt_htmx, name="add_receipt_htmx"),
    path("htmx/receipt/<int:receipt_id>/edit/", receipt_htmx.edit_receipt_htmx, name="edit_receipt_htmx"),
    path("htmx/receipt/<int:receipt_id>/details/", receipt_htmx.receipt_details_htmx, name="receipt_details_htmx"),
    path("htmx/receipt/<int:receipt_id>/file/", receipt_htmx.receipt_file_htmx, name="receipt_file_htmx"),
    path("htmx/transaction/<int:transaction_id>/edit/", transaction_htmx.edit_transaction_htmx, name="edit_transaction_htmx"),
    path("htmx/transaction/<int:receipt_id>/add/", transaction_htmx.add_transaction_htmx, name="add_transaction_htmx"),
    path("htmx/transaction/<int:transaction_id>/delete/", transaction_htmx.delete_transaction_htmx, name="delete_transaction_htmx"),
]
