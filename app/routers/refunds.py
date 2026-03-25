"""
Refunds Router - Refund request and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.refund import Refund, RefundStatus
from app.models.transaction import Transaction
from app.schemas.refund import (
    RefundCreate,
    RefundApprove,
    RefundReject,
    RefundResponse,
    RefundList,
    RefundStats,
)
from app.utils.auth import get_current_active_user, get_current_admin_user
from app.utils.helpers import generate_refund_id

router = APIRouter(prefix="/api/v1/refunds", tags=["Refunds"])


@router.post("/request", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
def request_refund(
    refund_data: RefundCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Request a refund for a transaction
    
    - **transaction_id**: ID of the transaction to refund
    - **refund_amount**: Amount to refund (optional, defaults to full amount)
    - **reason**: Reason for refund
    - **reason_details**: Detailed explanation
    """
    # Get transaction
    transaction = db.query(Transaction).filter(
        Transaction.id == refund_data.transaction_id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify transaction belongs to user
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to refund this transaction"
        )
    
    # Check if transaction can be refunded
    if not transaction.can_be_refunded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction cannot be refunded"
        )
    
    # Check if refund already exists
    existing = db.query(Refund).filter(
        Refund.transaction_id == refund_data.transaction_id,
        Refund.status.in_([RefundStatus.PENDING, RefundStatus.PROCESSING, RefundStatus.COMPLETED])
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund request already exists for this transaction"
        )
    
    # Determine refund amount
    refund_amount = refund_data.refund_amount or transaction.amount
    is_partial = refund_amount < transaction.amount
    
    # Validate refund amount
    if refund_amount > transaction.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refund amount cannot exceed transaction amount"
        )
    
    # Create refund
    refund = Refund(
        refund_id=generate_refund_id(),
        transaction_id=transaction.id,
        user_id=current_user.id,
        status=RefundStatus.PENDING,
        reason=refund_data.reason,
        reason_details=refund_data.reason_details,
        original_amount=transaction.amount,
        refund_amount=refund_amount,
        currency=transaction.currency,
        is_partial=is_partial,
    )
    
    db.add(refund)
    db.commit()
    db.refresh(refund)
    
    return refund


@router.get("/my-refunds", response_model=List[RefundResponse])
def get_my_refunds(
    status_filter: Optional[RefundStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get current user's refund requests
    
    - **status_filter**: Optional filter by refund status
    """
    query = db.query(Refund).filter(Refund.user_id == current_user.id)
    
    if status_filter:
        query = query.filter(Refund.status == status_filter)
    
    refunds = query.order_by(Refund.created_at.desc()).all()
    return refunds


@router.get("/{refund_id}", response_model=RefundResponse)
def get_refund(
    refund_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get specific refund details
    """
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found"
        )
    
    # Verify refund belongs to user or user is admin
    if refund.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this refund"
        )
    
    return refund


# ── Admin endpoints ────────────────────────────────────────────────────────

@router.get("/", response_model=RefundList)
def get_all_refunds(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[RefundStatus] = None,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get all refund requests (Admin only)
    """
    query = db.query(Refund)
    
    if status_filter:
        query = query.filter(Refund.status == status_filter)
    
    total = query.count()
    
    offset = (page - 1) * page_size
    refunds = query.order_by(Refund.created_at.desc()).offset(offset).limit(page_size).all()
    
    return RefundList(
        total=total,
        page=page,
        page_size=page_size,
        refunds=[RefundResponse.from_orm(r) for r in refunds],
    )


@router.post("/{refund_id}/approve", response_model=RefundResponse)
def approve_refund(
    refund_id: int,
    approval_data: RefundApprove,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Approve a refund request (Admin only)
    """
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found"
        )
    
    if refund.status != RefundStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending refunds can be approved"
        )
    
    refund.approve(current_user.id, approval_data.admin_notes)
    db.commit()
    db.refresh(refund)
    
    # TODO: Process refund through D-Money gateway
    # For now, just mark as completed
    refund.complete()
    db.commit()
    db.refresh(refund)
    
    return refund


@router.post("/{refund_id}/reject", response_model=RefundResponse)
def reject_refund(
    refund_id: int,
    rejection_data: RefundReject,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Reject a refund request (Admin only)
    """
    refund = db.query(Refund).filter(Refund.id == refund_id).first()
    
    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Refund not found"
        )
    
    if refund.status != RefundStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending refunds can be rejected"
        )
    
    refund.reject(current_user.id, rejection_data.admin_notes)
    db.commit()
    db.refresh(refund)
    
    return refund


@router.get("/stats/overview", response_model=RefundStats)
def get_refund_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """
    Get refund statistics (Admin only)
    """
    total = db.query(Refund).count()
    pending = db.query(Refund).filter(Refund.status == RefundStatus.PENDING).count()
    completed = db.query(Refund).filter(Refund.status == RefundStatus.COMPLETED).count()
    rejected = db.query(Refund).filter(Refund.status == RefundStatus.CANCELED).count()
    
    # Total refunded amount
    total_refunded = db.query(Refund).filter(
        Refund.status == RefundStatus.COMPLETED
    ).with_entities(
        db.func.sum(Refund.refund_amount)
    ).scalar() or 0.0
    
    # Average refund amount
    avg_refund = total_refunded / completed if completed > 0 else 0.0
    
    # Refund rate
    total_transactions = db.query(Transaction).count()
    refund_rate = (completed / total_transactions * 100) if total_transactions > 0 else 0.0
    
    return RefundStats(
        total_refunds=total,
        pending_refunds=pending,
        completed_refunds=completed,
        rejected_refunds=rejected,
        total_refunded_amount=round(total_refunded, 2),
        average_refund_amount=round(avg_refund, 2),
        refund_rate=round(refund_rate, 2),
    )
