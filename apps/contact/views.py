import logging
import threading
import resend
from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)

from .serializers import ContactSubmissionSerializer

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
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">Thank You for Reaching Out!</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">We've received your message and will get back to you shortly.</p>
            </td>
          </tr>

          <!-- Summary -->
          <tr>
            <td style="padding:24px 40px;">
              <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                <tr style="background:#f9f9f9;">
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;width:30%;border-bottom:1px solid #eee;">Name</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{name}</td>
                </tr>
                <tr>
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;border-bottom:1px solid #eee;">Subject</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;border-bottom:1px solid #eee;">{subject}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Message -->
          <tr>
            <td style="padding:0 40px 32px;">
              <p style="margin:0 0 8px;font-weight:bold;color:#555;font-size:14px;">Your Message:</p>
              <div style="background:#f9f9f9;border-left:4px solid #ac1c7a;padding:16px;border-radius:4px;color:#333;font-size:14px;line-height:1.6;">
                {message}
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#ac1c7a;padding:16px 40px;text-align:center;">
              <p style="margin:0;color:#ffffff;font-size:12px;">&copy; Noorrix Motors &mdash; This is an automated confirmation. Please do not reply to this email.</p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

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
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">New Contact Form Inquiry</h2>
              <p style="margin:8px 0 0;color:#888;font-size:14px;">A customer has submitted a message via the website.</p>
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
                  <td style="padding:12px 16px;font-weight:bold;color:#555;font-size:14px;">Subject</td>
                  <td style="padding:12px 16px;color:#222;font-size:14px;">{subject}</td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Message -->
          <tr>
            <td style="padding:0 40px 32px;">
              <p style="margin:0 0 8px;font-weight:bold;color:#555;font-size:14px;">Message:</p>
              <div style="background:#f9f9f9;border-left:4px solid #ac1c7a;padding:16px;border-radius:4px;color:#333;font-size:14px;line-height:1.6;">
                {message}
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


@extend_schema(
    tags=['Contact'],
    summary='Submit a contact form',
    request=ContactSubmissionSerializer,
    responses={
        201: inline_serializer(
            name='ContactSubmissionSuccess',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            },
        ),
        400: inline_serializer(
            name='ContactSubmissionError',
            fields={
                'success': serializers.BooleanField(),
                'errors': serializers.DictField(),
            },
        ),
    },
)
class ContactSubmissionView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = serializer.save()

        threading.Thread(target=self._send_emails, args=(submission,), daemon=True).start()

        return Response(
            {"success": True, "message": "Your message has been sent. We'll be in touch shortly."},
            status=status.HTTP_201_CREATED,
        )

    def _send_emails(self, submission):
        self._send_admin_email(submission)
        self._send_confirmation_email(submission)

    def _send_admin_email(self, submission):
        html_body = HTML_TEMPLATE.format(
            name=submission.name,
            email=submission.email,
            phone=submission.phone or "-",
            subject=submission.subject,
            message=submission.message.replace("\n", "<br>"),
        )
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [settings.ADMIN_EMAIL],
                "reply_to": [submission.email],
                "subject": f"[Contact Form] {submission.subject}",
                "html": html_body,
            })
            logger.info("Admin notification sent for submission %s", submission.pk)
        except Exception as exc:
            logger.error("Admin email failed for submission %s: %s", submission.pk, exc, exc_info=True)

    def _send_confirmation_email(self, submission):
        html_body = CONFIRMATION_TEMPLATE.format(
            name=submission.name,
            subject=submission.subject,
            message=submission.message.replace("\n", "<br>"),
        )
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [submission.email],
                "reply_to": [settings.ADMIN_EMAIL],
                "subject": "We've received your message — Noorrix Motors",
                "html": html_body,
            })
            logger.info("Confirmation sent to %s for submission %s", submission.email, submission.pk)
        except Exception as exc:
            logger.error("Confirmation email to %s failed for submission %s: %s", submission.email, submission.pk, exc, exc_info=True)

