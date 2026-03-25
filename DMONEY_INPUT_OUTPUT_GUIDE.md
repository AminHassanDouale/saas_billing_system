# 📊 D-Money Payment Integration - Complete Input/Output Guide

## 🎯 Quick Summary

This document shows **EVERY piece of data** that flows through your D-Money payment system, where it comes from, and where it's saved.

---

## 🔄 Complete Payment Flow with ALL Inputs/Outputs

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: USER REGISTRATION                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ USER PROVIDES (Frontend Form):                                  │
│ ✅ email            → "john@example.com"                         │
│ ✅ username         → "john_doe"                                 │
│ ✅ password         → "SecurePass123!"                           │
│ ⭕ first_name       → "John"                                     │
│ ⭕ last_name        → "Doe"                                      │
│ ⭕ company_name     → "Acme Corp"                                │
│ ⭕ phone            → "+253 77 12 34 56"                         │
│                                                                  │
│ SYSTEM GENERATES:                                                │
│ 🔧 id               → 5 (auto-increment)                         │
│ 🔧 hashed_password  → "$2b$12$..." (bcrypt)                      │
│ 🔧 role             → "user"                                     │
│ 🔧 status           → "active"                                   │
│ 🔧 created_at       → "2026-03-25 10:00:00"                      │
│                                                                  │
│ SAVED TO DATABASE:                                               │
│ 💾 users table (all above fields)                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: USER SELECTS SUBSCRIPTION PLAN                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ USER SELECTS (Frontend):                                         │
│ ✅ plan_id          → 2 (Professional plan)                      │
│ ✅ auto_renew       → true                                       │
│                                                                  │
│ SYSTEM RETRIEVES (from subscription_plans table):               │
│ 📖 name             → "Professional"                             │
│ 📖 price            → 5000.00                                    │
│ 📖 currency         → "DJF"                                      │
│ 📖 interval         → "monthly"                                  │
│ 📖 trial_period_days → 14                                        │
│                                                                  │
│ SYSTEM GENERATES:                                                │
│ 🔧 id               → 1 (auto-increment)                         │
│ 🔧 user_id          → 5 (current user)                           │
│ 🔧 status           → "trial" (because trial_period > 0)         │
│ 🔧 trial_start      → "2026-03-25 10:00:00"                      │
│ 🔧 trial_end        → "2026-04-08 10:00:00" (+14 days)           │
│ 🔧 current_period_start → "2026-03-25 10:00:00"                  │
│ 🔧 current_period_end   → "2026-04-25 10:00:00" (+1 month)       │
│ 🔧 created_at       → "2026-03-25 10:00:00"                      │
│                                                                  │
│ SAVED TO DATABASE:                                               │
│ 💾 subscriptions table (all above fields)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: SYSTEM CREATES PAYMENT TRANSACTION                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ SYSTEM USES (from subscription):                                 │
│ 📖 amount           → 5000.00 (from plan.price)                  │
│ 📖 currency         → "DJF" (from plan.currency)                 │
│ 📖 subscription_id  → 1                                          │
│ 📖 user_id          → 5                                          │
│                                                                  │
│ SYSTEM GENERATES:                                                │
│ 🔧 id               → 1 (auto-increment)                         │
│ 🔧 transaction_id   → "TXN_20260325100500ABC"                    │
│ 🔧 order_id         → "ORD20260325100500XYZ"                     │
│ 🔧 type             → "payment"                                  │
│ 🔧 status           → "pending"                                  │
│ 🔧 payment_method   → "dmoney"                                   │
│ 🔧 title            → "Professional - Monthly"                   │
│ 🔧 description      → "Payment for Professional subscription"    │
│ 🔧 net_amount       → 5000.00                                    │
│ 🔧 created_at       → "2026-03-25 10:05:00"                      │
│                                                                  │
│ SAVED TO DATABASE:                                               │
│ 💾 transactions table (all above fields)                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: CALL D-MONEY API (PreOrder)                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ SYSTEM SENDS TO D-MONEY:                                         │
│ 📤 appid            → "1293049431398401" (from settings)         │
│ 📤 merch_code       → "9988" (from settings)                     │
│ 📤 merch_order_id   → "ORD20260325100500XYZ"                     │
│ 📤 total_amount     → "5000" (integer string)                    │
│ 📤 trans_currency   → "DJF"                                      │
│ 📤 title            → "Professional - Monthly"                   │
│ 📤 notify_url       → "https://yourdomain.com/webhooks/dmoney"   │
│ 📤 redirect_url     → "https://yourdomain.com/payment/success"   │
│ 📤 timeout_express  → "120m"                                     │
│ 📤 trade_type       → "Checkout"                                 │
│ 📤 business_type    → "OnlineMerchant"                           │
│ 📤 callback_info    → "subscription_id:1" (optional)             │
│ 📤 nonce_str        → "abcd1234efgh..." (random)                 │
│ 📤 timestamp        → "1711360500"                               │
│ 📤 sign             → "base64_signature..." (RSA-PSS)            │
│                                                                  │
│ D-MONEY RETURNS:                                                 │
│ 📥 code             → "0" (success)                              │
│ 📥 message          → "Success"                                  │
│ 📥 biz_content.prepay_id → "wx789def456ghi123"                   │
│ 📥 biz_content.order_id  → "dmoney_order_98765"                  │
│ 📥 biz_content.status    → "created"                             │
│                                                                  │
│ SYSTEM GENERATES:                                                │
│ 🔧 checkout_url     → "https://pg.d-moneyservice.dj/paygate?..." │
│                                                                  │
│ SAVED TO DATABASE (update transactions):                         │
│ 💾 prepay_id        → "wx789def456ghi123"                        │
│ 💾 checkout_url     → "https://pg.d-moneyservice.dj/..."         │
│ 💾 raw_response     → {"code":"0","message":"Success",...}       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: USER REDIRECTED TO D-MONEY PAYMENT PAGE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ USER SEES (on D-Money website):                                  │
│ - Payment amount: 5000 DJF                                       │
│ - Merchant: Your Company Name                                    │
│ - Description: Professional - Monthly                            │
│                                                                  │
│ USER ENTERS (on D-Money page - NOT saved in your system):       │
│ - D-Money wallet phone number OR                                 │
│ - Credit/Debit card details OR                                   │
│ - Other payment method                                           │
│                                                                  │
│ ⚠️ IMPORTANT: This data NEVER touches your database!             │
│    It stays between user and D-Money.                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: D-MONEY SENDS WEBHOOK TO YOUR SERVER                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ D-MONEY SENDS (POST to your notify_url):                        │
│ 📥 merch_order_id   → "ORD20260325100500XYZ"                     │
│ 📥 trade_status     → "completed" or "failure"                   │
│ 📥 transId          → "DMONEY_TXN_456789"                        │
│ 📥 payment_order_id → "dmoney_order_98765"                       │
│ 📥 total_amount     → "5000"                                     │
│ 📥 trans_currency   → "DJF"                                      │
│ 📥 trans_end_time   → "2026-03-25 10:15:30"                      │
│ 📥 callback_info    → "subscription_id:1"                        │
│ 📥 notify_time      → "1711360530"                               │
│ 📥 sign             → "webhook_signature..."                     │
│ 📥 sign_type        → "SHA256WithRSA"                            │
│                                                                  │
│ SYSTEM PROCESSES:                                                │
│ 1️⃣ Verify signature (using D-Money public key)                  │
│ 2️⃣ Check for duplicate (using transId)                          │
│ 3️⃣ Find transaction (using merch_order_id)                      │
│ 4️⃣ Update transaction status                                    │
│ 5️⃣ Update subscription status                                   │
│ 6️⃣ Send confirmation email                                      │
│                                                                  │
│ SAVED TO DATABASE:                                               │
│                                                                  │
│ 💾 webhook_events table (new row):                               │
│    - event_id       → "DMONEY_TXN_456789"                        │
│    - event_type     → "payment.completed"                        │
│    - transaction_id → 1                                          │
│    - order_id       → "ORD20260325100500XYZ"                     │
│    - payload        → {full webhook JSON}                        │
│    - processed      → true                                       │
│    - processed_at   → "2026-03-25 10:15:31"                      │
│    - received_at    → "2026-03-25 10:15:30"                      │
│                                                                  │
│ 💾 transactions table (update):                                  │
│    - status         → "completed" (was "pending")                │
│    - payment_transaction_id → "DMONEY_TXN_456789"                │
│    - paid_at        → "2026-03-25 10:15:30"                      │
│    - webhook_received → true                                     │
│    - webhook_data   → {full webhook JSON}                        │
│                                                                  │
│ 💾 subscriptions table (update):                                 │
│    - status         → "active" (was "trial")                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 7: USER REDIRECTED BACK TO YOUR WEBSITE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ D-Money redirects to: redirect_url                               │
│ → "https://yourdomain.com/payment/success?order_id=ORD..."      │
│                                                                  │
│ YOUR FRONTEND:                                                   │
│ 1️⃣ Extracts order_id from URL                                    │
│ 2️⃣ Calls your API: GET /api/v1/transactions/{order_id}          │
│ 3️⃣ Shows success/failure message based on status                │
│                                                                  │
│ NO NEW DATA SAVED - Just reading from database                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Complete Input Summary Table

### All User Inputs (Frontend Forms)

| Step | Field | Type | Required | Example | Saved To |
|------|-------|------|----------|---------|----------|
| **Registration** | email | String | ✅ | john@example.com | users.email |
| | username | String | ✅ | john_doe | users.username |
| | password | String | ✅ | SecurePass123! | users.hashed_password |
| | first_name | String | ⭕ | John | users.first_name |
| | last_name | String | ⭕ | Doe | users.last_name |
| | company_name | String | ⭕ | Acme Corp | users.company_name |
| | phone | String | ⭕ | +253 77 12 34 56 | users.phone |
| **Plan Selection** | plan_id | Integer | ✅ | 2 | subscriptions.plan_id |
| | auto_renew | Boolean | ✅ | true | subscriptions.auto_renew |

### System-Generated Data

| Step | Field | Source | Example | Saved To |
|------|-------|--------|---------|----------|
| **Registration** | id | Auto-increment | 5 | users.id |
| | hashed_password | bcrypt(password) | $2b$12$... | users.hashed_password |
| | role | Default | user | users.role |
| | status | Default | active | users.status |
| **Subscription** | id | Auto-increment | 1 | subscriptions.id |
| | user_id | Current user | 5 | subscriptions.user_id |
| | status | Conditional | trial | subscriptions.status |
| | trial_start | now() | 2026-03-25 10:00:00 | subscriptions.trial_start |
| | trial_end | now() + trial_days | 2026-04-08 10:00:00 | subscriptions.trial_end |
| | current_period_start | now() | 2026-03-25 10:00:00 | subscriptions.current_period_start |
| | current_period_end | now() + interval | 2026-04-25 10:00:00 | subscriptions.current_period_end |
| **Transaction** | id | Auto-increment | 1 | transactions.id |
| | transaction_id | Generated | TXN_20260325100500ABC | transactions.transaction_id |
| | order_id | Generated | ORD20260325100500XYZ | transactions.order_id |
| | user_id | Current user | 5 | transactions.user_id |
| | subscription_id | From subscription | 1 | transactions.subscription_id |
| | amount | From plan | 5000.00 | transactions.amount |
| | currency | From plan | DJF | transactions.currency |
| | status | Default | pending | transactions.status |

### D-Money API Data

| Direction | Field | Example | Saved To |
|-----------|-------|---------|----------|
| **To D-Money** | appid | 1293049431398401 | Config only |
| | merch_code | 9988 | Config only |
| | merch_order_id | ORD20260325100500XYZ | Already in transactions.order_id |
| | total_amount | 5000 | From transactions.amount |
| | notify_url | https://yourdomain.com/webhooks/dmoney | Config only |
| **From D-Money** | prepay_id | wx789def456ghi123 | transactions.prepay_id |
| | checkout_url | https://pg.d-moneyservice.dj/... | transactions.checkout_url |
| | full response | {...} | transactions.raw_response |

### Webhook Data from D-Money

| Field | Example | Saved To |
|-------|---------|----------|
| transId | DMONEY_TXN_456789 | webhook_events.event_id |
| | | transactions.payment_transaction_id |
| trade_status | completed | webhook_events.event_type |
| | | transactions.status |
| trans_end_time | 2026-03-25 10:15:30 | transactions.paid_at |
| full webhook | {...} | webhook_events.payload |
| | | transactions.webhook_data |

---

## 🗄️ Database Schema (Simplified)

### 1. users Table

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    phone VARCHAR(20),
    role ENUM('admin', 'merchant', 'user') DEFAULT 'user',
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2. subscription_plans Table

```sql
CREATE TABLE subscription_plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'DJF',
    interval ENUM('monthly', 'quarterly', 'yearly') DEFAULT 'monthly',
    trial_period_days INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 3. subscriptions Table

```sql
CREATE TABLE subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    plan_id INT NOT NULL,
    status ENUM('trial', 'active', 'past_due', 'canceled', 'expired') DEFAULT 'trial',
    trial_start DATETIME,
    trial_end DATETIME,
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    auto_renew BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (plan_id) REFERENCES subscription_plans(id)
);
```

### 4. transactions Table

```sql
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    prepay_id VARCHAR(100),
    
    user_id INT NOT NULL,
    subscription_id INT,
    
    type ENUM('payment', 'refund') DEFAULT 'payment',
    status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
    payment_method ENUM('dmoney') DEFAULT 'dmoney',
    
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'DJF',
    net_amount DECIMAL(10, 2) NOT NULL,
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    checkout_url VARCHAR(500),
    redirect_url VARCHAR(500),
    payment_transaction_id VARCHAR(100),
    
    paid_at DATETIME,
    failed_at DATETIME,
    
    webhook_received BOOLEAN DEFAULT FALSE,
    webhook_data JSON,
    raw_response JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
);
```

### 5. webhook_events Table

```sql
CREATE TABLE webhook_events (
    id INT PRIMARY KEY AUTO_INCREMENT,
    event_id VARCHAR(100) UNIQUE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    transaction_id INT,
    order_id VARCHAR(100),
    payload JSON NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at DATETIME,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id)
);
```

### 6. refunds Table (Optional)

```sql
CREATE TABLE refunds (
    id INT PRIMARY KEY AUTO_INCREMENT,
    refund_id VARCHAR(100) UNIQUE NOT NULL,
    transaction_id INT NOT NULL,
    user_id INT NOT NULL,
    
    status ENUM('pending', 'completed', 'failed') DEFAULT 'pending',
    reason VARCHAR(255),
    
    original_amount DECIMAL(10, 2) NOT NULL,
    refund_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'DJF',
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 📊 Example with Real Data

### Step-by-Step Data Flow

#### 1. User Registers

**Input (Frontend):**
```json
{
  "email": "alice@example.com",
  "username": "alice",
  "password": "SecurePass123!",
  "first_name": "Alice",
  "last_name": "Johnson"
}
```

**Saved (users table):**
```sql
INSERT INTO users VALUES (
  5,                              -- id (auto)
  'alice@example.com',            -- email
  'alice',                        -- username
  '$2b$12$abc...',                -- hashed_password
  'Alice',                        -- first_name
  'Johnson',                      -- last_name
  NULL,                           -- company_name
  NULL,                           -- phone
  'user',                         -- role
  'active',                       -- status
  '2026-03-25 10:00:00'           -- created_at
);
```

#### 2. User Selects Plan

**Input (Frontend):**
```json
{
  "plan_id": 2,
  "auto_renew": true
}
```

**Plan Details (subscription_plans table):**
```
id=2, name="Professional", price=5000.00, currency="DJF", 
interval="monthly", trial_period_days=14
```

**Saved (subscriptions table):**
```sql
INSERT INTO subscriptions VALUES (
  1,                              -- id (auto)
  5,                              -- user_id
  2,                              -- plan_id
  'trial',                        -- status
  '2026-03-25 10:00:00',          -- trial_start
  '2026-04-08 10:00:00',          -- trial_end (+14 days)
  '2026-03-25 10:00:00',          -- current_period_start
  '2026-04-25 10:00:00',          -- current_period_end (+1 month)
  TRUE,                           -- auto_renew
  '2026-03-25 10:00:00'           -- created_at
);
```

#### 3. System Creates Transaction

**Saved (transactions table):**
```sql
INSERT INTO transactions VALUES (
  1,                              -- id (auto)
  'TXN_20260325100500ABC',        -- transaction_id (generated)
  'ORD20260325100500XYZ',         -- order_id (generated)
  NULL,                           -- prepay_id (from D-Money later)
  5,                              -- user_id
  1,                              -- subscription_id
  'payment',                      -- type
  'pending',                      -- status
  'dmoney',                       -- payment_method
  5000.00,                        -- amount
  'DJF',                          -- currency
  5000.00,                        -- net_amount
  'Professional - Monthly',       -- title
  'Payment for Professional...',  -- description
  NULL,                           -- checkout_url (from D-Money later)
  NULL,                           -- redirect_url
  NULL,                           -- payment_transaction_id (from webhook)
  NULL,                           -- paid_at
  NULL,                           -- failed_at
  FALSE,                          -- webhook_received
  NULL,                           -- webhook_data
  NULL,                           -- raw_response
  '2026-03-25 10:05:00'           -- created_at
);
```

#### 4. D-Money API Response

**Update (transactions table):**
```sql
UPDATE transactions SET
  prepay_id = 'wx789def456ghi123',
  checkout_url = 'https://pg.d-moneyservice.dj/paygate?prepay_id=...',
  raw_response = '{"code":"0","message":"Success",...}'
WHERE id = 1;
```

#### 5. Webhook Received

**Saved (webhook_events table):**
```sql
INSERT INTO webhook_events VALUES (
  1,                              -- id (auto)
  'DMONEY_TXN_456789',            -- event_id
  'payment.completed',            -- event_type
  1,                              -- transaction_id
  'ORD20260325100500XYZ',         -- order_id
  '{"merch_order_id":"ORD..."...}', -- payload (full JSON)
  TRUE,                           -- processed
  '2026-03-25 10:15:31',          -- processed_at
  '2026-03-25 10:15:30'           -- received_at
);
```

**Update (transactions table):**
```sql
UPDATE transactions SET
  status = 'completed',
  payment_transaction_id = 'DMONEY_TXN_456789',
  paid_at = '2026-03-25 10:15:30',
  webhook_received = TRUE,
  webhook_data = '{"trade_status":"completed"...}'
WHERE id = 1;
```

**Update (subscriptions table):**
```sql
UPDATE subscriptions SET
  status = 'active'
WHERE id = 1;
```

---

## 🎯 Summary Checklist

### All Inputs You Need to Collect

- [ ] **User Registration:** email, username, password, name, phone
- [ ] **Plan Selection:** plan_id, auto_renew
- [ ] **D-Money Config** (one-time setup in .env):
  - [ ] DMONEY_APPID
  - [ ] DMONEY_MERCH_CODE
  - [ ] DMONEY_X_APP_KEY
  - [ ] DMONEY_APP_SECRET
  - [ ] DMONEY_PRIVATE_KEY_B64
  - [ ] DMONEY_NOTIFY_URL
  - [ ] DMONEY_REDIRECT_URL

### Data Automatically Generated/Retrieved

- ✅ User ID, transaction ID, order ID
- ✅ Subscription dates, trial periods
- ✅ Payment status, timestamps
- ✅ D-Money prepay_id, checkout_url
- ✅ Webhook data, payment confirmation

### Database Tables Required

1. ✅ **users** - User accounts
2. ✅ **subscription_plans** - Available plans
3. ✅ **subscriptions** - User subscriptions
4. ✅ **transactions** - Payment records
5. ✅ **webhook_events** - Webhook log
6. ⭕ **refunds** - Optional for refund handling

---

**This is everything you need to know about data flow in your D-Money integration!** 🎉

Every input, every output, every database field - all documented above. Use this as your reference guide during development! 📚

