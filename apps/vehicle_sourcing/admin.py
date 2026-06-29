from django.contrib import admin
from .models import VehicleSourcingRequest


@admin.register(VehicleSourcingRequest)
class VehicleSourcingRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "make", "model", "year", "budget", "created_at", "contacted"]
    list_filter = ["contacted", "created_at", "budget"]
    list_editable = ["contacted"]
    search_fields = ["name", "email", "phone", "make", "model"]
    readonly_fields = ["name", "phone", "email", "make", "model", "year", "mileage", "budget", "notes", "created_at"]
