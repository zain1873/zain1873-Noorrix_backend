import smtplib
import socket

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Test email configuration'

    def add_arguments(self, parser):
        parser.add_argument('--to', default=settings.EMAIL_HOST_USER)

    def handle(self, *args, **options):
        to_email = options['to']

        self.stdout.write(f"HOST:     {settings.EMAIL_HOST}")
        self.stdout.write(f"PORT:     {settings.EMAIL_PORT}")
        self.stdout.write(f"TLS:      {settings.EMAIL_USE_TLS}")
        self.stdout.write(f"SSL:      {settings.EMAIL_USE_SSL}")
        self.stdout.write(f"USER:     {settings.EMAIL_HOST_USER}")
        self.stdout.write(f"FROM:     {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"TO:       {to_email}")
        self.stdout.write(f"TIMEOUT:  {settings.EMAIL_TIMEOUT}")
        self.stdout.write("")

        # Step 1: TCP connection test
        self.stdout.write(f"[1] Testing TCP connection to {settings.EMAIL_HOST}:{settings.EMAIL_PORT} ...")
        try:
            sock = socket.create_connection((settings.EMAIL_HOST, settings.EMAIL_PORT), timeout=10)
            sock.close()
            self.stdout.write(self.style.SUCCESS("    TCP OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    TCP FAILED: {e}"))
            return

        # Step 2: SMTP auth test
        self.stdout.write("[2] Testing SMTP authentication ...")
        try:
            if settings.EMAIL_USE_SSL:
                server = smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15)
            else:
                server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=15)
                if settings.EMAIL_USE_TLS:
                    server.starttls()
            server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.quit()
            self.stdout.write(self.style.SUCCESS("    SMTP AUTH OK"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    SMTP AUTH FAILED: {e}"))
            return

        # Step 3: Send test email
        self.stdout.write(f"[3] Sending test email to {to_email} ...")
        try:
            send_mail(
                subject="[Noorrix] Test Email from Railway",
                message="This is a test email sent from Railway to verify SMTP configuration.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"    EMAIL SENT — check inbox/spam at {to_email}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"    SEND FAILED: {e}"))
