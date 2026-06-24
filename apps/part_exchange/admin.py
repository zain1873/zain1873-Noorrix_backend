from django.contrib import admin
from .models import PartExchangeRequest


@admin.register(PartExchangeRequest)
class PartExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "make", "model", "year", "mileage", "created_at", "contacted"]
    list_filter = ["contacted", "created_at"]
    list_editable = ["contacted"]
    search_fields = ["name", "email", "phone", "make", "model"]
    readonly_fields = ["name", "phone", "email", "make", "model", "year", "mileage", "created_at"]
