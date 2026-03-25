"""
Payments Router - Payment creation and management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus
from app.schemas.transaction import (
    PaymentCreate,
    PaymentResponse,
    TransactionResponse,
    TransactionList,
    TransactionStats,
)
from app.services.payment_service import PaymentService
from app.utils.auth import get_current_active_user
from app.utils.helpers import calculate_pagination

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/create", response_model=PaymentResponse)
def create_payment(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Create a new payment
    
    - **amount**: Payment amount in DJF (must be positive)
    - **title**: Description of the payment
    - **subscription_id**: Optional subscription ID
    - **currency**: Currency code (default: DJF)
    - **timeout**: Payment timeout (default: 120m)
    - **language**: Checkout language (en/fr)
    
    Returns checkout URL to redirect user for payment
    """
    payment_service = PaymentService(db)
    
    try:
        result = payment_service.create_payment(
            user_id=current_user.id,
            amount=payment_data.amount,
            title=payment_data.title,
            subscription_id=payment_data.subscription_id,
            currency=payment_data.currency,
            timeout=payment_data.timeout,
            language=payment_data.language,
            metadata=payment_data.metadata,
        )
        
        # Get the full transaction
        transaction = payment_service.get_transaction_by_order_id(result["order_id"])
        
        return PaymentResponse(
            success=result["success"],
            transaction=TransactionResponse.from_orm(transaction),
            checkout_url=result["checkout_url"],
            message="Payment initiated successfully. Redirect user to checkout_url to complete payment.",
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Payment creation failed: {str(e)}"
        )


@router.get("/transactions", response_model=TransactionList)
def get_user_transactions(
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[TransactionStatus] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get user's transaction history
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **status_filter**: Optional filter by transaction status
    """
    if page_size > 100:
        page_size = 100
    
    payment_service = PaymentService(db)
    offset = (page - 1) * page_size
    
    transactions = payment_service.get_user_transactions(
        user_id=current_user.id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    
    # Get total count
    total = db.query(Transaction).filter(Transaction.user_id == current_user.id).count()
    
    return TransactionList(
        total=total,
        page=page,
        page_size=page_size,
        transactions=[TransactionResponse.from_orm(t) for t in transactions],
    )


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get specific transaction details
    
    - **transaction_id**: Transaction ID
    """
    payment_service = PaymentService(db)
    transaction = payment_service.get_transaction(transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify transaction belongs to user
    if transaction.user_id != current_user.id and current_user.role.value not in ["admin", "merchant"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transaction"
        )
    
    return TransactionResponse.from_orm(transaction)


@router.get("/stats", response_model=TransactionStats)
def get_payment_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get user's payment statistics
    """
    payment_service = PaymentService(db)
    stats = payment_service.get_transaction_stats(user_id=current_user.id)
    
    # Calculate average transaction value
    avg_value = (
        stats["total_amount"] / stats["completed_transactions"]
        if stats["completed_transactions"] > 0
        else 0
    )
    
    return TransactionStats(
        total_transactions=stats["total_transactions"],
        total_amount=stats["total_amount"],
        successful_transactions=stats["completed_transactions"],
        failed_transactions=stats["failed_transactions"],
        pending_transactions=stats["pending_transactions"],
        refunded_transactions=0,  # Add refund count
        average_transaction_value=round(avg_value, 2),
        total_fees=0,  # Calculate from transactions
        net_revenue=stats["total_amount"],
    )


@router.get("/transaction/order/{order_id}", response_model=TransactionResponse)
def get_transaction_by_order_id(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get transaction by D-Money order ID
    
    - **order_id**: D-Money order ID
    """
    payment_service = PaymentService(db)
    transaction = payment_service.get_transaction_by_order_id(order_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction with order_id {order_id} not found"
        )
    
    # Verify transaction belongs to user
    if transaction.user_id != current_user.id and current_user.role.value not in ["admin", "merchant"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this transaction"
        )
    
    return TransactionResponse.from_orm(transaction)
