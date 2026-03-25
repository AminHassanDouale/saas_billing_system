"""
Main FastAPI Application
SaaS Billing System with D-Money Payment Gateway
"""

import logging
import time
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.routers import auth, users, subscriptions, payments, webhooks, analytics
from app.middleware.rate_limit import RateLimitMiddleware
from app.utils.logging_config import setup_logging, request_logger

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Create database tables (use Alembic in production)
    if settings.DEBUG:
        logger.warning("Debug mode: Creating database tables automatically")
        Base.metadata.create_all(bind=engine)
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    🚀 **SaaS Billing System with D-Money Payment Gateway**
    
    A production-ready billing and subscription management system featuring:
    
    - 🔐 **JWT Authentication** - Secure user authentication and authorization
    - 💳 **Payment Processing** - D-Money payment gateway integration
    - 📊 **Subscription Management** - Flexible plans with trials and auto-renewal
    - 🔔 **Webhooks** - Real-time payment status updates

    - 📈 **Analytics** - MRR, LTV, churn metrics, and revenue trends
    - 👥 **Multi-tenant** - User, merchant, and admin roles
    
    ## Authentication
    
    Most endpoints require authentication using JWT bearer tokens.
    
    1. Register: `POST /api/v1/auth/register`
    2. Login: `POST /api/v1/auth/login`
    3. Use the returned `access_token` in the Authorization header:
       ```
       Authorization: Bearer <access_token>
       ```
    
    ## Roles
    
    - **User**: Standard user with subscription access
    - **Merchant**: Can view analytics and reports
    - **Admin**: Full system access
    
    ## Payment Flow
    
    1. Create payment: `POST /api/v1/payments/create`
    2. Redirect user to `checkout_url`
    3. User completes payment on D-Money
    4. D-Money sends webhook to `/api/v1/webhooks/dmoney`
    5. System updates transaction status
    6. User redirected back to your application
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ── Middleware ─────────────────────────────────────────────────────────────

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
)

# Rate limiting middleware
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.RATE_LIMIT_PER_MINUTE)

# Trusted host middleware (production security)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"],  # Configure with your actual domains in production
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    await request_logger.log_request(request, response, duration)
    
    return response


# ── Exception Handlers ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """
    API root endpoint
    """
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "operational",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# ── Include Routers ────────────────────────────────────────────────────────

# Authentication
app.include_router(auth.router)

# Users
app.include_router(users.router)

# Subscriptions
app.include_router(subscriptions.router)

# Payments
app.include_router(payments.router)

# Webhooks
app.include_router(webhooks.router)

# Analytics
app.include_router(analytics.router)


# ── Startup Message ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting {settings.APP_NAME} on {settings.HOST}:{settings.PORT}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else settings.WORKERS,
    )
