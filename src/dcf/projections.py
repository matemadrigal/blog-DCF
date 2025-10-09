"""FCF projection utilities using growth rates instead of absolute values."""

from typing import List
import numpy as np


def calculate_historical_growth_rates(fcf_history: List[float]) -> List[float]:
    """
    Calculate year-over-year growth rates from historical FCF data.

    Args:
        fcf_history: List of historical FCF values (ordered chronologically)

    Returns:
        List of growth rates (as decimals, e.g., 0.05 for 5% growth)
    """
    growth_rates = []
    for i in range(1, len(fcf_history)):
        if fcf_history[i - 1] != 0:
            growth = (fcf_history[i] - fcf_history[i - 1]) / abs(fcf_history[i - 1])
            growth_rates.append(growth)
        else:
            # Skip if previous value is zero
            continue
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
