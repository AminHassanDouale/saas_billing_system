# 🎯 D-Money Integration - Quick Reference Card

## 📥 USER INPUTS (Frontend Forms)

### Registration Form
```
✅ email            Example: john@example.com
✅ username         Example: john_doe
✅ password         Example: SecurePass123!
⭕ first_name       Example: John
⭕ last_name        Example: Doe
⭕ company_name     Example: Acme Corp
⭕ phone            Example: +253 77 12 34 56
```

### Plan Selection
```
✅ plan_id          Example: 2 (Professional)
✅ auto_renew       Example: true
```

---

## 🗄️ DATABASE TABLES & KEY FIELDS

### 1. users
```
id, email, username, hashed_password, first_name, last_name,
company_name, phone, role, status, created_at
```

### 2. subscription_plans
```
id, name, price, currency, interval, trial_period_days
```

### 3. subscriptions
```
id, user_id, plan_id, status, trial_start, trial_end,
current_period_start, current_period_end, auto_renew
```

### 4. transactions
```
id, transaction_id, order_id, prepay_id, user_id, subscription_id,
status, amount, currency, title, checkout_url, paid_at,
payment_transaction_id, webhook_data, raw_response
```

### 5. webhook_events
```
id, event_id, event_type, transaction_id, order_id, payload,
processed, processed_at, received_at
```

### 6. refunds (optional)
```
id, refund_id, transaction_id, user_id, status, reason,
refund_amount, original_amount
```

---

## 🔄 PAYMENT FLOW

```
1. User Registers          → users table
2. User Selects Plan       → subscriptions table (status: trial/pending)
3. System Creates Payment  → transactions table (status: pending)
4. Call D-Money API        → Update transactions (prepay_id, checkout_url)
5. User Pays on D-Money    → No database action
6. D-Money Sends Webhook   → webhook_events table + Update transactions
7. Update Subscription     → subscriptions table (status: active)
```

---

## 📊 DATA GENERATED AUTOMATICALLY

### Transaction Creation
```python
transaction_id = "TXN_" + timestamp + random_chars  
# Example: TXN_20260325100500ABC

order_id = "ORD" + timestamp + random_chars
# Example: ORD20260325100500XYZ
```

### D-Money Returns
```python
prepay_id = "wx789def456ghi123"
checkout_url = "https://pg.d-moneyservice.dj/paygate?prepay_id=..."
```

### Webhook Contains
```python
transId = "DMONEY_TXN_456789"
trade_status = "completed" | "failure" | "paying" | "expired"
```

---

## 🔐 ENVIRONMENT VARIABLES NEEDED

```bash
# D-Money Credentials
DMONEY_BASE_URL=https://pg.d-moneyservice.dj
DMONEY_X_APP_KEY=your_x_app_key_here
DMONEY_APP_SECRET=your_app_secret_here
DMONEY_APPID=your_merchant_id
DMONEY_MERCH_CODE=your_merchant_code
DMONEY_PRIVATE_KEY_B64=your_base64_private_key

# URLs
DMONEY_NOTIFY_URL=https://yourdomain.com/api/v1/webhooks/dmoney
DMONEY_REDIRECT_URL=https://yourdomain.com/payment/success

# Optional
DMONEY_BUSINESS_TYPE=OnlineMerchant
DMONEY_VERIFY_SSL=True
DMONEY_TIMEOUT_SEC=30
```

---

## 🎯 STATUS VALUES

### Subscription Status
```
trial       → User in trial period
active      → Subscription active (paid)
past_due    → Payment failed
canceled    → User canceled
expired     → Subscription ended
suspended   → Admin suspended
```

### Transaction Status
```
pending     → Waiting for payment
processing  → Payment in progress
completed   → Payment successful ✅
failed      → Payment failed ❌
canceled    → Transaction canceled
refunded    → Money returned
```

### Trade Status (from D-Money)
```
Paying      → User paid, awaiting confirmation
Expired     → Payment timeout
Completed   → Payment successful ✅
Failure     → Payment failed ❌
```

---

## 📝 SAMPLE DATABASE RECORDS

### After User Registers
```sql
users: id=5, email="alice@example.com", username="alice", status="active"
```

### After Plan Selection
```sql
subscriptions: id=1, user_id=5, plan_id=2, status="trial"
```

### After Transaction Created
```sql
transactions: id=1, transaction_id="TXN_20260325100500ABC", 
              order_id="ORD20260325100500XYZ", status="pending"
```

### After D-Money API Call
```sql
transactions: prepay_id="wx789def456ghi123", 
              checkout_url="https://pg.d-moneyservice.dj/..."
```

### After Payment Success
```sql
webhook_events: event_id="DMONEY_TXN_456789", processed=true
transactions: status="completed", paid_at="2026-03-25 10:15:30"
subscriptions: status="active"
```

---

## 🚀 API ENDPOINTS

### Your Backend
```
POST   /api/v1/auth/register           → Create user
POST   /api/v1/auth/login              → Login
GET    /api/v1/plans                   → List plans
POST   /api/v1/subscriptions           → Create subscription
POST   /api/v1/payments/create         → Create payment
POST   /api/v1/webhooks/dmoney         → D-Money webhook
GET    /api/v1/transactions/{id}       → Get transaction
```

### D-Money API
```
POST   /apiaccess/payment/gateway/payment/v1/token
POST   /apiaccess/payment/gateway/payment/v1/merchant/preOrder
POST   /apiaccess/payment/v1/merchant/queryOrder
```

---

## ✅ CHECKLIST

### Setup
- [ ] Database tables created
- [ ] D-Money credentials configured
- [ ] Webhook URL accessible from internet
- [ ] SSL certificate installed

### Testing
- [ ] User registration works
- [ ] Plan selection works
- [ ] Transaction creation works
- [ ] D-Money API call succeeds
- [ ] Checkout URL generated
- [ ] Webhook endpoint receives data
- [ ] Transaction status updates
- [ ] Subscription activates

### Security
- [ ] Passwords hashed (bcrypt)
- [ ] Webhook signature verified
- [ ] Duplicate webhooks prevented (idempotency)
- [ ] HTTPS enforced
- [ ] Environment variables secured

---

## 📞 HELP & RESOURCES

- **Integration Guide:** `DMONEY_INTEGRATION_GUIDE.md`
- **Database Schema:** `DMONEY_DATABASE_SCHEMA.md`
- **Input/Output Guide:** `DMONEY_INPUT_OUTPUT_GUIDE.md`
- **Implementation:** `app/services/dmoney_gateway_v2.py`
- **D-Money Support:** Contact D-Money team

---

**Print this page for quick reference during development!** 📄
