"""Rate limiting middleware to prevent brute-force attacks."""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using in-memory storage.
    
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(
        self,
        app,
        max_requests: int = 5,
        window_seconds: int = 60,
        paths: list[str] | None = None,
    ):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.paths = paths or ["/api/v1/auth/login", "/api/v1/auth/register"]
        # Store: {ip: [(timestamp1, timestamp2, ...)]}
        self.requests: dict[str, list[float]] = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only rate limit specific paths
        if not any(request.url.path.startswith(path) for path in self.paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Get current timestamp
        now = time.time()
        
        # Clean old requests outside the window
        self.requests[client_ip] = [
            ts for ts in self.requests[client_ip]
            if now - ts < self.window_seconds
        ]
        
        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests. Maximum {self.max_requests} requests per {self.window_seconds} seconds allowed.",
                headers={"Retry-After": str(self.window_seconds)},
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.max_requests - len(self.requests[client_ip])
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(now + self.window_seconds)
        )
        
        return response
