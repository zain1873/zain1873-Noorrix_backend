# Authentication Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build JWT-based authentication for Noorrix Motors staff/admin users with 5 endpoints: login, token refresh, logout, me (GET/PATCH), and change-password.

**Architecture:** `StaffUser` extends `AbstractUser` with email as the login field. simplejwt handles token generation and rotation; a custom serializer rejects non-staff/non-superuser users at login. All code lives in `apps/authentication/`. Environment variables loaded via python-decouple.

**Tech Stack:** Django 6.0.5, djangorestframework, djangorestframework-simplejwt, python-decouple, pytest-django, SQLite

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `requirements.txt` | Create | All Python dependencies |
| `.env` | Create | SECRET_KEY, DEBUG, ALLOWED_HOSTS |
| `pytest.ini` | Create | Test runner config pointing at config.settings |
| `config/settings.py` | Modify | Env var loading, INSTALLED_APPS, AUTH_USER_MODEL, REST_FRAMEWORK, SIMPLE_JWT |
| `config/urls.py` | Modify | Include `apps.authentication` URL patterns |
| `apps/__init__.py` | Create | Package marker |
| `apps/authentication/__init__.py` | Create | Package marker |
| `apps/authentication/models.py` | Create | StaffUser model |
| `apps/authentication/admin.py` | Create | Django admin registration |
| `apps/authentication/serializers.py` | Create | StaffTokenObtainPairSerializer, StaffUserProfileSerializer, ChangePasswordSerializer |
| `apps/authentication/views.py` | Create | LoginView, LogoutView, MeView, ChangePasswordView |
| `apps/authentication/urls.py` | Create | 5 URL patterns |
| `tests/__init__.py` | Create | Test package root |
| `tests/authentication/__init__.py` | Create | Auth test sub-package |
| `tests/authentication/test_models.py` | Create | StaffUser model tests |
| `tests/authentication/test_views.py` | Create | All endpoint tests |

---

### Task 1: Requirements, .env, and test runner config

**Files:**
- Create: `requirements.txt`
- Create: `.env`
- Create: `pytest.ini`

- [ ] **Step 1: Create requirements.txt**

```
Django==6.0.5
djangorestframework==3.15.2
djangorestframework-simplejwt==5.3.1
python-decouple==3.8
pytest==8.2.0
pytest-django==4.8.0
```

- [ ] **Step 2: Create .env**

```
SECRET_KEY=django-insecure-sq8q(-@-o(lw(!ts^^qg=)!i5zeq%r0#&d$c+7zcq8qeft$ag8
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

- [ ] **Step 3: Create pytest.ini**

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
git commit -m "chore: add dependencies and environment config"
```

---

### Task 2: Update config/settings.py

**Files:**
- Modify: `config/settings.py`

- [ ] **Step 1: Replace the full settings.py with this content**

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
    'rest_framework_simplejwt.token_blacklist',
    'apps.authentication',
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

AUTH_USER_MODEL = 'authentication.StaffUser'

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
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
```

- [ ] **Step 2: Verify settings load (app scaffold not created yet — expect ImportError on apps.authentication, that is fine)**

```bash
python -c "from decouple import config; print(config('DEBUG'))"
```

Expected: `True`

- [ ] **Step 3: Commit**

```bash
git add config/settings.py
git commit -m "feat: configure DRF, simplejwt, and env-based settings"
```

---

### Task 3: Create app scaffold

**Files:**
- Create: `apps/__init__.py`
- Create: `apps/authentication/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/authentication/__init__.py`

- [ ] **Step 1: Create all directories and package markers**

```bash
mkdir -p apps/authentication tests/authentication
touch apps/__init__.py
touch apps/authentication/__init__.py
touch tests/__init__.py
touch tests/authentication/__init__.py
```

- [ ] **Step 2: Commit**

```bash
git add apps/ tests/
git commit -m "chore: scaffold apps/authentication and tests directories"
```

---

### Task 4: StaffUser model (TDD)

**Files:**
- Create: `apps/authentication/models.py`
- Create: `tests/authentication/test_models.py`

- [ ] **Step 1: Write the failing model tests**

`tests/authentication/test_models.py`:
```python
import pytest
from apps.authentication.models import StaffUser


@pytest.mark.django_db
class TestStaffUser:
    def test_create_user_with_email(self):
        user = StaffUser.objects.create_user(
            email='staff@noorrix.com',
            password='Pass123!',
            first_name='Ali',
            last_name='Khan',
        )
        assert user.email == 'staff@noorrix.com'
        assert user.check_password('Pass123!')
        assert user.is_staff is False
        assert user.is_active is True

    def test_email_is_username_field(self):
        assert StaffUser.USERNAME_FIELD == 'email'

    def test_str_returns_email(self):
        user = StaffUser(email='admin@noorrix.com')
        assert str(user) == 'admin@noorrix.com'

    def test_email_must_be_unique(self):
        StaffUser.objects.create_user(
            email='dup@noorrix.com', password='Pass123!', first_name='A', last_name='B'
        )
        with pytest.raises(Exception):
            StaffUser.objects.create_user(
                email='dup@noorrix.com', password='Pass123!', first_name='C', last_name='D'
            )
```

- [ ] **Step 2: Run — expect failure (model not defined yet)**

```bash
pytest tests/authentication/test_models.py -v
```

Expected: `ImportError: cannot import name 'StaffUser'`

- [ ] **Step 3: Create apps/authentication/models.py**

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class StaffUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
```

- [ ] **Step 4: Create and run migrations**

```bash
python manage.py makemigrations authentication
python manage.py migrate
```

Expected: Migration file created and applied with no errors.

- [ ] **Step 5: Run tests — expect pass**

```bash
pytest tests/authentication/test_models.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 6: Commit**

```bash
git add apps/authentication/models.py apps/authentication/migrations/ tests/authentication/test_models.py
git commit -m "feat: add StaffUser custom model with email login"
```

---

### Task 5: Admin registration

**Files:**
- Create: `apps/authentication/admin.py`

- [ ] **Step 1: Create apps/authentication/admin.py**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import StaffUser


@admin.register(StaffUser)
class StaffUserAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'is_staff'),
        }),
    )
```

- [ ] **Step 2: Verify Django system check passes**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 3: Commit**

```bash
git add apps/authentication/admin.py
git commit -m "feat: register StaffUser in Django admin"
```

---

### Task 6: Wire up URLs and view scaffold

**Files:**
- Create: `apps/authentication/serializers.py`
- Create: `apps/authentication/views.py`
- Create: `apps/authentication/urls.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Create apps/authentication/serializers.py (full implementation — used by all views)**

```python
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import StaffUser


class StaffTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        if not (user.is_staff or user.is_superuser):
            raise serializers.ValidationError('Only staff and admin users can log in.')
        data['user'] = {
            'id': user.id,
            'email': user.email,
            'full_name': f'{user.first_name} {user.last_name}'.strip(),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        return data


class StaffUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaffUser
        fields = ['id', 'email', 'first_name', 'last_name', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'is_staff', 'is_superuser']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        validate_password(value)
        return value
```

- [ ] **Step 2: Create apps/authentication/views.py (full implementation)**

```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

from .serializers import StaffTokenObtainPairSerializer, StaffUserProfileSerializer, ChangePasswordSerializer


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = StaffTokenObtainPairSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({'detail': 'Logged out successfully.'})
        except (TokenError, InvalidToken):
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StaffUserProfileSerializer
    http_method_names = ['get', 'patch']

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Wrong password.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password changed successfully.'})
```

- [ ] **Step 3: Create apps/authentication/urls.py**

```python
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, LogoutView, MeView, ChangePasswordView

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='auth-token-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
]
```

- [ ] **Step 4: Update config/urls.py**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.authentication.urls')),
]
```

- [ ] **Step 5: Verify system check passes**

```bash
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

- [ ] **Step 6: Commit**

```bash
git add apps/authentication/serializers.py apps/authentication/views.py apps/authentication/urls.py config/urls.py
git commit -m "feat: implement all auth views, serializers, and URL routing"
```

---

### Task 7: Login endpoint tests

**Files:**
- Create: `tests/authentication/test_views.py`

- [ ] **Step 1: Create tests/authentication/test_views.py with login tests and shared fixtures**

```python
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.authentication.models import StaffUser


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def staff_user(db):
    return StaffUser.objects.create_user(
        email='staff@noorrix.com',
        password='StaffPass123!',
        first_name='Ali',
        last_name='Khan',
        is_staff=True,
    )


@pytest.fixture
def non_staff_user(db):
    return StaffUser.objects.create_user(
        email='regular@noorrix.com',
        password='RegPass123!',
        first_name='Sara',
        last_name='Ahmed',
        is_staff=False,
        is_superuser=False,
    )


@pytest.fixture
def auth_tokens(api_client, staff_user):
    response = api_client.post(
        reverse('auth-login'),
        {'email': 'staff@noorrix.com', 'password': 'StaffPass123!'},
    )
    return {'access': response.data['access'], 'refresh': response.data['refresh']}


@pytest.fixture
def auth_client(api_client, auth_tokens):
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {auth_tokens["access"]}')
    return api_client


@pytest.mark.django_db
class TestLoginView:
    def test_staff_login_returns_tokens_and_user(self, api_client, staff_user):
        response = api_client.post(
            reverse('auth-login'),
            {'email': 'staff@noorrix.com', 'password': 'StaffPass123!'},
        )
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['email'] == 'staff@noorrix.com'
        assert response.data['user']['full_name'] == 'Ali Khan'
        assert response.data['user']['is_staff'] is True

    def test_non_staff_login_rejected(self, api_client, non_staff_user):
        response = api_client.post(
            reverse('auth-login'),
            {'email': 'regular@noorrix.com', 'password': 'RegPass123!'},
        )
        assert response.status_code == 400

    def test_invalid_credentials_rejected(self, api_client, staff_user):
        response = api_client.post(
            reverse('auth-login'),
            {'email': 'staff@noorrix.com', 'password': 'wrongpass'},
        )
        assert response.status_code == 401

    def test_missing_password_rejected(self, api_client):
        response = api_client.post(reverse('auth-login'), {'email': 'staff@noorrix.com'})
        assert response.status_code == 400
```

- [ ] **Step 2: Run login tests — expect all pass**

```bash
pytest tests/authentication/test_views.py::TestLoginView -v
```

Expected: 4 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/authentication/test_views.py
git commit -m "test: add login endpoint tests"
```

---

### Task 8: Logout endpoint tests

**Files:**
- Modify: `tests/authentication/test_views.py`

- [ ] **Step 1: Append logout tests to tests/authentication/test_views.py**

```python


@pytest.mark.django_db
class TestLogoutView:
    def test_logout_returns_success(self, auth_client, auth_tokens):
        response = auth_client.post(reverse('auth-logout'), {'refresh': auth_tokens['refresh']})
        assert response.status_code == 200
        assert response.data['detail'] == 'Logged out successfully.'

    def test_blacklisted_token_cannot_be_refreshed(self, auth_client, auth_tokens):
        refresh = auth_tokens['refresh']
        auth_client.post(reverse('auth-logout'), {'refresh': refresh})
        auth_client.credentials()
        response = auth_client.post(reverse('auth-token-refresh'), {'refresh': refresh})
        assert response.status_code == 401

    def test_logout_requires_auth(self, api_client, auth_tokens):
        response = api_client.post(reverse('auth-logout'), {'refresh': auth_tokens['refresh']})
        assert response.status_code == 401

    def test_invalid_refresh_token_returns_400(self, auth_client):
        response = auth_client.post(reverse('auth-logout'), {'refresh': 'not-a-valid-token'})
        assert response.status_code == 400
```

- [ ] **Step 2: Run logout tests — expect all pass**

```bash
pytest tests/authentication/test_views.py::TestLogoutView -v
```

Expected: 4 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/authentication/test_views.py
git commit -m "test: add logout endpoint tests"
```

---

### Task 9: Me endpoint tests

**Files:**
- Modify: `tests/authentication/test_views.py`

- [ ] **Step 1: Append me endpoint tests to tests/authentication/test_views.py**

```python


@pytest.mark.django_db
class TestMeView:
    def test_get_me_returns_profile(self, auth_client, staff_user):
        response = auth_client.get(reverse('auth-me'))
        assert response.status_code == 200
        assert response.data['email'] == 'staff@noorrix.com'
        assert response.data['first_name'] == 'Ali'
        assert response.data['last_name'] == 'Khan'
        assert response.data['is_staff'] is True

    def test_patch_me_updates_name(self, auth_client):
        response = auth_client.patch(reverse('auth-me'), {'first_name': 'Updated'})
        assert response.status_code == 200
        assert response.data['first_name'] == 'Updated'

    def test_patch_me_updates_email(self, auth_client):
        response = auth_client.patch(reverse('auth-me'), {'email': 'newemail@noorrix.com'})
        assert response.status_code == 200
        assert response.data['email'] == 'newemail@noorrix.com'

    def test_me_requires_auth(self, api_client):
        response = api_client.get(reverse('auth-me'))
        assert response.status_code == 401

    def test_put_not_allowed(self, auth_client, staff_user):
        response = auth_client.put(
            reverse('auth-me'),
            {'first_name': 'X', 'last_name': 'Y', 'email': 'x@noorrix.com'},
        )
        assert response.status_code == 405
```

- [ ] **Step 2: Run me tests — expect all pass**

```bash
pytest tests/authentication/test_views.py::TestMeView -v
```

Expected: 5 tests PASSED

- [ ] **Step 3: Commit**

```bash
git add tests/authentication/test_views.py
git commit -m "test: add me endpoint tests"
```

---

### Task 10: Change password endpoint tests

**Files:**
- Modify: `tests/authentication/test_views.py`

- [ ] **Step 1: Append change-password tests to tests/authentication/test_views.py**

```python


@pytest.mark.django_db
class TestChangePasswordView:
    def test_change_password_success(self, auth_client, staff_user):
        response = auth_client.post(
            reverse('auth-change-password'),
            {'old_password': 'StaffPass123!', 'new_password': 'NewSecure456!'},
        )
        assert response.status_code == 200
        assert response.data['detail'] == 'Password changed successfully.'
        staff_user.refresh_from_db()
        assert staff_user.check_password('NewSecure456!')

    def test_wrong_old_password_rejected(self, auth_client):
        response = auth_client.post(
            reverse('auth-change-password'),
            {'old_password': 'wrongpass', 'new_password': 'NewSecure456!'},
        )
        assert response.status_code == 400
        assert 'old_password' in response.data

    def test_weak_new_password_rejected(self, auth_client):
        response = auth_client.post(
            reverse('auth-change-password'),
            {'old_password': 'StaffPass123!', 'new_password': '123'},
        )
        assert response.status_code == 400

    def test_change_password_requires_auth(self, api_client):
        response = api_client.post(
            reverse('auth-change-password'),
            {'old_password': 'StaffPass123!', 'new_password': 'NewSecure456!'},
        )
        assert response.status_code == 401
```

- [ ] **Step 2: Run change-password tests — expect all pass**

```bash
pytest tests/authentication/test_views.py::TestChangePasswordView -v
```

Expected: 4 tests PASSED

- [ ] **Step 3: Run the full test suite to confirm everything passes**

```bash
pytest tests/ -v
```

Expected: All 21 tests PASSED (4 model + 4 login + 4 logout + 5 me + 4 change-password)

- [ ] **Step 4: Commit**

```bash
git add tests/authentication/test_views.py
git commit -m "test: add change-password endpoint tests"
```

---

## Done

All 5 endpoints implemented and verified:

| Endpoint | Method | Auth |
|----------|--------|------|
| `/api/v1/auth/login/` | POST | Public |
| `/api/v1/auth/token/refresh/` | POST | Public |
| `/api/v1/auth/logout/` | POST | Bearer token |
| `/api/v1/auth/me/` | GET, PATCH | Bearer token |
| `/api/v1/auth/change-password/` | POST | Bearer token |
