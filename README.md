# SaaS Billing System with D-Money Payment Gateway

A production-ready SaaS billing system built with FastAPI, MySQL, and D-Money payment gateway integration.

## 🚀 Features

- ✅ **User & Merchant Management** - Multi-tenant architecture
- ✅ **Subscription Plans** - Flexible billing plans with trial periods
- ✅ **Payment Processing** - D-Money gateway integration
- ✅ **Webhook Handling** - Real-time payment status updates
- ✅ **Transaction History** - Complete audit trail
- ✅ **Refund Processing** - Automated refund management
- ✅ **Analytics Dashboard** - Revenue, MRR, churn metrics
- ✅ **JWT Authentication** - Secure API access
- ✅ **Auto Documentation** - Interactive API docs with Swagger

## 📁 Project Structure

```
saas-billing-system/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subscription.py
│   │   ├── transaction.py
│   │   └── refund.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── subscription.py
│   │   └── transaction.py
│   ├── routers/                # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── subscriptions.py
│   │   ├── payments.py
│   │   ├── webhooks.py
│   │   ├── transactions.py
│   │   ├── refunds.py
│   │   └── analytics.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── dmoney_gateway.py
│   │   ├── payment_service.py
│   │   ├── subscription_service.py
│   │   ├── webhook_service.py
│   │   └── analytics_service.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── auth.py
│       ├── security.py
│       └── helpers.py
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_payments.py
│   └── test_webhooks.py
├── .env.example                # Environment variables template
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Docker setup
├── Dockerfile
├── alembic.ini                 # Alembic configuration
└── README.md
```

## 🛠️ Installation

### Prerequisites

- Python 3.9+
- MySQL 8.0+
- Docker (optional)

### Option 1: Local Setup

1. **Clone and setup**
```bash
cd saas-billing-system
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Initialize database**
```bash
# Create MySQL database
mysql -u root -p -e "CREATE DATABASE saas_billing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Run migrations
alembic upgrade head
```

4. **Start the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker Setup

```bash
docker-compose up -d
```

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔑 Environment Variables

See `.env.example` for all required configuration.

Key variables:
- `DATABASE_URL` - MySQL connection string
- `SECRET_KEY` - JWT secret key
- `DMONEY_*` - D-Money gateway credentials

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📊 Database Schema

### Users
- Multi-tenant support
- Role-based access (admin, merchant, user)

### Subscriptions
- Flexible billing plans
- Trial periods
- Auto-renewal

### Transactions
- Complete payment history
- Status tracking
- Webhook events

### Refunds
- Automated processing
- Partial/full refunds
- Audit trail

## 🔄 Webhook Integration

D-Money webhooks are automatically processed at:
```
POST /api/v1/webhooks/dmoney
```

Configure this URL in your D-Money merchant dashboard.

## 📈 Analytics Endpoints

- Monthly Recurring Revenue (MRR)
- Customer Lifetime Value (LTV)
- Churn rate
- Revenue trends
- Subscription metrics

## 🚀 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring (Sentry, etc.)
- [ ] Enable rate limiting
- [ ] Review security headers

## 📝 License

MIT License

## 🤝 Support

For issues or questions, please contact support.
