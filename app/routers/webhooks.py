"""
Webhooks Router - Handle D-Money payment notifications
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.transaction import WebhookEventResponse, WebhookPayload
from app.services.webhook_service import WebhookService
from app.utils.helpers import generate_unique_id

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = logging.getLogger(__name__)


@router.post("/dmoney", response_model=WebhookEventResponse)
async def handle_dmoney_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
):
    """
    Handle D-Money payment webhook notifications
    
    This endpoint receives payment status updates from D-Money.
    Configure this URL in your D-Money merchant dashboard:
    https://api.scolapp.com/api/v1/webhooks/dmoney
    
    Security:
    - Webhook signature verification (if X-Signature header provided)
    - IP whitelisting (optional, implement in production)
    """
    try:
        # Get raw body
        body = await request.body()
        body_str = body.decode()
        
        # Parse JSON payload
        import json
        payload = json.loads(body_str)
        
        logger.info(f"Received D-Money webhook: {payload}")
        
        # Extract event details
        event_type = payload.get("event_type") or payload.get("trade_status") or "payment.notification"
        order_id = payload.get("order_id") or payload.get("merch_order_id")
        
        # Generate event ID if not provided
        event_id = payload.get("event_id") or f"evt_{order_id}_{generate_unique_id(length=8)}"
        
        # Verify webhook signature if provided
        webhook_service = WebhookService(db)
        
        if x_signature:
            is_valid = webhook_service.verify_webhook_signature(body_str, x_signature)
            if not is_valid:
                logger.warning(f"Invalid webhook signature for event {event_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid webhook signature"
                )
        
        # Process webhook
        webhook_event = webhook_service.process_webhook(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )
        
        return WebhookEventResponse.from_orm(webhook_event)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )
    
    except ValueError as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )


@router.get("/dmoney/test")
async def test_webhook_endpoint():
    """
    Test webhook endpoint connectivity
    
    Use this to verify that D-Money can reach your webhook URL
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is accessible",
        "timestamp": "2026-03-24T12:00:00Z",
    }


@router.post("/dmoney/retry/{event_id}", response_model=WebhookEventResponse)
def retry_webhook(
    event_id: str,
    db: Session = Depends(get_db),
):
    """
    Manually retry a failed webhook event
    
    - **event_id**: Webhook event ID
    
    Admin endpoint to retry processing of failed webhooks
    """
    from app.models.transaction import WebhookEvent
    import json
    
    webhook_event = db.query(WebhookEvent).filter(
        WebhookEvent.event_id == event_id
    ).first()
    
    if not webhook_event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook event {event_id} not found"
        )
    
    if webhook_event.processed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook already processed successfully"
        )
    
    try:
        webhook_service = WebhookService(db)
        payload = json.loads(webhook_event.payload)
        webhook_service._handle_webhook_event(webhook_event, payload)
        
        webhook_event.processed = True
        webhook_event.processed_at = datetime.utcnow()
        webhook_event.error = None
        db.commit()
        db.refresh(webhook_event)
        
        return WebhookEventResponse.from_orm(webhook_event)
    
    except Exception as e:
        webhook_event.error = str(e)
        webhook_event.retry_count += 1
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retry failed: {str(e)}"
        )


# Import datetime for retry endpoint
from datetime import datetime
