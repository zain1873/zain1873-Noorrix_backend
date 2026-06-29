import logging
import threading
import resend
from django.conf import settings
from django.contrib import admin
from .models import PartExchangeRequest

logger = logging.getLogger(__name__)

CUSTOMER_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8" />
</head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">

          <!-- Header -->
          <tr>
            <td style="background:#ac1c7a;padding:28px 40px;text-align:center;">
              <span style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">Noorrix Motors</span>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              <h2 style="margin:0 0 16px;color:#ac1c7a;font-size:22px;">Good news, {name}!</h2>
              <p style="margin:0 0 12px;color:#333;font-size:15px;line-height:1.6;">
                Your part exchange valuation for the <strong>{make} {model}</strong> is ready.
                Our team will be in touch shortly with the details.
              </p>
              <p style="margin:0;color:#333;font-size:15px;line-height:1.6;">
                If you have any questions in the meantime, just reply to this email.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#ac1c7a;padding:16px 40px;text-align:center;">
              <p style="margin:0;color:#ffffff;font-size:12px;">&copy; Noorrix Motors &mdash; This email was generated automatically.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


@admin.register(PartExchangeRequest)
class PartExchangeRequestAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "make", "model", "year", "mileage", "created_at", "status"]
    list_filter = ["status", "created_at"]
    list_editable = ["status"]
    search_fields = ["name", "email", "phone", "make", "model"]
    readonly_fields = ["name", "phone", "email", "make", "model", "year", "mileage", "created_at"]
    actions = ["mark_fulfilled_and_notify"]

    @admin.action(description="Mark as fulfilled & notify customer")
    def mark_fulfilled_and_notify(self, request, queryset):
        for submission in queryset:
            submission.status = PartExchangeRequest.STATUS_FULFILLED
            submission.save(update_fields=["status"])
            threading.Thread(target=self._send_customer_email, args=(submission,), daemon=True).start()
        self.message_user(request, f"Marked {queryset.count()} request(s) as fulfilled and notified customers.")

    def _send_customer_email(self, submission):
        html_body = CUSTOMER_EMAIL_TEMPLATE.format(
            name=submission.name,
            make=submission.make,
            model=submission.model,
        )
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [submission.email],
                "subject": "Your part exchange valuation is ready — Noorrix Motors",
                "html": html_body,
            })
            logger.info("Customer fulfilled-notification sent for part exchange request %s", submission.pk)
        except Exception as exc:
            logger.error("Customer email failed for part exchange request %s: %s", submission.pk, exc, exc_info=True)
