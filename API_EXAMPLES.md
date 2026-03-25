# 📖 API Usage Examples

Complete examples for using the SaaS Billing System API.

## Table of Contents

- [Authentication](#authentication)
- [User Management](#user-management)
- [Subscription Management](#subscription-management)
- [Payment Processing](#payment-processing)
- [Webhooks](#webhooks)
- [Refunds](#refunds)
- [Analytics](#analytics)

---

## Authentication

### Register a New User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "john",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "Acme Corp"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "password": "SecurePass123!"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Refresh Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

---

## User Management

### Get Current User Profile

```bash
curl "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Update Profile

```bash
curl -X PATCH "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Smith",
    "phone": "+253-12345678"
  }'
```

### Change Password

```bash
curl -X POST "http://localhost:8000/api/v1/users/me/change-password" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "SecurePass123!",
    "new_password": "NewSecurePass123!"
  }'
```

### Get User Statistics

```bash
curl "http://localhost:8000/api/v1/users/me/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Subscription Management

### List Available Plans

```bash
curl "http://localhost:8000/api/v1/subscriptions/plans"
```

Response:
```json
[
  {
    "id": 1,
    "name": "Professional",
    "description": "For growing teams and businesses",
    "price": 5000.0,
    "currency": "DJF",
    "interval": "monthly",
    "features": "[\"50 GB Storage\", \"10 Users\", \"Priority Support\"]",
    "max_users": 10,
    "max_storage_gb": 50,
    "trial_period_days": 14,
    "is_active": true,
    "is_featured": true
  }
]
```

### Subscribe to a Plan

```bash
curl -X POST "http://localhost:8000/api/v1/subscriptions/subscribe" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "auto_renew": true
  }'
```

### Get My Subscriptions

```bash
curl "http://localhost:8000/api/v1/subscriptions/my-subscriptions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Cancel Subscription

```bash
curl -X POST "http://localhost:8000/api/v1/subscriptions/1/cancel" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "immediate": false,
    "reason": "No longer needed"
  }'
```

### Create a Plan (Admin Only)

```bash
curl -X POST "http://localhost:8000/api/v1/subscriptions/plans" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Enterprise",
    "description": "For large organizations",
    "price": 15000.0,
    "currency": "DJF",
    "interval": "monthly",
    "max_users": 999,
    "max_storage_gb": 999,
    "trial_period_days": 30
  }'
```

---

## Payment Processing

### Create a Payment

```bash
curl -X POST "http://localhost:8000/api/v1/payments/create" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "title": "Monthly Subscription Payment",
    "subscription_id": 1,
    "currency": "DJF",
    "timeout": "120m",
    "language": "en"
  }'
```

Response:
```json
{
  "success": true,
  "transaction": {
    "id": 1,
    "transaction_id": "TXN_20260324120000ABC123",
    "order_id": "ORD20260324120000XYZ789",
    "amount": 5000.0,
    "currency": "DJF",
    "status": "pending"
  },
  "checkout_url": "https://pg.d-moneyservice.dj/payment/web/paygate?...",
  "message": "Payment initiated successfully. Redirect user to checkout_url"
}
```

### Get Transaction History

```bash
curl "http://localhost:8000/api/v1/payments/transactions?page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Specific Transaction

```bash
curl "http://localhost:8000/api/v1/payments/transactions/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Transaction by Order ID

```bash
curl "http://localhost:8000/api/v1/payments/transaction/order/ORD20260324120000XYZ789" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Get Payment Statistics

```bash
curl "http://localhost:8000/api/v1/payments/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Webhooks

### D-Money Webhook Endpoint

Configure this URL in your D-Money merchant dashboard:

```
https://yourdomain.com/api/v1/webhooks/dmoney
```

Example webhook payload from D-Money:

```json
{
  "event_type": "payment.success",
  "order_id": "ORD20260324120000XYZ789",
  "transaction_id": "DMONEY_TXN_123456",
  "status": "completed",
  "amount": 5000.0,
  "currency": "DJF",
  "timestamp": "2026-03-24T12:30:00Z"
}
```

### Test Webhook Endpoint

```bash
curl "http://localhost:8000/api/v1/webhooks/dmoney/test"
```

### Retry Failed Webhook

```bash
curl -X POST "http://localhost:8000/api/v1/webhooks/dmoney/retry/evt_123" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

---

## Refunds

### Request a Refund

```bash
curl -X POST "http://localhost:8000/api/v1/refunds/request" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": 1,
    "refund_amount": 5000.0,
    "reason": "customer_request",
    "reason_details": "Service not as expected"
  }'
```

### Get My Refunds

```bash
curl "http://localhost:8000/api/v1/refunds/my-refunds" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Approve Refund (Admin Only)

```bash
curl -X POST "http://localhost:8000/api/v1/refunds/1/approve" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_notes": "Refund approved as requested"
  }'
```

### Reject Refund (Admin Only)

```bash
curl -X POST "http://localhost:8000/api/v1/refunds/1/reject" \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_notes": "Refund denied - outside refund window"
  }'
```

---

## Analytics

### Get Dashboard Summary

```bash
curl "http://localhost:8000/api/v1/analytics/dashboard" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

### Get Revenue Metrics

```bash
curl "http://localhost:8000/api/v1/analytics/revenue?start_date=2026-01-01&end_date=2026-03-31" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

### Get MRR (Monthly Recurring Revenue)

```bash
curl "http://localhost:8000/api/v1/analytics/mrr" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

### Get Churn Metrics

```bash
curl "http://localhost:8000/api/v1/analytics/churn?start_date=2026-02-01&end_date=2026-02-29" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

### Get Customer Lifetime Value (LTV)

```bash
curl "http://localhost:8000/api/v1/analytics/ltv" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

### Get Revenue Trend

```bash
curl "http://localhost:8000/api/v1/analytics/revenue-trend?days=30&group_by=day" \
  -H "Authorization: Bearer MERCHANT_ACCESS_TOKEN"
```

---

## Complete Payment Flow Example

### Step 1: User Subscribes to a Plan

```bash
# Subscribe to Professional Plan
curl -X POST "http://localhost:8000/api/v1/subscriptions/subscribe" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"plan_id": 2, "auto_renew": true}'
```

### Step 2: Create Payment for Subscription

```bash
# Create payment
curl -X POST "http://localhost:8000/api/v1/payments/create" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "title": "Professional Plan - Monthly",
    "subscription_id": 1,
    "currency": "DJF"
  }'

# Response includes checkout_url
```

### Step 3: Redirect User to D-Money

```
Redirect user's browser to the checkout_url from step 2
```

### Step 4: D-Money Sends Webhook

```
D-Money automatically sends webhook to:
POST https://yourdomain.com/api/v1/webhooks/dmoney

System automatically:
1. Updates transaction status
2. Activates subscription if payment successful
3. Sends notifications (if configured)
```

### Step 5: User Redirected Back

```
User is redirected to your redirect_url with payment status
```

---

## Error Handling

All API errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

---

## Rate Limiting

API requests are rate-limited to prevent abuse:
- Default: 60 requests per minute per user
- Configure in `.env`: `RATE_LIMIT_PER_MINUTE=60`

---

## Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** - Never expose access tokens in client-side code
3. **Refresh tokens before expiry** - Access tokens expire in 30 minutes by default
4. **Handle webhooks idempotently** - Webhooks may be delivered multiple times
5. **Validate amounts** - Always validate payment amounts on the server
6. **Log all transactions** - Keep audit logs of all payment activities
7. **Test webhooks** - Use tools like ngrok for local webhook testing

---

For more information, visit the interactive API documentation at `/docs` when running the application.
