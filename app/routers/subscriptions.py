"""
Subscriptions Router - Subscription and plan management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.subscription import SubscriptionPlan, Subscription, SubscriptionStatus
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionWithPlan,
    SubscriptionCancelRequest,
    SubscriptionStats,
)
from app.services.subscription_service import SubscriptionService
from app.utils.auth import get_current_active_user, get_current_admin_user

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])


# ── Subscription Plans (Admin endpoints) ──────────────────────────────────

@router.post("/plans", response_model=SubscriptionPlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(
    plan_data: SubscriptionPlanCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Create a new subscription plan (Admin only)
    """
    # Check if plan name already exists
    existing = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.name == plan_data.name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan '{plan_data.name}' already exists"
        )
    
    plan = SubscriptionPlan(**plan_data.dict())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    
    return plan


@router.get("/plans", response_model=List[SubscriptionPlanResponse])
def get_plans(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """
    Get all subscription plans
    
    - **active_only**: Only return active plans (default: True)
    """
    query = db.query(SubscriptionPlan)
    
    if active_only:
        query = query.filter(SubscriptionPlan.is_active == True)
    
    plans = query.order_by(SubscriptionPlan.price).all()
    return plans


@router.get("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
):
    """
    Get specific subscription plan details
    """
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    return plan


@router.patch("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
def update_plan(
    plan_id: int,
    plan_data: SubscriptionPlanUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Update subscription plan (Admin only)
    """
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == plan_id).first()
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found"
        )
    
    # Update fields
    for field, value in plan_data.dict(exclude_unset=True).items():
        setattr(plan, field, value)
    
    db.commit()
    db.refresh(plan)
    
    return plan


# ── User Subscriptions ─────────────────────────────────────────────────────

@router.post("/subscribe", response_model=SubscriptionWithPlan, status_code=status.HTTP_201_CREATED)
def subscribe(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Subscribe to a plan
    
    - **plan_id**: ID of the plan to subscribe to
    - **auto_renew**: Enable auto-renewal (default: True)
    """
    subscription_service = SubscriptionService(db)
    
    try:
        subscription = subscription_service.create_subscription(
            user_id=current_user.id,
            plan_id=subscription_data.plan_id,
            auto_renew=subscription_data.auto_renew,
            start_trial=True,  # Always start with trial if available
        )
        
        db.refresh(subscription)
        return subscription
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my-subscriptions", response_model=List[SubscriptionWithPlan])
def get_my_subscriptions(
    status_filter: Optional[SubscriptionStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's subscriptions
    
    - **status_filter**: Optional filter by subscription status
    """
    subscription_service = SubscriptionService(db)
    subscriptions = subscription_service.get_user_subscriptions(
        user_id=current_user.id,
        status=status_filter,
    )
    
    return subscriptions


@router.get("/{subscription_id}", response_model=SubscriptionWithPlan)
def get_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get specific subscription details
    """
    subscription_service = SubscriptionService(db)
    subscription = subscription_service.get_subscription(subscription_id)
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    # Verify subscription belongs to user
    if subscription.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this subscription"
        )
    
    return subscription


@router.post("/{subscription_id}/cancel", response_model=SubscriptionResponse)
def cancel_subscription(
    subscription_id: int,
    cancel_data: SubscriptionCancelRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Cancel a subscription
    
    - **immediate**: Cancel immediately or at period end
    - **reason**: Optional cancellation reason
    """
    subscription_service = SubscriptionService(db)
    
    try:
        subscription = subscription_service.cancel_subscription(
            subscription_id=subscription_id,
            user_id=current_user.id,
            immediate=cancel_data.immediate,
        )
        
        return subscription
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{subscription_id}/renew", response_model=SubscriptionResponse)
def renew_subscription(
    subscription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Manually renew a subscription
    
    Note: Auto-renewal subscriptions renew automatically upon payment
    """
    subscription_service = SubscriptionService(db)
    
    # Verify subscription belongs to user
    subscription = subscription_service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    if subscription.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to renew this subscription"
        )
    
    try:
        renewed = subscription_service.renew_subscription(subscription_id)
        return renewed
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/stats/overview", response_model=SubscriptionStats)
def get_subscription_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get subscription statistics (Admin only)
    """
    subscription_service = SubscriptionService(db)
    stats = subscription_service.get_subscription_stats()
    
    return SubscriptionStats(**stats)
