import logging
import threading
import resend
from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny

from .models import NewsletterSubscriber
from .serializers import NewsletterSubscriberSerializer

logger = logging.getLogger(__name__)

WELCOME_TEMPLATE = """
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
          <tr>
            <td style="background:#ac1c7a;padding:28px 40px;text-align:center;">
              <span style="color:#ffffff;font-size:22px;font-weight:bold;letter-spacing:1px;">Noorrix Motors</span>
            </td>
          </tr>
          <tr>
            <td style="padding:32px 40px;text-align:center;">
              <h2 style="margin:0;color:#ac1c7a;font-size:22px;">You're Subscribed!</h2>
              <p style="margin:12px 0 0;color:#555;font-size:14px;line-height:1.6;">
                Thanks for joining the Noorrix Motors newsletter. We'll keep you posted on new arrivals, offers, and updates.
              </p>
            </td>
          </tr>
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


@extend_schema(
    tags=['Newsletter'],
    summary='Subscribe to the newsletter',
    request=NewsletterSubscriberSerializer,
    responses={
        201: inline_serializer(
            name='NewsletterSubscribeSuccess',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            },
        ),
        400: inline_serializer(
            name='NewsletterSubscribeError',
            fields={
                'success': serializers.BooleanField(),
                'errors': serializers.DictField(),
            },
        ),
    },
)
class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewsletterSubscriberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)

        if not created and subscriber.is_active:
            return Response(
                {"success": True, "message": "You're already subscribed."},
                status=status.HTTP_200_OK,
            )

        if not created and not subscriber.is_active:
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save(update_fields=["is_active", "unsubscribed_at"])

        threading.Thread(target=self._send_welcome_email, args=(subscriber,), daemon=True).start()

        return Response(
            {"success": True, "message": "Thanks for subscribing!"},
            status=status.HTTP_201_CREATED,
        )

    def _send_welcome_email(self, subscriber):
        try:
            resend.api_key = settings.RESEND_API_KEY
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": [subscriber.email],
                "subject": "Welcome to the Noorrix Motors newsletter",
                "html": WELCOME_TEMPLATE,
            })
            logger.info("Welcome email sent to %s", subscriber.email)
        except Exception as exc:
            logger.error("Welcome email to %s failed: %s", subscriber.email, exc, exc_info=True)


@extend_schema(
    tags=['Newsletter'],
    summary='Unsubscribe from the newsletter',
    request=NewsletterSubscriberSerializer,
    responses={
        200: inline_serializer(
            name='NewsletterUnsubscribeSuccess',
            fields={
                'success': serializers.BooleanField(),
                'message': serializers.CharField(),
            },
        ),
    },
)
class NewsletterUnsubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NewsletterSubscriberSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"success": False, "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]

        NewsletterSubscriber.objects.filter(email=email, is_active=True).update(
            is_active=False, unsubscribed_at=timezone.now()
        )

        return Response(
            {"success": True, "message": "You've been unsubscribed."},
            status=status.HTTP_200_OK,
        )
