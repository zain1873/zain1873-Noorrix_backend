from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "amount",
        "currency",
        "status",
        "payment_method",
        "customer_email",
        "created_at",
    ]
    list_filter = ["status", "currency", "payment_method", "created_at"]
    search_fields = [
        "reference",
        "stripe_payment_intent_id",
        "stripe_session_id",
        "customer_email",
    ]
    readonly_fields = [
        "reference",
        "user",
        "stripe_payment_intent_id",
        "stripe_session_id",
        "amount",
        "currency",
        "description",
        "customer_email",
        "payment_method",
        "created_at",
        "updated_at",
    ]
