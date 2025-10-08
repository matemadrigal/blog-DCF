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
    Predict future growth rates using linear regression on historical growth rates.

    Args:
        fcf_history: List of historical FCF values (at least 2 values required)
        years_to_predict: Number of years to predict growth rates for

    Returns:
        List of predicted growth rates for each future year
    """
    if len(fcf_history) < 2:
        # Not enough data, return conservative 2% growth
        return [0.02] * years_to_predict

    # Calculate historical growth rates
    growth_rates = calculate_historical_growth_rates(fcf_history)

    if len(growth_rates) == 0:
        # All zeros or single value, return conservative growth
        return [0.02] * years_to_predict

    # Simple linear regression on growth rates
    # x = year index, y = growth rate
    x = np.arange(len(growth_rates))
    y = np.array(growth_rates)

    # Handle outliers by capping extreme values
    y = np.clip(y, -0.5, 2.0)  # Cap between -50% and +200%

    # Linear regression: y = mx + b
    if len(x) > 1:
        m, b = np.polyfit(x, y, 1)
    else:
        # Single growth rate, use it as baseline
        m = 0
        b = y[0]

    # Predict future growth rates
    predicted_rates = []
    for i in range(years_to_predict):
        future_x = len(growth_rates) + i
        predicted_rate = m * future_x + b

        # Apply conservative constraints
        # Growth rates shouldn't be too extreme
        predicted_rate = max(-0.2, min(0.3, predicted_rate))  # Between -20% and +30%

        # If trend is negative, gradually converge to 0% (no growth)
        if m < 0 and predicted_rate < 0:
            # Gradually reduce negative impact
            decay_factor = 1 / (i + 1)
            predicted_rate = predicted_rate * decay_factor

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
