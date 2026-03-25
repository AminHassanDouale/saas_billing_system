"""
Payment Service - Business logic for payment processing
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transaction import Transaction, TransactionStatus, TransactionType, PaymentMethod
from app.models.subscription import Subscription
from app.models.user import User
from app.services.dmoney_gateway_v2 import DmoneyPaymentGateway
from app.config import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for managing payment operations"""

    def __init__(self, db: Session):
        self.db = db
        self.gateway = DmoneyPaymentGateway()

    def create_payment(
        self,
        user_id: int,
        amount: float,
        title: str,
        subscription_id: Optional[int] = None,
        currency: str = "DJF",
        timeout: str = "120m",
        language: str = "en",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict:
        """
        Create a new payment transaction
        
        Args:
            user_id: ID of the user making the payment
            amount: Payment amount
            title: Payment description
            subscription_id: Optional subscription this payment is for
            currency: Currency code (default: DJF)
            timeout: Payment timeout
            language: Checkout page language
            metadata: Additional metadata
            
        Returns:
            Dict containing transaction details and checkout URL
        """
        # Validate user exists
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Validate subscription if provided
        if subscription_id:
            subscription = self.db.query(Subscription).filter(
                Subscription.id == subscription_id,
                Subscription.user_id == user_id
            ).first()
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found or doesn't belong to user")

        try:
            # Create payment through D-Money gateway
            dmoney_response = self.gateway.create_payment(
                amount=amount,
                title=title,
                currency=currency,
                timeout=timeout,
                language=language,
            )

            # Calculate net amount (subtract estimated fees)
            # D-Money fees are typically 2-3%
            fee = amount * 0.025  # 2.5% fee estimate
            net_amount = amount - fee

            # Create transaction record
            transaction = Transaction(
                transaction_id=f"TXN_{dmoney_response['order_id']}",
                order_id=dmoney_response["order_id"],
                prepay_id=dmoney_response.get("prepay_id"),
                user_id=user_id,
                subscription_id=subscription_id,
                type=TransactionType.PAYMENT,
                status=TransactionStatus.PENDING,
                payment_method=PaymentMethod.DMONEY,
                amount=amount,
                currency=currency,
                fee=fee,
                net_amount=net_amount,
                title=title,
                checkout_url=dmoney_response.get("checkout_url"),
                redirect_url=settings.DMONEY_REDIRECT_URL,
                extra_data=json.dumps(metadata) if metadata else None,
                raw_response=json.dumps(dmoney_response.get("raw_response", {})),
            )

            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)

            logger.info(f"Payment created: {transaction.transaction_id} for user {user_id}")

            return {
                "success": True,
                "transaction_id": transaction.transaction_id,
                "order_id": transaction.order_id,
                "checkout_url": transaction.checkout_url,
                "amount": amount,
                "currency": currency,
                "status": transaction.status.value,
            }

        except Exception as e:
            logger.error(f"Payment creation failed: {str(e)}")
            self.db.rollback()
            raise

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        """Get transaction by ID"""
        return self.db.query(Transaction).filter(Transaction.id == transaction_id).first()

    def get_transaction_by_order_id(self, order_id: str) -> Optional[Transaction]:
        """Get transaction by D-Money order ID"""
        return self.db.query(Transaction).filter(Transaction.order_id == order_id).first()

    def mark_payment_completed(
        self,
        order_id: str,
        webhook_data: Optional[Dict] = None
    ) -> Transaction:
        """
        Mark a payment as completed
        
        Args:
            order_id: D-Money order ID
            webhook_data: Data from webhook
            
        Returns:
            Updated transaction
        """
        transaction = self.get_transaction_by_order_id(order_id)
        if not transaction:
            raise ValueError(f"Transaction with order_id {order_id} not found")

        transaction.mark_as_paid()
        transaction.webhook_received = True
        
        if webhook_data:
            transaction.webhook_data = json.dumps(webhook_data)

        self.db.commit()
        self.db.refresh(transaction)

        logger.info(f"Payment completed: {transaction.transaction_id}")

        return transaction

    def mark_payment_failed(
        self,
        order_id: str,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Transaction:
        """Mark a payment as failed"""
        transaction = self.get_transaction_by_order_id(order_id)
        if not transaction:
            raise ValueError(f"Transaction with order_id {order_id} not found")

        transaction.mark_as_failed(error_code, error_message)
        self.db.commit()
        self.db.refresh(transaction)

        logger.warning(f"Payment failed: {transaction.transaction_id} - {error_message}")

        return transaction

    def get_user_transactions(
        self,
        user_id: int,
        status: Optional[TransactionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Transaction]:
        """Get transactions for a user"""
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if status:
            query = query.filter(Transaction.status == status)
        
        return query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()

    def get_transaction_stats(self, user_id: Optional[int] = None) -> Dict:
        """Get transaction statistics"""
        query = self.db.query(Transaction)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)

        total = query.count()
        completed = query.filter(Transaction.status == TransactionStatus.COMPLETED).count()
        pending = query.filter(Transaction.status == TransactionStatus.PENDING).count()
        failed = query.filter(Transaction.status == TransactionStatus.FAILED).count()

        total_amount = self.db.query(
            Transaction
        ).filter(
            Transaction.status == TransactionStatus.COMPLETED
        )
        
        if user_id:
            total_amount = total_amount.filter(Transaction.user_id == user_id)

        amount_sum = sum(t.amount for t in total_amount.all())

        return {
            "total_transactions": total,
            "completed_transactions": completed,
            "pending_transactions": pending,
            "failed_transactions": failed,
            "total_amount": amount_sum,
        }
