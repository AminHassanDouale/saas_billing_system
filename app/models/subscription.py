"""
Subscription and Plan Models
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import enum

from app.database import Base


class PlanInterval(str, enum.Enum):
    """Billing interval for subscription plans"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class SubscriptionPlan(Base):
    """
    Subscription Plan model - Defines available billing plans
    """
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    
    # Pricing
    price = Column(Float, nullable=False)  # Price in DJF
    currency = Column(String(3), default="DJF", nullable=False)
    interval = Column(SQLEnum(PlanInterval), default=PlanInterval.MONTHLY, nullable=False)
    
    # Features
    features = Column(Text)  # JSON string of features
    max_users = Column(Integer, default=1)
    max_storage_gb = Column(Integer, default=10)
    
    # Trial
    trial_period_days = Column(Integer, default=14)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    def __repr__(self):
        return f"<SubscriptionPlan(id={self.id}, name='{self.name}', price={self.price})>"


class Subscription(Base):
    """
    Subscription model - User's active subscription
    """
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    
    # Status
    status = Column(SQLEnum(SubscriptionStatus), default=SubscriptionStatus.TRIAL, nullable=False)
    
    # Dates
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    
    # Billing
    auto_renew = Column(Boolean, default=True)
    payment_retry_count = Column(Integer, default=0)
    next_payment_date = Column(DateTime, nullable=True)
    
    # Metadata
    extra_data = Column(Text)  # JSON string for additional data
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    transactions = relationship("Transaction", back_populates="subscription")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, status='{self.status}')>"

    @property
    def is_trial(self) -> bool:
        """Check if subscription is in trial period"""
        return self.status == SubscriptionStatus.TRIAL

    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status in [SubscriptionStatus.TRIAL, SubscriptionStatus.ACTIVE]

    @property
    def days_until_renewal(self) -> int:
        """Calculate days until next renewal"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_expiring_soon(self) -> bool:
        """Check if subscription expires within 7 days"""
        return self.days_until_renewal <= 7

    def cancel(self, immediate: bool = False):
        """Cancel subscription"""
        self.status = SubscriptionStatus.CANCELED
        self.canceled_at = datetime.utcnow()
        self.auto_renew = False
        
        if immediate:
            self.ended_at = datetime.utcnow()
            self.current_period_end = datetime.utcnow()

    def renew(self, duration_days: int = 30):
        """Renew subscription for specified duration"""
        self.current_period_start = datetime.utcnow()
        self.current_period_end = datetime.utcnow() + timedelta(days=duration_days)
        self.status = SubscriptionStatus.ACTIVE
        self.payment_retry_count = 0
