"""
Application Configuration
Loads settings from environment variables with validation
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # ── Application ────────────────────────────────────────────────────────
    APP_NAME: str = "SaaS Billing System"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ── Security ───────────────────────────────────────────────────────────
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Server ─────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # ── CORS ───────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: List[str] = ["*"]
    CORS_HEADERS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", "CORS_METHODS", "CORS_HEADERS", mode="before")
    @classmethod
    def parse_list_fields(cls, v):
        if isinstance(v, str):
            return [item.strip() for item in v.split(",")]
        return v

    # ── D-Money Gateway ────────────────────────────────────────────────────
    DMONEY_BASE_URL: str
    DMONEY_X_APP_KEY: str
    DMONEY_APP_SECRET: str
    DMONEY_APPID: str
    DMONEY_MERCH_CODE: str
    DMONEY_BUSINESS_TYPE: str = "OnlineMerchant"
    DMONEY_PRIVATE_KEY_B64: str
    DMONEY_PUBLIC_KEY_B64: Optional[str] = None
    DMONEY_NOTIFY_URL: str
    DMONEY_REDIRECT_URL: str
    DMONEY_CHECKOUT_BASE_URL: str = "https://pg.d-moneyservice.dj/payment/web/paygate"
    DMONEY_VERIFY_SSL: bool = True
    DMONEY_TIMEOUT_SEC: int = 30
    DMONEY_LOG_LEVEL: str = "INFO"

    # ── Redis & Celery ─────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # ── Email ──────────────────────────────────────────────────────────────
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_FROM_NAME: str = "SaaS Billing System"

    # ── Logging ────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # ── Subscription ───────────────────────────────────────────────────────
    TRIAL_PERIOD_DAYS: int = 14
    GRACE_PERIOD_DAYS: int = 3
    PAYMENT_RETRY_ATTEMPTS: int = 3

    # ── Security Limits ────────────────────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30

    # ── Webhooks ───────────────────────────────────────────────────────────
    WEBHOOK_SECRET: str = secrets.token_urlsafe(32)
    WEBHOOK_TIMEOUT_SECONDS: int = 10

    # ── Frontend URLs ──────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"
    PAYMENT_SUCCESS_URL: str = "http://localhost:3000/payment/success"
    PAYMENT_CANCEL_URL: str = "http://localhost:3000/payment/cancel"

    # ── Analytics ──────────────────────────────────────────────────────────
    ANALYTICS_RETENTION_DAYS: int = 365
    METRICS_CACHE_TTL: int = 3600

    # ── Feature Flags ──────────────────────────────────────────────────────
    ENABLE_REFUNDS: bool = True
    ENABLE_ANALYTICS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_WEBHOOKS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
