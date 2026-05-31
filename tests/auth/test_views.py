import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
class TestRegisterView:
    def test_register_success_returns_201(self, api_client):
        response = api_client.post(reverse('auth-register'), {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        assert response.status_code == 201
        assert response.data['email'] == 'john@example.com'
        assert response.data['name'] == 'John Smith'
        assert 'id' in response.data
        assert 'password' not in response.data

    def test_register_creates_user_in_db(self, api_client):
        response = api_client.post(reverse('auth-register'), {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        assert response.status_code == 201
        assert User.objects.filter(email='john@example.com').exists()
        user = User.objects.get(email='john@example.com')
        assert user.check_password('SecurePass123!')

    def test_register_duplicate_email_returns_400(self, api_client, user):
        response = api_client.post(reverse('auth-register'), {
            'name': 'Another',
            'email': 'user@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_password_mismatch_returns_400(self, api_client):
        response = api_client.post(reverse('auth-register'), {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'DifferentPass123!',
        })
        assert response.status_code == 400
        assert 'confirm_password' in response.data

    def test_register_missing_name_returns_400(self, api_client):
        response = api_client.post(reverse('auth-register'), {
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        assert response.status_code == 400
        assert 'name' in response.data

    def test_register_weak_password_returns_400(self, api_client):
        response = api_client.post(reverse('auth-register'), {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'password',
            'confirm_password': 'password',
        })
        assert response.status_code == 400
        assert 'password' in response.data


@pytest.mark.django_db
class TestLoginView:
    def test_login_success_returns_tokens(self, api_client, user):
        response = api_client.post(reverse('auth-token'), {
            'email': 'user@example.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password_returns_401(self, api_client, user):
        response = api_client.post(reverse('auth-token'), {
            'email': 'user@example.com',
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_login_nonexistent_email_returns_401(self, api_client):
        response = api_client.post(reverse('auth-token'), {
            'email': 'nobody@example.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == 401

    def test_login_inactive_user_returns_401(self, api_client, db):
        inactive = User.objects.create_user(
            email='inactive@example.com', password='TestPass123!', name='Inactive', is_active=False
        )
        response = api_client.post(reverse('auth-token'), {
            'email': 'inactive@example.com',
            'password': 'TestPass123!',
        })
        assert response.status_code == 401


@pytest.mark.django_db
class TestPasswordResetView:
    def test_reset_known_email_returns_200(self, api_client, user):
        response = api_client.post(reverse('auth-password-reset'), {
            'email': 'user@example.com',
        })
        assert response.status_code == 200
        assert 'detail' in response.data

    def test_reset_unknown_email_still_returns_200(self, api_client):
        response = api_client.post(reverse('auth-password-reset'), {
            'email': 'nobody@example.com',
        })
        assert response.status_code == 200
        assert 'detail' in response.data

    def test_reset_invalid_email_format_returns_400(self, api_client):
        response = api_client.post(reverse('auth-password-reset'), {
            'email': 'not-an-email',
        })
        assert response.status_code == 400

    def test_reset_known_email_sends_email(self, api_client, user):
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            api_client.post(reverse('auth-password-reset'), {'email': 'user@example.com'})
        assert len(mail.outbox) == 1
        assert 'user@example.com' in mail.outbox[0].to
        assert 'OTP' in mail.outbox[0].body


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    def _create_otp(self, user, otp='123456'):
        from apps.auth.models import PasswordResetOTP
        PasswordResetOTP.objects.filter(user=user, is_used=False).delete()
        return PasswordResetOTP.objects.create(user=user, otp=otp)

    def test_confirm_valid_otp_resets_password(self, api_client, user):
        self._create_otp(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '123456',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 200
        assert response.data['detail'] == 'Password has been reset successfully.'
        user.refresh_from_db()
        assert user.check_password('NewSecure456!')

    def test_confirm_invalid_otp_returns_400(self, api_client, user):
        self._create_otp(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '000000',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 400
        assert 'otp' in response.data

    def test_confirm_unknown_email_returns_400(self, api_client, user):
        self._create_otp(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'nobody@example.com',
            'otp': '123456',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 400
        assert 'otp' in response.data

    def test_confirm_password_mismatch_returns_400(self, api_client, user):
        self._create_otp(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '123456',
            'new_password': 'NewSecure456!',
            'confirm_password': 'DifferentPass789!',
        })
        assert response.status_code == 400
        assert 'confirm_password' in response.data

    def test_confirm_otp_invalidated_after_use(self, api_client, user):
        self._create_otp(user)
        api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '123456',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '123456',
            'new_password': 'AnotherPass789!',
            'confirm_password': 'AnotherPass789!',
        })
        assert response.status_code == 400

    def test_confirm_expired_otp_returns_400(self, api_client, user):
        from datetime import timedelta
        from django.utils import timezone
        otp_obj = self._create_otp(user)
        otp_obj.created_at = timezone.now() - timedelta(minutes=11)
        otp_obj.save()
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'email': 'user@example.com',
            'otp': '123456',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 400
        assert 'otp' in response.data


@pytest.mark.django_db
class TestTokenRefreshView:
    def test_refresh_valid_token_returns_new_access(self, api_client, auth_tokens):
        response = api_client.post(reverse('auth-token-refresh'), {
            'refresh': auth_tokens['refresh'],
        })
        assert response.status_code == 200
        assert 'access' in response.data

    def test_refresh_invalid_token_returns_401(self, api_client):
        response = api_client.post(reverse('auth-token-refresh'), {
            'refresh': 'not-a-valid-token',
        })
        assert response.status_code == 401
