"""
Subscription Service - Business logic for subscription management
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.subscription import (
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
    PlanInterval,
)
from app.models.user import User
from app.config import settings

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for managing subscriptions"""

    def __init__(self, db: Session):
        self.db = db

    def create_subscription(
        self,
        user_id: int,
        plan_id: int,
        auto_renew: bool = True,
        start_trial: bool = True,
    ) -> Subscription:
        """
        Create a new subscription for a user
        
        Args:
            user_id: User ID
            plan_id: Subscription plan ID
            auto_renew: Enable auto-renewal
            start_trial: Start with trial period
            
        Returns:
            Created subscription
        """
        # Validate user
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Validate plan
        plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.id == plan_id,
            SubscriptionPlan.is_active == True
        ).first()
        if not plan:
            raise ValueError(f"Plan {plan_id} not found or inactive")

        # Check if user already has an active subscription to this plan
        existing = self.db.query(Subscription).filter(
            Subscription.user_id == user_id,
            Subscription.plan_id == plan_id,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        ).first()
        
        if existing:
            raise ValueError(f"User already has an active subscription to this plan")

        now = datetime.utcnow()
        
        # Calculate trial period
        if start_trial and plan.trial_period_days > 0:
            trial_start = now
            trial_end = now + timedelta(days=plan.trial_period_days)
            current_period_start = trial_start
            current_period_end = trial_end
            status = SubscriptionStatus.TRIAL
        else:
            trial_start = None
            trial_end = None
            # Calculate billing period based on plan interval
            current_period_start = now
            if plan.interval == PlanInterval.MONTHLY:
                current_period_end = now + timedelta(days=30)
            elif plan.interval == PlanInterval.QUARTERLY:
                current_period_end = now + timedelta(days=90)
            elif plan.interval == PlanInterval.YEARLY:
                current_period_end = now + timedelta(days=365)
            else:
                current_period_end = now + timedelta(days=30)
            
            status = SubscriptionStatus.ACTIVE

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=status,
            trial_start=trial_start,
            trial_end=trial_end,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            auto_renew=auto_renew,
            next_payment_date=current_period_end if auto_renew and status == SubscriptionStatus.ACTIVE else None,
        )

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        logger.info(f"Subscription created: ID={subscription.id} for user {user_id}")

        return subscription

    def cancel_subscription(
        self,
        subscription_id: int,
        user_id: int,
        immediate: bool = False,
    ) -> Subscription:
        """
        Cancel a subscription
        
        Args:
            subscription_id: Subscription ID
            user_id: User ID (for authorization)
            immediate: Cancel immediately or at period end
            
        Returns:
            Canceled subscription
        """
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id,
            Subscription.user_id == user_id
        ).first()

        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        if subscription.status == SubscriptionStatus.CANCELED:
            raise ValueError("Subscription is already canceled")

        subscription.cancel(immediate=immediate)
        self.db.commit()
        self.db.refresh(subscription)

        logger.info(f"Subscription canceled: ID={subscription_id}, immediate={immediate}")

        return subscription

    def renew_subscription(self, subscription_id: int) -> Subscription:
        """
        Renew a subscription for another billing period
        
        Args:
            subscription_id: Subscription ID
            
        Returns:
            Renewed subscription
        """
        subscription = self.db.query(Subscription).filter(
            Subscription.id == subscription_id
        ).first()

        if not subscription:
            raise ValueError(f"Subscription {subscription_id} not found")

        # Get plan to determine renewal period
        plan = subscription.plan
        
        if plan.interval == PlanInterval.MONTHLY:
            duration_days = 30
        elif plan.interval == PlanInterval.QUARTERLY:
            duration_days = 90
        elif plan.interval == PlanInterval.YEARLY:
            duration_days = 365
        else:
            duration_days = 30

        subscription.renew(duration_days=duration_days)
        
        if subscription.auto_renew:
            subscription.next_payment_date = subscription.current_period_end

        self.db.commit()
        self.db.refresh(subscription)

        logger.info(f"Subscription renewed: ID={subscription_id}")

        return subscription

    def get_subscription(self, subscription_id: int) -> Optional[Subscription]:
        """Get subscription by ID"""
        return self.db.query(Subscription).filter(Subscription.id == subscription_id).first()

    def get_user_subscriptions(
        self,
        user_id: int,
        status: Optional[SubscriptionStatus] = None,
    ) -> List[Subscription]:
        """Get all subscriptions for a user"""
        query = self.db.query(Subscription).filter(Subscription.user_id == user_id)
        
        if status:
            query = query.filter(Subscription.status == status)
        
        return query.order_by(Subscription.created_at.desc()).all()

    def check_expired_subscriptions(self) -> List[Subscription]:
        """
        Check for expired subscriptions and update their status
        
        Returns:
            List of expired subscriptions
        """
        now = datetime.utcnow()
        
        # Find subscriptions that have passed their end date
        expired = self.db.query(Subscription).filter(
            Subscription.current_period_end < now,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
            Subscription.auto_renew == False
        ).all()

        for subscription in expired:
            subscription.status = SubscriptionStatus.EXPIRED
            subscription.ended_at = now

        if expired:
            self.db.commit()
            logger.info(f"Marked {len(expired)} subscriptions as expired")

        return expired

    def get_expiring_subscriptions(self, days: int = 7) -> List[Subscription]:
        """
        Get subscriptions expiring within specified days
        
        Args:
            days: Number of days to look ahead
            
        Returns:
            List of expiring subscriptions
        """
        now = datetime.utcnow()
        future = now + timedelta(days=days)

        return self.db.query(Subscription).filter(
            Subscription.current_period_end.between(now, future),
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL]),
            Subscription.auto_renew == True
        ).all()

    def get_subscription_stats(self) -> dict:
        """Get subscription statistics"""
        total = self.db.query(Subscription).count()
        active = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).count()
        trial = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.TRIAL
        ).count()
        canceled = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.CANCELED
        ).count()
        expired = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.EXPIRED
        ).count()

        # Calculate MRR (Monthly Recurring Revenue)
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).all()

        mrr = 0
        for sub in active_subscriptions:
            plan_price = sub.plan.price
            if sub.plan.interval == PlanInterval.MONTHLY:
                mrr += plan_price
            elif sub.plan.interval == PlanInterval.QUARTERLY:
                mrr += plan_price / 3
            elif sub.plan.interval == PlanInterval.YEARLY:
                mrr += plan_price / 12

        # Calculate churn rate
        churn_rate = (canceled / total * 100) if total > 0 else 0

        return {
            "total_subscriptions": total,
            "active_subscriptions": active,
            "trial_subscriptions": trial,
            "canceled_subscriptions": canceled,
            "expired_subscriptions": expired,
            "mrr": round(mrr, 2),
            "churn_rate": round(churn_rate, 2),
        }
