from decimal import Decimal
from urllib.parse import urlparse

from django.conf import settings
from rest_framework import serializers

from apps.cars.models import Car

from .models import Payment

# Guard rails for the client-supplied amount. For a real product/order you
# should derive the amount server-side instead of trusting the request.
MIN_AMOUNT = Decimal("0.50")
MAX_AMOUNT = Decimal("999999.99")


def validate_amount_bounds(value):
    if value < MIN_AMOUNT:
        raise serializers.ValidationError(f"Amount must be at least {MIN_AMOUNT}.")
    if value > MAX_AMOUNT:
        raise serializers.ValidationError(f"Amount must not exceed {MAX_AMOUNT}.")
    return value


def is_allowed_redirect(url):
    """True if ``url``'s origin is in the configured allow-list."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return origin in settings.PAYMENT_REDIRECT_ALLOWED_ORIGINS


class CreatePaymentSerializer(serializers.Serializer):
    """Validates the request to start a payment.

    When ``car`` is given, the amount is the car's own ``deposit_amount`` —
    never the client-supplied figure, so a buyer can't reserve a car for an
    arbitrary amount. ``amount`` is only used for car-less/general payments.
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    car = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(), required=False, allow_null=True
    )

    def validate_amount(self, value):
        return validate_amount_bounds(value)

    def validate_currency(self, value):
        return value.lower()

    def validate(self, attrs):
        if not attrs.get("car") and attrs.get("amount") is None:
            raise serializers.ValidationError({"amount": "Required when no car is specified."})
        return attrs


class CreateCheckoutSessionSerializer(serializers.Serializer):
    """Validates the request to start a hosted Stripe Checkout Session.

    When ``car`` is given, the amount is the car's own ``deposit_amount`` —
    never the client-supplied figure, so a buyer can't reserve a car for an
    arbitrary amount. ``amount`` is only used for car-less/general payments.
    """

    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()
    car = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(), required=False, allow_null=True
    )

    def validate_amount(self, value):
        return validate_amount_bounds(value)

    def validate_currency(self, value):
        return value.lower()

    def validate_success_url(self, value):
        if not is_allowed_redirect(value):
            raise serializers.ValidationError("Redirect URL origin is not allowed.")
        return value

    def validate_cancel_url(self, value):
        if not is_allowed_redirect(value):
            raise serializers.ValidationError("Redirect URL origin is not allowed.")
        return value

    def validate(self, attrs):
        if not attrs.get("car") and attrs.get("amount") is None:
            raise serializers.ValidationError({"amount": "Required when no car is specified."})
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """Read-only representation returned to the client."""

    class Meta:
        model = Payment
        fields = [
            "reference",
            "car",
            "amount",
            "currency",
            "status",
            "description",
            "customer_email",
            "payment_method",
            "created_at",
        ]
        read_only_fields = fields
