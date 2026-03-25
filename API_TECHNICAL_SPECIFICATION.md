# 📋 API Technical Specification - Input/Output Reference

**Version:** 1.0  
**For:** Third-Party Integration  
**Format:** Complete Input/Output Tables for All Endpoints

---

## 🎯 Quick Reference

This document provides a **complete technical specification** of all API methods, showing:
- ✅ **Exact inputs required** for each endpoint
- ✅ **Exact outputs returned** from each endpoint
- ✅ **Data types and validation rules**
- ✅ **Example requests and responses**

---

## 📑 Table of Contents

1. [Authentication Methods](#authentication-methods)
2. [User Management Methods](#user-management-methods)
3. [Subscription Plan Methods](#subscription-plan-methods)
4. [Subscription Management Methods](#subscription-management-methods)
5. [Payment Processing Methods](#payment-processing-methods)
6. [Refund Methods](#refund-methods)
7. [Analytics Methods](#analytics-methods)
8. [Webhook Methods](#webhook-methods)

---

## 🔐 Authentication Methods

### 1. POST /api/v1/auth/register

Create new user account.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| email | string | ✅ Yes | Valid email format, unique | "user@example.com" |
| username | string | ✅ Yes | 3-50 chars, alphanumeric + underscore, unique | "john_doe" |
| password | string | ✅ Yes | Min 8 chars, 1 uppercase, 1 number, 1 special | "SecurePass123!" |
| first_name | string | ⭕ No | Max 100 chars | "John" |
| last_name | string | ⭕ No | Max 100 chars | "Doe" |
| company_name | string | ⭕ No | Max 255 chars | "Acme Corp" |
| phone | string | ⭕ No | Valid phone format | "+253 77 12 34 56" |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| access_token | string | JWT access token (expires in 1 hour) |
| refresh_token | string | JWT refresh token (expires in 7 days) |
| token_type | string | Always "bearer" |
| expires_in | integer | Token expiration in seconds |
| user | object | User object (see User Object structure) |

#### Example Request

```json
{
  "email": "john@example.com",
  "username": "john_doe",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "company_name": "Acme Corp",
  "phone": "+253 77 12 34 56"
}
```

#### Example Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzExMzY0MTAwfQ...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1IiwiZXhwIjoxNzExOTY0MTAwfQ...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 5,
    "email": "john@example.com",
    "username": "john_doe",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "Acme Corp",
    "phone": "+253 77 12 34 56",
    "role": "user",
    "status": "active",
    "is_email_verified": false,
    "is_phone_verified": false,
    "created_at": "2026-03-25T10:00:00Z",
    "updated_at": "2026-03-25T10:00:00Z"
  }
}
```

---

### 2. POST /api/v1/auth/login

Authenticate existing user.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| username | string | ✅ Yes | Email or username | "john_doe" or "john@example.com" |
| password | string | ✅ Yes | User's password | "SecurePass123!" |

#### Output Parameters

Same as register endpoint.

---

### 3. POST /api/v1/auth/refresh

Refresh access token using refresh token.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| refresh_token | string | ✅ Yes | Valid refresh token | "eyJhbGciOiJIUzI1..." |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| access_token | string | New JWT access token |
| expires_in | integer | Token expiration in seconds |

---

## 👤 User Management Methods

### 1. GET /api/v1/users/me

Get current user details.

#### Input Parameters

None (uses Authorization header token)

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | User ID |
| email | string | User email |
| username | string | Username |
| first_name | string\|null | First name |
| last_name | string\|null | Last name |
| company_name | string\|null | Company name |
| phone | string\|null | Phone number |
| role | enum | "admin", "merchant", or "user" |
| status | enum | "active", "inactive", "suspended", "deleted" |
| is_email_verified | boolean | Email verification status |
| is_phone_verified | boolean | Phone verification status |
| created_at | datetime | Account creation timestamp |
| updated_at | datetime | Last update timestamp |

---

### 2. PUT /api/v1/users/me

Update current user details.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| first_name | string | ⭕ No | Max 100 chars | "Jane" |
| last_name | string | ⭕ No | Max 100 chars | "Smith" |
| company_name | string | ⭕ No | Max 255 chars | "New Company" |
| phone | string | ⭕ No | Valid phone format | "+253 77 99 88 77" |

#### Output Parameters

Updated user object (same structure as GET /api/v1/users/me)

---

## 📦 Subscription Plan Methods

### 1. GET /api/v1/plans

Get all available subscription plans.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| is_active | boolean | ⭕ No | Filter by active status | true |
| interval | enum | ⭕ No | "monthly", "quarterly", "yearly" | "monthly" |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| plans | array | Array of plan objects |
| total | integer | Total number of plans |

#### Plan Object Structure

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Plan ID |
| name | string | Plan name |
| description | string | Plan description |
| price | decimal | Price amount |
| currency | string | Currency code (ISO 4217) |
| interval | enum | "monthly", "quarterly", "yearly" |
| features | array | List of feature strings |
| max_users | integer | Maximum users allowed |
| max_storage_gb | integer | Maximum storage in GB |
| trial_period_days | integer | Trial period in days |
| is_active | boolean | Plan availability status |
| is_featured | boolean | Featured plan flag |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

---

### 2. GET /api/v1/plans/{plan_id}

Get specific plan details.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| plan_id | integer | ✅ Yes | Valid plan ID (path parameter) | 2 |

#### Output Parameters

Single plan object (same structure as above)

---

## 🔄 Subscription Management Methods

### 1. POST /api/v1/subscriptions

Create new subscription.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| plan_id | integer | ✅ Yes | Valid, active plan ID | 2 |
| auto_renew | boolean | ⭕ No | Auto-renewal flag (default: true) | true |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| subscription | object | Created subscription object |
| message | string | Success message |

#### Subscription Object Structure

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Subscription ID |
| user_id | integer | User ID |
| plan_id | integer | Plan ID |
| plan | object | Nested plan object |
| status | enum | "trial", "active", "past_due", "canceled", "expired", "suspended" |
| trial_start | datetime\|null | Trial start timestamp |
| trial_end | datetime\|null | Trial end timestamp |
| current_period_start | datetime | Current billing period start |
| current_period_end | datetime | Current billing period end |
| canceled_at | datetime\|null | Cancellation timestamp |
| ended_at | datetime\|null | End timestamp |
| auto_renew | boolean | Auto-renewal status |
| payment_retry_count | integer | Failed payment retry count |
| next_payment_date | datetime\|null | Next payment due date |
| metadata | object\|null | Custom metadata |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

---

### 2. GET /api/v1/subscriptions

Get user's subscriptions.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| status | enum | ⭕ No | Filter by status (query param) | "active" |
| limit | integer | ⭕ No | Results per page (default: 10) | 10 |
| offset | integer | ⭕ No | Pagination offset (default: 0) | 0 |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| subscriptions | array | Array of subscription objects |
| total | integer | Total subscriptions count |
| limit | integer | Results per page |
| offset | integer | Current offset |

---

### 3. GET /api/v1/subscriptions/{subscription_id}

Get specific subscription details.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| subscription_id | integer | ✅ Yes | Valid subscription ID (path parameter) | 1 |

#### Output Parameters

Single subscription object (same structure as above)

---

### 4. PUT /api/v1/subscriptions/{subscription_id}/cancel

Cancel subscription.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| subscription_id | integer | ✅ Yes | Valid subscription ID (path parameter) | 1 |
| reason | string | ⭕ No | Cancellation reason | "No longer needed" |
| cancel_immediately | boolean | ⭕ No | Cancel now vs end of period (default: false) | false |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| subscription | object | Updated subscription object |
| message | string | Cancellation confirmation message |

---

## 💳 Payment Processing Methods

### 1. POST /api/v1/payments/create

Create payment transaction.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| subscription_id | integer | ✅ Yes | Valid subscription ID | 1 |
| amount | decimal | ✅ Yes | Positive amount | 5000.00 |
| currency | string | ⭕ No | ISO 4217 code (default: "DJF") | "DJF" |
| redirect_url | string | ⭕ No | Custom redirect URL | "https://yourapp.com/callback" |
| language | enum | ⭕ No | "en" or "fr" (default: "en") | "en" |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| transaction | object | Created transaction object |
| checkout_url | string | D-Money payment page URL |
| message | string | Instruction message |

#### Transaction Object Structure

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Transaction ID |
| transaction_id | string | Unique transaction ID (TXN_...) |
| order_id | string | Order ID sent to payment gateway (ORD...) |
| prepay_id | string\|null | Payment gateway prepay ID |
| user_id | integer | User ID |
| subscription_id | integer\|null | Associated subscription ID |
| type | enum | "payment", "refund", "credit", "debit" |
| status | enum | "pending", "processing", "completed", "failed", "canceled", "refunded" |
| payment_method | enum | "dmoney", "credit_card", "bank_transfer", "wallet" |
| amount | decimal | Transaction amount |
| currency | string | Currency code |
| fee | decimal\|null | Transaction fee |
| net_amount | decimal | Net amount after fees |
| title | string | Transaction title |
| description | string\|null | Transaction description |
| checkout_url | string\|null | Payment page URL |
| redirect_url | string\|null | User redirect URL after payment |
| payment_transaction_id | string\|null | Gateway transaction ID |
| paid_at | datetime\|null | Payment completion timestamp |
| failed_at | datetime\|null | Payment failure timestamp |
| refunded_at | datetime\|null | Refund timestamp |
| error_code | string\|null | Error code if failed |
| error_message | string\|null | Error message if failed |
| webhook_received | boolean | Webhook receipt status |
| webhook_data | object\|null | Webhook payload |
| metadata | object\|null | Custom metadata |
| raw_response | object\|null | Gateway API response |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

---

### 2. GET /api/v1/payments/transactions

Get user's transactions.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| status | enum | ⭕ No | Filter by status (query param) | "completed" |
| type | enum | ⭕ No | Filter by type (query param) | "payment" |
| subscription_id | integer | ⭕ No | Filter by subscription | 1 |
| start_date | date | ⭕ No | Filter from date | "2026-01-01" |
| end_date | date | ⭕ No | Filter to date | "2026-03-31" |
| limit | integer | ⭕ No | Results per page (default: 10) | 10 |
| offset | integer | ⭕ No | Pagination offset (default: 0) | 0 |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| transactions | array | Array of transaction objects |
| total | integer | Total transactions count |
| limit | integer | Results per page |
| offset | integer | Current offset |

---

### 3. GET /api/v1/payments/transactions/{transaction_id}

Get specific transaction details.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| transaction_id | string | ✅ Yes | Valid transaction_id or order_id (path param) | "TXN_..." or "ORD..." |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| transaction | object | Complete transaction object |

---

### 4. GET /api/v1/payments/verify/{order_id}

Verify payment status (use after user returns from payment).

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| order_id | string | ✅ Yes | Valid order ID (path parameter) | "ORD20260325100500XYZ" |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| order_id | string | Order ID |
| status | enum | Payment status |
| amount | decimal | Payment amount |
| currency | string | Currency code |
| paid_at | datetime\|null | Payment timestamp |
| subscription | object\|null | Updated subscription object |
| message | string | Status message |

---

## 🔁 Refund Methods

### 1. POST /api/v1/refunds/request

Request refund for a transaction.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| transaction_id | integer | ✅ Yes | Valid completed transaction ID | 1 |
| refund_amount | decimal | ✅ Yes | Positive amount <= original | 5000.00 |
| reason | enum | ✅ Yes | See reason codes below | "customer_request" |
| reason_details | string | ⭕ No | Additional details | "Service not as expected" |

#### Reason Codes

- `customer_request` - Customer requested refund
- `duplicate_payment` - Duplicate payment made
- `fraudulent` - Fraudulent transaction
- `service_not_provided` - Service not delivered
- `subscription_canceled` - Subscription canceled
- `other` - Other reason

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| refund | object | Created refund object |
| message | string | Confirmation message |

#### Refund Object Structure

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Refund ID |
| refund_id | string | Unique refund ID (REF_...) |
| transaction_id | integer | Original transaction ID |
| user_id | integer | User ID |
| processed_by | integer\|null | Admin user ID who processed |
| status | enum | "pending", "processing", "completed", "failed", "canceled" |
| reason | enum | Refund reason code |
| reason_details | string\|null | Additional reason details |
| original_amount | decimal | Original transaction amount |
| refund_amount | decimal | Refund amount |
| currency | string | Currency code |
| is_partial | boolean | Partial refund flag |
| approved_at | datetime\|null | Approval timestamp |
| rejected_at | datetime\|null | Rejection timestamp |
| completed_at | datetime\|null | Completion timestamp |
| admin_notes | string\|null | Admin notes |
| dmoney_refund_id | string\|null | Gateway refund ID |
| dmoney_response | object\|null | Gateway response |
| error_code | string\|null | Error code if failed |
| error_message | string\|null | Error message if failed |
| retry_count | integer | Retry attempts count |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Update timestamp |

---

### 2. GET /api/v1/refunds

Get user's refund requests.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| status | enum | ⭕ No | Filter by status (query param) | "pending" |
| limit | integer | ⭕ No | Results per page (default: 10) | 10 |
| offset | integer | ⭕ No | Pagination offset (default: 0) | 0 |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| refunds | array | Array of refund objects |
| total | integer | Total refunds count |
| limit | integer | Results per page |
| offset | integer | Current offset |

---

### 3. GET /api/v1/refunds/{refund_id}

Get specific refund details.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| refund_id | string | ✅ Yes | Valid refund ID (path parameter) | "REF_20260325_ABC123" |

#### Output Parameters

Single refund object (same structure as above)

---

## 📊 Analytics Methods

### 1. GET /api/v1/analytics/overview

Get billing analytics overview.

#### Input Parameters

| Parameter | Type | Required | Validation | Example |
|-----------|------|----------|------------|---------|
| start_date | date | ⭕ No | ISO date format (query param) | "2026-01-01" |
| end_date | date | ⭕ No | ISO date format (query param) | "2026-03-31" |

#### Output Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| period | object | Query period details |
| summary | object | Financial summary |
| active_subscriptions | integer | Active subscriptions count |
| next_payment | object\|null | Next payment details |

#### Summary Object Structure

| Field | Type | Description |
|-------|------|-------------|
| total_spent | decimal | Total amount spent |
| successful_payments | integer | Successful payment count |
| failed_payments | integer | Failed payment count |
| refunds | integer | Refund count |
| refunded_amount | decimal | Total refunded amount |
| net_amount | decimal | Net amount (spent - refunds) |

---

## 🔔 Webhook Methods

### Webhook Event Structure

All webhooks sent to your configured endpoint follow this structure:

#### Webhook Payload

| Field | Type | Description |
|-------|------|-------------|
| event | enum | Event type (see event types below) |
| event_id | string | Unique event ID |
| timestamp | datetime | Event timestamp (ISO 8601) |
| data | object | Event-specific data |
| signature | string | HMAC-SHA256 signature |

#### Event Types

| Event | Description | Data Object |
|-------|-------------|-------------|
| `payment.success` | Payment completed | Transaction object |
| `payment.failed` | Payment failed | Transaction object |
| `subscription.created` | Subscription created | Subscription object |
| `subscription.activated` | Subscription activated | Subscription object |
| `subscription.canceled` | Subscription canceled | Subscription object |
| `subscription.expired` | Subscription expired | Subscription object |
| `subscription.renewed` | Subscription renewed | Subscription object |
| `refund.requested` | Refund requested | Refund object |
| `refund.completed` | Refund processed | Refund object |

#### Webhook Response (Your System)

Your webhook endpoint should respond with:

```json
{
  "received": true,
  "event_id": "evt_abc123xyz"
}
```

Status Code: **200 OK**

---

## 📐 Data Types Reference

### Enumerations

#### User Role
- `admin` - System administrator
- `merchant` - Merchant account
- `user` - Regular user

#### User Status
- `active` - Active account
- `inactive` - Inactive account
- `suspended` - Suspended by admin
- `deleted` - Soft deleted

#### Subscription Status
- `trial` - In trial period
- `active` - Active subscription
- `past_due` - Payment overdue
- `canceled` - User canceled
- `expired` - Subscription ended
- `suspended` - Admin suspended

#### Transaction Status
- `pending` - Awaiting payment
- `processing` - Payment in progress
- `completed` - Payment successful
- `failed` - Payment failed
- `canceled` - Transaction canceled
- `refunded` - Amount refunded

#### Transaction Type
- `payment` - Regular payment
- `refund` - Refund transaction
- `credit` - Account credit
- `debit` - Account debit

#### Payment Method
- `dmoney` - D-Money payment
- `credit_card` - Credit/debit card
- `bank_transfer` - Bank transfer
- `wallet` - Digital wallet

#### Billing Interval
- `monthly` - Monthly billing
- `quarterly` - Quarterly billing (3 months)
- `yearly` - Yearly billing (12 months)

#### Refund Status
- `pending` - Awaiting approval
- `processing` - Being processed
- `completed` - Refund completed
- `failed` - Refund failed
- `canceled` - Request canceled

### Date/Time Format

All timestamps use **ISO 8601** format with UTC timezone:
```
2026-03-25T10:00:00Z
```

### Currency Codes

ISO 4217 three-letter codes:
- `DJF` - Djiboutian Franc
- `USD` - US Dollar
- `EUR` - Euro

### Decimal Precision

All monetary amounts use **2 decimal places**:
```
5000.00 (not 5000 or 5000.0)
```

---

## ✅ Validation Rules Summary

| Field Type | Validation |
|------------|------------|
| Email | Valid email format, unique in system |
| Username | 3-50 chars, alphanumeric + underscore, unique |
| Password | Min 8 chars, 1 uppercase, 1 number, 1 special char |
| Phone | Valid international format (E.164) |
| Amount | Positive decimal, 2 decimal places |
| Currency | Valid ISO 4217 code |
| Date | ISO 8601 format (YYYY-MM-DD) |
| DateTime | ISO 8601 format with timezone (YYYY-MM-DDTHH:MM:SSZ) |

---

## 🔍 Common Integration Patterns

### Pattern 1: Create User & Subscription

```
1. POST /api/v1/auth/register
   → Get access_token

2. GET /api/v1/plans
   → Choose plan_id

3. POST /api/v1/subscriptions
   → Create subscription (status: trial)

4. POST /api/v1/payments/create
   → Get checkout_url

5. Redirect user to checkout_url
   → User pays

6. Receive webhook: payment.success
   → Subscription activated

7. GET /api/v1/payments/verify/{order_id}
   → Confirm status
```

### Pattern 2: Check Payment Status

```
1. User returns from payment page

2. GET /api/v1/payments/verify/{order_id}
   → Check if completed

3. If status = completed:
   - GET /api/v1/subscriptions/{subscription_id}
   - Verify subscription.status = active
   - Grant user access

4. If status = failed:
   - Show error message
   - Offer retry option
```

### Pattern 3: Handle Subscription Renewal

```
1. Receive webhook: subscription.renewed
   → data.subscription contains updated dates

2. Update your local records:
   - subscription.current_period_end
   - subscription.next_payment_date

3. Notify user of successful renewal
```

---

**This document provides complete technical specifications for all API methods. Use it as your integration reference guide.**
