"""
Transaction Model - Payment transaction tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TransactionType(str, enum.Enum):
    """Transaction type enumeration"""
    PAYMENT = "payment"
    REFUND = "refund"
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionStatus(str, enum.Enum):
    """Transaction status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration"""
    DMONEY = "dmoney"
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"


class Transaction(Base):
    """
    Transaction model - All payment transactions
    """
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifiers
    transaction_id = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(String(100), index=True, nullable=False)  # D-Money order ID
    prepay_id = Column(String(100), index=True, nullable=True)  # D-Money prepay ID
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)
    
    # Transaction details
    type = Column(SQLEnum(TransactionType), default=TransactionType.PAYMENT, nullable=False)
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    payment_method = Column(SQLEnum(PaymentMethod), default=PaymentMethod.DMONEY, nullable=False)
    
    # Amounts
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="DJF", nullable=False)
    fee = Column(Float, default=0.0)
    net_amount = Column(Float, nullable=False)  # amount - fee
    
    # Payment details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # URLs
    checkout_url = Column(String(500), nullable=True)
    redirect_url = Column(String(500), nullable=True)
    
    # Status tracking
    paid_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    # Error handling
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Webhook data
    webhook_received = Column(Boolean, default=False)
    webhook_data = Column(Text, nullable=True)  # JSON string
    
    # Metadata
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    raw_response = Column(Text, nullable=True)  # Full D-Money API response
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    subscription = relationship("Subscription", back_populates="transactions")
    refunds = relationship("Refund", back_populates="transaction")

    def __repr__(self):
        return f"<Transaction(id={self.id}, order_id='{self.order_id}', status='{self.status}', amount={self.amount})>"

    @property
    def is_paid(self) -> bool:
        """Check if transaction is paid"""
        return self.status == TransactionStatus.COMPLETED

    @property
    def is_pending(self) -> bool:
        """Check if transaction is pending"""
        return self.status in [TransactionStatus.PENDING, TransactionStatus.PROCESSING]

    @property
    def can_be_refunded(self) -> bool:
        """Check if transaction can be refunded"""
        return (
            self.status == TransactionStatus.COMPLETED
            and self.type == TransactionType.PAYMENT
            and not self.refunded_at
        )

    def mark_as_paid(self):
        """Mark transaction as completed"""
        self.status = TransactionStatus.COMPLETED
        self.paid_at = datetime.utcnow()

    def mark_as_failed(self, error_code: str = None, error_message: str = None):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
        self.failed_at = datetime.utcnow()
        self.error_code = error_code
        self.error_message = error_message

    def mark_as_refunded(self):
        """Mark transaction as refunded"""
        self.status = TransactionStatus.REFUNDED
        self.refunded_at = datetime.utcnow()


class WebhookEvent(Base):
    """
    Webhook Event model - Stores all webhook events from D-Money
    """
    __tablename__ = "webhook_events"

    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_id = Column(String(100), unique=True, index=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    
    # Related transaction
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    order_id = Column(String(100), index=True, nullable=True)
    
    # Payload
    payload = Column(Text, nullable=False)  # Full webhook JSON
    
    # Processing
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', processed={self.processed})>"
