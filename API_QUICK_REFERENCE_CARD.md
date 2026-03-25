# 📄 API Quick Reference Card

**Base URL:** `https://api.yourdomain.com`  
**Authentication:** `Authorization: Bearer {token}`  
**Version:** 1.0

---

## 🔐 Authentication

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Register** | `POST /api/v1/auth/register` | email, username, password | access_token, user |
| **Login** | `POST /api/v1/auth/login` | username, password | access_token, user |
| **Refresh** | `POST /api/v1/auth/refresh` | refresh_token | access_token |

---

## 👤 Users

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Get Profile** | `GET /api/v1/users/me` | - | User object |
| **Update Profile** | `PUT /api/v1/users/me` | first_name, last_name, company_name, phone | Updated user |

---

## 📦 Plans

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **List Plans** | `GET /api/v1/plans` | - | plans[], total |
| **Get Plan** | `GET /api/v1/plans/{id}` | plan_id | Plan object |

---

## 🔄 Subscriptions

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Create** | `POST /api/v1/subscriptions` | plan_id, auto_renew | subscription, message |
| **List** | `GET /api/v1/subscriptions` | status?, limit?, offset? | subscriptions[], total |
| **Get** | `GET /api/v1/subscriptions/{id}` | subscription_id | Subscription object |
| **Cancel** | `PUT /api/v1/subscriptions/{id}/cancel` | reason? | Updated subscription |

---

## 💳 Payments

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Create Payment** | `POST /api/v1/payments/create` | subscription_id, amount, currency | transaction, checkout_url |
| **List Transactions** | `GET /api/v1/payments/transactions` | status?, type?, limit? | transactions[], total |
| **Get Transaction** | `GET /api/v1/payments/transactions/{id}` | transaction_id | Transaction object |
| **Verify Payment** | `GET /api/v1/payments/verify/{order_id}` | order_id | status, amount, subscription |

---

## 🔁 Refunds

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Request** | `POST /api/v1/refunds/request` | transaction_id, refund_amount, reason | refund, message |
| **List** | `GET /api/v1/refunds` | status?, limit? | refunds[], total |
| **Get** | `GET /api/v1/refunds/{id}` | refund_id | Refund object |

---

## 📊 Analytics

| Method | Endpoint | Input | Output |
|--------|----------|-------|--------|
| **Overview** | `GET /api/v1/analytics/overview` | start_date?, end_date? | period, summary, active_subscriptions |

---

## 🔔 Webhooks

**Configure your webhook URL to receive these events:**

| Event | Trigger |
|-------|---------|
| `payment.success` | Payment completed |
| `payment.failed` | Payment failed |
| `subscription.created` | Subscription created |
| `subscription.activated` | Subscription activated |
| `subscription.canceled` | Subscription canceled |
| `subscription.expired` | Subscription expired |
| `subscription.renewed` | Subscription renewed |
| `refund.requested` | Refund requested |
| `refund.completed` | Refund completed |

**Webhook Payload:**
```json
{
  "event": "payment.success",
  "event_id": "evt_...",
  "timestamp": "2026-03-25T10:15:30Z",
  "data": {...},
  "signature": "sha256=..."
}
```

**Your Response:** `200 OK` with `{"received": true, "event_id": "evt_..."}`

---

## 📋 Status Values

### Subscription Status
- `trial` - Trial period
- `active` - Active
- `past_due` - Payment overdue
- `canceled` - Canceled
- `expired` - Expired

### Transaction Status
- `pending` - Awaiting payment
- `processing` - In progress
- `completed` - Success ✅
- `failed` - Failed ❌
- `refunded` - Refunded

### Refund Status
- `pending` - Awaiting approval
- `processing` - Processing
- `completed` - Completed
- `failed` - Failed

---

## ⚡ Quick Start Flow

```
1. POST /api/v1/auth/register        → Get token
2. GET  /api/v1/plans                → Choose plan
3. POST /api/v1/subscriptions        → Create subscription
4. POST /api/v1/payments/create      → Get checkout_url
5. Redirect user → checkout_url      → User pays
6. Receive webhook → payment.success → Subscription active
7. GET  /api/v1/payments/verify      → Confirm status
```

---

## 🔑 Required Headers

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json
```

---

## ⚠️ Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid input |
| `AUTHENTICATION_ERROR` | 401 | Invalid token |
| `AUTHORIZATION_ERROR` | 403 | No permission |
| `RESOURCE_NOT_FOUND` | 404 | Not found |
| `PAYMENT_ERROR` | 400 | Payment failed |

---

## 📐 Data Formats

- **Dates:** `2026-03-25` (ISO 8601)
- **Times:** `2026-03-25T10:00:00Z` (ISO 8601 UTC)
- **Decimals:** `5000.00` (2 decimal places)
- **Currency:** `DJF`, `USD`, `EUR` (ISO 4217)

---

## 🔢 Rate Limits

- Auth endpoints: **10/min**
- Read operations: **100/min**
- Write operations: **30/min**

---

## 📞 Support

- **Email:** integration@yourdomain.com
- **Docs:** https://docs.yourdomain.com
- **Status:** https://status.yourdomain.com

---

**Print this page for quick API reference!**
