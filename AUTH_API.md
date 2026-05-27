# Auth API

Base URL: `http://127.0.0.1:8000/api/v1/auth`

---

## Register

**POST** `/api/v1/auth/register/`

**Payload**
```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "confirm_password": "SecurePass123!"
}
```

**Success `201`**
```json
{
  "id": 1,
  "name": "John Smith",
  "email": "john@example.com"
}
```

**Error `400`**
```json
{
  "email": ["A user with this email already exists."],
  "confirm_password": ["Passwords do not match."],
  "password": ["This password is too common."],
  "name": ["This field may not be blank."]
}
```

---

## Login

**POST** `/api/v1/auth/token/`

**Payload**
```json
{
  "email": "john@example.com",
  "password": "SecurePass123!"
}
```

**Success `200`**
```json
{
  "access": "<jwt_access_token>",
  "refresh": "<jwt_refresh_token>"
}
```

**Error `401`**
```json
{
  "detail": "No active account found with the given credentials."
}
```

---

## Forgot Password

**POST** `/api/v1/auth/password-reset/`

**Payload**
```json
{
  "email": "john@example.com"
}
```

**Success `200`**
```json
{
  "detail": "If this email is registered, a reset link has been sent to john@example.com."
}
```

> Always returns `200` even if the email does not exist.

**Error `400`**
```json
{
  "email": ["Enter a valid email address."]
}
```

---

## Reset Password (Confirm)

**POST** `/api/v1/auth/password-reset/confirm/`

> User clicks the emailed link. The link contains `uid` and `token` as query params — extract them and send in the body.
>
> Link format: `http://localhost:3000/reset-password?uid=<uid>&token=<token>`

**Payload**
```json
{
  "uid": "<uid_from_link>",
  "token": "<token_from_link>",
  "new_password": "NewSecure456!",
  "confirm_password": "NewSecure456!"
}
```

**Success `200`**
```json
{
  "detail": "Password has been reset successfully."
}
```

**Error `400`**
```json
{
  "token": ["Invalid or expired token."],
  "confirm_password": ["Passwords do not match."],
  "new_password": ["This password is too common."]
}
```

---

## Refresh Token

**POST** `/api/v1/auth/token/refresh/`

**Payload**
```json
{
  "refresh": "<jwt_refresh_token>"
}
```

**Success `200`**
```json
{
  "access": "<new_jwt_access_token>"
}
```

**Error `401`**
```json
{
  "detail": "Token is invalid or expired.",
  "code": "token_not_valid"
}
```

---

## Authenticated Requests

Send the access token in the `Authorization` header on all protected endpoints:

```
Authorization: Bearer <jwt_access_token>
```

Access token expires in **60 minutes**. Use the refresh endpoint to get a new one.
