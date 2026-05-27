# Authentication Feature Design
**Date:** 2026-05-28
**Status:** Approved

---

## Overview

JWT-based authentication for the Noorrix backend. Supports public registration, email/password login via simplejwt, and an email-based password reset flow. All business logic lives in serializers (thin views).

---

## Project Structure

```
apps/
└── auth/
    ├── apps.py          — AppConfig: name='apps.auth', label='user_auth'
    ├── models.py        — User custom model
    ├── serializers.py   — RegisterSerializer, PasswordResetSerializer, PasswordResetConfirmSerializer
    ├── views.py         — thin views, HTTP in/out only
    ├── urls.py          — 5 URL patterns
    └── migrations/
config/
    ├── settings.py      — updated with auth config, DRF, simplejwt, email, env vars
    └── urls.py          — include apps.auth.urls under api/v1/auth/
.env                     — SECRET_KEY, DEBUG, ALLOWED_HOSTS, EMAIL_*, FRONTEND_URL
requirements.txt
```

---

## Dependencies

```
Django==6.0.5
djangorestframework
djangorestframework-simplejwt
rest_framework_simplejwt.token_blacklist
python-decouple
```

---

## Environment Variables (.env)

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@noorrix.com
FRONTEND_URL=http://localhost:3000
```

---

## Settings

### INSTALLED_APPS additions
```python
'rest_framework',
'rest_framework_simplejwt',
'rest_framework_simplejwt.token_blacklist',
'apps.auth',
```

### AUTH_USER_MODEL
```python
AUTH_USER_MODEL = 'user_auth.User'
```

> The app directory is `apps/auth/` but the Django app label is `user_auth` (set in AppConfig) to avoid conflicting with `django.contrib.auth` which also uses label `auth`.

### REST_FRAMEWORK
```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### SIMPLE_JWT
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': False,
}
```

### Email
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')
FRONTEND_URL = config('FRONTEND_URL')
```

---

## User Model

`User` extends `AbstractUser`. `username` field is removed. `email` is the login field.

| Field | Type | Notes |
|---|---|---|
| email | EmailField | unique, `USERNAME_FIELD` |
| name | CharField(255) | full name |
| is_active | Boolean | inherited from AbstractUser |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

`REQUIRED_FIELDS = ['name']` — used by `createsuperuser`.

---

## Endpoints

### POST `/api/v1/auth/register/`
- Permission: `AllowAny`
- Request: `name`, `email`, `password`, `confirm_password`
- Logic (`RegisterSerializer`):
  - Validate `confirm_password == password`
  - Validate email uniqueness (DRF unique validator)
  - `create()` calls `User.objects.create_user(email, password, name=name)`
- Response `201`: `{ id, name, email }`
- Response `400`: field-level errors

### POST `/api/v1/auth/token/`
- Permission: `AllowAny`
- Uses simplejwt `TokenObtainPairView` directly — no customization needed
- simplejwt reads `USER_ID_FIELD` and `AUTH_TOKEN_CLASSES` from SIMPLE_JWT config
- The custom User model sets `USERNAME_FIELD = 'email'`; simplejwt picks this up automatically
- Request: `email`, `password`
- Response `200`: `{ access, refresh }`
- Response `401`: `{ detail: "No active account found with the given credentials." }`

### POST `/api/v1/auth/password-reset/`
- Permission: `AllowAny`
- Request: `email`
- Logic (`PasswordResetSerializer.save()`):
  - Look up user by email
  - If user exists: generate `uid = urlsafe_base64_encode(force_bytes(user.pk))`, `token` via `PasswordResetTokenGenerator`
  - Send email with link: `{FRONTEND_URL}/reset-password?uid={uid}&token={token}`
  - If user does not exist: do nothing (prevents user enumeration)
- Response `200`: `{ detail: "Password reset link sent to {email}." }` — always, regardless of whether email exists

### POST `/api/v1/auth/password-reset/confirm/`
- Permission: `AllowAny`
- Request: `uid`, `token`, `new_password`, `confirm_password`
- Logic (`PasswordResetConfirmSerializer`):
  - `validate()`: decode uid → get user, call `PasswordResetTokenGenerator().check_token(user, token)`
  - Validate `confirm_password == new_password`
  - Run `validate_password(new_password)` against Django's AUTH_PASSWORD_VALIDATORS
  - `save()`: `user.set_password(new_password)`, `user.save()` — token is invalidated automatically (token is time+password-hash based)
- Response `200`: `{ detail: "Password has been reset successfully." }`
- Response `400`: `{ token: ["Invalid or expired token."] }`

### POST `/api/v1/auth/token/refresh/`
- Permission: `AllowAny`
- Uses simplejwt `TokenRefreshView` directly — no customization
- Request: `refresh`
- Response `200`: `{ access }`

---

## Access Rules

| Endpoint | Auth required |
|---|---|
| register | No |
| token (login) | No |
| password-reset | No |
| password-reset/confirm | No |
| token/refresh | No |

All endpoints in this module are public. Protected endpoints will be added in future apps.

---

## Error Handling

- Validation errors: `400` with DRF field-level error format
- Invalid credentials on login: `401` (simplejwt default)
- Invalid/expired reset token: `400` with `{ token: ["Invalid or expired token."] }`
- Password reset email not found: `200` (silent — no enumeration)

---

## Design Decisions

- **Single `name` field over `first_name`/`last_name`:** API contract uses `name` throughout; no need for splitting logic.
- **`AbstractUser` over `AbstractBaseUser`:** Less boilerplate, `createsuperuser` and Django admin work out of the box.
- **`label = 'user_auth'` in AppConfig:** Avoids Django label conflict with `django.contrib.auth`. The directory stays `apps/auth/`.
- **Django's `PasswordResetTokenGenerator`:** Battle-tested, single-use (invalidated after password change), time-limited (default 3 days via `PASSWORD_RESET_TIMEOUT`).
- **Always-200 on password-reset:** Prevents user enumeration attacks.
- **Thin views:** Views only handle HTTP in/out. All validation and persistence is in serializers.
