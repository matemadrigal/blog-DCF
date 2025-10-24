"""
Bank Valuation Models - Optimized for Financial Institutions.

This module implements valuation models specifically designed for banks and
financial institutions, addressing the limitations of traditional DDM/DCF.

Models Implemented:
1. Residual Income Model (RIM) - Industry standard for banks
2. Price-to-Book (P/B) × ROE Model - Simple and effective
3. Excess Return Model - Variant of RIM
4. Hybrid Model - Weighted combination of all methods

References:
- CFA Institute: Residual Income Valuation (2025)
- Damodaran: Valuing Financial Services Firms
- McKinsey: Bank Valuation Handbook
"""

import logging
from typing import Dict, Tuple, Any, Optional

logger = logging.getLogger(__name__)


class BankValuation:
    """
    Valuation models optimized for banks and financial institutions.

    Why traditional DCF/DDM fails for banks:
    - Negative free cash flows (loans are "investments")
    - High leverage is normal (not distress signal)
    - Dividends don't reflect true earnings power
    - Book value is meaningful (unlike tech companies)

    Solution: Use RIM, P/B × ROE, or Hybrid approaches
    """

    def __init__(self, ticker: str):
        """Initialize bank valuation."""
        self.ticker = ticker
        self.logger = logging.getLogger(f"{__name__}.{ticker}")

    @staticmethod
    def residual_income_model(
        book_value_per_share: float,
        roe: float,
        cost_of_equity: float,
        forecast_years: int = 5,
        fade_years: int = 5,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Residual Income Model (RIM) - Industry standard for bank valuation.

        Formula (CFA Institute):
            V₀ = BV₀ + Σ[RI_t / (1+r)^t] + Terminal Value

            where:
                RI_t = (ROE_t - r) × BV_{t-1}
                BV_t = BV_{t-1} × (1 + ROE_t × retention_ratio)

        Key Concept:
            - Value = Book Value + PV(Excess Returns)
            - Excess Return = (ROE - Cost of Equity) × Book Value
            - If ROE > r: Bank creates value (trades above book)
            - If ROE < r: Bank destroys value (trades below book)

        Assumptions:
            - ROE fades to cost of equity over fade period
            - Book value grows with retained earnings
            - More realistic than perpetual growth models

        Best for:
            - Banks (ALL banks - this is the standard)
            - Insurance companies
            - Asset managers

        Args:
            book_value_per_share: Current book value per share
            roe: Return on Equity (as decimal)
            cost_of_equity: Required return (as decimal)
            forecast_years: Explicit forecast period (typically 5-10 years)
            fade_years: Years for ROE to fade to cost of equity

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        details = {
            "model": "Residual Income Model (RIM)",
            "formula": "V₀ = BV₀ + Σ[RI_t / (1+r)^t] + Terminal Value",
            "inputs": {
                "book_value_per_share": book_value_per_share,
                "roe": roe,
                "cost_of_equity": cost_of_equity,
                "forecast_years": forecast_years,
                "fade_years": fade_years,
            },
            "warnings": [],
            "errors": [],
            "yearly_details": [],
        }

        # Validation
        if book_value_per_share <= 0:
            details["errors"].append(
                f"Book value must be positive (current: ${book_value_per_share:.2f})"
            )
            return 0.0, details

        if roe <= 0:
            details["errors"].append(
                f"ROE must be positive (current: {roe:.2%})"
            )
            return 0.0, details

        if cost_of_equity <= 0:
            details["errors"].append(
                f"Cost of equity must be positive (current: {cost_of_equity:.2%})"
            )
            return 0.0, details

        # Validate reasonableness
        if roe < 0.03:
            details["warnings"].append(
                f"⚠️  Very low ROE ({roe:.2%}) - bank may be struggling"
            )
        elif roe > 0.25:
            details["warnings"].append(
                f"⚠️  Very high ROE ({roe:.2%}) - may not be sustainable"
            )

        # Calculate excess return (spread)
        excess_return = roe - cost_of_equity
        details["calculations"] = {
            "excess_return": excess_return,
            "excess_return_bps": excess_return * 10000,
        }

        if excess_return > 0:
            details["interpretation"] = (
                f"Bank creates value: ROE ({roe:.2%}) > Cost of Equity ({cost_of_equity:.2%})"
            )
        else:
            details["interpretation"] = (
                f"Bank destroys value: ROE ({roe:.2%}) < Cost of Equity ({cost_of_equity:.2%})"
            )

        # Assume payout ratio (typical for banks: 30-40%)
        # If ROE is high, retention is higher
        if roe > 0.15:
            payout_ratio = 0.35  # 35% payout, 65% retention
        elif roe > 0.10:
            payout_ratio = 0.40  # 40% payout, 60% retention
        else:
            payout_ratio = 0.50  # 50% payout (struggling banks pay less)

        retention_ratio = 1 - payout_ratio
        details["assumptions"] = {
            "payout_ratio": payout_ratio,
            "retention_ratio": retention_ratio,
        }

        # Explicit forecast period
        pv_residual_income = 0.0
        book_value = book_value_per_share

        for year in range(1, forecast_years + 1):
            # ROE fades linearly to cost of equity over fade_years
            if year <= fade_years:
                # Linear interpolation
                fade_factor = (fade_years - year + 1) / fade_years
                current_roe = cost_of_equity + (roe - cost_of_equity) * fade_factor
            else:
                # After fade period, ROE = cost of equity (no excess return)
                current_roe = cost_of_equity

            # Residual Income for this year
            # RI = (ROE - r) × BV_{t-1}
            residual_income = (current_roe - cost_of_equity) * book_value

            # Present value of residual income
            pv_ri = residual_income / ((1 + cost_of_equity) ** year)
            pv_residual_income += pv_ri

            # Book value grows with retained earnings
            # BV_t = BV_{t-1} × (1 + ROE × retention)
            book_value = book_value * (1 + current_roe * retention_ratio)

            details["yearly_details"].append({
                "year": year,
                "roe": current_roe,
                "book_value": book_value,
                "residual_income": residual_income,
                "pv_residual_income": pv_ri,
            })

        # Terminal value: After fade period, ROE = r, so RI = 0
        # No terminal value needed (conservative assumption)
        terminal_value = 0.0

        details["calculations"]["pv_residual_income"] = pv_residual_income
        details["calculations"]["terminal_value"] = terminal_value

        # Intrinsic value = Current BV + PV(Excess Returns)
        intrinsic_value = book_value_per_share + pv_residual_income

        details["intrinsic_value"] = intrinsic_value
        details["implied_pb_ratio"] = intrinsic_value / book_value_per_share

        return intrinsic_value, details

    @staticmethod
    def pb_roe_model(
        book_value_per_share: float,
        roe: float,
        cost_of_equity: float,
        growth_rate: float = 0.03,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Price-to-Book (P/B) × ROE Model - Simple and effective.

        Formula (Simplified RIM):
            Fair P/B = (ROE - g) / (r - g)
            Fair Value = Fair P/B × Book Value

            where:
                ROE = Return on Equity
                r = Cost of Equity
                g = Long-term growth rate

        Derivation from RIM:
            - Assumes constant ROE and growth
            - P/B ratio is function of ROE, r, and g
            - Higher ROE → Higher P/B
            - Higher r → Lower P/B

        Typical P/B Ratios:
            - ROE 15%, r 10%, g 3%: P/B ≈ 1.7x
            - ROE 10%, r 10%, g 3%: P/B ≈ 1.0x
            - ROE 5%, r 10%, g 3%: P/B ≈ 0.3x (below book)

        Best for:
            - Quick valuation check
            - Peer comparison
            - Mature banks with stable ROE

        Args:
            book_value_per_share: Current book value per share
            roe: Return on Equity (as decimal)
            cost_of_equity: Required return (as decimal)
            growth_rate: Long-term growth rate (typically 2-4%)

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        details = {
            "model": "P/B × ROE Model",
            "formula": "Fair P/B = (ROE - g) / (r - g)",
            "inputs": {
                "book_value_per_share": book_value_per_share,
                "roe": roe,
                "cost_of_equity": cost_of_equity,
                "growth_rate": growth_rate,
            },
            "warnings": [],
            "errors": [],
        }

        # Validation
        if book_value_per_share <= 0:
            details["errors"].append("Book value must be positive")
            return 0.0, details

        if roe <= 0:
            details["errors"].append("ROE must be positive")
            return 0.0, details

        if cost_of_equity <= growth_rate:
            details["errors"].append(
                f"Cost of equity ({cost_of_equity:.2%}) must be > growth rate ({growth_rate:.2%})"
            )
            return 0.0, details

        # Cap growth at 4% for conservatism
        if growth_rate > 0.04:
            growth_rate = 0.04
            details["warnings"].append(
                f"⚠️  Growth rate capped at 4% for conservatism"
            )

        # Calculate fair P/B ratio
        numerator = roe - growth_rate
        denominator = cost_of_equity - growth_rate

        if numerator <= 0:
            # ROE < g: Bank is not creating value even with growth
            fair_pb = 0.5  # Below book value
            details["warnings"].append(
                f"⚠️  ROE ({roe:.2%}) < growth ({growth_rate:.2%}): Bank destroys value"
            )
        else:
            fair_pb = numerator / denominator

        # Sanity bounds on P/B
        if fair_pb < 0.3:
            details["warnings"].append(
                f"⚠️  Very low P/B ({fair_pb:.2f}x) - bank may be in distress"
            )
            fair_pb = max(fair_pb, 0.3)  # Floor at 0.3x
        elif fair_pb > 4.0:
            details["warnings"].append(
                f"⚠️  Very high P/B ({fair_pb:.2f}x) - exceptional bank or overvalued"
            )
            fair_pb = min(fair_pb, 4.0)  # Cap at 4.0x

        details["calculations"] = {
            "fair_pb_ratio": fair_pb,
            "roe_minus_g": numerator,
            "r_minus_g": denominator,
        }

        # Fair value
        intrinsic_value = fair_pb * book_value_per_share
        details["intrinsic_value"] = intrinsic_value

        # Interpretation
        if fair_pb > 1.5:
            details["interpretation"] = f"High quality bank (P/B {fair_pb:.2f}x > 1.5x)"
        elif fair_pb > 1.0:
            details["interpretation"] = f"Average quality bank (P/B {fair_pb:.2f}x)"
        else:
            details["interpretation"] = f"Below-book bank (P/B {fair_pb:.2f}x < 1.0x)"

        return intrinsic_value, details

    @staticmethod
    def hybrid_bank_valuation(
        book_value_per_share: float,
        roe: float,
        cost_of_equity: float,
        dividend_per_share: float,
        growth_rate: float = 0.03,
        weights: Optional[Dict[str, float]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Hybrid Bank Valuation - Weighted combination of multiple methods.

        Combines:
        1. Residual Income Model (RIM) - 50% weight
        2. P/B × ROE Model - 30% weight
        3. DDM (if dividends exist) - 20% weight

        Rationale:
        - RIM is most theoretically sound for banks
        - P/B provides market-based reality check
        - DDM captures dividend policy (if applicable)

        Default Weights:
            - RIM: 50% (most important)
            - P/B: 30% (market validation)
            - DDM: 20% (dividend policy)

        Args:
            book_value_per_share: Current book value per share
            roe: Return on Equity (as decimal)
            cost_of_equity: Required return (as decimal)
            dividend_per_share: Annual dividend per share
            growth_rate: Long-term growth rate (2-4%)
            weights: Optional custom weights dict

        Returns:
            Tuple of (intrinsic_value_per_share, calculation_details)
        """
        # Default weights
        if weights is None:
            weights = {
                "rim": 0.50,
                "pb_roe": 0.30,
                "ddm": 0.20,
            }

        details = {
            "model": "Hybrid Bank Valuation",
            "formula": "Weighted average of RIM + P/B + DDM",
            "inputs": {
                "book_value_per_share": book_value_per_share,
                "roe": roe,
                "cost_of_equity": cost_of_equity,
                "dividend_per_share": dividend_per_share,
                "growth_rate": growth_rate,
            },
            "weights": weights,
            "warnings": [],
            "errors": [],
            "component_values": {},
        }

        # Validate total weights = 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.01:
            details["warnings"].append(
                f"⚠️  Weights sum to {total_weight:.2f}, normalizing to 1.0"
            )
            # Normalize weights
            weights = {k: v / total_weight for k, v in weights.items()}

        # 1. Residual Income Model
        rim_value, rim_details = BankValuation.residual_income_model(
            book_value_per_share=book_value_per_share,
            roe=roe,
            cost_of_equity=cost_of_equity,
            forecast_years=5,
            fade_years=5,
        )

        details["component_values"]["rim"] = rim_value
        details["rim_details"] = rim_details

        if rim_details.get("errors"):
            details["errors"].extend(rim_details["errors"])
            return 0.0, details

        # 2. P/B × ROE Model
        pb_value, pb_details = BankValuation.pb_roe_model(
            book_value_per_share=book_value_per_share,
            roe=roe,
            cost_of_equity=cost_of_equity,
            growth_rate=growth_rate,
        )

        details["component_values"]["pb_roe"] = pb_value
        details["pb_details"] = pb_details

        if pb_details.get("errors"):
            details["errors"].extend(pb_details["errors"])

        # 3. DDM (if dividends exist)
        if dividend_per_share > 0:
            # Simple Gordon Growth DDM
            # Use normalized growth (conservative)
            normalized_growth = min(growth_rate, 0.04)

            if cost_of_equity - normalized_growth < 0.02:
                # Not enough spread for DDM
                ddm_value = 0.0
                details["warnings"].append(
                    "⚠️  DDM skipped: insufficient spread (r - g < 2%)"
                )
            else:
                d1 = dividend_per_share * (1 + normalized_growth)
                ddm_value = d1 / (cost_of_equity - normalized_growth)
                details["component_values"]["ddm"] = ddm_value
        else:
            ddm_value = 0.0
            details["warnings"].append(
                "⚠️  DDM skipped: no dividends paid"
            )
            # Redistribute DDM weight to RIM and P/B
            if "ddm" in weights and weights["ddm"] > 0:
                ddm_weight = weights["ddm"]
                weights["rim"] += ddm_weight * 0.6  # 60% to RIM
                weights["pb_roe"] += ddm_weight * 0.4  # 40% to P/B
                weights["ddm"] = 0.0
                details["warnings"].append(
                    f"⚠️  DDM weight redistributed: {ddm_weight:.1%} → RIM/P/B"
                )

        # Calculate weighted average
        intrinsic_value = (
            weights["rim"] * rim_value +
            weights["pb_roe"] * pb_value +
            weights["ddm"] * ddm_value
        )

        details["intrinsic_value"] = intrinsic_value
        details["final_weights"] = weights

        # Value range (for sensitivity)
        values = [v for v in [rim_value, pb_value, ddm_value] if v > 0]
        if values:
            details["value_range"] = {
                "min": min(values),
                "max": max(values),
                "range_pct": ((max(values) - min(values)) / intrinsic_value) * 100
                if intrinsic_value > 0
                else 0,
            }

        return intrinsic_value, details


def get_fair_value_bank(
    ticker: str,
    book_value_per_share: float,
    roe: float,
    cost_of_equity: float,
    dividend_per_share: float = 0.0,
    growth_rate: float = 0.03,
    method: str = "hybrid",
) -> Tuple[float, Dict[str, Any]]:
    """
    Unified function to get fair value for a bank using the best method.

    This is the ONE function you should use for bank valuation.

    Args:
        ticker: Stock ticker
        book_value_per_share: Current book value per share
        roe: Return on Equity (as decimal, e.g., 0.15 for 15%)
        cost_of_equity: Required return (as decimal)
        dividend_per_share: Annual dividend per share (optional)
        growth_rate: Long-term growth rate (default 3%)
        method: Valuation method - "hybrid" (default), "rim", "pb_roe"

    Returns:
        Tuple of (fair_value_per_share, details)

    Example:
        >>> fair_value, details = get_fair_value_bank(
        ...     ticker="JPM",
        ...     book_value_per_share=95.00,
        ...     roe=0.164,
        ...     cost_of_equity=0.1076,
        ...     dividend_per_share=5.55,
        ... )
        >>> print(f"Fair Value: ${fair_value:.2f}")
    """
    valuation = BankValuation(ticker)

    if method == "rim":
        return valuation.residual_income_model(
            book_value_per_share=book_value_per_share,
            roe=roe,
            cost_of_equity=cost_of_equity,
        )
    elif method == "pb_roe":
        return valuation.pb_roe_model(
            book_value_per_share=book_value_per_share,
            roe=roe,
            cost_of_equity=cost_of_equity,
            growth_rate=growth_rate,
        )
    elif method == "hybrid":
        return valuation.hybrid_bank_valuation(
            book_value_per_share=book_value_per_share,
            roe=roe,
            cost_of_equity=cost_of_equity,
            dividend_per_share=dividend_per_share,
            growth_rate=growth_rate,
        )
    else:
        raise ValueError(f"Unknown method: {method}. Use 'rim', 'pb_roe', or 'hybrid'")
