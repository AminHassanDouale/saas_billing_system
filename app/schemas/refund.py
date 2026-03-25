"""
Refund Pydantic Schemas - Request/Response validation
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.refund import RefundStatus, RefundReason


# ── Refund Request Schemas ────────────────────────────────────────────────

class RefundCreate(BaseModel):
    """Refund creation request"""
    transaction_id: int = Field(..., description="ID of transaction to refund")
    refund_amount: Optional[float] = Field(None, gt=0, description="Amount to refund (full if not specified)")
    reason: RefundReason = Field(..., description="Reason for refund")
    reason_details: Optional[str] = Field(None, max_length=1000, description="Detailed explanation")


class RefundApprove(BaseModel):
    """Refund approval request"""
    admin_notes: Optional[str] = Field(None, max_length=1000)


class RefundReject(BaseModel):
    """Refund rejection request"""
    admin_notes: str = Field(..., max_length=1000, description="Reason for rejection")


class RefundFilter(BaseModel):
    """Refund filtering parameters"""
    user_id: Optional[int] = None
    transaction_id: Optional[int] = None
    status: Optional[RefundStatus] = None
    reason: Optional[RefundReason] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


# ── Refund Response Schemas ───────────────────────────────────────────────

class RefundResponse(BaseModel):
    """Refund response schema"""
    id: int
    refund_id: str
    transaction_id: int
    user_id: int
    processed_by: Optional[int] = None
    status: RefundStatus
    reason: RefundReason
    reason_details: Optional[str] = None
    original_amount: float
    refund_amount: float
    currency: str
    is_partial: bool
    approved_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    admin_notes: Optional[str] = None
    dmoney_refund_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RefundList(BaseModel):
    """Paginated refund list"""
    total: int
    page: int
    page_size: int
    refunds: list[RefundResponse]


class RefundStats(BaseModel):
    """Refund statistics"""
    total_refunds: int
    pending_refunds: int
    completed_refunds: int
    rejected_refunds: int
    total_refunded_amount: float
    average_refund_amount: float
    refund_rate: float  # Percentage of transactions refunded
