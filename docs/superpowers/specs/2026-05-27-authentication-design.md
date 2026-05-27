# Authentication Feature Design
**Date:** 2026-05-27
**Status:** Approved

---

## Overview

JWT-based authentication for Noorrix Motors backend. Only `is_staff` or `is_superuser` accounts can obtain tokens. Public registration is not supported.

---

## Project Structure

```
noorrix_backend/
├── apps/
│   └── authentication/
│       ├── __init__.py
│       ├── models.py        — StaffUser custom model
│       ├── serializers.py   — login, profile, change-password serializers
│       ├── views.py         — all auth views
│       ├── urls.py          — 5 URL patterns
│       └── admin.py         — StaffUser registered in Django admin
├── config/
│   ├── settings.py          — updated with auth config + env vars
│   └── urls.py              — include apps.authentication.urls
├── .env                     — SECRET_KEY, DEBUG, ALLOWED_HOSTS
├── requirements.txt
└── manage.py
```

---

## Dependencies

```
Django
djangorestframework
djangorestframework-simplejwt
python-decouple
```

---

## Settings

### Environment Variables (`.env`)
```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

### INSTALLED_APPS additions
```python
'rest_framework',
'rest_framework_simplejwt',
'rest_framework_simplejwt.token_blacklist',
'apps.authentication',
```

### AUTH_USER_MODEL
```python
AUTH_USER_MODEL = 'authentication.StaffUser'
```

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
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

## User Model

`StaffUser` extends `AbstractUser`. `username` is removed. `email` is the login field.

| Field | Type | Notes |
|-------|------|-------|
| email | EmailField | unique, `USERNAME_FIELD` |
| first_name | CharField | required |
| last_name | CharField | required |
| is_staff | Boolean | inherited from AbstractUser |
| is_superuser | Boolean | inherited from AbstractUser |
| is_active | Boolean | inherited from AbstractUser |
| created_at | DateTimeField | auto_now_add |
| updated_at | DateTimeField | auto_now |

`REQUIRED_FIELDS = ['first_name', 'last_name']` — used by `createsuperuser`.

---

## Endpoints

### POST `/api/v1/auth/login/`
- No auth required
- Request: `email`, `password`
- Rejects non-staff/non-superuser with `403`
- Response: `access`, `refresh`, `user { id, email, full_name, is_staff, is_superuser }`
  - `full_name` is a computed field: `first_name + ' ' + last_name`
- Implementation: override `TokenObtainPairSerializer` to add staff check + user data

### POST `/api/v1/auth/token/refresh/`
- No auth required
- Request: `refresh`
- Response: `access`, `refresh` (rotated)
- Implementation: simplejwt `TokenRefreshView` used directly, no customization

### POST `/api/v1/auth/logout/`
- Auth required
- Request: `refresh`
- Blacklists the refresh token
- Response: `{ "detail": "Logged out successfully." }`

### GET `/api/v1/auth/me/`
- Auth required
- Response: `id`, `email`, `first_name`, `last_name`, `is_staff`, `is_superuser`

### PATCH `/api/v1/auth/me/`
- Auth required
- Request: any of `first_name`, `last_name`, `email`
- Response: updated user profile

### POST `/api/v1/auth/change-password/`
- Auth required
- Request: `old_password`, `new_password`
- Validates `old_password` against current password
- Sets new password and returns `{ "detail": "Password changed successfully." }`

---

## Access Rules

| Endpoint | Public | Staff | Admin |
|----------|--------|-------|-------|
| login | yes | yes | yes |
| token/refresh | yes | yes | yes |
| logout | — | yes | yes |
| me (GET/PATCH) | — | yes | yes |
| change-password | — | yes | yes |

---

## Error Handling

- Invalid credentials or non-staff user on login: `401` with DRF default error format
- Missing/expired token on protected endpoints: `401`
- Validation errors (e.g. wrong old_password): `400` with field-level errors
- All errors use DRF's default JSON error format

---

## Design Decisions

- **Email login over username:** Staff system — employees remember email, not usernames. Simpler and more professional.
- **AbstractUser over AbstractBaseUser:** Less boilerplate, `createsuperuser` works out of the box, full Django admin compat.
- **apps.authentication import style:** Explicit namespacing, no sys.path manipulation needed.
- **Refresh token rotation:** Every refresh issues a new refresh token and blacklists the old one — prevents token reuse after logout.
