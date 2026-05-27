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
        api_client.post(reverse('auth-register'), {
            'name': 'John Smith',
            'email': 'john@example.com',
            'password': 'SecurePass123!',
            'confirm_password': 'SecurePass123!',
        })
        assert User.objects.filter(email='john@example.com').exists()

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
