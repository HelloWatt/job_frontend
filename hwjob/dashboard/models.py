from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Case, Exists, F, OuterRef, When, Subquery, Sum
from django.urls import reverse


class MonthMixin(models.Model):
    month = models.PositiveSmallIntegerField(
        "month", validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    year = models.PositiveSmallIntegerField("year")

    class Meta:
        abstract = True

class ClientQuerySet(models.QuerySet):
    def _subquery_conso_over_months(self, months):
        return Consumption.objects \
            .filter(client_id=OuterRef("pk"), month__in=months) \
            .values("client_id") \
            .annotate(total_kwh_consumed=Sum('kwh_consumed')) \
            .values('total_kwh_consumed')

    def annotate_has_elec_heating(self):
        cold_months_q = self._subquery_conso_over_months([11, 12, 1, 2, 3, 4])
        hot_months_q = self._subquery_conso_over_months([5, 6, 7, 8, 9, 10])

        has_elec_heating_case = Case(
            When(cold_consumption__gt=2 * F("hot_consumption"), then=True),
            default=False,
            output_field=models.BooleanField()
        )
        return self \
            .annotate(cold_consumption=Subquery(cold_months_q)) \
            .annotate(hot_consumption=Subquery(hot_months_q)) \
            .annotate(has_elec_heating=has_elec_heating_case)

    def annotate_anomaly(self):
        anomaly_q = Consumption.objects \
            .filter(
                client_id=OuterRef("pk"),
                client__consumption__month=F('month'),
                client__consumption__year=F('year') - 1,
                client__consumption__kwh_consumed__lte=F('kwh_consumed') / 1.9,
                client__consumption__client_id=F('client_id')
            ) \
            .order_by("year", "month")
        return self \
            .annotate(anomaly_year=Subquery(anomaly_q.values("year")[:1])) \
            .annotate(anomaly_month=Subquery(anomaly_q.values("month")[:1])) \
            .annotate(has_anomaly=Exists(anomaly_q))

class Client(models.Model):
    full_name = models.CharField("full name", max_length=50)

    objects = ClientQuerySet.as_manager()

    def __str__(self):
        return f"Client {self.pk}"


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

    def __str__(self):
        return f"Conso of {self.client} ({self.month}/{self.year}): {self.kwh_consumed}"

    def get_absolute_url(self):
        return reverse("dashboard:consumption_details", kwargs={"client_id": self.pk})


class ElectricityPrice(MonthMixin):
    """
        Store the electricity price during a month
    """

    cteuro_per_kwh = models.FloatField("price ct€/kwh")

    class Meta:
        verbose_name = "Electricity price"
        verbose_name_plural = "Electricity prices"
        unique_together = ("month", "year")

    def __str__(self):
        return f"Elec price ({self.month}/{self.year}): {self.cteuro_per_kwh}"
