import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Ensure admin user exists with correct credentials'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@noorrix.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', '')
        name = os.environ.get('DJANGO_SUPERUSER_NAME', 'Admin')

        password = password.strip()
        if not password:
            self.stdout.write('DJANGO_SUPERUSER_PASSWORD not set, skipping.')
            return

        user, created = User.objects.get_or_create(email=email, defaults={'name': name})
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.name = name
        user.save()

        action = 'Created' if created else 'Updated'
        self.stdout.write(f'{action} admin: {email}')
        self.stdout.write(f'Password check: {user.check_password(password)}')
