# Noorrix Backend — Claude Reference

## Project Overview
Django REST API backend. Auth (JWT + OTP password reset), contact form, payments (placeholder).

---

## Tech Stack
- Python / Django 6.0.5
- Django REST Framework 3.15.2
- SimpleJWT 5.3.1 — JWT auth (60min access, 7d refresh)
- drf-spectacular 0.29.0 — Swagger docs at `/api/docs/`
- django-cors-headers 4.3.1
- python-decouple 3.8 — env config
- SQLite (dev), SMTP Gmail (email)
- pytest + pytest-django

---

## Project Structure
```
noorrix_backend/         ← repo root & Django project root
├── config/              ← settings.py, urls.py, wsgi/asgi
├── apps/
│   ├── auth/            ← registration, JWT login, OTP password reset
│   ├── contact/         ← contact form + admin email notification
│   └── payments/        ← placeholder (empty)
├── tests/               ← pytest test suite
├── docs/
├── manage.py
├── requirements.txt
├── .env.example
└── CLAUDE.md            ← this file
```

---

## API Endpoints

### Auth — `/api/v1/auth/`
| Method | Path | Purpose |
|--------|------|---------|
| POST | `register/` | Register (name, email, password, confirm_password) |
| POST | `token/` | Login → access + refresh tokens + name + email |
| POST | `token/refresh/` | Refresh expired access token |
| POST | `password-reset/` | Send 6-digit OTP to email |
| POST | `password-reset/confirm/` | Confirm reset (email, otp, new_password, confirm_password) |

### Contact — `/api/contact/`
| Method | Path | Purpose |
|--------|------|---------|
| POST | `contact/` | Submit form → saved to DB + HTML email to admin |

### Docs
| Path | Purpose |
|------|---------|
| `/api/docs/` | Swagger UI |
| `/api/redoc/` | ReDoc |
| `/api/schema/` | OpenAPI JSON |

---

## Key Models

### `apps.auth.models.User`
Custom AbstractUser. Email is the login field (no username).
- `email` (unique), `name`, `created_at`, `updated_at`

### `apps.auth.models.PasswordResetOTP`
- `user` (FK → User), `otp` (6 chars), `created_at`, `is_used`
- `is_valid()` — expires after 10 minutes

### `apps.contact.models.ContactSubmission`
- `name`, `email`, `phone` (optional), `subject`, `message`, `submitted_at`, `is_read`

---

## Auth Flows

**Login:** POST `token/` → returns `access`, `refresh`, `name`, `email`

**Password Reset (OTP):**
1. POST `password-reset/` with `{email}` → 6-digit OTP emailed (10-min expiry)
2. POST `password-reset/confirm/` with `{email, otp, new_password, confirm_password}`

> Note: `views.py` response message still says "reset link" — needs fix (wrong text, OTP is correctly sent)

---

## Environment Variables (see `.env.example`)
```
SECRET_KEY, DEBUG, ALLOWED_HOSTS
EMAIL_HOST, EMAIL_PORT, EMAIL_USE_TLS
EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, DEFAULT_FROM_EMAIL
FRONTEND_URL (default: http://localhost:3000)
CORS_ALLOWED_ORIGINS
```

---

## Branches
- `main` — stable, current development
- `feature/auth` — OTP password reset (merged into main)
- `feature/contact-form` — contact form (merged into main)
- `feature/stripe-payments` — Stripe payments (in progress, not merged)

---

## Migrations
Run after any model change:
```bash
python manage.py makemigrations
python manage.py migrate
```
OTP migration: `apps/auth/migrations/0002_passwordresetotp.py` — must be applied before password reset works.

---

## Update Log
| Date | Task |
|------|------|
| 2026-06-03 | Initial CLAUDE.md created |
