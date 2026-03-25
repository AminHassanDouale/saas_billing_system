# 🔌 SaaS Billing System - Third-Party Integration Documentation

**Version:** 1.0  
**Last Updated:** March 25, 2026  
**Base URL:** `https://api.yourdomain.com`  
**Protocol:** HTTPS  
**Authentication:** JWT Bearer Token

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Data Models](#data-models)
5. [Integration Flow](#integration-flow)
6. [Error Handling](#error-handling)
7. [Webhooks](#webhooks)
8. [Testing](#testing)

---

## 🎯 Overview

This API allows third-party systems to integrate with our SaaS billing system, enabling:

- User management (create, update, retrieve users)
- Subscription management (plans, subscriptions, renewals)
- Payment processing (D-Money integration)
- Transaction tracking
- Webhook notifications

### System Architecture

```
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Your System     │ ←→   │  Our API         │ ←→   │  D-Money Gateway │
│  (Third Party)   │      │  (Billing System)│      │  (Payment)       │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## 🔐 Authentication

All API requests require authentication using JWT Bearer tokens.

### 1. Register/Login

**Endpoint:** `POST /api/v1/auth/register`

**Request:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Corp",
  "phone": "+253 77 12 34 56"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 5,
    "email": "user@example.com",
    "username": "username",
    "role": "user",
    "created_at": "2026-03-25T10:00:00Z"
  }
}
```

### 2. Use Token

Include token in all subsequent requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 📡 API Endpoints

### User Management

#### GET /api/v1/users/me

Get current user details.

**Input:** None (uses auth token)

**Output:**
```json
{
  "id": 5,
  "email": "user@example.com",
  "username": "username",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Corp",
  "phone": "+253 77 12 34 56",
  "role": "user",
  "status": "active",
  "is_email_verified": true,
  "created_at": "2026-03-25T10:00:00Z",
  "updated_at": "2026-03-25T10:00:00Z"
}
```

#### PUT /api/v1/users/me

Update current user.

**Input:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "company_name": "New Company",
  "phone": "+253 77 99 88 77"
}
```

**Output:** Updated user object (same structure as GET)

---

### Subscription Plans

#### GET /api/v1/plans

Get all available subscription plans.

**Input:** None

**Output:**
```json
{
  "plans": [
    {
      "id": 1,
      "name": "Basic",
      "description": "Basic plan for small teams",
      "price": 2500.00,
      "currency": "DJF",
      "interval": "monthly",
      "features": [
        "5 users",
        "10GB storage",
        "Email support"
      ],
      "max_users": 5,
      "max_storage_gb": 10,
      "trial_period_days": 7,
      "is_active": true,
      "is_featured": false
    },
    {
      "id": 2,
      "name": "Professional",
      "description": "Professional plan for growing teams",
      "price": 5000.00,
      "currency": "DJF",
      "interval": "monthly",
      "features": [
        "25 users",
        "100GB storage",
        "Priority support",
        "Advanced analytics"
      ],
      "max_users": 25,
      "max_storage_gb": 100,
      "trial_period_days": 14,
      "is_active": true,
      "is_featured": true
    }
  ],
  "total": 2
}
```

#### GET /api/v1/plans/{plan_id}

Get specific plan details.

**Input:** `plan_id` (path parameter)

**Output:** Single plan object

---

### Subscriptions

#### POST /api/v1/subscriptions

Create a new subscription for the current user.

**Input:**
```json
{
  "plan_id": 2,
  "auto_renew": true
}
```

**Output:**
```json
{
  "subscription": {
    "id": 1,
    "user_id": 5,
    "plan_id": 2,
    "plan": {
      "id": 2,
      "name": "Professional",
      "price": 5000.00,
      "currency": "DJF",
      "interval": "monthly"
    },
    "status": "trial",
    "trial_start": "2026-03-25T10:00:00Z",
    "trial_end": "2026-04-08T10:00:00Z",
    "current_period_start": "2026-03-25T10:00:00Z",
    "current_period_end": "2026-04-25T10:00:00Z",
    "auto_renew": true,
    "next_payment_date": "2026-04-08T10:00:00Z",
    "created_at": "2026-03-25T10:00:00Z"
  },
  "message": "Subscription created successfully. Payment required after trial."
}
```

#### GET /api/v1/subscriptions

Get user's subscriptions.

**Input:** None (uses auth token)

**Output:**
```json
{
  "subscriptions": [
    {
      "id": 1,
      "plan": {
        "id": 2,
        "name": "Professional",
        "price": 5000.00
      },
      "status": "active",
      "current_period_start": "2026-03-25T10:00:00Z",
      "current_period_end": "2026-04-25T10:00:00Z",
      "auto_renew": true
    }
  ],
  "total": 1
}
```

#### GET /api/v1/subscriptions/{subscription_id}

Get specific subscription details.

**Input:** `subscription_id` (path parameter)

**Output:** Single subscription object with full details

#### PUT /api/v1/subscriptions/{subscription_id}/cancel

Cancel a subscription.

**Input:**
```json
{
  "reason": "No longer needed"
}
```

**Output:**
```json
{
  "subscription": {
    "id": 1,
    "status": "canceled",
    "canceled_at": "2026-03-25T15:00:00Z",
    "ended_at": "2026-04-25T10:00:00Z"
  },
  "message": "Subscription canceled. Access until 2026-04-25."
}
```

---

### Payments

#### POST /api/v1/payments/create

Create a payment for a subscription.

**Input:**
```json
{
  "subscription_id": 1,
  "amount": 5000.00,
  "currency": "DJF",
  "redirect_url": "https://yourapp.com/payment/callback",
  "language": "en"
}
```

**Output:**
```json
{
  "transaction": {
    "id": 1,
    "transaction_id": "TXN_20260325100500ABC",
    "order_id": "ORD20260325100500XYZ",
    "amount": 5000.00,
    "currency": "DJF",
    "status": "pending",
    "title": "Professional - Monthly",
    "created_at": "2026-03-25T10:05:00Z"
  },
  "checkout_url": "https://pg.d-moneyservice.dj:38443/payment/web/paygate?prepay_id=...",
  "message": "Redirect user to checkout_url to complete payment"
}
```

**Next Steps:**
1. Redirect user to `checkout_url`
2. User completes payment on D-Money
3. User redirected back to your `redirect_url`
4. You receive webhook notification (see Webhooks section)

#### GET /api/v1/payments/transactions

Get user's payment transactions.

**Input:**
```
Query Parameters:
- status (optional): pending|completed|failed
- limit (optional): 10 (default)
- offset (optional): 0 (default)
```

**Output:**
```json
{
  "transactions": [
    {
      "id": 1,
      "transaction_id": "TXN_20260325100500ABC",
      "order_id": "ORD20260325100500XYZ",
      "subscription_id": 1,
      "type": "payment",
      "status": "completed",
      "payment_method": "dmoney",
      "amount": 5000.00,
      "currency": "DJF",
      "title": "Professional - Monthly",
      "paid_at": "2026-03-25T10:15:30Z",
      "payment_transaction_id": "DMONEY_TXN_456789",
      "created_at": "2026-03-25T10:05:00Z"
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### GET /api/v1/payments/transactions/{transaction_id}

Get specific transaction details.

**Input:** `transaction_id` (path parameter or order_id)

**Output:**
```json
{
  "transaction": {
    "id": 1,
    "transaction_id": "TXN_20260325100500ABC",
    "order_id": "ORD20260325100500XYZ",
    "prepay_id": "wx789def456ghi123",
    "user_id": 5,
    "subscription_id": 1,
    "type": "payment",
    "status": "completed",
    "payment_method": "dmoney",
    "amount": 5000.00,
    "currency": "DJF",
    "fee": 0.00,
    "net_amount": 5000.00,
    "title": "Professional - Monthly",
    "description": "Payment for Professional subscription",
    "checkout_url": "https://pg.d-moneyservice.dj/...",
    "payment_transaction_id": "DMONEY_TXN_456789",
    "paid_at": "2026-03-25T10:15:30Z",
    "webhook_received": true,
    "created_at": "2026-03-25T10:05:00Z",
    "updated_at": "2026-03-25T10:15:31Z"
  }
}
```

#### GET /api/v1/payments/verify/{order_id}

Verify payment status (call after user returns from payment).

**Input:** `order_id` (from transaction creation)

**Output:**
```json
{
  "order_id": "ORD20260325100500XYZ",
  "status": "completed",
  "amount": 5000.00,
  "currency": "DJF",
  "paid_at": "2026-03-25T10:15:30Z",
  "subscription": {
    "id": 1,
    "status": "active",
    "current_period_end": "2026-04-25T10:00:00Z"
  },
  "message": "Payment successful"
}
```

---

### Refunds

#### POST /api/v1/refunds/request

Request a refund for a transaction.

**Input:**
```json
{
  "transaction_id": 1,
  "refund_amount": 5000.00,
  "reason": "customer_request",
  "reason_details": "Service not as expected"
}
```

**Output:**
```json
{
  "refund": {
    "id": 1,
    "refund_id": "REF_20260325_ABC123",
    "transaction_id": 1,
    "status": "pending",
    "reason": "customer_request",
    "reason_details": "Service not as expected",
    "original_amount": 5000.00,
    "refund_amount": 5000.00,
    "currency": "DJF",
    "is_partial": false,
    "created_at": "2026-03-25T16:00:00Z"
  },
  "message": "Refund request submitted. Pending admin approval."
}
```

#### GET /api/v1/refunds

Get user's refund requests.

**Input:** None (uses auth token)

**Output:**
```json
{
  "refunds": [
    {
      "id": 1,
      "refund_id": "REF_20260325_ABC123",
      "transaction_id": 1,
      "status": "pending",
      "refund_amount": 5000.00,
      "created_at": "2026-03-25T16:00:00Z"
    }
  ],
  "total": 1
}
```

---

### Analytics

#### GET /api/v1/analytics/overview

Get user's billing analytics.

**Input:** 
```
Query Parameters:
- start_date (optional): 2026-01-01
- end_date (optional): 2026-03-31
```

**Output:**
```json
{
  "period": {
    "start_date": "2026-01-01",
    "end_date": "2026-03-31"
  },
  "summary": {
    "total_spent": 15000.00,
    "successful_payments": 3,
    "failed_payments": 0,
    "refunds": 1,
    "refunded_amount": 5000.00,
    "net_amount": 10000.00
  },
  "active_subscriptions": 1,
  "next_payment": {
    "date": "2026-04-25T10:00:00Z",
    "amount": 5000.00,
    "subscription": "Professional"
  }
}
```

---

## 📊 Data Models

### User Object

```typescript
{
  id: integer,
  email: string,
  username: string,
  first_name: string | null,
  last_name: string | null,
  company_name: string | null,
  phone: string | null,
  role: "admin" | "merchant" | "user",
  status: "active" | "inactive" | "suspended" | "deleted",
  is_email_verified: boolean,
  is_phone_verified: boolean,
  created_at: datetime,
  updated_at: datetime
}
```

### Subscription Plan Object

```typescript
{
  id: integer,
  name: string,
  description: string,
  price: decimal,
  currency: string,
  interval: "monthly" | "quarterly" | "yearly",
  features: string[],
  max_users: integer,
  max_storage_gb: integer,
  trial_period_days: integer,
  is_active: boolean,
  is_featured: boolean,
  created_at: datetime,
  updated_at: datetime
}
```

### Subscription Object

```typescript
{
  id: integer,
  user_id: integer,
  plan_id: integer,
  plan: SubscriptionPlan,
  status: "trial" | "active" | "past_due" | "canceled" | "expired" | "suspended",
  trial_start: datetime | null,
  trial_end: datetime | null,
  current_period_start: datetime,
  current_period_end: datetime,
  canceled_at: datetime | null,
  ended_at: datetime | null,
  auto_renew: boolean,
  next_payment_date: datetime | null,
  created_at: datetime,
  updated_at: datetime
}
```

### Transaction Object

```typescript
{
  id: integer,
  transaction_id: string,      // "TXN_20260325100500ABC"
  order_id: string,             // "ORD20260325100500XYZ"
  prepay_id: string | null,     // D-Money prepay ID
  user_id: integer,
  subscription_id: integer | null,
  type: "payment" | "refund" | "credit" | "debit",
  status: "pending" | "processing" | "completed" | "failed" | "canceled" | "refunded",
  payment_method: "dmoney" | "credit_card" | "bank_transfer" | "wallet",
  amount: decimal,
  currency: string,
  fee: decimal | null,
  net_amount: decimal,
  title: string,
  description: string | null,
  checkout_url: string | null,
  redirect_url: string | null,
  payment_transaction_id: string | null,  // D-Money transaction ID
  paid_at: datetime | null,
  failed_at: datetime | null,
  refunded_at: datetime | null,
  error_code: string | null,
  error_message: string | null,
  webhook_received: boolean,
  created_at: datetime,
  updated_at: datetime
}
```

### Refund Object

```typescript
{
  id: integer,
  refund_id: string,
  transaction_id: integer,
  user_id: integer,
  status: "pending" | "processing" | "completed" | "failed" | "canceled",
  reason: "customer_request" | "duplicate_payment" | "fraudulent" | 
          "service_not_provided" | "subscription_canceled" | "other",
  reason_details: string | null,
  original_amount: decimal,
  refund_amount: decimal,
  currency: string,
  is_partial: boolean,
  approved_at: datetime | null,
  rejected_at: datetime | null,
  completed_at: datetime | null,
  created_at: datetime,
  updated_at: datetime
}
```

---

## 🔄 Integration Flow

### Complete Payment Flow

```
1. USER SELECTS PLAN
   ↓
   POST /api/v1/subscriptions
   {plan_id: 2, auto_renew: true}
   ↓
   Response: subscription created (status: trial)

2. CREATE PAYMENT
   ↓
   POST /api/v1/payments/create
   {subscription_id: 1, amount: 5000}
   ↓
   Response: {checkout_url: "https://pg.d-moneyservice.dj/..."}

3. REDIRECT USER
   ↓
   window.location.href = checkout_url
   ↓
   User pays on D-Money website

4. USER REDIRECTED BACK
   ↓
   https://yourapp.com/payment/callback?order_id=ORD...
   ↓
   GET /api/v1/payments/verify/{order_id}
   ↓
   Response: {status: "completed", subscription: {...}}

5. WEBHOOK RECEIVED (in background)
   ↓
   POST https://yourapp.com/api/webhooks/payment
   {trade_status: "completed", merch_order_id: "ORD..."}
   ↓
   Process webhook → Update records
```

### Subscription Lifecycle

```
NEW SUBSCRIPTION
status: trial (if trial_period_days > 0)
↓
TRIAL ENDS
status: pending → waiting for payment
↓
PAYMENT SUCCESSFUL
status: active → subscription active
↓
RENEWAL (if auto_renew = true)
status: active → auto-renewed
↓
CANCELATION (optional)
status: canceled → ended_at set
↓
END OF PERIOD
status: expired → access terminated
```

---

## ⚠️ Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "email",
      "reason": "Email already exists"
    }
  },
  "request_id": "req_abc123xyz"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Input validation failed |
| `AUTHENTICATION_ERROR` | Invalid or expired token |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Resource doesn't exist |
| `DUPLICATE_RESOURCE` | Resource already exists |
| `PAYMENT_ERROR` | Payment processing failed |
| `WEBHOOK_ERROR` | Webhook processing failed |

---

## 🔔 Webhooks

### Configure Webhook URL

Set your webhook endpoint in your account settings or contact support.

### Webhook Events

| Event | Trigger |
|-------|---------|
| `payment.success` | Payment completed successfully |
| `payment.failed` | Payment failed |
| `subscription.created` | New subscription created |
| `subscription.activated` | Subscription activated (trial ended, payment successful) |
| `subscription.canceled` | Subscription canceled |
| `subscription.expired` | Subscription expired |
| `subscription.renewed` | Subscription renewed |
| `refund.requested` | Refund requested |
| `refund.completed` | Refund processed |

### Webhook Payload

```json
{
  "event": "payment.success",
  "event_id": "evt_abc123xyz",
  "timestamp": "2026-03-25T10:15:30Z",
  "data": {
    "transaction_id": "TXN_20260325100500ABC",
    "order_id": "ORD20260325100500XYZ",
    "user_id": 5,
    "subscription_id": 1,
    "amount": 5000.00,
    "currency": "DJF",
    "status": "completed",
    "payment_transaction_id": "DMONEY_TXN_456789",
    "paid_at": "2026-03-25T10:15:30Z"
  },
  "signature": "sha256=abc123..."
}
```

### Webhook Verification

Verify webhook signatures to ensure authenticity:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Webhook Response

Respond with `200 OK` to acknowledge receipt:

```json
{
  "received": true,
  "event_id": "evt_abc123xyz"
}
```

---

## 🧪 Testing

### Test Environment

```
Base URL: https://api-test.yourdomain.com
Test Credentials: Provided separately
```

### Test Cards (D-Money Sandbox)

Contact D-Money for test credentials and test wallet numbers.

### Sample Test Flow

```bash
# 1. Register test user
curl -X POST https://api-test.yourdomain.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!"
  }'

# 2. Get plans
curl -X GET https://api-test.yourdomain.com/api/v1/plans \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. Create subscription
curl -X POST https://api-test.yourdomain.com/api/v1/subscriptions \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 2,
    "auto_renew": true
  }'

# 4. Create payment
curl -X POST https://api-test.yourdomain.com/api/v1/payments/create \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subscription_id": 1,
    "amount": 5000.00,
    "currency": "DJF"
  }'

# 5. Verify payment
curl -X GET https://api-test.yourdomain.com/api/v1/payments/verify/ORD... \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📞 Support

### Contact

- **Email:** integration@yourdomain.com
- **Slack:** #api-integration
- **Documentation:** https://docs.yourdomain.com
- **Status Page:** https://status.yourdomain.com

### Rate Limits

- **Authentication endpoints:** 10 requests/minute
- **Read operations:** 100 requests/minute
- **Write operations:** 30 requests/minute

### SLA

- **Uptime:** 99.9%
- **Response Time:** < 200ms (p95)
- **Support Response:** < 4 hours (business hours)

---

## 📋 Changelog

### Version 1.0 (2026-03-25)

- Initial API release
- User management endpoints
- Subscription management
- Payment processing with D-Money
- Webhook notifications
- Refund system
- Analytics endpoints

---

## ✅ Quick Start Checklist

- [ ] Obtain API credentials (contact support)
- [ ] Set up test environment
- [ ] Implement authentication flow
- [ ] Test user registration/login
- [ ] Test subscription creation
- [ ] Test payment flow
- [ ] Configure webhook endpoint
- [ ] Test webhook reception
- [ ] Implement error handling
- [ ] Move to production environment

---

**Ready to integrate? Contact us at integration@yourdomain.com for API credentials!**
