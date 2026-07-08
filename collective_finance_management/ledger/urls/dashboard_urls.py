from django.urls import path
from django.views.generic import RedirectView

from ..views.pages import dashboard

urlpatterns = [
    path("", RedirectView.as_view(url="/ledger/dashboard/", permanent=False)),
    path("dashboard/", dashboard.dashboard_page, name="dashboard_page"),
]
