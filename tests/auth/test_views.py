import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model

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

    def test_reset_invalid_email_format_returns_400(self, api_client):
        response = api_client.post(reverse('auth-password-reset'), {
            'email': 'not-an-email',
        })
        assert response.status_code == 400

    def test_reset_known_email_sends_email(self, api_client, user):
        from django.test import override_settings
        from django.core import mail
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            api_client.post(reverse('auth-password-reset'), {'email': 'user@example.com'})
        assert len(mail.outbox) == 1
        assert 'user@example.com' in mail.outbox[0].to
        assert 'reset-password' in mail.outbox[0].body
