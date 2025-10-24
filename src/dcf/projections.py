"""FCF projection utilities using growth rates instead of absolute values."""

from typing import List, Tuple, Dict, Optional
import numpy as np


def calculate_historical_growth_rates(fcf_history: List[float]) -> List[float]:
    """
    Calculate year-over-year growth rates from historical FCF data.

    [AuditFix] Corrected to preserve sign and handle negative-to-positive transitions.

    Formula:
        g = (FCF_t - FCF_{t-1}) / |FCF_{t-1}|

    This formula correctly handles:
    1. Both positive: standard growth
    2. Both negative: growth in losses (more negative = worse, less negative = better)
    3. Negative to positive: large positive growth (turnaround)
    4. Positive to negative: large negative growth (distress)

    Edge cases:
    - Zero previous FCF: Cap at ±500% to avoid infinity
    - Extreme growth: Cap at [-100%, +500%] to avoid distorting statistics

    Args:
        fcf_history: List of historical FCF values (ordered chronologically)

    Returns:
        List of growth rates (as decimals, e.g., 0.05 for 5% growth)
    """
    growth_rates = []

    for i in range(1, len(fcf_history)):
        fcf_prev = fcf_history[i - 1]
        fcf_curr = fcf_history[i]

        # [AuditFix] Handle zero previous FCF explicitly
        if fcf_prev == 0:
            if fcf_curr > 0:
                # 0 to positive: cap at +500% (conceptually infinite growth)
                growth_rates.append(5.0)
            elif fcf_curr < 0:
                # 0 to negative: cap at -100% (became loss-making)
                growth_rates.append(-1.0)
            else:
                # [BugFix #1] both zero: add 0% growth (maintain index alignment)
                # Previous bug: continue without appending caused len(growth_rates) != len(fcf_history) - 1
                growth_rates.append(0.0)
            continue

        # [AuditFix] Standard growth calculation (preserves sign correctly)
        # Formula: g = (FCF_t - FCF_{t-1}) / |FCF_{t-1}|
        #
        # Why abs() in denominator is correct:
        # - If FCF -100 to -50: g = (-50 - (-100))/100 = +50% ✓ (improving)
        # - If FCF -100 to -150: g = (-150 - (-100))/100 = -50% ✓ (worsening)
        # - If FCF -100 to +50: g = (50 - (-100))/100 = +150% ✓ (turnaround)
        # - If FCF +100 to -50: g = (-50 - 100)/100 = -150% ✓ (distress)
        growth = (fcf_curr - fcf_prev) / abs(fcf_prev)

        # [AuditFix] Cap extreme growth rates to avoid distorting median/mean
        # Caps prevent single outlier from dominating projected growth
        if growth > 5.0:
            growth = 5.0  # Cap at +500% (turnaround already captured)
        elif growth < -1.0:
            growth = -1.0  # Cap at -100% (can't lose more than 100% of base)

        growth_rates.append(growth)

    return growth_rates


def predict_growth_rate_linear_regression(
    fcf_history: List[float], years_to_predict: int = 5
) -> List[float]:
    """
    Predict future growth rates using intelligent analysis of historical data.

    Strategy:
    1. Calculate historical growth rates
    2. Use median growth (robust to outliers)
    3. Apply conservative decay for projections
    4. Never project persistent negative growth (use GDP floor)

    Args:
        fcf_history: List of historical FCF values (at least 2 values required)
        years_to_predict: Number of years to predict growth rates for

    Returns:
        List of predicted growth rates for each future year
    """
    if len(fcf_history) < 2:
        # Not enough data, return conservative GDP growth
        return [0.025] * years_to_predict

    # Calculate historical growth rates
    growth_rates = calculate_historical_growth_rates(fcf_history)

    if len(growth_rates) == 0:
        # All zeros or single value, return conservative growth
        return [0.025] * years_to_predict

    # Use median for robustness (less sensitive to outliers)
    median_growth = float(np.median(growth_rates))

    # Calculate average for recent trend
    recent_growth = (
        float(np.mean(growth_rates[-3:])) if len(growth_rates) >= 3 else median_growth
    )

    # Conservative floor: GDP growth rate (2.5%)
    GDP_FLOOR = 0.025

    # If historical growth is negative, gradually converge to GDP floor
    if median_growth < 0:
        # Start from current trend but converge to GDP floor
        predicted_rates = []
        for i in range(years_to_predict):
            # Exponential decay towards GDP floor
            weight = np.exp(-i * 0.5)  # Faster convergence
            predicted_rate = recent_growth * weight + GDP_FLOOR * (1 - weight)

            # Floor at 0% (no company should have persistent negative FCF growth in DCF)
            predicted_rate = max(0.0, predicted_rate)
            predicted_rates.append(predicted_rate)

        return predicted_rates

    # If historical growth is positive, use tiered decay
    else:
        # High growth gradually decays to sustainable terminal rate
        predicted_rates = []

        # Start from recent growth
        base_rate = max(recent_growth, median_growth)

        # Cap extreme growth
        base_rate = min(0.40, base_rate)  # Max 40% (unrealistic beyond this)

        for i in range(years_to_predict):
            # Decay formula: higher growth decays faster
            if base_rate > 0.30:  # Very high growth (>30%)
                decay = 0.85 ** (i + 1)  # Fast decay
            elif base_rate > 0.15:  # High growth (15-30%)
                decay = 0.90 ** (i + 1)  # Medium decay
            else:  # Moderate growth (<15%)
                decay = 0.95 ** (i + 1)  # Slow decay

            predicted_rate = base_rate * decay

            # Converge towards sustainable terminal growth (3-5%)
            terminal_rate = 0.04  # 4% sustainable long-term
            predicted_rate = max(predicted_rate, terminal_rate)

            predicted_rates.append(predicted_rate)

        return predicted_rates


def apply_growth_rates_to_base(
    base_fcf: float, growth_rates: List[float]
) -> List[float]:
    """
    Apply growth rates to a base FCF value to generate projected FCF.

    Args:
        base_fcf: Base year FCF value
        growth_rates: List of growth rates to apply (one per year)

    Returns:
        List of projected FCF values
    """
    projections = []
    current_fcf = base_fcf

    for rate in growth_rates:
        current_fcf = current_fcf * (1 + rate)
        projections.append(current_fcf)

    return projections


def get_average_historical_growth(fcf_history: List[float]) -> float:
    """
    Calculate the average historical growth rate.

    Args:
        fcf_history: List of historical FCF values

    Returns:
        Average growth rate as decimal
    """
    growth_rates = calculate_historical_growth_rates(fcf_history)
    if not growth_rates:
        return 0.02  # Default 2%

    # Use median to reduce impact of outliers
    return float(np.median(growth_rates))


# ============================================================================
# [AuditFix] REINVESTMENT RATE CONSISTENCY
# ============================================================================
# These functions ensure FCF growth is consistent with capital deployment
# Formula: g = Reinvestment Rate × ROIC (Damodaran)
# ============================================================================


def calculate_implied_reinvestment_rate(
    fcf_growth_rate: float,
    roic: float = 0.15,
) -> float:
    """
    Calculate implied reinvestment rate for given FCF growth.

    [AuditFix] Ensures growth and reinvestment are mathematically consistent.

    Formula (Damodaran):
        Reinvestment Rate = g / ROIC

    Where:
        g = FCF growth rate (or revenue/EBIT growth as proxy)
        ROIC = Return on Invested Capital

    This formula is fundamental:
    - If g = 10% and ROIC = 20%: Need to reinvest 50% of EBIT
    - If g = 10% and ROIC = 10%: Need to reinvest 100% of EBIT
    - If g > ROIC: Impossible to sustain (reinvestment > 100%)

    Args:
        fcf_growth_rate: Expected FCF growth rate (as decimal)
        roic: Return on Invested Capital (typical 12-20% for healthy companies)

    Returns:
        Implied reinvestment rate (as decimal, 0-1)

    Example:
        >>> calculate_implied_reinvestment_rate(0.10, 0.15)
        0.667  # Need to reinvest 66.7% to grow at 10% with 15% ROIC

        >>> calculate_implied_reinvestment_rate(0.20, 0.15)
        1.333  # Impossible! Can't reinvest >100%
    """
    # [BugFix #3] ROIC <= 0 should raise error, not silently return 0
    # Negative/zero ROIC means company destroys value - this is critical input error
    if roic <= 0:
        raise ValueError(
            f"ROIC must be positive. Got: {roic:.2%}. "
            f"Negative or zero ROIC means the company destroys value. "
            f"Check your ROIC calculation or use a different valuation method."
        )

    reinvestment_rate = fcf_growth_rate / roic

    # Cap at 100% (can't reinvest more than you earn)
    # If this triggers, growth rate is too high for given ROIC
    if reinvestment_rate > 1.0:
        return 1.0

    # Floor at 0% (can't have negative reinvestment)
    if reinvestment_rate < 0:
        return 0.0

    return reinvestment_rate


def validate_fcf_growth_consistency(
    fcf_growth: float,
    roic: float,
    max_reinvestment_rate: float = 0.80,
) -> Tuple[bool, float, List[str]]:
    """
    Validate that FCF growth is consistent with sustainable reinvestment.

    [AuditFix] Prevents unrealistic growth projections.

    Args:
        fcf_growth: Projected FCF growth rate
        roic: Return on Invested Capital
        max_reinvestment_rate: Maximum sustainable reinvestment (default 80%)

    Returns:
        Tuple of (is_consistent, adjusted_growth, warnings)
    """
    warnings = []

    # Calculate implied reinvestment
    implied_reinv = calculate_implied_reinvestment_rate(fcf_growth, roic)

    # Check if sustainable
    if implied_reinv > max_reinvestment_rate:
        warnings.append(
            f"⚠️  Growth {fcf_growth:.1%} requires {implied_reinv:.1%} reinvestment "
            f"(max sustainable: {max_reinvestment_rate:.1%})"
        )

        # Calculate sustainable growth given max reinvestment
        sustainable_growth = max_reinvestment_rate * roic
        warnings.append(
            f"💡 Sustainable growth with {max_reinvestment_rate:.1%} reinvestment: "
            f"{sustainable_growth:.1%}"
        )

        return False, sustainable_growth, warnings

    # Growth is sustainable
    return True, fcf_growth, warnings


def adjust_growth_rates_for_reinvestment(
    growth_rates: List[float],
    roic: float = 0.15,
    max_reinvestment_rate: float = 0.80,
) -> Tuple[List[float], Dict]:
    """
    Adjust projected growth rates to ensure reinvestment consistency.

    [AuditFix] Applied to forecast period to prevent unrealistic projections.

    Args:
        growth_rates: List of projected growth rates
        roic: Return on Invested Capital
        max_reinvestment_rate: Maximum sustainable reinvestment rate

    Returns:
        Tuple of (adjusted_growth_rates, adjustment_details)
    """
    adjusted_rates = []
    adjustments_made = []

    for i, g in enumerate(growth_rates):
        is_consistent, adjusted_g, warnings = validate_fcf_growth_consistency(
            g, roic, max_reinvestment_rate
        )

        if not is_consistent:
            adjustments_made.append({
                "year": i + 1,
                "original_growth": g,
                "adjusted_growth": adjusted_g,
                "implied_reinvestment_original": calculate_implied_reinvestment_rate(g, roic),
                "implied_reinvestment_adjusted": calculate_implied_reinvestment_rate(adjusted_g, roic),
                "warnings": warnings,
            })

        adjusted_rates.append(adjusted_g)

    details = {
        "roic_used": roic,
        "max_reinvestment_rate": max_reinvestment_rate,
        "adjustments_made": adjustments_made,
        "num_adjustments": len(adjustments_made),
    }

    return adjusted_rates, details


def calculate_terminal_reinvestment_rate(
    terminal_growth: float,
    roic: float = 0.15,
) -> float:
    """
    Calculate required reinvestment rate for terminal growth.

    [AuditFix] Links terminal value growth to sustainable reinvestment.

    In perpetuity, reinvestment must be sustainable:
    - Terminal g should be low (2-4%)
    - Implies low reinvestment (13-27% with ROIC=15%)
    - This is realistic for mature companies

    Args:
        terminal_growth: Perpetual growth rate
        roic: Return on Invested Capital

    Returns:
        Terminal period reinvestment rate
    """
    return calculate_implied_reinvestment_rate(terminal_growth, roic)
