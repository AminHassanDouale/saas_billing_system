# 📊 D-Money Integration - Complete Database Schema & Data Flow

## Table of Contents

1. [Data Flow Overview](#data-flow-overview)
2. [Input Collection Points](#input-collection-points)
3. [Database Tables](#database-tables)
4. [Complete SQL Schema](#complete-sql-schema)
5. [Data Mapping](#data-mapping)
6. [Example Data Flow](#example-data-flow)

---

## 🔄 Data Flow Overview

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: USER CREATES SUBSCRIPTION                          │
│  Input: user_id, plan_id, auto_renew                        │
│  ↓                                                           │
│  Save to: subscriptions table                               │
│  Status: trial or pending                                   │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: SYSTEM CREATES TRANSACTION                         │
│  Input: amount, title, subscription_id, user_id            │
│  ↓                                                           │
│  Save to: transactions table                                │
│  Status: pending                                            │
│  Generate: transaction_id, order_id                         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: CALL D-MONEY API (PreOrder)                        │
│  Input: amount, title, order_id, currency, notify_url      │
│  ↓                                                           │
│  D-Money Returns: prepay_id, checkout_url                   │
│  ↓                                                           │
│  Update transactions table:                                 │
│  - prepay_id                                                │
│  - checkout_url                                             │
│  - raw_response (full API response)                         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: USER REDIRECTED TO D-MONEY                         │
│  User enters payment details on D-Money page                │
│  (No data saved yet)                                        │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: D-MONEY SENDS WEBHOOK                              │
│  Input: trade_status, transId, amount, merch_order_id      │
│  ↓                                                           │
│  Save to: webhook_events table (raw webhook data)          │
│  Update transactions table:                                 │
│  - status (completed/failed)                                │
│  - payment_transaction_id (D-Money transId)                 │
│  - paid_at or failed_at                                     │
│  - webhook_data                                             │
│  ↓                                                           │
│  Update subscriptions table:                                │
│  - status (active if payment completed)                     │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP 6: USER REDIRECTED BACK                               │
│  User lands on success/failure page                         │
│  (Read from transactions table to show status)              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📝 Input Collection Points

### 1. User Registration/Login

**Where:** `/api/v1/auth/register`

| Field | Type | Required | Saved To | Notes |
|-------|------|----------|----------|-------|
| `email` | String | ✅ | `users.email` | Unique |
| `username` | String | ✅ | `users.username` | Unique |
| `password` | String | ✅ | `users.hashed_password` | Bcrypt hashed |
| `first_name` | String | ⭕ | `users.first_name` | Optional |
| `last_name` | String | ⭕ | `users.last_name` | Optional |
| `company_name` | String | ⭕ | `users.company_name` | Optional |
| `phone` | String | ⭕ | `users.phone` | Optional |

**Auto-generated:**
- `users.id` (primary key)
- `users.role` (default: 'user')
- `users.status` (default: 'active')
- `users.created_at`, `users.updated_at`

---

### 2. Plan Selection

**Where:** User selects from available plans

| Field | Type | Source | Saved To | Notes |
|-------|------|--------|----------|-------|
| `plan_id` | Integer | User selection | `subscriptions.plan_id` | Foreign key |
| `user_id` | Integer | Current user | `subscriptions.user_id` | Foreign key |
| `auto_renew` | Boolean | User choice | `subscriptions.auto_renew` | Default: true |

**Retrieved from subscription_plans table:**
- `price`
- `currency`
- `interval`
- `trial_period_days`

**Auto-generated:**
- `subscriptions.id`
- `subscriptions.status` (default: 'trial' if trial_period > 0)
- `subscriptions.current_period_start`
- `subscriptions.current_period_end`
- `subscriptions.trial_start`, `subscriptions.trial_end`

---

### 3. Payment Initiation

**Where:** `/api/v1/payments/create`

| Field | Type | Source | Saved To | Notes |
|-------|------|--------|----------|-------|
| `amount` | Float | Subscription plan price | `transactions.amount` | From plan |
| `title` | String | Generated or provided | `transactions.title` | "Plan Name - Monthly" |
| `subscription_id` | Integer | From step 2 | `transactions.subscription_id` | Optional |
| `currency` | String | From plan (default: DJF) | `transactions.currency` | ISO code |
| `timeout` | String | Default: "120m" | API only | Not saved |
| `language` | String | Default: "en" | API only | Not saved |

**Auto-generated:**
- `transactions.id`
- `transactions.transaction_id` (e.g., "TXN_20260325120000ABC")
- `transactions.order_id` (e.g., "ORD20260325120000XYZ")
- `transactions.user_id` (current user)
- `transactions.status` (default: 'pending')
- `transactions.type` (default: 'payment')
- `transactions.payment_method` (default: 'dmoney')
- `transactions.created_at`

---

### 4. D-Money API Call (PreOrder)

**What system sends to D-Money:**

| Field | Value | Source |
|-------|-------|--------|
| `appid` | Your merchant ID | `settings.DMONEY_APPID` |
| `merch_code` | Your merchant code | `settings.DMONEY_MERCH_CODE` |
| `merch_order_id` | Order ID | `transactions.order_id` |
| `total_amount` | Amount in cents | `transactions.amount` |
| `trans_currency` | Currency | `transactions.currency` |
| `title` | Payment description | `transactions.title` |
| `notify_url` | Webhook URL | `settings.DMONEY_NOTIFY_URL` |
| `redirect_url` | Success page URL | `settings.DMONEY_REDIRECT_URL` |
| `timeout_express` | Payment timeout | "120m" |
| `trade_type` | Payment type | "Checkout" |
| `business_type` | Business type | "OnlineMerchant" |
| `callback_info` | Custom data | Optional (e.g., "sub_id:123") |

**What D-Money returns:**

| Field | Type | Saved To | Notes |
|-------|------|----------|-------|
| `prepay_id` | String | `transactions.prepay_id` | Used for checkout URL |
| `order_id` | String | Not saved | D-Money's order ID |
| `status` | String | Not saved | Usually "created" |
| *(full response)* | JSON | `transactions.raw_response` | Complete API response |

**Generated after API call:**
- `transactions.checkout_url` (generated from prepay_id)
- `transactions.redirect_url` (where user returns after payment)

---

### 5. User Payment on D-Money

**User enters on D-Money page:**
- Payment method selection (D-Money wallet, card, etc.)
- Account credentials (if D-Money wallet)
- Payment authorization

**Note:** This data never touches your system - it stays between user and D-Money.

---

### 6. Webhook from D-Money

**What D-Money sends to your webhook:**

| Field | Type | Saved To | Notes |
|-------|------|----------|-------|
| `merch_order_id` | String | Match with `transactions.order_id` | Your order ID |
| `trade_status` | String | → `transactions.status` | "completed", "failure", etc. |
| `transId` | String | `transactions.payment_transaction_id` | D-Money's transaction ID |
| `payment_order_id` | String | Not primary | D-Money's payment order ID |
| `total_amount` | String | Verify against `transactions.amount` | Amount paid |
| `trans_currency` | String | Verify against `transactions.currency` | Currency |
| `trans_end_time` | String | → `transactions.paid_at` | Payment timestamp |
| `callback_info` | String | Extract custom data | Your custom data |
| `notify_time` | String | Not saved | Notification timestamp |
| `sign` | String | For verification only | Webhook signature |
| `sign_type` | String | For verification only | "SHA256WithRSA" |
| *(full webhook)* | JSON | `transactions.webhook_data` | Complete webhook |

**Save to webhook_events table:**

| Field | Source | Notes |
|-------|--------|-------|
| `event_id` | `webhook.transId` | Unique identifier |
| `event_type` | `webhook.trade_status` | "payment.success", etc. |
| `transaction_id` | Lookup from order_id | Link to transactions |
| `order_id` | `webhook.merch_order_id` | Your order ID |
| `payload` | Full webhook JSON | Complete data |
| `processed` | Boolean | Initially false |
| `processed_at` | Timestamp | When processed |
| `error` | String | If processing failed |
| `retry_count` | Integer | Number of retries |
| `received_at` | Timestamp | When received |

**Update transactions table:**

```python
if trade_status == "completed":
    transaction.status = "completed"
    transaction.paid_at = datetime.now()
    transaction.payment_transaction_id = webhook["transId"]
    transaction.webhook_received = True
    transaction.webhook_data = json.dumps(webhook)
elif trade_status == "failure":
    transaction.status = "failed"
    transaction.failed_at = datetime.now()
    transaction.error_message = webhook.get("error_message")
```

**Update subscriptions table:**

```python
if trade_status == "completed" and transaction.subscription_id:
    subscription.status = "active"
    subscription.current_period_start = datetime.now()
    subscription.current_period_end = datetime.now() + interval
```

---

### 7. Refund Request (Optional)

**Where:** `/api/v1/refunds/request`

| Field | Type | Source | Saved To |
|-------|------|--------|----------|
| `transaction_id` | Integer | User selects | `refunds.transaction_id` |
| `refund_amount` | Float | User enters | `refunds.refund_amount` |
| `reason` | Enum | User selects | `refunds.reason` |
| `reason_details` | String | User enters | `refunds.reason_details` |

**Auto-generated:**
- `refunds.id`
- `refunds.refund_id` (e.g., "REF_20260325_ABC")
- `refunds.user_id` (current user)
- `refunds.status` (default: 'pending')
- `refunds.original_amount` (from transaction)
- `refunds.currency` (from transaction)
- `refunds.is_partial` (amount < original_amount)
- `refunds.created_at`

---

## 🗄️ Database Tables

### Complete Schema with All Fields

#### 1. **users** table

```sql
CREATE TABLE users (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Authentication
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(100) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    
    -- Profile Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    phone VARCHAR(20),
    
    -- Role & Status
    role ENUM('admin', 'merchant', 'user') NOT NULL DEFAULT 'user',
    status ENUM('active', 'inactive', 'suspended', 'deleted') NOT NULL DEFAULT 'active',
    
    -- Verification
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    
    -- Security
    failed_login_attempts INT DEFAULT 0,
    locked_until DATETIME NULL,
    last_login DATETIME NULL,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at DATETIME NULL,
    
    -- Indexes
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 2. **subscription_plans** table

```sql
CREATE TABLE subscription_plans (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Plan Details
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'DJF',
    interval ENUM('monthly', 'quarterly', 'yearly') NOT NULL DEFAULT 'monthly',
    
    -- Features
    features JSON,  -- Array of features
    max_users INT,
    max_storage_gb INT,
    
    -- Trial
    trial_period_days INT DEFAULT 0,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_active (is_active),
    INDEX idx_price (price)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 3. **subscriptions** table

```sql
CREATE TABLE subscriptions (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Foreign Keys
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    
    -- Status
    status ENUM('trial', 'active', 'past_due', 'canceled', 'expired', 'suspended') 
           NOT NULL DEFAULT 'trial',
    
    -- Trial Period
    trial_start DATETIME,
    trial_end DATETIME,
    
    -- Billing Period
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    
    -- Cancellation
    canceled_at DATETIME,
    ended_at DATETIME,
    
    -- Renewal
    auto_renew BOOLEAN DEFAULT TRUE,
    payment_retry_count INT DEFAULT 0,
    next_payment_date DATETIME,
    
    -- Metadata
    metadata JSON,  -- Store custom data
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id),
    
    -- Indexes
    INDEX idx_user_status (user_id, status),
    INDEX idx_status (status),
    INDEX idx_period_end (current_period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 4. **transactions** table

```sql
CREATE TABLE transactions (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Transaction Identifiers
    transaction_id VARCHAR(100) NOT NULL UNIQUE,  -- Your generated ID
    order_id VARCHAR(100) NOT NULL,               -- Your order ID sent to D-Money
    prepay_id VARCHAR(100),                       -- D-Money prepay ID
    
    -- Foreign Keys
    user_id INT NOT NULL,
    subscription_id INT,
    
    -- Transaction Type & Status
    type ENUM('payment', 'refund', 'credit', 'debit') NOT NULL DEFAULT 'payment',
    status ENUM('pending', 'processing', 'completed', 'failed', 'canceled', 'refunded') 
           NOT NULL DEFAULT 'pending',
    payment_method ENUM('dmoney', 'credit_card', 'bank_transfer', 'wallet') 
                   NOT NULL DEFAULT 'dmoney',
    
    -- Amount Details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'DJF',
    fee DECIMAL(10, 2),
    net_amount DECIMAL(10, 2) NOT NULL,
    
    -- Payment Details
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- D-Money Integration
    checkout_url VARCHAR(500),                    -- Generated checkout URL
    redirect_url VARCHAR(500),                    -- Where user returns
    payment_transaction_id VARCHAR(100),          -- D-Money's transId from webhook
    
    -- Timestamps
    paid_at DATETIME,
    failed_at DATETIME,
    refunded_at DATETIME,
    
    -- Error Handling
    error_code VARCHAR(50),
    error_message TEXT,
    
    -- Webhook Data
    webhook_received BOOLEAN DEFAULT FALSE,
    webhook_data JSON,                            -- Complete webhook payload
    
    -- API Responses
    metadata JSON,                                -- Custom metadata
    raw_response JSON,                            -- D-Money PreOrder API response
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_transaction_id (transaction_id),
    INDEX idx_order_id (order_id),
    INDEX idx_prepay_id (prepay_id),
    INDEX idx_user_status (user_id, status),
    INDEX idx_created_at (created_at),
    INDEX idx_payment_transaction_id (payment_transaction_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 5. **webhook_events** table

```sql
CREATE TABLE webhook_events (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Event Identifiers
    event_id VARCHAR(100) NOT NULL UNIQUE,        -- D-Money transId
    event_type VARCHAR(50) NOT NULL,               -- "payment.success", etc.
    
    -- Foreign Keys
    transaction_id INT,                            -- Link to transaction
    order_id VARCHAR(100),                         -- Your order ID
    
    -- Webhook Payload
    payload JSON NOT NULL,                         -- Complete webhook data
    
    -- Processing Status
    processed BOOLEAN DEFAULT FALSE,
    processed_at DATETIME,
    error TEXT,
    retry_count INT DEFAULT 0,
    
    -- Timestamps
    received_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_event_id (event_id),
    INDEX idx_order_id (order_id),
    INDEX idx_processed (processed),
    INDEX idx_received_at (received_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### 6. **refunds** table

```sql
CREATE TABLE refunds (
    -- Primary Key
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Refund Identifier
    refund_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Foreign Keys
    transaction_id INT NOT NULL,
    user_id INT NOT NULL,
    processed_by INT,                              -- Admin who approved
    
    -- Status
    status ENUM('pending', 'processing', 'completed', 'failed', 'canceled') 
           NOT NULL DEFAULT 'pending',
    
    -- Reason
    reason ENUM('customer_request', 'duplicate_payment', 'fraudulent', 
                'service_not_provided', 'subscription_canceled', 'other') NOT NULL,
    reason_details TEXT,
    
    -- Amount Details
    original_amount DECIMAL(10, 2) NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'DJF',
    is_partial BOOLEAN DEFAULT FALSE,
    
    -- Processing
    approved_at DATETIME,
    rejected_at DATETIME,
    completed_at DATETIME,
    admin_notes TEXT,
    
    -- D-Money Refund
    dmoney_refund_id VARCHAR(100),
    dmoney_response JSON,
    
    -- Error Handling
    error_code VARCHAR(50),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    
    -- Timestamps
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (processed_by) REFERENCES users(id) ON DELETE SET NULL,
    
    -- Indexes
    INDEX idx_refund_id (refund_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 🔄 Data Mapping

### Payment Creation Flow

```python
# Step 1: User selects plan
plan = db.query(SubscriptionPlan).get(plan_id)

# Step 2: Create subscription
subscription = Subscription(
    user_id=current_user.id,
    plan_id=plan.id,
    status="trial" if plan.trial_period_days > 0 else "pending",
    trial_start=datetime.now() if plan.trial_period_days > 0 else None,
    trial_end=datetime.now() + timedelta(days=plan.trial_period_days) if plan.trial_period_days > 0 else None,
    current_period_start=datetime.now(),
    current_period_end=datetime.now() + get_interval_delta(plan.interval),
    auto_renew=True
)
db.add(subscription)
db.commit()

# Step 3: Create transaction
transaction = Transaction(
    transaction_id=generate_transaction_id(),  # "TXN_20260325120000ABC"
    order_id=generate_order_id(),              # "ORD20260325120000XYZ"
    user_id=current_user.id,
    subscription_id=subscription.id,
    type="payment",
    status="pending",
    payment_method="dmoney",
    amount=plan.price,
    currency=plan.currency,
    net_amount=plan.price,  # No fees initially
    title=f"{plan.name} - {plan.interval.capitalize()}",
    description=f"Payment for {plan.name} subscription"
)
db.add(transaction)
db.commit()

# Step 4: Call D-Money API
dmoney_result = gateway.create_payment(
    amount=transaction.amount,
    title=transaction.title,
    order_id=transaction.order_id,
    currency=transaction.currency,
    notify_url=settings.DMONEY_NOTIFY_URL,
    redirect_url=settings.DMONEY_REDIRECT_URL,
    callback_info=f"subscription_id:{subscription.id}"
)

# Step 5: Update transaction with D-Money response
transaction.prepay_id = dmoney_result["prepay_id"]
transaction.checkout_url = dmoney_result["checkout_url"]
transaction.raw_response = json.dumps(dmoney_result["raw_response"])
db.commit()

# Step 6: Return checkout URL to frontend
return {"checkout_url": transaction.checkout_url}
```

### Webhook Processing Flow

```python
# Step 1: Receive webhook
webhook_data = request.json()

# Step 2: Save to webhook_events
webhook_event = WebhookEvent(
    event_id=webhook_data["transId"],
    event_type=f"payment.{webhook_data['trade_status']}",
    order_id=webhook_data["merch_order_id"],
    payload=json.dumps(webhook_data),
    processed=False,
    received_at=datetime.now()
)
db.add(webhook_event)
db.commit()

# Step 3: Find transaction
transaction = db.query(Transaction).filter(
    Transaction.order_id == webhook_data["merch_order_id"]
).first()

if not transaction:
    webhook_event.error = "Transaction not found"
    db.commit()
    return

webhook_event.transaction_id = transaction.id

# Step 4: Process based on status
if webhook_data["trade_status"] == "completed":
    # Update transaction
    transaction.status = "completed"
    transaction.payment_transaction_id = webhook_data["transId"]
    transaction.paid_at = datetime.now()
    transaction.webhook_received = True
    transaction.webhook_data = json.dumps(webhook_data)
    
    # Update subscription (if applicable)
    if transaction.subscription_id:
        subscription = transaction.subscription
        subscription.status = "active"
    
    # Mark webhook as processed
    webhook_event.processed = True
    webhook_event.processed_at = datetime.now()
    
    db.commit()
    
    # Send confirmation email (async)
    send_payment_receipt_task.delay(transaction.id)

elif webhook_data["trade_status"] == "failure":
    transaction.status = "failed"
    transaction.failed_at = datetime.now()
    transaction.error_message = webhook_data.get("error_message", "Payment failed")
    
    webhook_event.processed = True
    webhook_event.processed_at = datetime.now()
    
    db.commit()
```

---

## 📋 Example Data Flow

### Complete Example: User Subscribes to Professional Plan

#### Initial State

**subscription_plans table:**
```
id | name         | price  | currency | interval | trial_period_days
---|--------------|--------|----------|----------|------------------
2  | Professional | 5000.0 | DJF      | monthly  | 14
```

#### Step 1: User selects plan

**Input:**
```json
{
  "plan_id": 2,
  "auto_renew": true
}
```

**subscriptions table (after insert):**
```
id | user_id | plan_id | status | trial_start         | trial_end           | current_period_start | current_period_end  | auto_renew
---|---------|---------|--------|---------------------|---------------------|----------------------|---------------------|------------
1  | 5       | 2       | trial  | 2026-03-25 10:00:00 | 2026-04-08 10:00:00 | 2026-03-25 10:00:00  | 2026-04-25 10:00:00 | true
```

#### Step 2: Create payment

**transactions table (after insert):**
```
id | transaction_id        | order_id              | user_id | subscription_id | type    | status  | amount | currency | title
---|-----------------------|-----------------------|---------|-----------------|---------|---------|--------|----------|---------------------------
1  | TXN_20260325100500ABC | ORD20260325100500XYZ  | 5       | 1               | payment | pending | 5000.0 | DJF      | Professional - Monthly
```

#### Step 3: D-Money API call

**Request to D-Money:**
```json
{
  "appid": "1293049431398401",
  "merch_code": "9988",
  "merch_order_id": "ORD20260325100500XYZ",
  "total_amount": "5000",
  "trans_currency": "DJF",
  "title": "Professional - Monthly",
  "notify_url": "https://yourdomain.com/api/v1/webhooks/dmoney",
  "redirect_url": "https://yourdomain.com/payment/success"
}
```

**Response from D-Money:**
```json
{
  "code": "0",
  "message": "Success",
  "biz_content": {
    "prepay_id": "wx789def456ghi123",
    "order_id": "dmoney_order_98765",
    "status": "created"
  }
}
```

**transactions table (after update):**
```
id | prepay_id          | checkout_url                                  | raw_response
---|--------------------|-----------------------------------------------|-------------
1  | wx789def456ghi123  | https://pg.d-moneyservice.dj/paygate?prepay_id=... | {"code":"0",...}
```

#### Step 4: User pays on D-Money

*(User interaction - no database changes)*

#### Step 5: Webhook received

**Webhook payload:**
```json
{
  "merch_order_id": "ORD20260325100500XYZ",
  "trade_status": "completed",
  "transId": "DMONEY_TXN_456789",
  "payment_order_id": "dmoney_order_98765",
  "total_amount": "5000",
  "trans_currency": "DJF",
  "trans_end_time": "2026-03-25 10:15:30",
  "callback_info": "subscription_id:1",
  "timestamp": "1711360530",
  "sign": "signature_here...",
  "sign_type": "SHA256WithRSA"
}
```

**webhook_events table (after insert):**
```
id | event_id          | event_type        | transaction_id | order_id              | processed | received_at
---|-------------------|-------------------|----------------|-----------------------|-----------|--------------------
1  | DMONEY_TXN_456789 | payment.completed | 1              | ORD20260325100500XYZ  | true      | 2026-03-25 10:15:30
```

**transactions table (after update):**
```
id | status    | payment_transaction_id | paid_at             | webhook_received | webhook_data
---|-----------|------------------------|---------------------|------------------|-------------
1  | completed | DMONEY_TXN_456789      | 2026-03-25 10:15:30 | true             | {"merch_order_id":...}
```

**subscriptions table (after update):**
```
id | status | current_period_start | current_period_end  
---|--------|----------------------|---------------------
1  | active | 2026-03-25 10:00:00  | 2026-04-25 10:00:00
```

---

## ✅ Summary

### All Inputs Required

1. **User Registration:** email, username, password, name, phone
2. **Plan Selection:** plan_id, auto_renew
3. **Payment Creation:** amount, title (auto from plan)
4. **D-Money Config:** API credentials, URLs (from settings)
5. **Webhook:** Automatic from D-Money
6. **Refund (optional):** transaction_id, amount, reason

### All Database Tables

1. **users** - User accounts
2. **subscription_plans** - Available plans
3. **subscriptions** - User subscriptions
4. **transactions** - Payment records
5. **webhook_events** - Webhook log
6. **refunds** - Refund requests

### Data Relationships

```
users (1) ----< (M) subscriptions
subscription_plans (1) ----< (M) subscriptions
users (1) ----< (M) transactions
subscriptions (1) ----< (M) transactions
transactions (1) ----< (M) webhook_events
transactions (1) ----< (M) refunds
```

---

This provides the complete picture of all data flowing through your D-Money payment integration! 🎯
