"""
Read helpers shared by the JSON API and by any template that prefers to embed
its data directly. Both paths call the same functions, so both see exactly the
same numbers.
"""

from typing import TypedDict

from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Q

from dashboard.models import AnomalyDate, Client, Consumption

CLIENTS_PER_PAGE = 10
DEFAULT_MONTHS = 12


class InvalidPageRequested(Exception):
    """The requested page is not a positive integer, or is out of range."""


class ClientPayload(TypedDict):
    id: int
    full_name: str
    has_elec_heating: bool
    has_anomaly: bool


class SearchPayload(TypedDict):
    clients: list[ClientPayload]
    page: int
    page_count: int


class MonthPayload(TypedDict):
    year: int
    month: int
    kwh_consumed: float


class ClientDetailsPayload(ClientPayload):
    anomaly_date: AnomalyDate | None
    available_years: list[int]
    consumptions: list[MonthPayload]


def search_clients(query: str | None = None, page: str | int = 1) -> SearchPayload:
    """
    Paginated client search. `query` matches an exact id or a name fragment.

    Raises InvalidPageRequested for anything unusable, so the view can answer
    400 instead of crashing on int("abc").
    """
    clients = Client.objects.with_diagnosis()

    if query:
        match = Q(full_name__icontains=query)
        if query.isdigit():
            match = Q(id=int(query)) | match
        clients = clients.filter(match)

    try:
        page_number = int(page)
    except (TypeError, ValueError):
        raise InvalidPageRequested(f"Parameter page must be an integer, got {page!r}.")

    paginator = Paginator(clients, CLIENTS_PER_PAGE)
    try:
        current_page = paginator.page(page_number)
    except (InvalidPage, EmptyPage):
        raise InvalidPageRequested(f"Page {page_number} is out of range.")

    return {
        "clients": [serialize_client(client) for client in current_page],
        "page": page_number,
        "page_count": paginator.num_pages,
    }


def client_details(
    client_id: int, year: str | int | None = None
) -> ClientDetailsPayload | None:
    """
    One client, its diagnosis, and a consumption series ready to plot.

    `year` selects the series: an int/str year for that calendar year, "all"
    for the full history, or None for the last DEFAULT_MONTHS months.
    Returns None when the client does not exist.
    """
    client = Client.objects.with_diagnosis().filter(pk=client_id).first()
    if client is None:
        return None

    months = Consumption.objects.filter(client_id=client.pk)
    # order_by() clears Consumption.Meta.ordering: leaving "month" in the
    # ORDER BY would make DISTINCT operate on (year, month) pairs.
    available_years = sorted(
        months.order_by().values_list("year", flat=True).distinct()
    )

    series: list[Consumption]
    if year in (None, ""):
        series = list(months.order_by("-year", "-month")[:DEFAULT_MONTHS])[::-1]
    elif str(year) == "all":
        series = list(months)
    else:
        series = list(months.filter(year=int(year)))

    return {
        **serialize_client(client),
        "anomaly_date": client.anomaly_date,
        "available_years": available_years,
        "consumptions": [
            {
                "year": month.year,
                "month": month.month,
                "kwh_consumed": round(month.kwh_consumed, 2),
            }
            for month in series
        ],
    }


def serialize_client(client: Client) -> ClientPayload:
    return {
        "id": client.id,
        "full_name": client.full_name,
        "has_elec_heating": client.has_elec_heating,
        "has_anomaly": client.has_anomaly,
    }
