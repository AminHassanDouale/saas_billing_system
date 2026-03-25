"""
Rate Limiting Middleware
Protect API from abuse by limiting requests per user
"""

import time
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis

from app.config import settings

# Initialize Redis client for rate limiting
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    redis_client = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm
    
    Limits requests per IP address or authenticated user
    """

    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window = 60  # 1 minute window

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with rate limiting"""
        
        # Skip rate limiting if Redis is not available
        if not redis_client:
            return await call_next(request)

        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Get identifier (user ID if authenticated, otherwise IP)
        identifier = self._get_identifier(request)
        
        # Check rate limit
        if not self._is_allowed(identifier):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed."
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )

        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining(identifier)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response

    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting"""
        # Try to get user ID from authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # Extract user info from token (simplified)
                token = auth_header.split(" ")[1]
                # In production, decode JWT to get user ID
                return f"user:{token[:20]}"  # Use first 20 chars as identifier
            except Exception:
                pass
        
        # Fallback to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"

    def _is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit"""
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())
        
        try:
            # Get current count
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, current_time - self.window)
            pipe.zadd(key, {str(current_time): current_time})
            pipe.zcard(key)
            pipe.expire(key, self.window)
            results = pipe.execute()
            
            request_count = results[2]
            
            return request_count <= self.requests_per_minute
        
        except Exception:
            # If Redis fails, allow the request
            return True

    def _get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier"""
        key = f"rate_limit:{identifier}"
        current_time = int(time.time())
        
        try:
            # Clean up old entries
            redis_client.zremrangebyscore(key, 0, current_time - self.window)
            
            # Get current count
            count = redis_client.zcard(key)
            remaining = max(0, self.requests_per_minute - count)
            
            return remaining
        
        except Exception:
            return self.requests_per_minute


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP Whitelist middleware for webhook endpoints
    Only allow requests from trusted IPs
    """

    def __init__(self, app, whitelisted_ips: list = None):
        super().__init__(app)
        self.whitelisted_ips = whitelisted_ips or []
        # Add D-Money IPs here when available
        # self.whitelisted_ips.extend(["52.1.2.3", "52.4.5.6"])

    async def dispatch(self, request: Request, call_next: Callable):
        """Check IP whitelist for sensitive endpoints"""
        
        # Only apply to webhook endpoints
        if not request.url.path.startswith("/api/v1/webhooks/"):
            return await call_next(request)

        # Skip if no whitelist configured
        if not self.whitelisted_ips:
            return await call_next(request)

        # Get client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"

        # Check whitelist
        if client_ip not in self.whitelisted_ips:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "IP address not authorized"}
            )

        return await call_next(request)
