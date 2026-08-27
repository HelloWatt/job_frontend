from typing import Any

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import URLPattern, URLResolver, path
from django.views.generic.list import ListView

from dashboard.models import Client, ClientQuerySet


class ClientsListView(ListView[Client]):
    context_object_name = "clients_list"
    template_name = "dashboard/clients_list.html"
    paginate_by = 50

    def get_queryset(self) -> ClientQuerySet:
        clients = Client.objects.with_diagnosis()
        query = self.request.GET.get("query")
        if query:
            clients = clients.filter(full_name__icontains=query)
        return clients

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("query", "")
        context["meta"] = {
            "title": "Clients list",
            "description": "Browse which clients have electrical heating or an anomaly",
        }
        return context


class DashboardAdminSite(admin.sites.AdminSite):
    def get_urls(self) -> list[URLPattern | URLResolver]:
        return [
            path("clients", staff_member_required(ClientsListView.as_view())),
        ] + super().get_urls()
