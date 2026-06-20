import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Set admin password from environment variable'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@noorrix.com')

        user = User.objects.filter(email=email).first()
        if user:
            user.set_password('testpass123')
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(f'Password set to testpass123 for {email}')
        else:
            self.stdout.write(f'No user found with email {email}')
