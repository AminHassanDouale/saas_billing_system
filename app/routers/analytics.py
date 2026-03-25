"""
Analytics Router - Reports and business metrics
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.services.analytics_service import AnalyticsService
from app.utils.auth import get_current_admin_user, get_current_merchant_user

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get complete dashboard summary with all key metrics
    
    Requires merchant or admin role
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_dashboard_summary()


@router.get("/revenue")
def get_revenue_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get revenue metrics for a date range
    
    - **start_date**: Start date (default: 30 days ago)
    - **end_date**: End date (default: now)
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_revenue_metrics(start_date, end_date)


@router.get("/mrr")
def get_mrr(
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get Monthly Recurring Revenue (MRR) breakdown
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_mrr()


@router.get("/churn")
def get_churn_metrics(
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get churn rate and related metrics
    
    - **start_date**: Start date (default: 30 days ago)
    - **end_date**: End date (default: now)
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_churn_metrics(start_date, end_date)


@router.get("/ltv")
def get_ltv(
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get Customer Lifetime Value (LTV) metrics
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_ltv()


@router.get("/revenue-trend")
def get_revenue_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    group_by: str = Query("day", regex="^(day|week|month)$", description="Grouping interval"),
    current_user: User = Depends(get_current_merchant_user),
    db: Session = Depends(get_db),
):
    """
    Get revenue trend over time
    
    - **days**: Number of days to look back (1-365)
    - **group_by**: Grouping interval (day/week/month)
    """
    analytics_service = AnalyticsService(db)
    return analytics_service.get_revenue_trend(days, group_by)
