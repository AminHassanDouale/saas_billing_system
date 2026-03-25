"""
Celery Tasks for Background Processing
"""

from celery import Celery
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.services.email_service import EmailService
from app.services.subscription_service import SubscriptionService
from app.services.webhook_service import WebhookService
from app.models.user import User
from app.models.subscription import Subscription
from app.models.transaction import Transaction

# Initialize Celery
celery_app = Celery(
    'saas_billing',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
)


def get_db() -> Session:
    """Get database session"""
    return SessionLocal()


@celery_app.task(name='send_welcome_email')
def send_welcome_email_task(user_id: int):
    """
    Send welcome email to new user (background task)
    
    Args:
        user_id: User ID
    """
    db = get_db()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            email_service = EmailService()
            email_service.send_welcome_email(user)
    finally:
        db.close()


@celery_app.task(name='send_payment_receipt')
def send_payment_receipt_task(transaction_id: int):
    """
    Send payment receipt email (background task)
    
    Args:
        transaction_id: Transaction ID
    """
    db = get_db()
    try:
        transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if transaction:
            user = transaction.user
            email_service = EmailService()
            email_service.send_payment_receipt(user, transaction)
    finally:
        db.close()


@celery_app.task(name='send_subscription_confirmation')
def send_subscription_confirmation_task(subscription_id: int):
    """
    Send subscription confirmation email (background task)
    
    Args:
        subscription_id: Subscription ID
    """
    db = get_db()
    try:
        subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
        if subscription:
            user = subscription.user
            email_service = EmailService()
            email_service.send_subscription_confirmation(user, subscription)
    finally:
        db.close()


@celery_app.task(name='check_expired_subscriptions')
def check_expired_subscriptions_task():
    """
    Check for expired subscriptions and update their status
    Runs periodically (e.g., daily)
    """
    db = get_db()
    try:
        subscription_service = SubscriptionService(db)
        expired = subscription_service.check_expired_subscriptions()
        return f"Marked {len(expired)} subscriptions as expired"
    finally:
        db.close()


@celery_app.task(name='send_expiring_subscription_reminders')
def send_expiring_subscription_reminders_task():
    """
    Send reminders for subscriptions expiring soon
    Runs daily
    """
    db = get_db()
    try:
        subscription_service = SubscriptionService(db)
        email_service = EmailService()
        
        # Get subscriptions expiring in 7 days
        expiring_soon = subscription_service.get_expiring_subscriptions(days=7)
        
        count = 0
        for subscription in expiring_soon:
            user = subscription.user
            days_left = subscription.days_until_renewal
            
            if email_service.send_subscription_expiring(user, subscription, days_left):
                count += 1
        
        return f"Sent {count} expiring subscription reminders"
    finally:
        db.close()


@celery_app.task(name='retry_failed_webhooks')
def retry_failed_webhooks_task():
    """
    Retry processing failed webhooks
    Runs periodically (e.g., every hour)
    """
    db = get_db()
    try:
        webhook_service = WebhookService(db)
        retried = webhook_service.retry_failed_webhooks(max_retries=3)
        return f"Retried {retried} failed webhooks"
    finally:
        db.close()


@celery_app.task(name='cleanup_old_webhook_events')
def cleanup_old_webhook_events_task(days: int = 90):
    """
    Clean up old webhook events
    
    Args:
        days: Delete events older than this many days
    """
    from app.models.transaction import WebhookEvent
    
    db = get_db()
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old processed webhook events
        deleted = db.query(WebhookEvent).filter(
            WebhookEvent.received_at < cutoff_date,
            WebhookEvent.processed == True
        ).delete()
        
        db.commit()
        return f"Deleted {deleted} old webhook events"
    finally:
        db.close()


@celery_app.task(name='generate_daily_report')
def generate_daily_report_task():
    """
    Generate daily analytics report
    Can be sent to admins via email
    """
    from app.services.analytics_service import AnalyticsService
    
    db = get_db()
    try:
        analytics_service = AnalyticsService(db)
        
        # Get yesterday's metrics
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        revenue = analytics_service.get_revenue_metrics(start_of_day, end_of_day)
        mrr = analytics_service.get_mrr()
        
        report = {
            'date': yesterday.strftime('%Y-%m-%d'),
            'revenue': revenue,
            'mrr': mrr,
        }
        
        # TODO: Send report via email to admins
        
        return f"Daily report generated for {yesterday.strftime('%Y-%m-%d')}"
    finally:
        db.close()


# Periodic tasks configuration
celery_app.conf.beat_schedule = {
    'check-expired-subscriptions-daily': {
        'task': 'check_expired_subscriptions',
        'schedule': 86400.0,  # Every 24 hours
    },
    'send-expiring-reminders-daily': {
        'task': 'send_expiring_subscription_reminders',
        'schedule': 86400.0,  # Every 24 hours
    },
    'retry-failed-webhooks-hourly': {
        'task': 'retry_failed_webhooks',
        'schedule': 3600.0,  # Every hour
    },
    'cleanup-old-webhooks-weekly': {
        'task': 'cleanup_old_webhook_events',
        'schedule': 604800.0,  # Every 7 days
        'args': (90,)  # Delete events older than 90 days
    },
    'generate-daily-report': {
        'task': 'generate_daily_report',
        'schedule': 86400.0,  # Every 24 hours
    },
}
