from django.urls import URLPattern, URLResolver, path

from dashboard.views import client_view, root_view, search_client_view

app_name = "dashboard"
urlpatterns: list[URLPattern | URLResolver] = [
    path("", root_view, name="root_view"),
    path("api/search-clients", search_client_view, name="search_clients"),
    path("api/client/<int:client_id>", client_view, name="client_details"),
]
