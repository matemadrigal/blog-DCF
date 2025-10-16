"""
Report calculations - Business logic separated from presentation.

This module contains all calculation logic for PDF reports, separated from
the rendering layer. This allows for:
- Easy unit testing of calculations
- Reusability across different report formats
- Type safety with dataclasses
- Clear separation of concerns

Following SOLID principles and clean architecture.
"""

from dataclasses import dataclass
from typing import Optional, List, Tuple
from enum import Enum


class RecommendationType(Enum):
    """Investment recommendation types."""

    STRONG_BUY = "COMPRA FUERTE"
    BUY = "COMPRAR"
    HOLD = "MANTENER"
    SELL = "VENDER"
    STRONG_SELL = "VENTA FUERTE"


class RecommendationColor(Enum):
    """Color codes for recommendations."""

    STRONG_BUY = "success"  # Green
    BUY = "success"
    HOLD = "warning"  # Orange
    SELL = "danger"  # Red
    STRONG_SELL = "danger"


@dataclass
class DCFReportData:
    """
    Type-safe data structure for DCF report.

    All financial amounts are in company's reporting currency unless specified.
    Prices are per share unless specified.
    """

    # Company identification (required)
    ticker: str
    company_name: str

    # Valuation results (required)
    fair_value_total: float  # Total equity value
    shares_outstanding: float
    market_price: float  # Current market price per share

    # DCF parameters (required)
    wacc: float  # Weighted Average Cost of Capital
    terminal_growth: float  # Terminal growth rate
    base_fcf: float  # Base year FCF

    # Company classification (optional)
    sector: str = ""
    industry: str = ""

    # Projection parameters
    projection_years: int = 5

    # Cash flow data (optional)
    fcf_projections: Optional[List[float]] = None  # Projected FCF for each year
    terminal_value: float = 0.0

    # Debt and cash
    total_debt: float = 0.0
    cash: float = 0.0

    # Additional metrics
    revenue: float = 0.0
    ebitda: float = 0.0
    net_income: float = 0.0

    # Scenarios (optional)
    bear_case: Optional[float] = None
    base_case: Optional[float] = None
    bull_case: Optional[float] = None

    def __post_init__(self):
        """Validate data after initialization."""
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive")
        if self.market_price < 0:
            raise ValueError("market_price cannot be negative")
        if not 0 <= self.wacc <= 1:
            raise ValueError("wacc must be between 0 and 1")
        if not -0.1 <= self.terminal_growth <= 0.1:
            raise ValueError("terminal_growth must be between -10% and 10%")

    @property
    def fair_value_per_share(self) -> float:
        """Calculate fair value per share."""
        if self.shares_outstanding <= 0:
            return 0.0
        return self.fair_value_total / self.shares_outstanding

    @property
    def enterprise_value(self) -> float:
        """Calculate enterprise value (equity value + net debt)."""
        net_debt = self.total_debt - self.cash
        return self.fair_value_total + net_debt

    @property
    def market_cap(self) -> float:
        """Calculate current market capitalization."""
        return self.market_price * self.shares_outstanding


@dataclass
class DDMReportData:
    """
    Type-safe data structure for DDM (Dividend Discount Model) report.

    Used for financial companies where dividends are more relevant than FCF.
    """

    # Company identification (required)
    ticker: str
    company_name: str

    # Valuation results (required)
    fair_value_per_share: float
    shares_outstanding: float
    market_price: float

    # DDM parameters (required)
    cost_of_equity: float
    dividend_growth_rate: float
    current_dividend: float  # Annual dividend per share

    # Company classification (optional)
    sector: str = ""

    # Model configuration
    model_type: str = "Gordon Growth Model"  # Or "Two-Stage DDM", "H-Model"

    # Dividend data (optional)
    historical_dividends: Optional[List[float]] = None  # Historical annual dividends

    # Additional metrics
    payout_ratio: float = 0.0
    roe: float = 0.0  # Return on Equity
    beta: float = 1.0

    # Two-Stage parameters (if applicable)
    high_growth_rate: Optional[float] = None
    high_growth_years: Optional[int] = None
    stable_growth_rate: Optional[float] = None

    def __post_init__(self):
        """Validate data after initialization."""
        if self.shares_outstanding <= 0:
            raise ValueError("shares_outstanding must be positive")
        if self.market_price < 0:
            raise ValueError("market_price cannot be negative")
        if not 0 <= self.cost_of_equity <= 1:
            raise ValueError("cost_of_equity must be between 0 and 1")
        if self.current_dividend < 0:
            raise ValueError("current_dividend cannot be negative")

    @property
    def fair_value_total(self) -> float:
        """Calculate total equity value."""
        return self.fair_value_per_share * self.shares_outstanding

    @property
    def dividend_yield(self) -> float:
        """Calculate dividend yield based on fair value."""
        if self.fair_value_per_share <= 0:
            return 0.0
        return self.current_dividend / self.fair_value_per_share

    @property
    def market_dividend_yield(self) -> float:
        """Calculate current market dividend yield."""
        if self.market_price <= 0:
            return 0.0
        return self.current_dividend / self.market_price


class ReportCalculations:
    """
    Pure calculation functions for reports.

    All methods are static and side-effect free.
    Separated from rendering logic for testability.
    """

    @staticmethod
    def calculate_upside(fair_value_per_share: float, market_price: float) -> float:
        """
        Calculate upside/downside percentage.

        Formula: ((Fair Value - Market Price) / Market Price) × 100

        Args:
            fair_value_per_share: Calculated fair value per share
            market_price: Current market price per share

        Returns:
            Upside percentage (positive = undervalued, negative = overvalued)

        Examples:
            >>> ReportCalculations.calculate_upside(120, 100)
            20.0  # 20% upside
            >>> ReportCalculations.calculate_upside(80, 100)
            -20.0  # 20% overvalued
        """
        if market_price <= 0:
            return 0.0

        return ((fair_value_per_share - market_price) / market_price) * 100

    @staticmethod
    def get_recommendation(
        upside_pct: float,
    ) -> Tuple[RecommendationType, RecommendationColor]:
        """
        Get investment recommendation based on upside percentage.

        Conservative thresholds aligned with professional analysts:
        - Strong Buy: > 30% upside
        - Buy: 15-30% upside
        - Hold: -15% to 15%
        - Sell: -30% to -15% downside
        - Strong Sell: < -30% downside

        Args:
            upside_pct: Upside percentage from calculate_upside()

        Returns:
            Tuple of (RecommendationType, RecommendationColor)

        Examples:
            >>> rec, color = ReportCalculations.get_recommendation(35)
            >>> rec == RecommendationType.STRONG_BUY
            True
        """
        if upside_pct > 30:
            return RecommendationType.STRONG_BUY, RecommendationColor.STRONG_BUY
        elif upside_pct > 15:
            return RecommendationType.BUY, RecommendationColor.BUY
        elif upside_pct > -15:
            return RecommendationType.HOLD, RecommendationColor.HOLD
        elif upside_pct > -30:
            return RecommendationType.SELL, RecommendationColor.SELL
        else:
            return RecommendationType.STRONG_SELL, RecommendationColor.STRONG_SELL

    @staticmethod
    def format_currency(value: float, decimals: int = 2, suffix: str = "") -> str:
        """
        Format currency values with appropriate scale.

        Args:
            value: Numeric value to format
            decimals: Number of decimal places
            suffix: Optional suffix (e.g., "B" for billions)

        Returns:
            Formatted string with thousands separators

        Examples:
            >>> ReportCalculations.format_currency(1234567.89)
            '$1,234,567.89'
            >>> ReportCalculations.format_currency(1.234e9, decimals=2, suffix='B')
            '$1.23B'
        """
        if suffix:
            return f"${value:,.{decimals}f}{suffix}"
        return f"${value:,.{decimals}f}"

    @staticmethod
    def format_percentage(value: float, decimals: int = 2) -> str:
        """
        Format percentage values.

        Args:
            value: Percentage value (e.g., 0.15 for 15% or 15 for 15%)
            decimals: Number of decimal places

        Returns:
            Formatted percentage string

        Examples:
            >>> ReportCalculations.format_percentage(0.15)
            '15.00%'
            >>> ReportCalculations.format_percentage(15.5, decimals=1)
            '15.5%'
        """
        # Handle both decimal (0.15) and percentage (15) input
        if abs(value) < 1 and value != 0:
            value = value * 100
        return f"{value:.{decimals}f}%"

    @staticmethod
    def calculate_discount_rate_spread(wacc: float, terminal_growth: float) -> float:
        """
        Calculate the spread between WACC and terminal growth.

        A healthy spread is typically 4-5 percentage points minimum.

        Args:
            wacc: Weighted Average Cost of Capital
            terminal_growth: Terminal growth rate

        Returns:
            Spread in percentage points

        Examples:
            >>> ReportCalculations.calculate_discount_rate_spread(0.10, 0.03)
            7.0  # 7 percentage points
        """
        return (wacc - terminal_growth) * 100

    @staticmethod
    def calculate_implied_perpetuity_multiple(
        wacc: float, terminal_growth: float
    ) -> float:
        """
        Calculate implied EV/FCF multiple in perpetuity.

        Formula: 1 / (WACC - g)

        Args:
            wacc: Weighted Average Cost of Capital
            terminal_growth: Terminal growth rate

        Returns:
            Implied perpetuity multiple

        Examples:
            >>> ReportCalculations.calculate_implied_perpetuity_multiple(0.10, 0.03)
            14.285...  # ~14.3x EV/FCF
        """
        if wacc <= terminal_growth:
            return 0.0
        return 1 / (wacc - terminal_growth)

    @staticmethod
    def validate_dcf_sanity(data: DCFReportData) -> List[str]:
        """
        Validate DCF model for common errors and warnings.

        Returns list of warning messages if any issues detected.

        Args:
            data: DCFReportData to validate

        Returns:
            List of warning strings (empty if all checks pass)

        Examples:
            >>> data = DCFReportData(...)
            >>> warnings = ReportCalculations.validate_dcf_sanity(data)
            >>> if warnings:
            ...     print("⚠️ Warnings:", warnings)
        """
        warnings = []

        # Check WACC vs terminal growth spread
        spread = (data.wacc - data.terminal_growth) * 100
        if spread < 4:
            warnings.append(
                f"⚠️ WACC-growth spread muy bajo ({spread:.1f}pp). "
                f"Mínimo recomendado: 4pp"
            )

        # Check if terminal growth is reasonable
        if data.terminal_growth > 0.05:
            warnings.append(
                f"⚠️ Terminal growth muy alto ({data.terminal_growth:.1%}). "
                f"Típicamente no debe exceder GDP + inflación (~3-4%)"
            )

        # Check if fair value is extremely different from market
        upside = ReportCalculations.calculate_upside(
            data.fair_value_per_share, data.market_price
        )
        if abs(upside) > 100:
            warnings.append(
                f"⚠️ Divergencia extrema del mercado ({upside:+.1f}%). "
                f"Revisar supuestos del modelo"
            )

        # Check if base FCF is negative
        if data.base_fcf < 0:
            warnings.append(
                "⚠️ FCF base negativo. DCF puede no ser apropiado. "
                "Considere usar método alternativo (P/B, P/E, DDM)"
            )

        return warnings

    @staticmethod
    def validate_ddm_sanity(data: DDMReportData) -> List[str]:
        """
        Validate DDM model for common errors and warnings.

        Args:
            data: DDMReportData to validate

        Returns:
            List of warning strings (empty if all checks pass)
        """
        warnings = []

        # Check cost of equity vs dividend growth spread
        spread = (data.cost_of_equity - data.dividend_growth_rate) * 100
        if spread < 2:
            warnings.append(
                f"⚠️ Cost of equity vs growth spread muy bajo ({spread:.1f}pp). "
                f"Gordon Model puede no ser estable"
            )

        # Check if dividend growth is reasonable
        if data.dividend_growth_rate > 0.10:
            warnings.append(
                f"⚠️ Dividend growth muy alto ({data.dividend_growth_rate:.1%}). "
                f"Considere usar Two-Stage DDM"
            )

        # Check payout ratio sustainability
        if data.payout_ratio > 0.80:
            warnings.append(
                f"⚠️ Payout ratio muy alto ({data.payout_ratio:.1%}). "
                f"Crecimiento de dividendos puede no ser sostenible"
            )

        # Check if current dividend exists
        if data.current_dividend <= 0:
            warnings.append("⚠️ Empresa no paga dividendos. DDM no es apropiado")

        return warnings


# Backward compatibility - expose calculations at module level
calculate_upside = ReportCalculations.calculate_upside
get_recommendation = ReportCalculations.get_recommendation
format_currency = ReportCalculations.format_currency
format_percentage = ReportCalculations.format_percentage
