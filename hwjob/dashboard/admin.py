from django.contrib import admin

from dashboard.models import Client, Consumption, ElectricityPrice


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin[Client]):
    list_display = ("id", "full_name")
    search_fields = ("id", "full_name")


@admin.register(Consumption)
class ConsumptionAdmin(admin.ModelAdmin[Consumption]):
    list_display = ("client", "year", "month", "kwh_consumed")
    list_filter = ("year", "month")
    list_select_related = ("client",)


@admin.register(ElectricityPrice)
class ElectricityPriceAdmin(admin.ModelAdmin[ElectricityPrice]):
    list_display = ("year", "month", "cteuro_per_kwh")
    list_filter = ("year",)
