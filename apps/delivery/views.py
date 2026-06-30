import logging
import threading
import resend
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny

from .serializers import DeliveryRequestSerializer

logger = logging.getLogger(__name__)

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
              <span style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">Noorrix Motors</span>
            </td>
          </tr>

          <!-- Title -->
          <tr>
            <td style="padding:32px 40px 8px;text-align:center;">
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">New Delivery Request</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">A customer wants their vehicle delivered.</p>
            </td>
          </tr>

          <!-- Details Table -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:30%;border-bottom:1px solid #eee;">Name</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{name}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Email</td>
                  <td style="padding:12px 16px;font-size:14px;border-bottom:1px solid #eee;"><a href="mailto:{email}" style="color:#ac1c7a;text-decoration:none;">{email}</a></td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Phone</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{phone}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Vehicle</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{vehicle}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Address</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{address}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Postcode</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{postcode}</td>
                </tr>
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Preferred Date</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;">{preferred_date}</td>
                </tr>{notes_row}
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

NOTES_ROW_TEMPLATE = """
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Notes</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;">{notes}</td>
                </tr>"""


@extend_schema(
    tags=['Delivery'],
    summary='Submit a vehicle delivery request',
    request=DeliveryRequestSerializer,
    responses={
        201: inline_serializer(
            name='DeliveryRequestSuccess',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            },
        ),
        400: inline_serializer(
            name='DeliveryRequestError',
            fields={
                'success': serializers.BooleanField(),
                'errors': serializers.DictField(),
            },
        ),
    },
)
class DeliveryRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = DeliveryRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = serializer.save()

        threading.Thread(target=self._send_admin_email, args=(submission,), daemon=True).start()

        return Response(
            {"success": True, "message": "Thanks! We'll confirm your delivery details shortly."},
            status=status.HTTP_201_CREATED,
        )

    def _send_admin_email(self, submission):
        notes_row = NOTES_ROW_TEMPLATE.format(notes=submission.notes) if submission.notes else ""
        html_body = HTML_TEMPLATE.format(
            name=submission.name,
            email=submission.email,
            phone=submission.phone,
            vehicle=submission.vehicle,
            address=submission.address,
            postcode=submission.postcode,
            preferred_date=submission.preferred_date if submission.preferred_date else "Not specified",
            notes_row=notes_row,
        )
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [settings.ADMIN_EMAIL],
                "reply_to": [submission.email],
                "subject": f"[Delivery Request] {submission.vehicle}",
                "html": html_body,
            })
            logger.info("Admin notification sent for delivery request %s", submission.pk)
        except Exception as exc:
            logger.error("Admin email failed for delivery request %s: %s", submission.pk, exc, exc_info=True)
