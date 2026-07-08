from django.urls import path

from ..views.pages import accounts as account_pages
from ..views.partials import accounts as account_htmx

urlpatterns = [
    # pages
    path("finance-account/", account_pages.account_management_page, name="account_management_page"),
    path("finance-account/<int:account_id>/overview/", account_pages.account_overview_page, name="account_overview_page"),

    # htmx
    path("htmx/finance-account/<int:account_id>/transactions/", account_htmx.account_transactions_htmx, name="account_transactions_htmx"),
    path("htmx/finance-account-holder/<int:account_holder_id>/accounts-by-holder/", account_htmx.accounts_by_holder_htmx, name="accounts_by_holder_htmx"),
    path("htmx/finance-account-holder/<int:account_holder_id>/add-cash-account/", account_htmx.add_cash_account_htmx, name="add_cash_account_htmx"),
    path("htmx/finance-account-holder/<int:account_holder_id>/add-bank-account/", account_htmx.add_bank_account_htmx, name="add_bank_account_htmx"),
    path("htmx/finance-account/<int:account_id>/edit-cash-account/", account_htmx.edit_cash_account_htmx, name="edit_cash_account_htmx"),
    path("htmx/finance-account/<int:account_id>/edit-bank-account/", account_htmx.edit_bank_account_htmx, name="edit_bank_account_htmx"),
    path("htmx/finance-account/<int:account_id>/delete/", account_htmx.delete_account_htmx, name="delete_account_htmx"),
]
