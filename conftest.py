import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(db):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User.objects.create_user(
        email='user@example.com',
        password='TestPass123!',
        name='Test User',
    )


@pytest.fixture
def auth_tokens(api_client, user):
    from django.urls import reverse
    response = api_client.post(
        reverse('auth-token'),
        {'email': 'user@example.com', 'password': 'TestPass123!'},
    )
    return {'access': response.data['access'], 'refresh': response.data['refresh']}


@pytest.fixture
def auth_client(api_client, auth_tokens):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_tokens["access"]}')
    return api_client
