# Authentication API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build JWT auth API with register, login, password reset (SMTP email), and token refresh endpoints.

**Architecture:** Custom `User` model (AbstractUser, email login, single `name` field) in `apps/auth/`. Business logic in serializers; views are thin HTTP adapters. Password reset uses Django's built-in `PasswordResetTokenGenerator`. Smoke test (`manage.py check`) before every migration.

**Tech Stack:** Django 6.0.5, djangorestframework, djangorestframework-simplejwt, python-decouple, pytest-django, SQLite

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Create | Python dependencies |
| `.env` | Create | SECRET_KEY, DEBUG, ALLOWED_HOSTS, EMAIL_*, FRONTEND_URL |
| `pytest.ini` | Create | Test runner pointing at config.settings |
| `conftest.py` | Create | Shared fixtures: api_client, user, auth_tokens, auth_client |
| `config/settings.py` | Modify | Env vars, INSTALLED_APPS, AUTH_USER_MODEL, DRF, simplejwt, email |
| `config/urls.py` | Modify | Include apps.auth URLs at api/v1/auth/ |
| `apps/__init__.py` | Create | Package marker |
| `apps/auth/__init__.py` | Create | Package marker |
| `apps/auth/apps.py` | Create | AppConfig — name='apps.auth', label='user_auth' |
| `apps/auth/models.py` | Create | User model with custom manager |
| `apps/auth/serializers.py` | Create | RegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer |
| `apps/auth/views.py` | Create | RegisterView, PasswordResetView, PasswordResetConfirmView |
| `apps/auth/urls.py` | Create | 5 URL patterns |
| `apps/auth/migrations/` | Generated | DB migration for User model |
| `tests/__init__.py` | Create | Package marker |
| `tests/auth/__init__.py` | Create | Package marker |
| `tests/auth/test_models.py` | Create | User model unit tests |
| `tests/auth/test_views.py` | Create | All endpoint integration tests |

---

### Task 1: Requirements, .env, and test runner

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `pytest.ini`

- [ ] **Step 1: Create `requirements.txt`**

```
Django==6.0.5
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
python-decouple==3.8
pytest==8.2.0
pytest-django==4.8.0
```

- [ ] **Step 2: Create `.env`**

```
SECRET_KEY=django-insecure-sq8q(-@-o(lw(!ts^^qg=)!i5zeq%r0#&d$c+7zcq8qeft$ag8
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
DEFAULT_FROM_EMAIL=noreply@noorrix.com
FRONTEND_URL=http://localhost:3000
```

- [ ] **Step 3: Create `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
```

- [ ] **Step 4: Install dependencies**

```bash
pip install -r requirements.txt
```

Expected: All packages install without errors.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env pytest.ini
git commit -m "chore: add dependencies, .env, and pytest config"
```

---

### Task 2: Update settings.py

**Files:**
- Modify: `config/settings.py`

- [ ] **Step 1: Replace `config/settings.py` with this content**

```python
from pathlib import Path
from datetime import timedelta
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'apps.auth.apps.AuthConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'user_auth.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@noorrix.com')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
```

- [ ] **Step 2: Verify decouple reads .env correctly**

```bash
python -c "from decouple import config; print(config('DEBUG'))"
```

Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add config/settings.py
git commit -m "feat: configure DRF, simplejwt, email, and env-based settings"
```

---

### Task 3: App scaffold, URL wiring, and test infrastructure

**Files:**
- Create: `apps/__init__.py`
- Create: `apps/auth/__init__.py`
- Create: `apps/auth/apps.py`
- Create: `apps/auth/urls.py`
- Create: `apps/auth/serializers.py` (stub)
- Create: `apps/auth/views.py` (stub)
- Modify: `config/urls.py`
- Create: `conftest.py`
- Create: `tests/__init__.py`
- Create: `tests/auth/__init__.py`

- [ ] **Step 1: Create package markers**

Create `apps/__init__.py` — empty file.

Create `apps/auth/__init__.py` — empty file.

Create `tests/__init__.py` — empty file.

Create `tests/auth/__init__.py` — empty file.

- [ ] **Step 2: Create `apps/auth/apps.py`**

```python
from django.apps import AppConfig


class AuthConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.auth'
    label = 'user_auth'
```

- [ ] **Step 3: Create stub `apps/auth/models.py`**

```python
# populated in Task 4
```

- [ ] **Step 4: Create stub `apps/auth/serializers.py`**

```python
# populated in Tasks 5, 7, 8
```

- [ ] **Step 5: Create stub `apps/auth/views.py`**

```python
# populated in Tasks 5, 7, 8
```

- [ ] **Step 6: Create `apps/auth/urls.py`**

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import RegisterView, PasswordResetView, PasswordResetConfirmView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('token/', TokenObtainPairView.as_view(), name='auth-token'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('password-reset/', PasswordResetView.as_view(), name='auth-password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='auth-password-reset-confirm'),
]
```

- [ ] **Step 7: Replace `config/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.auth.urls')),
]
```

- [ ] **Step 8: Create `conftest.py` at the project root (same level as `manage.py`)**

```python
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
```

- [ ] **Step 9: Commit**

```bash
git add apps/ tests/ conftest.py config/urls.py
git commit -m "chore: scaffold apps/auth app, test dirs, and URL routing"
```

---

### Task 4: User model (TDD + smoke test + migration)

**Files:**
- Create: `tests/auth/test_models.py`
- Create: `apps/auth/models.py`
- Generated: `apps/auth/migrations/0001_initial.py`

- [ ] **Step 1: Create `tests/auth/test_models.py`**

```python
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
```

- [ ] **Step 2: Run tests — expect failure (model not defined)**

```bash
pytest tests/auth/test_models.py -v
```

Expected: `ImportError` or `LookupError` — model does not exist yet.

- [ ] **Step 3: Create `apps/auth/models.py`**

```python
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    objects = UserManager()

    def __str__(self):
        return self.email
```

- [ ] **Step 4: Smoke test — verify system check passes before migrating**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

If any errors appear, fix them before continuing. Do NOT run migrations until this passes.

- [ ] **Step 5: Create and run migrations**

```bash
python manage.py makemigrations
python manage.py migrate
```

Expected: Migration file created at `apps/auth/migrations/0001_initial.py` and applied with no errors.

- [ ] **Step 6: Run model tests — expect all pass**

```bash
pytest tests/auth/test_models.py -v
```

Expected: 5 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add apps/auth/models.py apps/auth/migrations/ tests/auth/test_models.py
git commit -m "feat: add User model with email login and custom manager"
```

---

### Task 5: Register endpoint (TDD)

**Files:**
- Create: `tests/auth/test_views.py`
- Modify: `apps/auth/serializers.py`
- Modify: `apps/auth/views.py`

- [ ] **Step 1: Create `tests/auth/test_views.py` with register tests**

```python
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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/auth/test_views.py::TestRegisterView -v
```

Expected: All 5 tests FAIL (views/serializers not implemented yet).

- [ ] **Step 3: Replace `apps/auth/serializers.py` with**

All future serializers will be added to this file, so all imports are declared now.

```python
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'confirm_password']
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name'],
        )
```

- [ ] **Step 4: Replace `apps/auth/views.py` with**

```python
from rest_framework import generics
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer


class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
```

- [ ] **Step 5: Run smoke test**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Run register tests — expect all pass**

```bash
pytest tests/auth/test_views.py::TestRegisterView -v
```

Expected: 5 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add apps/auth/serializers.py apps/auth/views.py tests/auth/test_views.py
git commit -m "feat: add register endpoint"
```

---

### Task 6: Login endpoint (TDD)

**Files:**
- Modify: `tests/auth/test_views.py` (append)

simplejwt's `TokenObtainPairView` handles this endpoint. No new serializer or view code needed — it picks up `USERNAME_FIELD = 'email'` automatically from the User model.

- [ ] **Step 1: Append login tests to `tests/auth/test_views.py`**

```python


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
```

- [ ] **Step 2: Run login tests — expect all pass**

```bash
pytest tests/auth/test_views.py::TestLoginView -v
```

Expected: 4 tests PASSED.

- [ ] **Step 3: Commit**

```bash
git add tests/auth/test_views.py
git commit -m "test: verify login endpoint via simplejwt"
```

---

### Task 7: Password reset endpoint (TDD)

**Files:**
- Modify: `tests/auth/test_views.py` (append)
- Modify: `apps/auth/serializers.py` (append)
- Modify: `apps/auth/views.py` (append)

- [ ] **Step 1: Append password reset tests to `tests/auth/test_views.py`**

```python


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
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/auth/test_views.py::TestPasswordResetView -v
```

Expected: All 4 tests FAIL.

- [ ] **Step 3: Append `PasswordResetSerializer` to `apps/auth/serializers.py`**

Add this class after `RegisterSerializer` (all imports are already at the top of the file from Task 5):

```python
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def save(self):
        email = self.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        reset_link = (
            f'{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'
        )
        send_mail(
            subject='Password Reset Request',
            message=f'Click the link below to reset your password:\n\n{reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )
```

- [ ] **Step 4: Append `PasswordResetView` to `apps/auth/views.py`**

Add these imports at the top of views.py:

```python
from rest_framework.response import Response
from rest_framework.views import APIView
```

Then append this class:

```python


class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        email = serializer.validated_data['email']
        return Response({'detail': f'Password reset link sent to {email}.'})
```

Also add `PasswordResetSerializer` to the import at the top of views.py:

```python
from .serializers import RegisterSerializer, PasswordResetSerializer
```

- [ ] **Step 5: Run smoke test**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Run password reset tests — expect all pass**

```bash
pytest tests/auth/test_views.py::TestPasswordResetView -v
```

Expected: 4 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add apps/auth/serializers.py apps/auth/views.py tests/auth/test_views.py
git commit -m "feat: add password reset request endpoint"
```

---

### Task 8: Password reset confirm endpoint (TDD)

**Files:**
- Modify: `tests/auth/test_views.py` (append)
- Modify: `apps/auth/serializers.py` (append)
- Modify: `apps/auth/views.py` (append)

- [ ] **Step 1: Append confirm tests to `tests/auth/test_views.py`**

```python


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    def _get_uid_token(self, user):
        from django.contrib.auth.tokens import PasswordResetTokenGenerator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        return uid, token

    def test_confirm_valid_token_resets_password(self, api_client, user):
        uid, token = self._get_uid_token(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid,
            'token': token,
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 200
        assert response.data['detail'] == 'Password has been reset successfully.'
        user.refresh_from_db()
        assert user.check_password('NewSecure456!')

    def test_confirm_invalid_token_returns_400(self, api_client, user):
        uid, _ = self._get_uid_token(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid,
            'token': 'invalid-token',
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 400
        assert 'token' in response.data

    def test_confirm_invalid_uid_returns_400(self, api_client, user):
        _, token = self._get_uid_token(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': 'invalid-uid',
            'token': token,
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        assert response.status_code == 400
        assert 'token' in response.data

    def test_confirm_password_mismatch_returns_400(self, api_client, user):
        uid, token = self._get_uid_token(user)
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid,
            'token': token,
            'new_password': 'NewSecure456!',
            'confirm_password': 'DifferentPass789!',
        })
        assert response.status_code == 400
        assert 'confirm_password' in response.data

    def test_confirm_token_invalidated_after_use(self, api_client, user):
        uid, token = self._get_uid_token(user)
        api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid,
            'token': token,
            'new_password': 'NewSecure456!',
            'confirm_password': 'NewSecure456!',
        })
        response = api_client.post(reverse('auth-password-reset-confirm'), {
            'uid': uid,
            'token': token,
            'new_password': 'AnotherPass789!',
            'confirm_password': 'AnotherPass789!',
        })
        assert response.status_code == 400
```

- [ ] **Step 2: Run tests — expect failure**

```bash
pytest tests/auth/test_views.py::TestPasswordResetConfirmView -v
```

Expected: All 5 tests FAIL.

- [ ] **Step 3: Append `PasswordResetConfirmSerializer` to `apps/auth/serializers.py`**

Add this class after `PasswordResetSerializer` (all imports are already at the top of the file from Task 5):

```python


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            pk = force_str(urlsafe_base64_decode(attrs['uid']))
            user = User.objects.get(pk=pk)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({'token': ['Invalid or expired token.']})

        if not PasswordResetTokenGenerator().check_token(user, attrs['token']):
            raise serializers.ValidationError({'token': ['Invalid or expired token.']})

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': ['Passwords do not match.']})

        try:
            validate_password(attrs['new_password'], user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})

        attrs['user'] = user
        return attrs

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['new_password'])
        user.save()
```

- [ ] **Step 4: Append `PasswordResetConfirmView` to `apps/auth/views.py`**

Update the serializers import line at the top of views.py:

```python
from .serializers import RegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
```

Then append this class:

```python


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password has been reset successfully.'})
```

- [ ] **Step 5: Run smoke test**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Run confirm tests — expect all pass**

```bash
pytest tests/auth/test_views.py::TestPasswordResetConfirmView -v
```

Expected: 5 tests PASSED.

- [ ] **Step 7: Commit**

```bash
git add apps/auth/serializers.py apps/auth/views.py tests/auth/test_views.py
git commit -m "feat: add password reset confirm endpoint"
```

---

### Task 9: Token refresh endpoint (TDD) + full suite

**Files:**
- Modify: `tests/auth/test_views.py` (append)

simplejwt's `TokenRefreshView` handles this endpoint. No new code needed.

- [ ] **Step 1: Append token refresh tests to `tests/auth/test_views.py`**

```python


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
```

- [ ] **Step 2: Run token refresh tests — expect all pass**

```bash
pytest tests/auth/test_views.py::TestTokenRefreshView -v
```

Expected: 2 tests PASSED.

- [ ] **Step 3: Run the full test suite**

```bash
pytest tests/ -v
```

Expected: All 25 tests PASSED (5 model + 5 register + 4 login + 4 password-reset + 5 confirm + 2 refresh).

- [ ] **Step 4: Final system check**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 5: Commit**

```bash
git add tests/auth/test_views.py
git commit -m "test: add token refresh tests and verify full suite"
```

---

## Done

All 5 endpoints implemented and verified:

| Endpoint | Method | Auth | Status |
|---|---|---|---|
| `/api/v1/auth/register/` | POST | Public | ✓ |
| `/api/v1/auth/token/` | POST | Public | ✓ |
| `/api/v1/auth/password-reset/` | POST | Public | ✓ |
| `/api/v1/auth/password-reset/confirm/` | POST | Public | ✓ |
| `/api/v1/auth/token/refresh/` | POST | Public | ✓ |
