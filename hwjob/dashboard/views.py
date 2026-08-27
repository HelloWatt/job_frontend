from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_GET

from dashboard.selectors import InvalidPageRequested, client_details, search_clients


@require_GET
def root_view(request: HttpRequest) -> HttpResponse:
    """
    The empty page the dashboard is meant to replace. Yours to rebuild.
    """
    return render(
        request,
        "dashboard/index.html",
        {"meta": {"title": "Diagnostic", "description": "Diagnostic en un clic"}},
    )


@require_GET
def search_client_view(request: HttpRequest) -> HttpResponse:
    """
    GET /api/search-clients?query=&page=

    Search clients by exact id or by name fragment, 10 per page.
    """
    try:
        payload = search_clients(
            query=request.GET.get("query"), page=request.GET.get("page", 1)
        )
    except InvalidPageRequested as error:
        return HttpResponseBadRequest(str(error))

    return JsonResponse(payload)


@require_GET
def client_view(request: HttpRequest, client_id: int) -> HttpResponse:
    """
    GET /api/client/<client_id>?year=

    The client, its diagnosis, and its consumption series. `year` accepts a
    year, "all", or nothing at all for the last 12 months.
    """
    year = request.GET.get("year")
    if year not in (None, "", "all") and not str(year).isdigit():
        return HttpResponseBadRequest(f"Parameter year is invalid: {year!r}.")

    payload = client_details(client_id, year=year)
    if payload is None:
        return HttpResponseNotFound(f"Client {client_id} not found.")

    return JsonResponse(payload)
