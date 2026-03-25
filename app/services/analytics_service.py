"""
Analytics Service - Generate reports and metrics
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionStatus
from app.models.subscription import Subscription, SubscriptionStatus, PlanInterval
from app.models.user import User
from app.models.refund import Refund, RefundStatus

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for generating analytics and reports"""

    def __init__(self, db: Session):
        self.db = db

    def get_revenue_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Get revenue metrics for a date range
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Revenue metrics dictionary
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Total revenue (completed transactions)
        revenue_query = self.db.query(
            func.sum(Transaction.amount).label('total'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.created_at.between(start_date, end_date)
        ).first()

        total_revenue = revenue_query.total or 0
        transaction_count = revenue_query.count or 0

        # Total fees
        fees = self.db.query(
            func.sum(Transaction.fee)
        ).filter(
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.created_at.between(start_date, end_date)
        ).scalar() or 0

        # Net revenue
        net_revenue = total_revenue - fees

        # Average transaction value
        avg_transaction = total_revenue / transaction_count if transaction_count > 0 else 0

        # Refunds
        refunds = self.db.query(
            func.sum(Refund.refund_amount)
        ).filter(
            Refund.status == RefundStatus.COMPLETED,
            Refund.created_at.between(start_date, end_date)
        ).scalar() or 0

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_revenue": round(total_revenue, 2),
            "net_revenue": round(net_revenue, 2),
            "total_fees": round(fees, 2),
            "total_refunds": round(refunds, 2),
            "transaction_count": transaction_count,
            "average_transaction_value": round(avg_transaction, 2),
        }

    def get_mrr(self) -> Dict:
        """
        Calculate Monthly Recurring Revenue (MRR)
        
        Returns:
            MRR breakdown by plan
        """
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status == SubscriptionStatus.ACTIVE
        ).all()

        total_mrr = 0
        mrr_by_plan = {}

        for sub in active_subscriptions:
            plan = sub.plan
            plan_price = plan.price

            # Normalize to monthly
            if plan.interval == PlanInterval.MONTHLY:
                monthly_value = plan_price
            elif plan.interval == PlanInterval.QUARTERLY:
                monthly_value = plan_price / 3
            elif plan.interval == PlanInterval.YEARLY:
                monthly_value = plan_price / 12
            else:
                monthly_value = plan_price

            total_mrr += monthly_value

            # Track by plan
            if plan.name not in mrr_by_plan:
                mrr_by_plan[plan.name] = {
                    "count": 0,
                    "mrr": 0,
                }
            
            mrr_by_plan[plan.name]["count"] += 1
            mrr_by_plan[plan.name]["mrr"] += monthly_value

        return {
            "total_mrr": round(total_mrr, 2),
            "by_plan": {
                name: {
                    "count": data["count"],
                    "mrr": round(data["mrr"], 2),
                }
                for name, data in mrr_by_plan.items()
            },
        }

    def get_churn_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate churn rate and related metrics
        
        Args:
            start_date: Start date (default: 30 days ago)
            end_date: End date (default: now)
            
        Returns:
            Churn metrics dictionary
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Count active subscriptions at start of period
        active_start = self.db.query(Subscription).filter(
            Subscription.created_at < start_date,
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        ).count()

        # Count canceled subscriptions during period
        canceled = self.db.query(Subscription).filter(
            Subscription.canceled_at.between(start_date, end_date)
        ).count()

        # Calculate churn rate
        churn_rate = (canceled / active_start * 100) if active_start > 0 else 0

        # Count new subscriptions
        new_subscriptions = self.db.query(Subscription).filter(
            Subscription.created_at.between(start_date, end_date)
        ).count()

        # Net growth rate
        net_growth = new_subscriptions - canceled
        growth_rate = (net_growth / active_start * 100) if active_start > 0 else 0

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "active_at_start": active_start,
            "new_subscriptions": new_subscriptions,
            "canceled_subscriptions": canceled,
            "churn_rate": round(churn_rate, 2),
            "net_growth": net_growth,
            "growth_rate": round(growth_rate, 2),
        }

    def get_ltv(self) -> Dict:
        """
        Calculate Customer Lifetime Value (LTV)
        
        Returns:
            LTV metrics
        """
        # Average revenue per user
        total_users = self.db.query(User).count()
        
        total_revenue = self.db.query(
            func.sum(Transaction.amount)
        ).filter(
            Transaction.status == TransactionStatus.COMPLETED
        ).scalar() or 0

        arpu = total_revenue / total_users if total_users > 0 else 0

        # Average subscription lifetime (in months)
        avg_lifetime_query = self.db.query(
            func.avg(
                func.julianday(Subscription.ended_at) - func.julianday(Subscription.created_at)
            )
        ).filter(
            Subscription.ended_at.isnot(None)
        ).scalar()

        avg_lifetime_days = avg_lifetime_query or 90  # Default 90 days
        avg_lifetime_months = avg_lifetime_days / 30

        # Churn rate (last 30 days)
        churn = self.get_churn_metrics()
        churn_rate = churn["churn_rate"] / 100  # Convert to decimal

        # LTV = ARPU / Churn Rate
        ltv = (arpu / churn_rate) if churn_rate > 0 else arpu * avg_lifetime_months

        return {
            "arpu": round(arpu, 2),
            "average_lifetime_months": round(avg_lifetime_months, 2),
            "churn_rate": round(churn_rate * 100, 2),
            "ltv": round(ltv, 2),
        }

    def get_revenue_trend(
        self,
        days: int = 30,
        group_by: str = "day"  # day, week, month
    ) -> List[Dict]:
        """
        Get revenue trend over time
        
        Args:
            days: Number of days to look back
            group_by: Grouping interval (day/week/month)
            
        Returns:
            List of revenue data points
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Determine SQL date truncation based on grouping
        if group_by == "month":
            date_format = "%Y-%m"
        elif group_by == "week":
            date_format = "%Y-W%W"
        else:  # day
            date_format = "%Y-%m-%d"

        # Query transactions grouped by date
        results = self.db.query(
            func.strftime(date_format, Transaction.created_at).label('period'),
            func.sum(Transaction.amount).label('revenue'),
            func.count(Transaction.id).label('count')
        ).filter(
            Transaction.status == TransactionStatus.COMPLETED,
            Transaction.created_at.between(start_date, end_date)
        ).group_by('period').order_by('period').all()

        return [
            {
                "period": result.period,
                "revenue": round(result.revenue or 0, 2),
                "transaction_count": result.count or 0,
            }
            for result in results
        ]

    def get_dashboard_summary(self) -> Dict:
        """
        Get complete dashboard summary with all key metrics
        
        Returns:
            Dashboard summary dictionary
        """
        # Revenue metrics (last 30 days)
        revenue = self.get_revenue_metrics()

        # MRR
        mrr = self.get_mrr()

        # Churn metrics
        churn = self.get_churn_metrics()

        # LTV
        ltv = self.get_ltv()

        # User stats
        total_users = self.db.query(User).count()
        
        # Subscription stats
        active_subscriptions = self.db.query(Subscription).filter(
            Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
        ).count()

        # Recent transactions
        recent_transactions = self.db.query(Transaction).order_by(
            Transaction.created_at.desc()
        ).limit(10).count()

        return {
            "revenue": revenue,
            "mrr": mrr["total_mrr"],
            "mrr_by_plan": mrr["by_plan"],
            "churn": churn,
            "ltv": ltv,
            "total_users": total_users,
            "active_subscriptions": active_subscriptions,
            "recent_transactions_count": recent_transactions,
        }
