"""Middleware for request validation, logging, and error handling."""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from .exceptions import DCFException
from .models import ErrorResponse

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Response: {response.status_code} ({duration:.3f}s)",
                extra={
                    "status_code": response.status_code,
                    "duration": duration,
                    "path": request.url.path,
                }
            )

            # Add custom headers
            response.headers["X-Process-Time"] = str(duration)

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"Request failed: {str(e)} ({duration:.3f}s)",
                exc_info=True,
                extra={
                    "path": request.url.path,
                    "duration": duration,
                }
            )
            raise


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all exceptions uniformly."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)

        except DCFException as e:
            # Handle custom DCF exceptions
            logger.warning(
                f"DCF Exception: {e.message}",
                extra={
                    "status_code": e.status_code,
                    "detail": e.detail,
                    "path": request.url.path,
                }
            )

            return JSONResponse(
                status_code=e.status_code,
                content=ErrorResponse(
                    error=e.message,
                    detail=e.detail,
                    timestamp=time.time()
                ).model_dump()
            )

        except ValueError as e:
            # Handle validation errors
            logger.warning(f"Validation error: {str(e)}")

            return JSONResponse(
                status_code=422,
                content=ErrorResponse(
                    error="Validation Error",
                    detail=str(e)
                ).model_dump()
            )

        except Exception as e:
            # Handle unexpected exceptions
            logger.error(
                f"Unexpected error: {str(e)}",
                exc_info=True,
                extra={"path": request.url.path}
            )

            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="Internal Server Error",
                    detail="An unexpected error occurred. Please try again later."
                ).model_dump()
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # {ip: [(timestamp, count)]}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)

        # Get current time
        current_time = time.time()

        # Clean old entries
        if client_ip in self.requests:
            self.requests[client_ip] = [
                (ts, count) for ts, count in self.requests[client_ip]
                if current_time - ts < self.window_seconds
            ]

        # Count requests in current window
        request_count = sum(
            count for ts, count in self.requests.get(client_ip, [])
        )

        # Check rate limit
        if request_count >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {client_ip}")

            return JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error="Rate Limit Exceeded",
                    detail=f"Maximum {self.max_requests} requests per {self.window_seconds} seconds"
                ).model_dump(),
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Add request to tracking
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append((current_time, 1))

        return await call_next(request)
