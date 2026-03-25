# 🚀 Quick Start Guide

Get your SaaS Billing System up and running in 5 minutes!

## Prerequisites

- Python 3.9+
- MySQL 8.0+ (or Docker)
- Git

## Option 1: Docker Setup (Recommended)

### 1. Clone and Configure

```bash
cd saas-billing-system
cp .env.example .env
```

### 2. Edit .env File

Update the following D-Money credentials in `.env`:

```bash
DMONEY_X_APP_KEY=your_x_app_key_here
DMONEY_APP_SECRET=your_app_secret_here
DMONEY_APPID=your_app_id_here
DMONEY_MERCH_CODE=your_merchant_code_here
DMONEY_PRIVATE_KEY_B64=your_base64_encoded_private_key_here
DMONEY_NOTIFY_URL=https://yourdomain.com/api/v1/webhooks/dmoney
DMONEY_REDIRECT_URL=https://yourdomain.com/payment/success
```

### 3. Start with Docker

```bash
docker-compose up -d
```

### 4. Run Migrations and Seed Data

```bash
docker-compose exec app alembic upgrade head
docker-compose exec app python scripts/seed_data.py
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **phpMyAdmin**: http://localhost:8080 (optional)

## Option 2: Local Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup MySQL Database

```bash
mysql -u root -p -e "CREATE DATABASE saas_billing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Seed Sample Data

```bash
python scripts/seed_data.py
```

### 7. Start the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🎯 Test the API

### 1. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@saas.com",
    "password": "User123!"
  }'
```

### 2. Get Available Plans

```bash
curl http://localhost:8000/api/v1/subscriptions/plans
```

### 3. Subscribe to a Plan

```bash
curl -X POST http://localhost:8000/api/v1/subscriptions/subscribe \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": 1,
    "auto_renew": true
  }'
```

### 4. Create a Payment

```bash
curl -X POST http://localhost:8000/api/v1/payments/create \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 5000,
    "title": "Subscription Payment",
    "currency": "DJF"
  }'
```

## 📝 Sample Credentials

After seeding, you can login with:

- **Admin**: admin@saas.com / Admin123!
- **Merchant**: merchant@saas.com / Merchant123!
- **User**: user@saas.com / User123!

## 🔗 Important Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token

### Subscriptions
- `GET /api/v1/subscriptions/plans` - List all plans
- `POST /api/v1/subscriptions/subscribe` - Subscribe to a plan
- `GET /api/v1/subscriptions/my-subscriptions` - Get user's subscriptions
- `POST /api/v1/subscriptions/{id}/cancel` - Cancel subscription

### Payments
- `POST /api/v1/payments/create` - Create a payment
- `GET /api/v1/payments/transactions` - Get transaction history
- `GET /api/v1/payments/stats` - Get payment statistics

### Webhooks
- `POST /api/v1/webhooks/dmoney` - D-Money webhook endpoint

### Analytics (Admin/Merchant)
- `GET /api/v1/analytics/dashboard` - Dashboard summary
- `GET /api/v1/analytics/revenue` - Revenue metrics
- `GET /api/v1/analytics/mrr` - Monthly Recurring Revenue
- `GET /api/v1/analytics/churn` - Churn metrics

## 🔧 Common Tasks

### Run Tests

```bash
pytest tests/ -v
```

### Run Database Migrations

```bash
alembic upgrade head
```

### Create New Migration

```bash
alembic revision --autogenerate -m "description"
```

### Reset Database

```bash
make db-reset  # or manually drop and recreate
```

## 🐛 Troubleshooting

### Database Connection Error

Ensure MySQL is running and credentials in `.env` are correct.

### Migration Error

```bash
alembic downgrade -1
alembic upgrade head
```

### Port Already in Use

Change the port in `.env` or `docker-compose.yml`:

```bash
PORT=8001
```

## 📚 Next Steps

1. **Configure D-Money Webhook**: Update your D-Money merchant dashboard with your webhook URL
2. **Setup SSL**: Configure HTTPS for production
3. **Email Notifications**: Configure SMTP settings for email notifications
4. **Monitoring**: Set up logging and monitoring tools
5. **Deploy**: Deploy to your preferred cloud platform

## 🆘 Need Help?

- Check the full documentation in `README.md`
- View API documentation at `/docs`
- Review example tests in `tests/` directory

Happy coding! 🎉
