import uuid

from django.conf import settings
from django.db import models


class Payment(models.Model):
    """A single Stripe payment.

    One row is created when the frontend requests a PaymentIntent. Its status
    is then driven by Stripe webhooks (the client is never trusted to confirm
    a payment — only the signed webhook can move a payment to ``succeeded``).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"
        REFUNDED = "refunded", "Refunded"

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
    )
    # The vehicle this payment reserves. SET_NULL so deleting a car never
    # destroys the payment record.
    car = models.ForeignKey(
        "cars.Car",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payments",
        help_text="The vehicle this payment reserves (if any).",
    )
    # Nullable: a Checkout Session has no PaymentIntent until the buyer pays.
    stripe_payment_intent_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    # Set only for the hosted Checkout flow (create-checkout-session).
    stripe_session_id = models.CharField(
        max_length=255, unique=True, null=True, blank=True
    )
    # Amount in the currency's major unit (e.g. pounds), Stripe stores minor units.
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="gbp")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    description = models.CharField(max_length=255, blank=True, default="")
    customer_email = models.EmailField(blank=True, default="")
    # The payment method type Stripe actually charged (card, paypal, apple_pay…).
    payment_method = models.CharField(max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} — {self.amount} {self.currency.upper()} ({self.status})"

    @property
    def amount_minor(self):
        """Amount in the smallest currency unit, as Stripe expects."""
        return int(self.amount * 100)

    def update_linked_car(self):
        """Keep the linked car's status in sync with this payment's status.

        Succeeded → reserve an available car. Failed/canceled/refunded →
        release a car we had reserved. A car already marked ``sold`` is never
        touched automatically (admin keeps manual control of that).

        Locks the car row for the duration of the check-then-set so two
        webhook deliveries for the same car (e.g. two buyers paying at once)
        can't both read ``available`` before either writes ``reserved``.
        """
        if not self.car_id:
            return
        # Local import: the payments app loads before cars, so importing at
        # module level could run before the cars app is ready.
        from django.db import transaction

        from apps.cars.models import Car, CarStatus

        with transaction.atomic():
            car = Car.objects.select_for_update().get(pk=self.car_id)

            if self.status == self.Status.SUCCEEDED:
                if car.status == CarStatus.AVAILABLE:
                    car.status = CarStatus.RESERVED
                    car.save(update_fields=["status", "updated_at"])
            elif self.status in (self.Status.FAILED, self.Status.CANCELED, self.Status.REFUNDED):
                if car.status == CarStatus.RESERVED:
                    car.status = CarStatus.AVAILABLE
                    car.save(update_fields=["status", "updated_at"])
