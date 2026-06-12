import base64
import logging
from pathlib import Path

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

LOGO_PATH = Path(__file__).parent.parent / "contact" / "noorix_logo.jpg"

HTML_TEMPLATE = """
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
              <img src="cid:noorrix_logo" alt="Noorrix Motors" style="max-height:60px;max-width:200px;" />
            </td>
          </tr>

          <!-- Title -->
          <tr>
            <td style="padding:32px 40px 8px;text-align:center;">
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">Payment Confirmed</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">Thank you! Your deposit has been successfully received.</p>
            </td>
          </tr>

          <!-- Details -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:40%;border-bottom:1px solid #eee;">Vehicle</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{description}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Deposit Paid</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">&pound;{amount} {currency}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Payment Method</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{payment_method}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Reference</td>
                  <td style="padding:12px 16px;color:#222;font-size:13px;word-break:break-all;">{reference}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Next steps -->
          <tr>
            <td style="padding:0 40px 32px;">
              <div style="background:#f9f9f9;border-left:4px solid #ac1c7a;padding:16px;border-radius:4px;color:#333;font-size:14px;line-height:1.6;">
                Our team will be in touch shortly to confirm the next steps for your vehicle reservation.
                If you have any questions, please reply to this email or visit our website.
              </div>
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


def send_payment_confirmation(payment):
    """Send a confirmation email to the customer after payment succeeds."""
    if not payment.customer_email:
        logger.warning("Payment %s succeeded but has no customer email — skipping confirmation.", payment.reference)
        return

    amount = f"{payment.amount:.2f}"
    currency = payment.currency.upper()
    description = payment.description or "Vehicle reservation deposit"
    method = payment.payment_method.replace("_", " ").title() if payment.payment_method else "Card"

    html_body = HTML_TEMPLATE.format(
        description=description,
        amount=amount,
        currency=currency,
        payment_method=method,
        reference=str(payment.reference),
    )

    plain_body = (
        f"Payment Confirmed\n\n"
        f"Vehicle:        {description}\n"
        f"Deposit Paid:   £{amount} {currency}\n"
        f"Payment Method: {method}\n"
        f"Reference:      {payment.reference}\n\n"
        "Our team will be in touch shortly to confirm the next steps.\n"
        "If you have any questions please reply to this email."
    )

    params = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [payment.customer_email],
        "subject": "Payment Confirmed — Noorrix Motors",
        "html": html_body,
        "text": plain_body,
    }

    if LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as f:
            params["attachments"] = [{
                "filename": "noorix_logo.jpg",
                "content": base64.b64encode(f.read()).decode(),
                "content_id": "noorrix_logo",
            }]

    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send(params)
        logger.info("Payment confirmation sent to %s for payment %s", payment.customer_email, payment.reference)
    except Exception:
        logger.exception("Failed to send payment confirmation for payment %s", payment.reference)
