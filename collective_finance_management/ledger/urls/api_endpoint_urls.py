from django.urls import path

from ..views.api import finance_accounts as finance_account_api

urlpatterns = [
    path("api/finance-accounts-by-holder/<int:account_holder_id>/", finance_account_api.finance_accounts_by_holder_api, name="finance_accounts_by_holder_api"),
    path("api/finance-account-holders-by-type/", finance_account_api.finance_account_holders_by_type_api, name="finance_account_holders_by_type_api"),
]
