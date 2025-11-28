"""Pydantic models for API request/response validation."""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Request Models
class DCFCalculationRequest(BaseModel):
    """Request model for DCF calculation."""

    ticker: str = Field(..., description="Stock ticker symbol", min_length=1, max_length=10)
    projection_years: int = Field(default=5, ge=3, le=10, description="Number of projection years")
    growth_rate: Optional[float] = Field(None, ge=-0.5, le=1.0, description="Revenue growth rate")
    terminal_growth_rate: Optional[float] = Field(None, ge=0, le=0.1, description="Terminal growth rate")
    discount_rate: Optional[float] = Field(None, ge=0, le=0.5, description="Discount rate (WACC)")
    use_intelligent_values: bool = Field(default=True, description="Use intelligent parameter selection")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "ticker": "AAPL",
            "projection_years": 5,
            "growth_rate": 0.05,
            "terminal_growth_rate": 0.025,
            "discount_rate": 0.08,
            "use_intelligent_values": False
        }
    })


class CompanySearchRequest(BaseModel):
    """Request model for company search."""

    query: str = Field(..., min_length=1, description="Search query")
    limit: Optional[int] = Field(default=20, ge=1, le=100, description="Maximum results")


# Response Models
class CompanyInfo(BaseModel):
    """Company information model."""

    ticker: str
    name: str
    sector: str
    market_cap: Optional[float] = None
    current_price: Optional[float] = None


class DCFResult(BaseModel):
    """DCF calculation result model."""

    ticker: str
    company_name: str
    calculation_date: datetime
    current_price: float
    fair_value: float
    upside_percentage: float
    recommendation: Literal["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
    confidence_score: float = Field(ge=0, le=1, description="Confidence in valuation (0-1)")

    # DCF Parameters Used
    projection_years: int
    growth_rate: float
    terminal_growth_rate: float
    discount_rate: float

    # Financial Metrics
    fcf_current: Optional[float] = None
    revenue_current: Optional[float] = None
    shares_outstanding: Optional[float] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "ticker": "AAPL",
            "company_name": "Apple Inc.",
            "calculation_date": "2024-01-15T10:30:00",
            "current_price": 185.50,
            "fair_value": 210.30,
            "upside_percentage": 13.4,
            "recommendation": "Buy",
            "confidence_score": 0.85,
            "projection_years": 5,
            "growth_rate": 0.06,
            "terminal_growth_rate": 0.025,
            "discount_rate": 0.082,
            "fcf_current": 99800000000,
            "revenue_current": 383930000000,
            "shares_outstanding": 15550000000
        }
    })


class SensitivityAnalysis(BaseModel):
    """Sensitivity analysis result."""

    ticker: str
    base_fair_value: float
    optimistic_fair_value: float
    pessimistic_fair_value: float
    scenarios: dict[str, dict]


class HistoricalValuation(BaseModel):
    """Historical valuation data point."""

    date: datetime
    fair_value: float
    market_price: float
    upside_percentage: float


class DashboardSummary(BaseModel):
    """Executive dashboard summary."""

    total_companies: int
    avg_upside: float
    strong_buys: int
    buys: int
    holds: int
    sells: int
    last_updated: datetime
    top_opportunities: list[DCFResult]


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class HealthCheck(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"]
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    services: dict[str, bool]
