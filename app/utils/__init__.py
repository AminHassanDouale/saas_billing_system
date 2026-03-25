"""
Utility Functions
"""

from app.utils.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_current_merchant_user,
    refresh_access_token,
)

from app.utils.security import (
    hash_password,
    verify_password,
    generate_password_reset_token,
    verify_password_strength,
    sanitize_input,
    generate_verification_code,
    is_safe_redirect_url,
)

from app.utils.helpers import (
    generate_unique_id,
    generate_transaction_id,
    generate_refund_id,
    safe_json_loads,
    safe_json_dumps,
    format_currency,
    calculate_pagination,
    mask_sensitive_data,
    get_client_ip,
    is_valid_email,
    truncate_string,
    dict_to_query_string,
)

__all__ = [
    # Auth
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_merchant_user",
    "refresh_access_token",
    # Security
    "hash_password",
    "verify_password",
    "generate_password_reset_token",
    "verify_password_strength",
    "sanitize_input",
    "generate_verification_code",
    "is_safe_redirect_url",
    # Helpers
    "generate_unique_id",
    "generate_transaction_id",
    "generate_refund_id",
    "safe_json_loads",
    "safe_json_dumps",
    "format_currency",
    "calculate_pagination",
    "mask_sensitive_data",
    "get_client_ip",
    "is_valid_email",
    "truncate_string",
    "dict_to_query_string",
]
