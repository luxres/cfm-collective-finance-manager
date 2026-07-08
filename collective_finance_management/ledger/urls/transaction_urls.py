from django.urls import path

from ..views.api import transactions as transaction_api

urlpatterns = [
    path("api/transaction/create/", transaction_api.create_transaction_api, name="create_transaction_api"),
]
