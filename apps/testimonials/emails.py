import logging

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8" /></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <tr><td style="background:#ac1c7a;padding:28px 40px;text-align:center;">
          <span style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">Noorrix Motors</span>
        </td></tr>
        <tr><td style="padding:32px 40px 8px;text-align:center;">
          <h2 style="margin:0;color:#ac1c7a;font-size:22px;">New Testimonial Received</h2>
          <p style="margin:8px 0 0;color:#888;font-size:14px;">A customer submitted a review on the website — it's already live.</p>
        </td></tr>
        <tr><td style="padding:24px 40px;">
          <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background:#f9f9f9;">
              <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:30%;border-bottom:1px solid #eee;">Name</td>
              <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{name}</td>
            </tr>
            <tr>
              <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Rating</td>
              <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{rating}/5</td>
            </tr>
            <tr style="background:#f9f9f9;">
              <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Review</td>
              <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{review}</td>
            </tr>
          </table>
          <p style="margin-top:20px;color:#888;font-size:13px;">You can hide it from the admin if needed (e.g. spam).</p>
        </td></tr>
        <tr><td style="background:#ac1c7a;padding:16px 40px;text-align:center;">
          <p style="margin:0;color:#ffffff;font-size:12px;">&copy; Noorrix Motors &mdash; This email was generated automatically.</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
"""


def send_admin_testimonial_notification(testimonial):
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [settings.ADMIN_EMAIL],
            "subject": f"New testimonial from {testimonial.name} ({testimonial.rating}★)",
            "html": ADMIN_TEMPLATE.format(
                name=testimonial.name,
                rating=testimonial.rating,
                review=testimonial.review.replace("\n", "<br>"),
            ),
        })
    except Exception:
        logger.exception("Failed to send admin testimonial notification for #%s", testimonial.pk)
