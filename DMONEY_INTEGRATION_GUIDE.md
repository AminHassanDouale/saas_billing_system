# 📘 D-Money Payment Gateway Integration Guide

Based on **D-Money Payment Gateway API Documentation v2.1** (November 2024)

## 📋 Table of Contents

1. [Overview](#overview)
2. [API Flow](#api-flow)
3. [Implementation Updates](#implementation-updates)
4. [Complete Payment Flow](#complete-payment-flow)
5. [Webhook Implementation](#webhook-implementation)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The D-Money Payment Gateway integration follows a 5-step process:

```
┌─────────────────────────────────────────────────────────────┐
│  COMPLETE PAYMENT FLOW                                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: Generate Token                                      │
│           ↓                                                  │
│  Step 2: Create PreOrder (get prepay_id)                    │
│           ↓                                                  │
│  Step 3: Generate Checkout URL                              │
│           ↓                                                  │
│  Step 4: User Pays → D-Money sends Webhook                  │
│           ↓                                                  │
│  Step 5: Query Order Status (optional verification)          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 API Flow

### Step 1: Generate Authentication Token

**Endpoint Options** (try in order):
1. `POST /apiaccess/payment/gateway/payment/v1/token`
2. `POST /payment/gateway/payment/v1/token`

**Request:**
```json
{
  "appSecret": "your_app_secret_here"
}
```

**Headers:**
```json
{
  "X-APP-Key": "your_x_app_key",
  "Content-Type": "application/json"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "code": "0",
  "message": "Success"
}
```

### Step 2: Create Payment Order (PreOrder)

**Endpoint Options** (try in order):
1. `POST /apiaccess/payment/gateway/payment/v1/merchant/preOrder`
2. `POST /payment/gateway/payment/v1/merchant/preOrder`

**Critical Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `appid` | String | ✅ | Merchant ID |
| `merch_code` | String | ✅ | Merchant code |
| `merch_order_id` | String | ✅ | Your order ID (letters, digits, underscores only) |
| `trade_type` | String | ✅ | Must be `"Checkout"` |
| `total_amount` | String | ✅ | Amount in integer format (e.g., "1000" for 1000 DJF) |
| `trans_currency` | String | ✅ | Currency code (DJF, USD, etc.) |
| `title` | String | ✅ | Payment description |
| `notify_url` | String | ✅ | Webhook callback URL |
| `redirect_url` | String | ✅ | User redirect after payment |
| `timeout_express` | String | ✅ | Payment timeout (e.g., "120m") |
| `business_type` | String | Optional | "OnlineMerchant" or "BuyGoods" |

**Signature Generation:**

1. **Exclude** from signing: `sign`, `sign_type`, `biz_content`
2. **Sort** parameters alphabetically
3. **Format**: `key1=value1&key2=value2&...`
4. **Sign** with RSA-PSS (SHA256 + MGF1)
5. **Encode** signature to Base64

**Example Signing String:**
```
appid=1293049431398401&business_type=OnlineMerchant&merch_code=9988&
merch_order_id=1685123456789&method=payment.preorder&nonce_str=abcd1234&
notify_url=https://yourdomain.com/webhooks/payment&redirect_url=https://yourdomain.com/success&
timeout_express=120m&timestamp=1685123456&title=Payment&total_amount=1000&
trade_type=Checkout&trans_currency=DJF&version=1.0
```

**Response:**
```json
{
  "code": "0",
  "message": "Success",
  "biz_content": {
    "prepay_id": "wx123456789abcdef",
    "order_id": "dmoney_order_12345",
    "status": "created"
  }
}
```

### Step 3: Generate Checkout URL

**Format:**
```
https://pg.d-moneyservice.dj:38443/payment/web/paygate?{signed_parameters}
```

**Required Parameters:**
- `appid`
- `merch_code`
- `nonce_str`
- `prepay_id` (from Step 2)
- `timestamp`
- `sign` (signature of all above parameters)
- `sign_type="SHA256WithRSA"`
- `version="1.0"`
- `trade_type="Checkout"`
- `language="en"` or `"fr"`

### Step 4: Query Order Status

**Endpoint:**
```
POST /apiaccess/payment/v1/merchant/queryOrder
```

**Request:**
```json
{
  "timestamp": "1685123456",
  "method": "payment.queryorder",
  "nonce_str": "abcd1234",
  "sign_type": "SHA256WithRSA",
  "sign": "signature_here",
  "version": "1.0",
  "biz_content": {
    "appid": "your_appid",
    "merch_code": "your_merchant_code",
    "merch_order_id": "your_order_id"
  }
}
```

**Response:**
```json
{
  "result": "SUCCESS",
  "code": "0",
  "biz_content": {
    "merch_order_id": "1685123456789",
    "order_status": "PAID",
    "payment_order_id": "dmoney_order_12345",
    "trans_time": "2024-05-27 14:30:25",
    "trans_currency": "DJF",
    "total_amount": "1000"
  }
}
```

### Step 5: Handle Webhooks

**Webhook Endpoint:** Your `notify_url` from Step 2

**Webhook Payload:**
```json
{
  "merch_order_id": "1685123456789",
  "trade_status": "completed",
  "transId": "dmoney_trans_12345",
  "total_amount": "1000",
  "trans_currency": "DJF",
  "callback_info": "your_custom_data",
  "timestamp": "1685123800",
  "sign": "signature_from_dmoney",
  "sign_type": "SHA256WithRSA"
}
```

**Trade Status Values:**
- `"Paying"` - User paid, awaiting confirmation
- `"Expired"` - Payment timeout
- `"Completed"` - Payment successful ✅
- `"Failure"` - Payment failed ❌

**Important:** Always verify webhook signature!

---

## 🔧 Implementation Updates

### Updated D-Money Gateway Service

The new implementation (`dmoney_gateway_v2.py`) includes:

✅ **Multiple endpoint fallbacks** (per documentation)
✅ **Complete signature generation** (RSA-PSS with SHA256 + MGF1)
✅ **Order query functionality**
✅ **Webhook signature verification framework**
✅ **Proper error handling**
✅ **Token management with auto-refresh**

### Key Changes from Previous Version

| Feature | Old | New |
|---------|-----|-----|
| Endpoints | Single endpoint | Multiple fallback endpoints |
| Order Query | ❌ Not implemented | ✅ Implemented |
| Webhook Verification | ❌ Missing | ✅ Framework ready |
| Signature Method | Basic | RSA-PSS with MGF1 (per spec) |
| Error Handling | Basic | Comprehensive |

---

## 🚀 Complete Payment Flow

### Backend Implementation

```python
from app.services.dmoney_gateway_v2 import DmoneyPaymentGateway

# Initialize gateway
gateway = DmoneyPaymentGateway()

# Create payment
payment_result = gateway.create_payment(
    amount=5000.0,              # Amount in DJF
    title="Subscription Payment",
    order_id="ORD20260325001",  # Optional - auto-generated if not provided
    currency="DJF",
    timeout="120m",
    notify_url="https://yourdomain.com/api/v1/webhooks/dmoney",
    redirect_url="https://yourdomain.com/payment/success",
    callback_info="subscription_id:123",  # Optional custom data
    language="en"  # or "fr"
)

# Returns:
{
    "success": True,
    "order_id": "ORD20260325001",
    "prepay_id": "wx123456789abcdef",
    "checkout_url": "https://pg.d-moneyservice.dj:38443/payment/web/paygate?...",
    "amount": 5000.0,
    "currency": "DJF"
}

# Redirect user to checkout_url
return redirect(payment_result["checkout_url"])
```

### Query Order Status

```python
# Check payment status
status = gateway.query_order("ORD20260325001")

print(status["biz_content"]["order_status"])  # PAID, UNPAID, etc.
```

---

## 🔔 Webhook Implementation

### Webhook Endpoint

```python
from fastapi import Request, HTTPException
from app.services.dmoney_gateway_v2 import DmoneyPaymentGateway

@app.post("/api/v1/webhooks/dmoney")
async def handle_dmoney_webhook(request: Request):
    """
    Handle D-Money payment webhooks
    MUST be accessible from external networks
    """
    try:
        # Parse webhook data
        webhook_data = await request.json()
        
        # Extract signature
        signature = webhook_data.get("sign")
        trade_status = webhook_data.get("trade_status")
        merchant_order_id = webhook_data.get("merch_order_id")
        
        # Verify signature (implement with D-Money public key)
        gateway = DmoneyPaymentGateway()
        if not gateway.verify_webhook_signature(webhook_data, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Check for duplicate processing (idempotency)
        existing_log = db.query(OrderLog).filter(
            OrderLog.order_id == merchant_order_id,
            OrderLog.type == "payment_notification",
            OrderLog.data["transId"].astext == webhook_data.get("transId")
        ).first()
        
        if existing_log:
            return {"success": True, "message": "Already processed"}
        
        # Process based on trade_status
        if trade_status == "completed":
            # Update transaction status
            transaction = db.query(Transaction).filter(
                Transaction.order_id == merchant_order_id
            ).first()
            
            if transaction:
                transaction.status = TransactionStatus.COMPLETED
                transaction.paid_at = datetime.utcnow()
                transaction.webhook_data = json.dumps(webhook_data)
                
                # Activate subscription if applicable
                if transaction.subscription_id:
                    subscription = transaction.subscription
                    subscription.status = SubscriptionStatus.ACTIVE
                
                db.commit()
                
                # Send confirmation email (async)
                send_payment_receipt_task.delay(transaction.id)
        
        elif trade_status == "failure":
            # Handle failed payment
            transaction = db.query(Transaction).filter(
                Transaction.order_id == merchant_order_id
            ).first()
            
            if transaction:
                transaction.status = TransactionStatus.FAILED
                transaction.failed_at = datetime.utcnow()
                transaction.error_message = webhook_data.get("error_message")
                db.commit()
        
        # Log webhook event
        log = OrderLog(
            order_id=merchant_order_id,
            message=f"Webhook received: {trade_status}",
            data=webhook_data,
            type="payment_notification"
        )
        db.add(log)
        db.commit()
        
        return {"success": True, "message": "Webhook processed successfully"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return {"error": "Processing failed", "message": str(e)}
```

### Idempotency Handling

**Critical:** Webhooks may be sent multiple times. Always check for duplicates!

```python
# Check if already processed
if db.query(WebhookEvent).filter(
    WebhookEvent.event_id == webhook_data["transId"],
    WebhookEvent.processed == True
).first():
    return {"message": "Already processed"}
```

---

## 🧪 Testing

### Test Environment

```bash
# .env for testing
DMONEY_BASE_URL=https://pgtest.d-money.dj:38443
DMONEY_X_APP_KEY=test_key_from_dmoney
DMONEY_APP_SECRET=test_secret_from_dmoney
# ... other test credentials from D-Money
```

### Test Flow

1. **Generate Token**
```python
gateway = DmoneyPaymentGateway()
token_response = gateway.get_token()
print(f"Token: {token_response['token'][:20]}...")
```

2. **Create Test Payment**
```python
payment = gateway.create_payment(
    amount=100.0,  # Test amount
    title="Test Payment",
    currency="DJF"
)
print(f"Checkout URL: {payment['checkout_url']}")
```

3. **Simulate Webhook** (use tools like Postman)
```bash
curl -X POST https://yourdomain.com/api/v1/webhooks/dmoney \
  -H "Content-Type: application/json" \
  -d '{
    "merch_order_id": "ORD20260325001",
    "trade_status": "completed",
    "transId": "test_trans_123",
    "total_amount": "100",
    "trans_currency": "DJF",
    "timestamp": "1685123800",
    "sign": "test_signature"
  }'
```

4. **Query Order Status**
```python
status = gateway.query_order("ORD20260325001")
print(f"Status: {status['biz_content']['order_status']}")
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Token Generation Fails (401/403)

**Solutions:**
- ✅ Verify `X-APP-Key` matches your D-Money account
- ✅ Verify `appSecret` is correct
- ✅ Try alternative endpoint paths
- ✅ Check SSL certificate validity

#### 2. Signature Verification Fails

**Solutions:**
- ✅ Ensure parameters are sorted alphabetically
- ✅ Exclude `sign`, `sign_type`, `biz_content` from signing
- ✅ Verify RSA private key format (Base64-encoded DER)
- ✅ Check signature algorithm (RSA-PSS with SHA256 + MGF1)
- ✅ Log signing string for debugging

#### 3. Webhooks Not Received

**Solutions:**
- ✅ Ensure webhook URL is accessible from external networks
- ✅ Use HTTPS (not HTTP) for webhook endpoint
- ✅ Check server firewall rules
- ✅ Verify SSL certificate is valid
- ✅ Test webhook endpoint manually with curl
- ✅ Check server logs for incoming requests

#### 4. Order Query Returns "Order Not Found"

**Solutions:**
- ✅ Verify `merch_order_id` matches exactly
- ✅ Ensure order was successfully created (check PreOrder response)
- ✅ Wait a few seconds after creation before querying
- ✅ Check order status in D-Money merchant dashboard

### Debug Logging

Enable detailed logging:

```python
import logging

logging.getLogger("DmoneyGateway").setLevel(logging.DEBUG)
```

This will log:
- API URLs being tried
- Signing strings
- Request/response payloads (sanitized)
- Token expiry times

---

## 📚 Additional Resources

- **Official Documentation:** D-Money Payment Gateway API Documentation v2.1
- **Support:** Contact D-Money support team
- **Merchant Dashboard:** Access your D-Money merchant account

---

## ✅ Checklist for Go-Live

Before deploying to production:

- [ ] All credentials updated in production `.env`
- [ ] SSL certificate installed and verified
- [ ] Webhook endpoint accessible from internet
- [ ] Webhook signature verification implemented
- [ ] Idempotency handling in place
- [ ] Error logging configured
- [ ] Payment flow tested end-to-end
- [ ] Refund workflow tested
- [ ] Email notifications configured
- [ ] Database backups enabled
- [ ] Monitoring alerts configured

---

**Need Help?** Check the main documentation or contact D-Money support team.
