from django.contrib import admin
from .models import FAQ


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display  = ("question", "order", "is_active", "updated_at")
    list_editable = ("order", "is_active")
    list_filter   = ("is_active",)
    search_fields = ("question", "answer")
    ordering      = ("order",)
