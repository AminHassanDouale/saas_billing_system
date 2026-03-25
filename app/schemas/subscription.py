"""
Subscription Pydantic Schemas - Request/Response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.subscription import PlanInterval, SubscriptionStatus


# ── Subscription Plan Schemas ─────────────────────────────────────────────

class SubscriptionPlanBase(BaseModel):
    """Base subscription plan schema"""
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    currency: str = Field(default="DJF", max_length=3)
    interval: PlanInterval = PlanInterval.MONTHLY
    features: Optional[str] = None  # JSON string
    max_users: int = Field(default=1, ge=1)
    max_storage_gb: int = Field(default=10, ge=1)
    trial_period_days: int = Field(default=14, ge=0)


class SubscriptionPlanCreate(SubscriptionPlanBase):
    """Subscription plan creation schema"""
    pass


class SubscriptionPlanUpdate(BaseModel):
    """Subscription plan update schema"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    interval: Optional[PlanInterval] = None
    features: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_storage_gb: Optional[int] = Field(None, ge=1)
    trial_period_days: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class SubscriptionPlanResponse(SubscriptionPlanBase):
    """Subscription plan response schema"""
    id: int
    is_active: bool
    is_featured: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Subscription Schemas ──────────────────────────────────────────────────

class SubscriptionBase(BaseModel):
    """Base subscription schema"""
    plan_id: int
    auto_renew: bool = True


class SubscriptionCreate(SubscriptionBase):
    """Subscription creation schema"""
    pass


class SubscriptionUpdate(BaseModel):
    """Subscription update schema"""
    auto_renew: Optional[bool] = None
    status: Optional[SubscriptionStatus] = None


class SubscriptionResponse(BaseModel):
    """Subscription response schema"""
    id: int
    user_id: int
    plan_id: int
    status: SubscriptionStatus
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    current_period_start: datetime
    current_period_end: datetime
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    auto_renew: bool
    payment_retry_count: int
    next_payment_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionWithPlan(SubscriptionResponse):
    """Subscription response with plan details"""
    plan: SubscriptionPlanResponse


class SubscriptionCancelRequest(BaseModel):
    """Subscription cancellation request"""
    immediate: bool = False
    reason: Optional[str] = None


class SubscriptionStats(BaseModel):
    """Subscription statistics"""
    total_subscriptions: int
    active_subscriptions: int
    trial_subscriptions: int
    canceled_subscriptions: int
    expired_subscriptions: int
    mrr: float  # Monthly Recurring Revenue
    churn_rate: float
