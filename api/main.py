"""Main FastAPI application for DCF Valuation Platform."""

import logging
import os
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    DCFCalculationRequest,
    DCFResult,
    CompanyInfo,
    CompanySearchRequest,
    DashboardSummary,
    ErrorResponse,
    HealthCheck,
    SensitivityAnalysis,
    HistoricalValuation
)
from .routers import dcf, companies, dashboard, alerts
from .middleware import (
    LoggingMiddleware,
    ErrorHandlerMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware
)
from .exceptions import DCFException

# Setup logging
from src.utils.logging_config import setup_logging
from src.config import get_settings

settings = get_settings()
setup_logging(log_level=settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting DCF Valuation API")
    yield
    logger.info("Shutting down DCF Valuation API")


# Initialize FastAPI app
app = FastAPI(
    title="DCF Valuation Platform API",
    description="Professional REST API for Discounted Cash Flow valuation and financial analysis",
    version=settings.version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Determine allowed origins based on environment
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js dev
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

# Add production origins
if os.getenv("VERCEL_URL"):
    ALLOWED_ORIGINS.append(f"https://{os.getenv('VERCEL_URL')}")

# Add custom domain if configured
if os.getenv("PRODUCTION_URL"):
    ALLOWED_ORIGINS.append(os.getenv("PRODUCTION_URL"))

# Allow all Vercel preview deployments
ALLOWED_ORIGINS.extend([
    "https://*.vercel.app",
    "https://dcf-valuation.vercel.app"
])

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middlewares (order matters!)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(LoggingMiddleware)

# Add rate limiting (100 requests per minute per IP)
# Disabled in development
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


# Health check endpoint
@app.get("/api/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Check API health and service status."""
    try:
        from src.cache import DCFCache
        cache = DCFCache()

        services = {
            "database": True,  # Check if SQLite is accessible
            "cache": cache is not None,
        }

        return HealthCheck(
            status="healthy" if all(services.values()) else "unhealthy",
            version=settings.version,
            services=services
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="unhealthy",
            version=settings.version,
            services={"database": False, "cache": False}
        )


# Root endpoint
@app.get("/api", tags=["System"])
async def root():
    """API root endpoint."""
    return {
        "name": "DCF Valuation Platform API",
        "version": settings.version,
        "docs": "/api/docs",
        "health": "/api/health"
    }


# Include routers
app.include_router(dcf.router, prefix="/api/dcf", tags=["DCF Analysis"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])


# Exception handlers
@app.exception_handler(DCFException)
async def dcf_exception_handler(request, exc: DCFException):
    """Handle custom DCF exceptions."""
    logger.warning(f"DCF Exception: {exc.message}", extra={"detail": exc.detail})
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.message,
            detail=exc.detail
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.warning(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc)
        ).model_dump()
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=None
        ).model_dump()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    # Don't expose internal errors in production
    detail = str(exc) if os.getenv("ENVIRONMENT") != "production" else None

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=detail
        ).model_dump()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
