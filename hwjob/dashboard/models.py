from collections.abc import Sequence
from typing import Any, TypedDict

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Case, F, FloatField, OuterRef, Subquery, Sum, Value, When
from django.urls import reverse

# A client is considered to heat with electricity when the electricity consumed
# during the cold months is disproportionate compared to the warm months.
COLD_MONTHS = (11, 12, 1, 2, 3, 4)
WARM_MONTHS = (5, 6, 7, 8, 9, 10)
HEATING_RATIO = 1.5

# An anomaly is a durable jump in consumption: a month that consumes much more
# than the same month one year earlier.
ANOMALY_RATIO = 1.9

_UNANNOTATED = object()


class AnomalyDate(TypedDict):
    year: int
    month: int


def seasonal_sum(months: Sequence[int]) -> Sum:
    return Sum(
        Case(
            When(month__in=months, then=F("kwh_consumed")),
            default=Value(0.0),
            output_field=FloatField(),
        )
    )


class MonthMixin(models.Model):
    month = models.PositiveSmallIntegerField(
        "month", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.PositiveSmallIntegerField("year")

    class Meta:
        abstract = True


class ClientQuerySet(models.QuerySet["Client"]):
    def with_diagnosis(self) -> "ClientQuerySet":
        return self.annotate(
            heating_margin=Subquery(self._heating_margin()),
            anomaly_period=Subquery(self._anomaly_period()),
        )

    @staticmethod
    def _heating_margin() -> models.QuerySet[Any, Any]:
        return (
            Consumption.objects.filter(client_id=OuterRef("pk"))
            .values("client_id")
            .annotate(
                margin=seasonal_sum(COLD_MONTHS)
                - HEATING_RATIO * seasonal_sum(WARM_MONTHS)
            )
            .values("margin")[:1]
        )

    @staticmethod
    def _anomaly_period() -> models.QuerySet[Any, Any]:
        return (
            Consumption.objects.filter(
                client_id=OuterRef("pk"),
                client__consumption__client_id=F("client_id"),
                client__consumption__month=F("month"),
                client__consumption__year=F("year") - 1,
                client__consumption__kwh_consumed__lte=F("kwh_consumed")
                / ANOMALY_RATIO,
            )
            .order_by("year", "month")
            .annotate(period=F("year") * 100 + F("month"))
            .values("period")[:1]
        )


class Client(models.Model):
    full_name = models.CharField("full name", max_length=50)

    objects = ClientQuerySet.as_manager()

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"Client {self.pk}"

    def get_absolute_url(self) -> str:
        return reverse("dashboard:client_details", kwargs={"client_id": self.pk})

    def _annotated(self, name: str) -> Any:
        value = getattr(self, name, _UNANNOTATED)
        if value is _UNANNOTATED:
            raise AttributeError(
                f"{name} is missing: build the queryset with "
                "Client.objects.with_diagnosis() to use this property."
            )
        return value

    @property
    def has_elec_heating(self) -> bool:
        margin = self._annotated("heating_margin")
        return margin is not None and margin > 0

    @property
    def has_anomaly(self) -> bool:
        return self._annotated("anomaly_period") is not None

    @property
    def anomaly_date(self) -> AnomalyDate | None:
        """{"year": ..., "month": ...} of the first faulty month, or None."""
        period = self._annotated("anomaly_period")
        if period is None:
            return None
        return {"year": period // 100, "month": period % 100}


class Consumption(MonthMixin):
    """
    Store the electricity consumption of a client over a month
    """

    client = models.ForeignKey(
        "dashboard.Client", verbose_name="client", on_delete=models.CASCADE
    )
    kwh_consumed = models.FloatField("kwh consumed")

    class Meta:
        verbose_name = "Consumption"
        verbose_name_plural = "Consumptions"
        unique_together = ("client", "month", "year")
        ordering = ("year", "month")

    def __str__(self) -> str:
        return f"Conso of {self.client} ({self.month}/{self.year}): {self.kwh_consumed}"


class ElectricityPrice(MonthMixin):
    """
    Store the electricity price during a month
    """

    cteuro_per_kwh = models.FloatField("price ct€/kwh")

    class Meta:
        verbose_name = "Electricity price"
        verbose_name_plural = "Electricity prices"
        unique_together = ("month", "year")
        ordering = ("year", "month")

    def __str__(self) -> str:
        return f"Elec price ({self.month}/{self.year}): {self.cteuro_per_kwh}"
