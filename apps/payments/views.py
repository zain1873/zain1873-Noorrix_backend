import logging
from urllib.parse import urlparse

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Payment
from .serializers import (
    CreateCheckoutSessionSerializer,
    CreatePaymentSerializer,
    PaymentSerializer,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Maps Stripe PaymentIntent statuses to our local Payment.Status values.
STRIPE_STATUS_MAP = {
    "succeeded": Payment.Status.SUCCEEDED,
    "processing": Payment.Status.PROCESSING,
    "canceled": Payment.Status.CANCELED,
    "requires_payment_method": Payment.Status.FAILED,
}


def _safe_get(obj, key, default=None):
    """Key access that works for both Stripe objects (no .get) and dicts."""
    try:
        value = obj[key]
    except (KeyError, TypeError):
        return default
    return value if value is not None else default


def _reference_from(obj):
    """Pull our Payment.reference out of a Checkout Session object."""
    ref = _safe_get(obj, "client_reference_id")
    if ref:
        return ref
    metadata = _safe_get(obj, "metadata") or {}
    return _safe_get(metadata, "reference")


class CreatePaymentIntentView(APIView):
    """Create a Stripe PaymentIntent and a matching local Payment record.

    Returns the ``client_secret`` the frontend feeds to Stripe.js. With
    ``automatic_payment_methods`` enabled, Stripe shows every method enabled in
    the Dashboard (cards, Apple Pay, PayPal) — no per-method code needed here.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreatePaymentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        amount = data["amount"]
        currency = data.get("currency") or settings.STRIPE_CURRENCY
        description = data.get("description", "")
        email = data.get("email", "")
        user = request.user if request.user.is_authenticated else None

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency,
                automatic_payment_methods={"enabled": True},
                description=description or None,
                receipt_email=email or None,
                metadata={"user_id": user.id if user else ""},
            )
        except stripe.StripeError as exc:
            logger.exception("Stripe PaymentIntent creation failed")
            return Response(
                {"success": False, "error": str(exc.user_message or "Payment provider error.")},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment = Payment.objects.create(
            user=user,
            stripe_payment_intent_id=intent.id,
            amount=amount,
            currency=currency,
            description=description,
            customer_email=email,
            status=Payment.Status.PENDING,
        )

        return Response(
            {
                "success": True,
                "client_secret": intent.client_secret,
                "publishable_key": settings.STRIPE_PUBLISHABLE_KEY,
                "reference": str(payment.reference),
            },
            status=status.HTTP_201_CREATED,
        )


class CreateCheckoutSessionView(APIView):
    """Create a Stripe hosted Checkout Session and a matching Payment record.

    Returns the hosted ``url`` the frontend redirects to. The payment methods
    shown on Stripe's page are driven by the Dashboard config (cards, Apple Pay,
    PayPal); we deliberately don't pin ``payment_method_types`` so enabling a
    method later needs no code change and an unactivated method can't 502 us.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateCheckoutSessionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        amount = data["amount"]
        currency = data.get("currency") or settings.STRIPE_CURRENCY
        description = data.get("description") or "Vehicle reservation deposit"
        success_url = data["success_url"]
        cancel_url = data["cancel_url"]
        user = request.user if request.user.is_authenticated else None

        # Create our record first so GET /payments/{reference}/ works immediately.
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            currency=currency,
            description=description,
            status=Payment.Status.PENDING,
        )
        reference = str(payment.reference)

        # Append our reference (+ Stripe's session id) so the success page can
        # poll right away. {CHECKOUT_SESSION_ID} must stay literal for Stripe.
        sep = "&" if urlparse(success_url).query else "?"
        success_with_ref = (
            f"{success_url}{sep}ref={reference}&session_id={{CHECKOUT_SESSION_ID}}"
        )

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                success_url=success_with_ref,
                cancel_url=cancel_url,
                line_items=[
                    {
                        "quantity": 1,
                        "price_data": {
                            "currency": currency,
                            "unit_amount": int(amount * 100),
                            "product_data": {"name": description},
                        },
                    }
                ],
                # Link Stripe's objects back to our record for the webhook.
                client_reference_id=reference,
                payment_intent_data={"metadata": {"reference": reference}},
                metadata={"reference": reference},
            )
        except stripe.StripeError as exc:
            logger.exception("Stripe Checkout Session creation failed")
            payment.status = Payment.Status.FAILED
            payment.save(update_fields=["status", "updated_at"])
            return Response(
                {"success": False, "error": str(exc.user_message or "Payment provider error.")},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payment.stripe_session_id = session.id
        intent_id = _safe_get(session, "payment_intent")
        if intent_id:
            payment.stripe_payment_intent_id = intent_id
        payment.save(
            update_fields=["stripe_session_id", "stripe_payment_intent_id", "updated_at"]
        )

        return Response(
            {"success": True, "url": session.url, "reference": reference},
            status=status.HTTP_201_CREATED,
        )


class PaymentDetailView(RetrieveAPIView):
    """Fetch a payment's current status by its (unguessable) reference UUID."""

    permission_classes = [AllowAny]
    serializer_class = PaymentSerializer
    queryset = Payment.objects.all()
    lookup_field = "reference"


class StripeWebhookView(APIView):
    """Receive Stripe webhooks and update payment status.

    This is the only trusted source of truth for a payment's outcome. The
    signature is verified against STRIPE_WEBHOOK_SECRET so the endpoint can be
    public without accepting forged events.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        secrets = settings.STRIPE_WEBHOOK_SECRETS
        if not secrets:
            logger.error("STRIPE_WEBHOOK_SECRET is not configured")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Try each configured secret; accept the event if any one verifies.
        event = None
        for secret in secrets:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, secret)
                break
            except ValueError:
                # Malformed payload — a different secret won't help.
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except stripe.SignatureVerificationError:
                continue

        if event is None:
            logger.warning("Stripe webhook signature verification failed")
            return Response(status=status.HTTP_400_BAD_REQUEST)

        event_type = event["type"]
        obj = event["data"]["object"]

        if event_type == "checkout.session.completed":
            # Only mark paid once Stripe confirms the funds (async methods may
            # still be pending here and finish via async_payment_succeeded).
            if _safe_get(obj, "payment_status") == "paid":
                self._set_status_by_reference(obj, Payment.Status.SUCCEEDED)
        elif event_type == "checkout.session.async_payment_succeeded":
            self._set_status_by_reference(obj, Payment.Status.SUCCEEDED)
        elif event_type == "checkout.session.async_payment_failed":
            self._set_status_by_reference(obj, Payment.Status.FAILED)
        elif event_type == "checkout.session.expired":
            self._set_status_by_reference(obj, Payment.Status.CANCELED)
        elif event_type in (
            "payment_intent.succeeded",
            "payment_intent.payment_failed",
            "payment_intent.processing",
            "payment_intent.canceled",
        ):
            self._update_payment(obj)
        elif event_type == "charge.refunded":
            self._handle_refund(obj)

        return Response({"received": True}, status=status.HTTP_200_OK)

    def _set_status_by_reference(self, session, new_status):
        """Resolve a Payment from a Checkout Session and set its status."""
        reference = _reference_from(session)
        if not reference:
            logger.warning("Checkout event without reference: %s", _safe_get(session, "id"))
            return
        try:
            payment = Payment.objects.get(reference=reference)
        except (Payment.DoesNotExist, ValidationError, ValueError):
            logger.warning("Checkout event for unknown reference %s", reference)
            return

        payment.status = new_status
        update_fields = ["status", "updated_at"]

        # The PaymentIntent id may only become known once the session completes.
        intent_id = _safe_get(session, "payment_intent")
        if intent_id and not payment.stripe_payment_intent_id:
            payment.stripe_payment_intent_id = intent_id
            update_fields.append("stripe_payment_intent_id")

        payment.save(update_fields=update_fields)

    def _handle_refund(self, charge):
        """Mark a Payment refunded based on a charge.refunded event."""
        intent_id = _safe_get(charge, "payment_intent")
        if not intent_id:
            return
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        except Payment.DoesNotExist:
            logger.warning("Refund for unknown PaymentIntent %s", intent_id)
            return
        payment.status = Payment.Status.REFUNDED
        payment.save(update_fields=["status", "updated_at"])

    def _update_payment(self, intent):
        # Stripe objects (StripeObject) are NOT dicts and have no .get(), so we
        # use __getitem__ guarded by try/except for any optional field.
        intent_id = intent["id"]
        try:
            payment = Payment.objects.get(stripe_payment_intent_id=intent_id)
        except Payment.DoesNotExist:
            logger.warning("Webhook for unknown PaymentIntent %s", intent_id)
            return

        payment.status = STRIPE_STATUS_MAP.get(intent["status"], payment.status)

        method = self._extract_payment_method(intent)
        if method:
            payment.payment_method = method

        payment.save(update_fields=["status", "payment_method", "updated_at"])

    @staticmethod
    def _extract_payment_method(intent):
        """Best-effort read of the method type (card / paypal / …).

        The PaymentIntent in a webhook may not include expanded charge details,
        so every access is guarded. Falls back to payment_method_types.
        """
        try:
            charges = intent["charges"]["data"]
            if charges:
                return charges[0]["payment_method_details"]["type"]
        except (KeyError, TypeError, IndexError):
            pass
        try:
            types = intent["payment_method_types"]
            if types:
                return types[0]
        except (KeyError, TypeError, IndexError):
            pass
        return ""
