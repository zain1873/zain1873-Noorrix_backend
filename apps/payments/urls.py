from django.urls import path

from .views import (
    CreateCheckoutSessionView,
    CreatePaymentIntentView,
    PaymentDetailView,
    StripeWebhookView,
)

urlpatterns = [
    path("create-intent/", CreatePaymentIntentView.as_view(), name="payment-create-intent"),
    path(
        "create-checkout-session/",
        CreateCheckoutSessionView.as_view(),
        name="payment-create-checkout-session",
    ),
    path("webhook/", StripeWebhookView.as_view(), name="payment-webhook"),
    path("<uuid:reference>/", PaymentDetailView.as_view(), name="payment-detail"),
]
