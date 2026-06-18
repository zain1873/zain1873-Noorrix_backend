from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "car",
        "amount",
        "currency",
        "status",
        "payment_method",
        "customer_email",
        "created_at",
    ]
    list_filter = ["status", "currency", "payment_method", "created_at"]
    list_select_related = ["car", "user"]
    search_fields = [
        "reference",
        "stripe_payment_intent_id",
        "stripe_session_id",
        "customer_email",
        "car__title",
        "car__make",
        "car__model",
    ]
    # ``car`` is intentionally left editable so an admin can manually link or
    # correct the vehicle on an older payment. Everything else is Stripe-driven
    # and read-only.
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
