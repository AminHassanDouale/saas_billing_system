"""
Transaction Pydantic Schemas - Request/Response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.transaction import TransactionType, TransactionStatus, PaymentMethod


# ── Transaction Request Schemas ───────────────────────────────────────────

class PaymentCreate(BaseModel):
    """Payment creation request"""
    amount: float = Field(..., gt=0, description="Payment amount in DJF")
    title: str = Field(..., max_length=255, description="Payment title/description")
    subscription_id: Optional[int] = Field(None, description="Related subscription ID")
    currency: str = Field(default="DJF", max_length=3)
    timeout: str = Field(default="120m", description="Payment timeout (e.g., 120m)")
    language: str = Field(default="en", description="Checkout page language (en/fr)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class TransactionFilter(BaseModel):
    """Transaction filtering parameters"""
    user_id: Optional[int] = None
    subscription_id: Optional[int] = None
    status: Optional[TransactionStatus] = None
    type: Optional[TransactionType] = None
    payment_method: Optional[PaymentMethod] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None


# ── Transaction Response Schemas ──────────────────────────────────────────

class TransactionResponse(BaseModel):
    """Transaction response schema"""
    id: int
    transaction_id: str
    order_id: str
    prepay_id: Optional[str] = None
    user_id: int
    subscription_id: Optional[int] = None
    type: TransactionType
    status: TransactionStatus
    payment_method: PaymentMethod
    amount: float
    currency: str
    fee: float
    net_amount: float
    title: str
    description: Optional[str] = None
    checkout_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    webhook_received: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaymentResponse(BaseModel):
    """Payment creation response"""
    success: bool
    transaction: TransactionResponse
    checkout_url: str
    message: str = "Payment initiated successfully"


class TransactionList(BaseModel):
    """Paginated transaction list"""
    total: int
    page: int
    page_size: int
    transactions: list[TransactionResponse]


class TransactionStats(BaseModel):
    """Transaction statistics"""
    total_transactions: int
    total_amount: float
    successful_transactions: int
    failed_transactions: int
    pending_transactions: int
    refunded_transactions: int
    average_transaction_value: float
    total_fees: float
    net_revenue: float


# ── Webhook Schemas ───────────────────────────────────────────────────────

class WebhookEventResponse(BaseModel):
    """Webhook event response"""
    id: int
    event_id: str
    event_type: str
    order_id: Optional[str] = None
    processed: bool
    processed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int
    received_at: datetime

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Generic webhook payload structure"""
    event_type: str
    order_id: str
    transaction_id: Optional[str] = None
    status: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    timestamp: datetime
    data: Dict[str, Any]
