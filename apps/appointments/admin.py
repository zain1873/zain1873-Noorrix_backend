from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "time", "type", "name", "car", "email", "phone", "created_at")
    list_filter = ("type", "date")
    search_fields = ("name", "email", "phone", "car__title", "car__make", "car__model")
    list_select_related = ("car",)
    readonly_fields = ("created_at",)
