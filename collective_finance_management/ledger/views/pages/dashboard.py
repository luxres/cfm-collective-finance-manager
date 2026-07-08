"""PAGES: the site root and the logged-in-user dashboard."""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from ...services import dashboard as dashboard_service


def home_page(request):
    """PAGE: unauthenticated landing page."""
    return render(request, "home.html")


@login_required
def dashboard_page(request):
    """PAGE: overview of every account (personal + collectives) the user can see."""
    context = dashboard_service.build_dashboard_context(request.user)
    return render(request, "ledger/dashboard.html", context)
