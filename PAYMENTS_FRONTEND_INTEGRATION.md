# Noorrix Motors — Payments Frontend Integration Guide

This guide explains how to integrate the Noorrix payments backend (Stripe) into the
frontend. It covers the payment flow, the API contract, and ready-to-use React /
Next.js code. The accepted methods are **Visa, Mastercard, American Express,
Apple Pay, and PayPal** — all rendered by a single Stripe **Payment Element**.
You do **not** write any per-method code; Stripe shows whatever is enabled.

---

## 1. How the flow works

```
Frontend                         Backend (Django)              Stripe
   |                                   |                          |
   |  1. POST /create-intent/  ──────► |                          |
   |     {amount, email, ...}          |  create PaymentIntent ─► |
   |                                   | ◄── client_secret        |
   | ◄── {client_secret, reference}    |                          |
   |                                   |                          |
   |  2. Mount Payment Element with client_secret                 |
   |  3. User pays (card / Apple Pay / PayPal)                    |
   |     stripe.confirmPayment() ───────────────────────────────► |
   |                                   |                          |
   |  4. Redirect to return_url        |                          |
   |                                   | ◄── webhook (truth) ──────|
   |  5. GET /payments/{reference}/ ─► | (status from webhook)    |
   | ◄── {status: "succeeded"}         |                          |
```

**Key rule:** never treat a payment as paid based on the frontend redirect alone.
The **webhook** is the source of truth — always confirm final status via
`GET /payments/{reference}/`, which reflects the webhook-verified state.

---

## 2. Prerequisites

Install the official Stripe libraries:

```bash
npm install @stripe/stripe-js @stripe/react-stripe-js
```

### Frontend environment variables (`.env.local`)

```bash
# Stripe TEST publishable key (safe to expose in the browser).
# Get it from the backend team / Stripe Dashboard, or from the create-intent response.
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key

# Backend API base URL
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

> The `pk_test_…` (publishable) key is **safe in the browser**. The secret
> `sk_test_…` key lives only on the backend — never put it in frontend code.
> The backend also returns the publishable key in the create-intent response, so
> you can use either source.

---

## 3. API reference

Base URL: `http://localhost:8000` (dev). All endpoints are public (no auth token
required), though if the user is logged in you may forward the JWT and the payment
will be linked to their account automatically.

> **Two flows are supported.** Use **one** of them:
> - **§3.0 Hosted Checkout** (`create-checkout-session/`) — redirect to Stripe's
>   own page. Simplest; this is the current frontend flow.
> - **§3.1 Embedded Payment Element** (`create-intent/`) — collect payment on your
>   own page with Stripe.js. More control, more frontend code (see §4).
>
> Both create the same `Payment` record and are confirmed the same way: poll
> `GET /payments/{reference}/` (§3.2) until `status === "succeeded"`.

### 3.0 Create a hosted Checkout Session (recommended)

Creates a Stripe-hosted checkout page and returns its `url`. Redirect the buyer
to that URL; Stripe shows whatever methods are enabled in the Dashboard (cards,
Apple Pay, PayPal).

```
POST /api/v1/payments/create-checkout-session/
Content-Type: application/json
```

**Request body**

| Field         | Type            | Required | Notes                                                        |
|---------------|-----------------|----------|--------------------------------------------------------------|
| `amount`      | string / number | ✅       | **Major units** (pounds), e.g. `"200.00"`. Min `0.50`, max `999999.99`. |
| `currency`    | string          | ❌       | ISO code, defaults to `"gbp"`.                               |
| `description` | string          | ❌       | Shown on Stripe + receipt, e.g. `"Reservation deposit — BMW 3 Series"`. |
| `success_url` | string          | ✅       | Absolute URL to return to on success. **Must be an allow-listed origin** (your frontend domain), else `400`. |
| `cancel_url`  | string          | ✅       | Absolute URL to return to if the buyer cancels. Same allow-list rule. |

> The backend appends `?ref=<reference>&session_id={CHECKOUT_SESSION_ID}` to your
> `success_url`, so the success page receives the reference in the query string.

**Success — `201 Created`**

```json
{
  "success": true,
  "url": "https://checkout.stripe.com/c/pay/cs_test_a1...",
  "reference": "d7622756-2689-4a1e-aebd-bb947cc697d6"
}
```

Store `reference`, then `window.location.href = url`.

**Errors:** `400` (validation, incl. disallowed redirect origin) and `502`
(Stripe error) — same shapes as §3.1.

**Minimal frontend usage**

```js
const res = await fetch(`${API}/api/v1/payments/create-checkout-session/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    amount: '200.00',
    description: 'Reservation deposit — BMW 3 Series',
    success_url: `${window.location.origin}/payment/complete`,
    cancel_url: `${window.location.origin}/checkout`,
  }),
});
const { url, reference } = await res.json();
sessionStorage.setItem('payment_reference', reference);
window.location.href = url; // → Stripe-hosted page
```

After the redirect back, the `/payment/complete` page polls
`GET /payments/{reference}/` (see §4.4) until `status === "succeeded"`.

### 3.1 Create a payment intent (embedded Payment Element — alternative)

```
POST /api/v1/payments/create-intent/
Content-Type: application/json
```

**Request body**

| Field         | Type            | Required | Notes                                                        |
|---------------|-----------------|----------|--------------------------------------------------------------|
| `amount`      | string / number | ✅       | In **major units** (e.g. `250.00` = £250.00). Min `0.50`, max `999999.99`. |
| `currency`    | string          | ❌       | ISO code, e.g. `"gbp"`. Defaults to `gbp`.                   |
| `description` | string          | ❌       | Shown on the Stripe receipt / dashboard.                     |
| `email`       | string          | ❌       | Customer email for the Stripe receipt.                       |

> ⚠️ **Amount is in pounds, not pence.** Send `250.00` for £250. The backend
> converts to pence for Stripe.

**Success — `201 Created`**

```json
{
  "success": true,
  "client_secret": "pi_3Tc..._secret_Ikj...",
  "publishable_key": "pk_test_...",
  "reference": "d7622756-2689-4a1e-aebd-bb947cc697d6"
}
```

- `client_secret` → feed to the Payment Element.
- `reference` → **store this**; use it to poll payment status later.

**Validation error — `400 Bad Request`**

```json
{ "success": false, "errors": { "amount": ["Amount must be at least 0.50."] } }
```

**Stripe/provider error — `502 Bad Gateway`**

```json
{ "success": false, "error": "Your card was declined." }
```

**curl example**

```bash
curl -X POST http://localhost:8000/api/v1/payments/create-intent/ \
  -H "Content-Type: application/json" \
  -d '{"amount":"250.00","currency":"gbp","email":"buyer@example.com","description":"Vehicle deposit"}'
```

### 3.2 Get payment status

```
GET /api/v1/payments/{reference}/
```

Use the `reference` from step 3.1. Reflects the **webhook-verified** status.

**Response — `200 OK`**

```json
{
  "reference": "d7622756-2689-4a1e-aebd-bb947cc697d6",
  "amount": "250.00",
  "currency": "gbp",
  "status": "succeeded",
  "description": "Vehicle deposit",
  "customer_email": "buyer@example.com",
  "payment_method": "card",
  "created_at": "2026-05-29T20:15:00Z"
}
```

**`status` values:** `pending` → `processing` → `succeeded` | `failed` |
`canceled` | `refunded`. Treat **`succeeded`** as paid.

---

## 4. React / Next.js integration

### 4.1 Initialise Stripe (module-level, once)

```js
// lib/stripe.js
import { loadStripe } from '@stripe/stripe-js';

export const stripePromise = loadStripe(
  process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
);
```

### 4.2 Checkout page — create intent, then mount Element

```jsx
// components/Checkout.jsx
import { useEffect, useState } from 'react';
import { Elements } from '@stripe/react-stripe-js';
import { stripePromise } from '../lib/stripe';
import CheckoutForm from './CheckoutForm';

const API = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function Checkout({ amount, email, description }) {
  const [clientSecret, setClientSecret] = useState(null);
  const [reference, setReference] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/v1/payments/create-intent/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, currency: 'gbp', email, description }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (!data.success) throw new Error(JSON.stringify(data.errors || data.error));
        setClientSecret(data.client_secret);
        setReference(data.reference);
        // Persist reference so the return page can check status
        sessionStorage.setItem('payment_reference', data.reference);
      })
      .catch((e) => setError(e.message));
  }, [amount, email, description]);

  if (error) return <p>Could not start payment: {error}</p>;
  if (!clientSecret) return <p>Loading payment…</p>;

  // appearance is optional — theme the Element to match the site
  const options = { clientSecret, appearance: { theme: 'stripe' } };

  return (
    <Elements stripe={stripePromise} options={options}>
      <CheckoutForm reference={reference} />
    </Elements>
  );
}
```

### 4.3 The payment form (renders cards + Apple Pay + PayPal automatically)

```jsx
// components/CheckoutForm.jsx
import { useState } from 'react';
import { PaymentElement, useStripe, useElements } from '@stripe/react-stripe-js';

export default function CheckoutForm({ reference }) {
  const stripe = useStripe();
  const elements = useElements();
  const [message, setMessage] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!stripe || !elements) return;
    setLoading(true);

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        // Stripe redirects here after card auth / PayPal / Apple Pay
        return_url: `${window.location.origin}/payment/complete`,
      },
    });

    // Only reached if there's an immediate error (e.g. invalid card).
    // On success the user is redirected to return_url.
    if (error) setMessage(error.message);
    setLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* This single component shows Visa/MC/Amex, Apple Pay, and PayPal */}
      <PaymentElement />
      <button disabled={!stripe || loading} style={{ marginTop: 16 }}>
        {loading ? 'Processing…' : 'Pay now'}
      </button>
      {message && <div role="alert">{message}</div>}
    </form>
  );
}
```

### 4.4 The return / confirmation page

After payment, Stripe redirects to `return_url` with query params
`payment_intent` and `redirect_status`. Confirm the **real** status from your
backend (not just `redirect_status`):

```jsx
// pages/payment/complete.jsx  (or app/payment/complete/page.jsx)
import { useEffect, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_BASE_URL;

export default function PaymentComplete() {
  const [status, setStatus] = useState('checking');

  useEffect(() => {
    const reference = sessionStorage.getItem('payment_reference');
    if (!reference) return setStatus('unknown');

    // Poll because the webhook may land a moment after the redirect
    let tries = 0;
    const check = () => {
      fetch(`${API}/api/v1/payments/${reference}/`)
        .then((r) => r.json())
        .then((p) => {
          if (p.status === 'succeeded') return setStatus('succeeded');
          if (['failed', 'canceled'].includes(p.status)) return setStatus(p.status);
          if (tries++ < 5) setTimeout(check, 1500); // retry up to ~7.5s
          else setStatus('pending');
        });
    };
    check();
  }, []);

  if (status === 'succeeded') return <h1>✅ Payment successful</h1>;
  if (status === 'pending') return <h1>⏳ Payment is processing…</h1>;
  if (status === 'checking') return <h1>Confirming payment…</h1>;
  return <h1>❌ Payment {status}</h1>;
}
```

---

## 5. Vanilla JS (no React)

The API contract is framework-agnostic. Core calls:

```js
// 1. Create intent
const res = await fetch('http://localhost:8000/api/v1/payments/create-intent/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ amount: '250.00', currency: 'gbp' }),
});
const { client_secret, reference } = await res.json();

// 2. Mount the Payment Element (Stripe.js loaded via <script src="https://js.stripe.com/v3/">)
const stripe = Stripe('pk_test_...');
const elements = stripe.elements({ clientSecret: client_secret });
elements.create('payment').mount('#payment-element');

// 3. On submit
const { error } = await stripe.confirmPayment({
  elements,
  confirmParams: { return_url: 'http://localhost:3000/payment/complete' },
});
```

---

## 6. Testing

### Test cards (test mode only)

| Scenario              | Card number           | Exp / CVC / ZIP        |
|-----------------------|-----------------------|------------------------|
| Successful payment    | `4242 4242 4242 4242` | any future date / any  |
| Requires 3D Secure    | `4000 0027 6000 3184` | any future date / any  |
| Declined              | `4000 0000 0000 0002` | any future date / any  |

- **PayPal** in test mode opens a Stripe-hosted sandbox — just approve it.
- **Apple Pay** only appears in **Safari on an Apple device over HTTPS** with the
  domain registered in Stripe. It will **not** show on `http://localhost`. Test it
  via the production HTTPS domain (or an ngrok HTTPS URL registered in Stripe).

---

## 7. Important notes

- **CORS:** the backend already allows the frontend origin (`http://localhost:3000`).
  In dev (`DEBUG=True`) all origins are allowed; in production set
  `CORS_ALLOWED_ORIGINS` on the backend.
- **Amounts are in major units** (£, not pence). `250.00` = £250.00.
- **Status comes from the webhook**, not the browser. Always confirm with
  `GET /payments/{reference}/` before showing "paid".
- **Currency** defaults to `gbp`. Pass `currency` only if you need another.
- **Don't hardcode the amount client-side for real orders** — the backend will be
  updated to derive the price from a vehicle/order record. For now the frontend
  sends the amount, but treat that as temporary.

---

## 8. Quick reference

| Action          | Method & path                          |
|-----------------|----------------------------------------|
| Start a payment | `POST /api/v1/payments/create-intent/` |
| Check status    | `GET  /api/v1/payments/{reference}/`   |

Questions about the backend contract → ask the backend team.
