import logging

import resend
from django.conf import settings

logger = logging.getLogger(__name__)

SHOWROOM_ADDRESS = "16 Eastside, Cauldwell Walk, Bedford MK42 9DT"

CONFIRMATION_TEMPLATE = """
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

          <!-- Title -->
          <tr>
            <td style="padding:32px 40px 8px;text-align:center;">
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">{type_display} Confirmed</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">We've booked your slot — see you then!</p>
            </td>
          </tr>

          <!-- Details -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:40%;border-bottom:1px solid #eee;">Vehicle</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{vehicle}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Date</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{date}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Time</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{time}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Location</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;">{address}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Next steps -->
          <tr>
            <td style="padding:0 40px 32px;">
              <div style="background:#f9f9f9;border-left:4px solid #ac1c7a;padding:16px;border-radius:4px;color:#333;font-size:14px;line-height:1.6;">
                If you need to change or cancel this booking, please reply to this email or call us.
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

ADMIN_TEMPLATE = """
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

          <!-- Title -->
          <tr>
            <td style="padding:32px 40px 8px;text-align:center;">
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">New {type_display} Booking</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">A customer has booked a slot via the website.</p>
            </td>
          </tr>

          <!-- Details -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:40%;border-bottom:1px solid #eee;">Vehicle</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{vehicle}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Date</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{date}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Time</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{time}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Customer</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{name}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Email</td>
                  <td style="padding:12px 16px;font-size:14px;border-bottom:1px solid #eee;"><a href="mailto:{email}" style="color:#ac1c7a;text-decoration:none;">{email}</a></td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Phone</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;">{phone}</td>
                </tr>
              </table>
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


def send_appointment_confirmation(appointment):
    """Confirm the booking to the customer who made it."""
    vehicle = appointment.car.title if appointment.car else "N/A"
    html_body = CONFIRMATION_TEMPLATE.format(
        type_display=appointment.get_type_display(),
        vehicle=vehicle,
        date=appointment.date.strftime("%A, %d %B %Y"),
        time=appointment.time.strftime("%H:%M"),
        address=SHOWROOM_ADDRESS,
    )
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [appointment.email],
            "subject": f"{appointment.get_type_display()} Confirmed — Noorrix Motors",
            "html": html_body,
        })
        logger.info("Appointment confirmation sent to %s for appointment %s", appointment.email, appointment.pk)
    except Exception:
        logger.exception("Failed to send appointment confirmation for appointment %s", appointment.pk)


def send_admin_appointment_notification(appointment):
    """Notify the dealership that a customer has booked a slot."""
    if not settings.ADMIN_EMAIL:
        logger.warning("ADMIN_EMAIL not configured — skipping appointment notification for %s", appointment.pk)
        return

    vehicle = appointment.car.title if appointment.car else "N/A"
    html_body = ADMIN_TEMPLATE.format(
        type_display=appointment.get_type_display(),
        vehicle=vehicle,
        date=appointment.date.strftime("%A, %d %B %Y"),
        time=appointment.time.strftime("%H:%M"),
        name=appointment.name,
        email=appointment.email,
        phone=appointment.phone,
    )
    try:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [settings.ADMIN_EMAIL],
            "reply_to": [appointment.email],
            "subject": f"New {appointment.get_type_display()} Booking — {vehicle}",
            "html": html_body,
        })
        logger.info("Admin appointment notification sent for appointment %s", appointment.pk)
    except Exception:
        logger.exception("Failed to send admin appointment notification for appointment %s", appointment.pk)
