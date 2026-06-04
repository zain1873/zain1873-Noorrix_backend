from pathlib import Path
from email.mime.image import MIMEImage

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny

from .serializers import ContactSubmissionSerializer

LOGO_PATH = Path(__file__).parent / "noorix_logo.jpg"

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

        html_body = HTML_TEMPLATE.format(
            name=submission.name,
            email=submission.email,
            phone=submission.phone or "-",
            subject=submission.subject,
            message=submission.message.replace("\n", "<br>"),
        )

        plain_body = (
            f"Name:    {submission.name}\n"
            f"Email:   {submission.email}\n"
            f"Phone:   {submission.phone or '-'}\n"
            f"Subject: {submission.subject}\n\n"
            f"Message:\n{submission.message}"
        )

        email = EmailMultiAlternatives(
            subject=f"[Contact Form] {submission.subject}",
            body=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.EMAIL_HOST_USER],
        )
        email.attach_alternative(html_body, "text/html")

        if LOGO_PATH.exists():
            with open(LOGO_PATH, "rb") as f:
                logo = MIMEImage(f.read())
                logo.add_header("Content-ID", "<noorrix_logo>")
                logo.add_header("Content-Disposition", "inline", filename="noorix_logo.jpg")
                email.attach(logo)

        try:
            email.send(fail_silently=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"EMAIL SEND FAILED: {e}")

        return Response(
            {"success": True, "message": "Your message has been sent. We'll be in touch shortly."},
            status=status.HTTP_201_CREATED,
        )
