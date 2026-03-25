"""
Security Utilities - Password hashing and verification
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_password_reset_token() -> str:
    """
    Generate a secure password reset token
    
    Returns:
        Random token string
    """
    import secrets
    return secrets.token_urlsafe(32)


def verify_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    Verify password meets strength requirements
    
    Args:
        password: Password to check
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one digit"
    
    if not any(char.isupper() for char in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(char.islower() for char in password):
        return False, "Password must contain at least one lowercase letter"
    
    # Optional: Check for special characters
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(char in special_chars for char in password):
        return False, "Password must contain at least one special character"
    
    return True, None


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks
    
    Args:
        text: User input text
        
    Returns:
        Sanitized text
    """
    import html
    return html.escape(text.strip())


def generate_verification_code(length: int = 6) -> str:
    """
    Generate a numeric verification code
    
    Args:
        length: Length of the code
        
    Returns:
        Numeric verification code
    """
    import random
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])


def is_safe_redirect_url(url: str, allowed_hosts: list[str]) -> bool:
    """
    Check if a redirect URL is safe
    
    Args:
        url: URL to check
        allowed_hosts: List of allowed hostnames
        
    Returns:
        True if URL is safe to redirect to
    """
    from urllib.parse import urlparse
    
    try:
        parsed = urlparse(url)
        
        # Allow relative URLs
        if not parsed.netloc:
            return True
        
        # Check if hostname is in allowed list
        return parsed.netloc in allowed_hosts
    
    except Exception:
        return False
