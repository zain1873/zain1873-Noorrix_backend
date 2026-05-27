import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_sets_fields(self):
        user = User.objects.create_user(
            email='user@example.com', password='Pass123!', name='John Smith'
        )
        assert user.email == 'user@example.com'
        assert user.name == 'John Smith'
        assert user.check_password('Pass123!')
        assert user.is_active is True
        assert user.is_staff is False

    def test_email_is_username_field(self):
        assert User.USERNAME_FIELD == 'email'

    def test_str_returns_email(self):
        user = User(email='test@example.com')
        assert str(user) == 'test@example.com'

    def test_email_must_be_unique(self):
        User.objects.create_user(email='dup@example.com', password='Pass123!', name='A')
        with pytest.raises(Exception):
            User.objects.create_user(email='dup@example.com', password='Pass123!', name='B')

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com', password='Admin123!', name='Admin'
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
