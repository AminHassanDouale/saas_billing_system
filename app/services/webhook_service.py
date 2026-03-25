"""
Webhook Service - Process D-Money payment notifications
"""

import json
import hmac
import hashlib
import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.transaction import WebhookEvent, Transaction, TransactionStatus
from app.services.payment_service import PaymentService
from app.services.subscription_service import SubscriptionService
from app.config import settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for processing webhooks from D-Money"""

    def __init__(self, db: Session):
        self.db = db
        self.payment_service = PaymentService(db)
        self.subscription_service = SubscriptionService(db)

    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature for security
        
        Args:
            payload: Raw webhook payload
            signature: Signature from webhook header
            
        Returns:
            True if signature is valid
        """
        if not settings.WEBHOOK_SECRET:
            logger.warning("WEBHOOK_SECRET not configured - skipping signature verification")
            return True

        expected_signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    def process_webhook(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> WebhookEvent:
        """
        Process incoming webhook from D-Money
        
        Args:
            event_id: Unique event ID
            event_type: Type of webhook event
            payload: Webhook payload data
            
        Returns:
            Created webhook event record
        """
        # Check if webhook already processed
        existing = self.db.query(WebhookEvent).filter(
            WebhookEvent.event_id == event_id
        ).first()

        if existing:
            logger.info(f"Webhook {event_id} already processed, skipping")
            return existing

        # Extract order ID from payload
        order_id = payload.get("order_id") or payload.get("merch_order_id")

        # Create webhook event record
        webhook_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            order_id=order_id,
            payload=json.dumps(payload),
            processed=False,
        )

        self.db.add(webhook_event)
        self.db.commit()
        self.db.refresh(webhook_event)

        # Process the webhook based on type
        try:
            self._handle_webhook_event(webhook_event, payload)
            webhook_event.processed = True
            webhook_event.processed_at = datetime.utcnow()
            logger.info(f"Webhook {event_id} processed successfully")
        except Exception as e:
            webhook_event.error = str(e)
            webhook_event.retry_count += 1
            logger.error(f"Webhook {event_id} processing failed: {str(e)}")
            raise
        finally:
            self.db.commit()
            self.db.refresh(webhook_event)

        return webhook_event

    def _handle_webhook_event(
        self,
        webhook_event: WebhookEvent,
        payload: Dict[str, Any]
    ):
        """
        Handle specific webhook event types
        
        Args:
            webhook_event: Webhook event record
            payload: Webhook payload
        """
        event_type = webhook_event.event_type.lower()
        order_id = webhook_event.order_id

        if not order_id:
            raise ValueError("order_id not found in webhook payload")

        # Find the transaction
        transaction = self.payment_service.get_transaction_by_order_id(order_id)
        if not transaction:
            raise ValueError(f"Transaction with order_id {order_id} not found")

        # Link webhook to transaction
        webhook_event.transaction_id = transaction.id

        # Process based on event type
        if event_type in ["payment.success", "payment.completed", "trade.success"]:
            self._handle_payment_success(transaction, payload)
        
        elif event_type in ["payment.failed", "payment.error"]:
            self._handle_payment_failed(transaction, payload)
        
        elif event_type in ["payment.refunded", "refund.success"]:
            self._handle_payment_refunded(transaction, payload)
        
        elif event_type in ["payment.pending", "payment.processing"]:
            self._handle_payment_pending(transaction, payload)
        
        else:
            logger.warning(f"Unknown webhook event type: {event_type}")

    def _handle_payment_success(
        self,
        transaction: Transaction,
        payload: Dict[str, Any]
    ):
        """Handle successful payment webhook"""
        logger.info(f"Processing payment success for transaction {transaction.id}")

        # Update transaction status
        self.payment_service.mark_payment_completed(
            transaction.order_id,
            webhook_data=payload
        )

        # If this is a subscription payment, activate/renew the subscription
        if transaction.subscription_id:
            subscription = self.subscription_service.get_subscription(
                transaction.subscription_id
            )
            
            if subscription:
                # If subscription is in trial, activate it
                if subscription.is_trial:
                    subscription.status = SubscriptionStatus.ACTIVE
                    self.db.commit()
                    logger.info(f"Subscription {subscription.id} activated from trial")
                
                # If subscription needs renewal
                elif subscription.status == SubscriptionStatus.PAST_DUE:
                    self.subscription_service.renew_subscription(subscription.id)
                    logger.info(f"Subscription {subscription.id} renewed")

    def _handle_payment_failed(
        self,
        transaction: Transaction,
        payload: Dict[str, Any]
    ):
        """Handle failed payment webhook"""
        logger.warning(f"Processing payment failure for transaction {transaction.id}")

        error_code = payload.get("error_code") or payload.get("errorCode")
        error_message = payload.get("error_message") or payload.get("errorMsg")

        self.payment_service.mark_payment_failed(
            transaction.order_id,
            error_code=error_code,
            error_message=error_message,
        )

        # If this is a subscription payment, mark as past due
        if transaction.subscription_id:
            subscription = self.subscription_service.get_subscription(
                transaction.subscription_id
            )
            
            if subscription and subscription.is_active:
                subscription.status = SubscriptionStatus.PAST_DUE
                subscription.payment_retry_count += 1
                self.db.commit()
                logger.warning(f"Subscription {subscription.id} marked as past due")

    def _handle_payment_refunded(
        self,
        transaction: Transaction,
        payload: Dict[str, Any]
    ):
        """Handle refunded payment webhook"""
        logger.info(f"Processing payment refund for transaction {transaction.id}")

        transaction.mark_as_refunded()
        self.db.commit()

        # Handle subscription cancellation if needed
        if transaction.subscription_id:
            subscription = self.subscription_service.get_subscription(
                transaction.subscription_id
            )
            
            if subscription and subscription.is_active:
                # Optionally cancel subscription on refund
                logger.info(f"Payment refunded for subscription {subscription.id}")

    def _handle_payment_pending(
        self,
        transaction: Transaction,
        payload: Dict[str, Any]
    ):
        """Handle pending payment webhook"""
        logger.info(f"Processing payment pending for transaction {transaction.id}")

        if transaction.status == TransactionStatus.PENDING:
            transaction.status = TransactionStatus.PROCESSING
            self.db.commit()

    def retry_failed_webhooks(self, max_retries: int = 3) -> int:
        """
        Retry processing failed webhooks
        
        Args:
            max_retries: Maximum retry attempts
            
        Returns:
            Number of webhooks retried
        """
        failed_webhooks = self.db.query(WebhookEvent).filter(
            WebhookEvent.processed == False,
            WebhookEvent.retry_count < max_retries
        ).all()

        retried_count = 0
        for webhook in failed_webhooks:
            try:
                payload = json.loads(webhook.payload)
                self._handle_webhook_event(webhook, payload)
                webhook.processed = True
                webhook.processed_at = datetime.utcnow()
                retried_count += 1
            except Exception as e:
                webhook.error = str(e)
                webhook.retry_count += 1
                logger.error(f"Retry failed for webhook {webhook.event_id}: {str(e)}")
            
            self.db.commit()

        logger.info(f"Retried {retried_count} failed webhooks")
        return retried_count

    def get_webhook_stats(self) -> Dict:
        """Get webhook processing statistics"""
        total = self.db.query(WebhookEvent).count()
        processed = self.db.query(WebhookEvent).filter(
            WebhookEvent.processed == True
        ).count()
        failed = self.db.query(WebhookEvent).filter(
            WebhookEvent.processed == False
        ).count()

        return {
            "total_webhooks": total,
            "processed_webhooks": processed,
            "failed_webhooks": failed,
            "success_rate": (processed / total * 100) if total > 0 else 0,
        }
