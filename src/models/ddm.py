"""
Dividend Discount Model (DDM) Implementation.

This module implements multiple DDM variants following CFA Institute methodology
and industry best practices from Wall Street institutions.

Models Implemented:
1. Gordon Growth Model (Constant Growth DDM)
2. Two-Stage DDM
3. H-Model (Half-Life Growth Model)

References:
- CFA Institute: Discounted Dividend Valuation (2025)
- Wall Street Prep: DDM Methodology
- Aswath Damodaran: DDM Framework
"""

import logging
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class DDMValuation:
    """
    Dividend Discount Model implementation with multiple variants.

    Particularly suitable for:
    - Banks and financial institutions
    - Insurance companies
    - Mature companies with stable dividend policies
    - REITs (Real Estate Investment Trusts)
    """

    def __init__(self, ticker: str):
        """
        Initialize DDM valuation.

        Args:
            ticker: Stock ticker symbol
        """
        self.ticker = ticker
        self.logger = logging.getLogger(f"{__name__}.{ticker}")

    @staticmethod
    def calculate_sustainable_growth_rate(roe: float, payout_ratio: float) -> float:
        """
        Calculate sustainable growth rate using retention ratio.

        Formula (CFA Institute):
            g = b × ROE
            where b = retention ratio = 1 - payout_ratio

        Args:
            roe: Return on Equity (as decimal, e.g., 0.15 for 15%)
            payout_ratio: Dividend payout ratio (as decimal, e.g., 0.40 for 40%)

        Returns:
            Sustainable growth rate (as decimal)
        """
        retention_ratio = 1 - payout_ratio
        return retention_ratio * roe

    @staticmethod
    def gordon_growth_model(
        dividend_per_share: float,
        cost_of_equity: float,
        growth_rate: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Gordon Growth Model (Constant Growth DDM).

        Formula (CFA Institute):
            V₀ = D₁ / (r - g)
            where:
                V₀ = Intrinsic value per share
                D₁ = Expected dividend next year
                r = Required rate of return (cost of equity)
                g = Constant dividend growth rate

        Assumptions:
        - Dividends grow at constant rate g forever
        - g < r (growth rate less than discount rate)
        - Company has stable dividend policy

        Best for:
        - Mature companies with predictable dividends
        - Banks with stable dividend policies

        Args:
            dividend_per_share: Most recent annual dividend per share (D₀)
            cost_of_equity: Required rate of return (as decimal)
            growth_rate: Constant dividend growth rate (as decimal)

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        details = {
            "model": "Gordon Growth Model (Constant Growth DDM)",
            "formula": "V₀ = D₁ / (r - g)",
            "inputs": {
                "D₀ (Current Dividend)": dividend_per_share,
                "r (Cost of Equity)": cost_of_equity,
                "g (Growth Rate)": growth_rate,
            },
            "warnings": [],
            "errors": [],
        }

        # Validation
        if dividend_per_share <= 0:
            details["errors"].append(
                f"Dividend must be positive (current: ${dividend_per_share:.2f})"
            )
            return 0.0, details

        if cost_of_equity <= 0:
            details["errors"].append(
                f"Cost of equity must be positive (current: {cost_of_equity:.2%})"
            )
            return 0.0, details

        if growth_rate >= cost_of_equity:
            details["errors"].append(
                f"Growth rate ({growth_rate:.2%}) must be less than cost of equity ({cost_of_equity:.2%})"
            )
            return 0.0, details

        if growth_rate < 0:
            details["warnings"].append(
                f"⚠️  Negative growth rate ({growth_rate:.2%}) - implies declining dividends"
            )

        if growth_rate > 0.10:
            details["warnings"].append(
                f"⚠️  High growth rate ({growth_rate:.2%}) - perpetual growth >10% may be unrealistic"
            )

        # Calculate D₁ (next year's dividend)
        d1 = dividend_per_share * (1 + growth_rate)
        details["calculations"] = {"D₁ (Next Year Dividend)": d1}

        # Calculate intrinsic value
        intrinsic_value = d1 / (cost_of_equity - growth_rate)
        details["intrinsic_value"] = intrinsic_value

        return intrinsic_value, details

    @staticmethod
    def two_stage_ddm(
        dividend_per_share: float,
        cost_of_equity: float,
        high_growth_rate: float,
        stable_growth_rate: float,
        high_growth_years: int,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Two-Stage Dividend Discount Model.

        Formula (CFA Institute):
            V₀ = PV(High Growth Dividends) + PV(Terminal Value)

            Stage 1 (High Growth):
                PV = Σ[D₀(1+g_h)^t / (1+r)^t] for t=1 to n

            Stage 2 (Stable Growth):
                Terminal Value = D_{n+1} / (r - g_l)
                PV(Terminal Value) = TV / (1+r)^n

        Assumptions:
        - Initial period of high growth (e.g., 5-10 years)
        - Then perpetual stable growth
        - Sudden transition from high to stable growth

        Best for:
        - Growing financial institutions
        - Companies transitioning to maturity

        Args:
            dividend_per_share: Most recent annual dividend per share (D₀)
            cost_of_equity: Required rate of return (as decimal)
            high_growth_rate: Growth rate during high growth period (as decimal)
            stable_growth_rate: Perpetual growth rate after transition (as decimal)
            high_growth_years: Number of years of high growth

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        details = {
            "model": "Two-Stage Dividend Discount Model",
            "formula": "V₀ = Σ PV(High Growth Dividends) + PV(Terminal Value)",
            "inputs": {
                "D₀ (Current Dividend)": dividend_per_share,
                "r (Cost of Equity)": cost_of_equity,
                "g_high (High Growth Rate)": high_growth_rate,
                "g_stable (Stable Growth Rate)": stable_growth_rate,
                "n (High Growth Years)": high_growth_years,
            },
            "warnings": [],
            "errors": [],
            "stage_1_dividends": [],
            "stage_2_terminal_value": 0.0,
        }

        # Validation
        if dividend_per_share <= 0:
            details["errors"].append(
                f"Dividend must be positive (current: ${dividend_per_share:.2f})"
            )
            return 0.0, details

        if cost_of_equity <= 0:
            details["errors"].append(
                f"Cost of equity must be positive (current: {cost_of_equity:.2%})"
            )
            return 0.0, details

        if stable_growth_rate >= cost_of_equity:
            details["errors"].append(
                f"Stable growth rate ({stable_growth_rate:.2%}) must be less than cost of equity ({cost_of_equity:.2%})"
            )
            return 0.0, details

        if high_growth_years <= 0 or high_growth_years > 20:
            details["warnings"].append(
                f"⚠️  High growth period should typically be 5-10 years (current: {high_growth_years})"
            )

        if stable_growth_rate > 0.05:
            details["warnings"].append(
                f"⚠️  Stable growth rate ({stable_growth_rate:.2%}) seems high - consider using <5% for perpetuity"
            )

        # Stage 1: Present value of high growth dividends
        pv_high_growth = 0.0
        dividend = dividend_per_share

        for year in range(1, high_growth_years + 1):
            # Calculate dividend for this year
            dividend = dividend * (1 + high_growth_rate)

            # Calculate present value
            pv = dividend / ((1 + cost_of_equity) ** year)
            pv_high_growth += pv

            details["stage_1_dividends"].append(
                {
                    "year": year,
                    "dividend": dividend,
                    "pv": pv,
                }
            )

        # Stage 2: Terminal value using Gordon Growth Model
        # D_{n+1} = D_n * (1 + g_stable)
        terminal_dividend = dividend * (1 + stable_growth_rate)
        terminal_value = terminal_dividend / (cost_of_equity - stable_growth_rate)

        # Present value of terminal value
        pv_terminal = terminal_value / ((1 + cost_of_equity) ** high_growth_years)

        details["stage_2_terminal_value"] = terminal_value
        details["stage_2_pv_terminal"] = pv_terminal
        details["calculations"] = {
            "PV(High Growth Dividends)": pv_high_growth,
            "Terminal Value": terminal_value,
            "PV(Terminal Value)": pv_terminal,
        }

        # Total intrinsic value
        intrinsic_value = pv_high_growth + pv_terminal
        details["intrinsic_value"] = intrinsic_value

        return intrinsic_value, details

    @staticmethod
    def h_model(
        dividend_per_share: float,
        cost_of_equity: float,
        initial_growth_rate: float,
        stable_growth_rate: float,
        half_life_years: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        H-Model (Half-Life Growth Model).

        Formula (CFA Institute):
            V₀ = D₀(1+g_L)/(r-g_L) + D₀×H×(g_S-g_L)/(r-g_L)

            where:
                D₀ = Current dividend
                r = Cost of equity
                g_S = Initial high growth rate
                g_L = Long-term stable growth rate
                H = Half-life (years for growth to decline linearly from g_S to g_L)

        Assumptions:
        - Growth declines LINEARLY from high to stable rate
        - More realistic than sudden transition in two-stage model
        - Smoother transition period

        Best for:
        - Companies with gradual growth decline
        - More realistic growth transition assumptions

        Args:
            dividend_per_share: Most recent annual dividend per share (D₀)
            cost_of_equity: Required rate of return (as decimal)
            initial_growth_rate: Initial high growth rate (as decimal)
            stable_growth_rate: Long-term stable growth rate (as decimal)
            half_life_years: Years for growth to decline linearly (typically 5-10)

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        details = {
            "model": "H-Model (Half-Life Growth Model)",
            "formula": "V₀ = D₀(1+g_L)/(r-g_L) + D₀×H×(g_S-g_L)/(r-g_L)",
            "inputs": {
                "D₀ (Current Dividend)": dividend_per_share,
                "r (Cost of Equity)": cost_of_equity,
                "g_S (Initial Growth Rate)": initial_growth_rate,
                "g_L (Stable Growth Rate)": stable_growth_rate,
                "H (Half-Life Years)": half_life_years,
            },
            "warnings": [],
            "errors": [],
        }

        # Validation
        if dividend_per_share <= 0:
            details["errors"].append(
                f"Dividend must be positive (current: ${dividend_per_share:.2f})"
            )
            return 0.0, details

        if cost_of_equity <= 0:
            details["errors"].append(
                f"Cost of equity must be positive (current: {cost_of_equity:.2%})"
            )
            return 0.0, details

        if stable_growth_rate >= cost_of_equity:
            details["errors"].append(
                f"Stable growth rate ({stable_growth_rate:.2%}) must be less than cost of equity ({cost_of_equity:.2%})"
            )
            return 0.0, details

        if initial_growth_rate < stable_growth_rate:
            details["warnings"].append(
                f"⚠️  Initial growth ({initial_growth_rate:.2%}) should be higher than stable growth ({stable_growth_rate:.2%})"
            )

        if half_life_years <= 0 or half_life_years > 15:
            details["warnings"].append(
                f"⚠️  Half-life should typically be 5-10 years (current: {half_life_years})"
            )

        # H-Model calculation
        # Component 1: Stable growth value
        stable_component = (
            dividend_per_share
            * (1 + stable_growth_rate)
            / (cost_of_equity - stable_growth_rate)
        )

        # Component 2: Excess growth value
        excess_component = (
            dividend_per_share
            * half_life_years
            * (initial_growth_rate - stable_growth_rate)
            / (cost_of_equity - stable_growth_rate)
        )

        intrinsic_value = stable_component + excess_component

        details["calculations"] = {
            "Stable Growth Component": stable_component,
            "Excess Growth Component": excess_component,
        }
        details["intrinsic_value"] = intrinsic_value

        return intrinsic_value, details

    @staticmethod
    def validate_ddm_inputs(
        dividend_per_share: float,
        cost_of_equity: float,
        growth_rate: float,
        shares_outstanding: int,
    ) -> Tuple[bool, List[str]]:
        """
        Validate DDM inputs before calculation.

        Args:
            dividend_per_share: Annual dividend per share
            cost_of_equity: Required rate of return
            growth_rate: Dividend growth rate
            shares_outstanding: Number of shares outstanding

        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        errors = []
        warnings = []

        # Validate dividend
        if dividend_per_share <= 0:
            errors.append(
                "⛔ Dividend per share must be positive - company may not pay dividends"
            )
        elif dividend_per_share > 1000:
            warnings.append(
                f"⚠️  Dividend per share (${dividend_per_share:.2f}) seems very high - verify units"
            )

        # Validate cost of equity
        if cost_of_equity <= 0:
            errors.append("⛔ Cost of equity must be positive")
        elif cost_of_equity < 0.05:
            warnings.append(
                f"⚠️  Cost of equity ({cost_of_equity:.2%}) seems low - typical range is 8-15%"
            )
        elif cost_of_equity > 0.30:
            warnings.append(
                f"⚠️  Cost of equity ({cost_of_equity:.2%}) seems very high - verify calculation"
            )

        # Validate growth rate
        if growth_rate >= cost_of_equity:
            errors.append(
                f"⛔ Growth rate ({growth_rate:.2%}) must be less than cost of equity ({cost_of_equity:.2%})"
            )
        elif growth_rate < -0.10:
            warnings.append(
                f"⚠️  Large negative growth rate ({growth_rate:.2%}) - company may be in distress"
            )
        elif growth_rate > 0.10:
            warnings.append(
                f"⚠️  High perpetual growth ({growth_rate:.2%}) may be unrealistic - consider two-stage model"
            )

        # Validate shares
        if shares_outstanding <= 0:
            errors.append("⛔ Shares outstanding must be positive")
        elif shares_outstanding < 1000:
            warnings.append(
                f"⚠️  Shares outstanding ({shares_outstanding:,}) seems low - verify units (millions vs. actual shares)"
            )

        # Combine messages
        all_messages = errors + warnings
        is_valid = len(errors) == 0

        return is_valid, all_messages

    @staticmethod
    def calculate_implied_growth_rate(
        current_price: float,
        dividend_per_share: float,
        cost_of_equity: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate implied growth rate from current market price (reverse DDM).

        Rearranging Gordon Growth Model:
            g = r - D₁/P₀

        Useful for:
        - Understanding market expectations
        - Comparing with fundamental growth estimates

        Args:
            current_price: Current market price per share
            dividend_per_share: Current annual dividend per share
            cost_of_equity: Required rate of return

        Returns:
            Tuple of (implied_growth_rate, details)
        """
        details = {
            "calculation": "Implied Growth Rate (Reverse DDM)",
            "formula": "g = r - D₁/P₀",
            "inputs": {
                "P₀ (Current Price)": current_price,
                "D₀ (Current Dividend)": dividend_per_share,
                "r (Cost of Equity)": cost_of_equity,
            },
        }

        if current_price <= 0:
            details["error"] = "Current price must be positive"
            return 0.0, details

        if dividend_per_share <= 0:
            details["error"] = "Dividend must be positive"
            return 0.0, details

        # Calculate implied growth rate
        # From Gordon Model: V = D₁/(r-g) where D₁ = D₀(1+g)
        # Substituting: V = D₀(1+g)/(r-g)
        # Rearranging: V(r-g) = D₀(1+g)
        #              Vr - Vg = D₀ + D₀g
        #              Vr - D₀ = Vg + D₀g
        #              Vr - D₀ = g(V + D₀)
        #              g = (Vr - D₀)/(V + D₀)
        #
        # This is the exact formula for implied growth rate

        numerator = current_price * cost_of_equity - dividend_per_share
        denominator = current_price + dividend_per_share

        if denominator == 0:
            details["error"] = "Cannot calculate implied growth (denominator zero)"
            return 0.0, details

        implied_growth = numerator / denominator

        details["implied_growth_rate"] = implied_growth
        details["interpretation"] = (
            f"Market expects {implied_growth:.2%} perpetual dividend growth"
        )
        details["formula_used"] = "g = (V×r - D₀)/(V + D₀)"

        return implied_growth, details
