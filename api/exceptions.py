"""Custom exception handlers and error models for the API."""

from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status


class DCFException(Exception):
    """Base exception for DCF-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[str] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class DataFetchException(DCFException):
    """Exception raised when data fetching fails."""

    def __init__(self, ticker: str, source: str, detail: Optional[str] = None):
        message = f"Failed to fetch data for {ticker} from {source}"
        super().__init__(
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail
        )


class ValidationException(DCFException):
    """Exception raised when validation fails."""

    def __init__(self, field: str, detail: str):
        message = f"Validation failed for field: {field}"
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class CalculationException(DCFException):
    """Exception raised when DCF calculation fails."""

    def __init__(self, ticker: str, detail: Optional[str] = None):
        message = f"DCF calculation failed for {ticker}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class CompanyNotFoundException(DCFException):
    """Exception raised when company is not found."""

    def __init__(self, ticker: str):
        message = f"Company not found: {ticker}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data available for ticker {ticker}"
        )


class RateLimitException(DCFException):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, source: str, retry_after: Optional[int] = None):
        message = f"Rate limit exceeded for {source}"
        detail = f"Try again in {retry_after} seconds" if retry_after else "Try again later"
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )


class CacheException(DCFException):
    """Exception raised when cache operations fail."""

    def __init__(self, operation: str, detail: Optional[str] = None):
        message = f"Cache operation failed: {operation}"
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )
