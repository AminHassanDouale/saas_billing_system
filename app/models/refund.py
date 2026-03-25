"""
Refund Model - Payment refund tracking
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class RefundStatus(str, enum.Enum):
    """Refund status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class RefundReason(str, enum.Enum):
    """Refund reason enumeration"""
    CUSTOMER_REQUEST = "customer_request"
    DUPLICATE_PAYMENT = "duplicate_payment"
    FRAUDULENT = "fraudulent"
    SERVICE_NOT_PROVIDED = "service_not_provided"
    SUBSCRIPTION_CANCELED = "subscription_canceled"
    OTHER = "other"


class Refund(Base):
    """
    Refund model - Payment refund requests and processing
    """
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    
    # Unique identifier
    refund_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Foreign Keys
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who processed
    
    # Refund details
    status = Column(SQLEnum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    reason = Column(SQLEnum(RefundReason), nullable=False)
    reason_details = Column(Text, nullable=True)
    
    # Amounts
    original_amount = Column(Float, nullable=False)
    refund_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="DJF", nullable=False)
    is_partial = Column(Boolean, default=False)
    
    # Processing
    approved_at = Column(DateTime, nullable=True)
    rejected_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Admin notes
    admin_notes = Column(Text, nullable=True)
    
    # D-Money response
    dmoney_refund_id = Column(String(100), nullable=True)
    dmoney_response = Column(Text, nullable=True)  # JSON string
    
    # Error tracking
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    transaction = relationship("Transaction", back_populates="refunds")
    user = relationship("User", back_populates="refunds", foreign_keys=[user_id])

    def __repr__(self):
        return f"<Refund(id={self.id}, refund_id='{self.refund_id}', status='{self.status}', amount={self.refund_amount})>"

    @property
    def is_pending(self) -> bool:
        """Check if refund is pending"""
        return self.status == RefundStatus.PENDING

    @property
    def is_completed(self) -> bool:
        """Check if refund is completed"""
        return self.status == RefundStatus.COMPLETED

    def approve(self, admin_id: int, notes: str = None):
        """Approve refund"""
        self.status = RefundStatus.PROCESSING
        self.approved_at = datetime.utcnow()
        self.processed_by = admin_id
        if notes:
            self.admin_notes = notes

    def reject(self, admin_id: int, notes: str = None):
        """Reject refund"""
        self.status = RefundStatus.CANCELED
        self.rejected_at = datetime.utcnow()
        self.processed_by = admin_id
        if notes:
            self.admin_notes = notes

    def complete(self, dmoney_refund_id: str = None):
        """Mark refund as completed"""
        self.status = RefundStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        if dmoney_refund_id:
            self.dmoney_refund_id = dmoney_refund_id

    def fail(self, error_code: str = None, error_message: str = None):
        """Mark refund as failed"""
        self.status = RefundStatus.FAILED
        self.error_code = error_code
        self.error_message = error_message
        self.retry_count += 1


