"""
Logging Configuration
Structured logging for the application
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pythonjsonlogger import jsonlogger

from app.config import settings


def setup_logging():
    """
    Configure application logging with both file and console handlers
    """
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # ── Console Handler (Human-readable) ──────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # ── File Handler (JSON format for parsing) ───────────────────────────
    file_handler = RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(json_formatter)
    
    # ── Error File Handler (Errors only) ──────────────────────────────────
    error_handler = RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # ── Access Log Handler (HTTP requests) ────────────────────────────────
    access_handler = TimedRotatingFileHandler(
        filename=log_dir / "access.log",
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(json_formatter)
    
    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Configure access logger separately
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.addHandler(access_handler)
    
    # Configure library loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Log startup
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
            "log_dir": str(log_dir)
        }
    )


class RequestLogger:
    """
    Middleware-compatible request logger
    Logs all incoming requests with details
    """
    
    def __init__(self):
        self.logger = logging.getLogger("api.requests")
    
    async def log_request(self, request, response, duration: float):
        """
        Log request details
        
        Args:
            request: FastAPI request object
            response: Response object
            duration: Request duration in seconds
        """
        
        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        status_code = getattr(response, 'status_code', 0)
        
        # Get user info if authenticated
        user_id = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # In production, decode JWT to get user ID
                user_id = "authenticated"
            except Exception:
                pass
        
        # Log with structured data
        self.logger.info(
            f"{method} {path} - {status_code}",
            extra={
                "client_ip": client_ip,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration * 1000, 2),
                "user_id": user_id,
                "user_agent": request.headers.get("User-Agent", "unknown"),
            }
        )


class AuditLogger:
    """
    Audit logger for tracking important business events
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        
        # Create dedicated audit log file
        audit_handler = RotatingFileHandler(
            filename="logs/audit.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
            encoding='utf-8'
        )
        
        json_formatter = jsonlogger.JsonFormatter(
            '%(asctime)s %(name)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(json_formatter)
        
        self.logger.addHandler(audit_handler)
        self.logger.setLevel(logging.INFO)
    
    def log_user_action(self, action: str, user_id: int, details: dict = None):
        """Log user action"""
        self.logger.info(
            f"User action: {action}",
            extra={
                "action": action,
                "user_id": user_id,
                "details": details or {},
            }
        )
    
    def log_payment(self, action: str, transaction_id: str, amount: float, user_id: int):
        """Log payment event"""
        self.logger.info(
            f"Payment {action}",
            extra={
                "action": action,
                "transaction_id": transaction_id,
                "amount": amount,
                "user_id": user_id,
            }
        )
    
    def log_subscription(self, action: str, subscription_id: int, user_id: int, plan: str):
        """Log subscription event"""
        self.logger.info(
            f"Subscription {action}",
            extra={
                "action": action,
                "subscription_id": subscription_id,
                "user_id": user_id,
                "plan": plan,
            }
        )
    
    def log_refund(self, action: str, refund_id: str, amount: float, user_id: int):
        """Log refund event"""
        self.logger.info(
            f"Refund {action}",
            extra={
                "action": action,
                "refund_id": refund_id,
                "amount": amount,
                "user_id": user_id,
            }
        )


# Global instances
request_logger = RequestLogger()
audit_logger = AuditLogger()
