"""
Helper Utilities - Common helper functions
"""

import secrets
import string
from datetime import datetime
from typing import Any, Dict, Optional
import json


def generate_unique_id(prefix: str = "", length: int = 12) -> str:
    """
    Generate a unique ID with optional prefix
    
    Args:
        prefix: Optional prefix for the ID
        length: Length of random part
        
    Returns:
        Unique ID string
    """
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
    return f"{prefix}{random_part}" if prefix else random_part


def generate_transaction_id() -> str:
    """Generate a unique transaction ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_unique_id(length=6)
    return f"TXN{timestamp}{random_part}"


def generate_refund_id() -> str:
    """Generate a unique refund ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_unique_id(length=6)
    return f"RFD{timestamp}{random_part}"


def safe_json_loads(json_str: Optional[str], default: Any = None) -> Any:
    """
    Safely load JSON string with fallback
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely dump object to JSON string
    
    Args:
        obj: Object to serialize
        default: Default value if serialization fails
        
    Returns:
        JSON string
    """
    if obj is None:
        return default
    
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        return default


def format_currency(amount: float, currency: str = "DJF") -> str:
    """
    Format amount as currency string
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    return f"{amount:,.2f} {currency}"


def calculate_pagination(page: int, page_size: int, total: int) -> Dict:
    """
    Calculate pagination metadata
    
    Args:
        page: Current page number (1-indexed)
        page_size: Items per page
        total: Total number of items
        
    Returns:
        Pagination metadata dictionary
    """
    total_pages = (total + page_size - 1) // page_size
    has_next = page < total_pages
    has_prev = page > 1
    
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "has_next": has_next,
        "has_prev": has_prev,
    }


def mask_sensitive_data(data: str, visible_start: int = 4, visible_end: int = 4) -> str:
    """
    Mask sensitive data showing only start and end
    
    Args:
        data: Data to mask
        visible_start: Number of characters to show at start
        visible_end: Number of characters to show at end
        
    Returns:
        Masked string
    """
    if len(data) <= visible_start + visible_end:
        return "*" * len(data)
    
    return f"{data[:visible_start]}{'*' * (len(data) - visible_start - visible_end)}{data[-visible_end:]}"


def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: FastAPI request object
        
    Returns:
        Client IP address
    """
    # Check for forwarded IP first (if behind proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    return request.client.host if request.client else "unknown"


def is_valid_email(email: str) -> bool:
    """
    Basic email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def dict_to_query_string(params: Dict[str, Any]) -> str:
    """
    Convert dictionary to URL query string
    
    Args:
        params: Parameters dictionary
        
    Returns:
        URL query string
    """
    from urllib.parse import urlencode
    
    # Filter out None values
    filtered_params = {k: v for k, v in params.items() if v is not None}
    return urlencode(filtered_params)
