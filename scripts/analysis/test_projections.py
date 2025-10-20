"""Test script for FCF projection functionality."""

from src.dcf.projections import (
    predict_growth_rate_linear_regression,
    apply_growth_rates_to_base,
    calculate_historical_growth_rates,
)

# Test with sample historical FCF data (in millions)
historical_fcf = [
    10000,  # 5 years ago
    11000,  # 4 years ago (10% growth)
    12100,  # 3 years ago (10% growth)
    13310,  # 2 years ago (10% growth)
    14641,  # 1 year ago (10% growth)
]

print("=" * 60)
print("Testing FCF Projection System with Growth Rates")
print("=" * 60)
print()

# Calculate historical growth rates
print("Historical FCF (millions):")
for i, fcf in enumerate(historical_fcf, 1):
    print(f"  Year {i}: ${fcf:,.0f}M")
print()

growth_rates = calculate_historical_growth_rates(historical_fcf)
print("Historical Growth Rates:")
for i, rate in enumerate(growth_rates, 1):
    print(f"  Year {i} -> {i+1}: {rate*100:+.2f}%")
print()

# Predict future growth rates
years_to_predict = 5
predicted_rates = predict_growth_rate_linear_regression(
    historical_fcf, years_to_predict
)

print(f"Predicted Growth Rates (next {years_to_predict} years):")
for i, rate in enumerate(predicted_rates, 1):
    print(f"  Year {i}: {rate*100:+.2f}%")
print()

# Apply predicted rates to base FCF
base_fcf = historical_fcf[-1]  # Most recent year
projected_fcf = apply_growth_rates_to_base(base_fcf, predicted_rates)

print(f"Base Year FCF: ${base_fcf:,.0f}M")
print()
print("Projected FCF (applying growth rates):")
for i, (fcf, rate) in enumerate(zip(projected_fcf, predicted_rates), 1):
    print(f"  Year {i}: ${fcf:,.0f}M (growth: {rate*100:+.2f}%)")
print()

# Test with negative/declining growth
print("=" * 60)
print("Testing with Declining FCF")
print("=" * 60)
print()

declining_fcf = [
    15000,  # 5 years ago
    14000,  # 4 years ago (-6.7% growth)
    13000,  # 3 years ago (-7.1% growth)
    12000,  # 2 years ago (-7.7% growth)
    11000,  # 1 year ago (-8.3% growth)
]

print("Historical FCF (millions):")
for i, fcf in enumerate(declining_fcf, 1):
    print(f"  Year {i}: ${fcf:,.0f}M")
print()

growth_rates_declining = calculate_historical_growth_rates(declining_fcf)
print("Historical Growth Rates:")
for i, rate in enumerate(growth_rates_declining, 1):
    print(f"  Year {i} -> {i+1}: {rate*100:+.2f}%")
print()

predicted_rates_declining = predict_growth_rate_linear_regression(
    declining_fcf, years_to_predict
)

print(f"Predicted Growth Rates (next {years_to_predict} years):")
for i, rate in enumerate(predicted_rates_declining, 1):
    print(f"  Year {i}: {rate*100:+.2f}%")
print()

base_fcf_declining = declining_fcf[-1]
projected_fcf_declining = apply_growth_rates_to_base(
    base_fcf_declining, predicted_rates_declining
)

print(f"Base Year FCF: ${base_fcf_declining:,.0f}M")
print()
print("Projected FCF (applying growth rates):")
for i, (fcf, rate) in enumerate(
    zip(projected_fcf_declining, predicted_rates_declining), 1
):
    print(f"  Year {i}: ${fcf:,.0f}M (growth: {rate*100:+.2f}%)")
print()

print("=" * 60)
print("Test Completed Successfully!")
print("=" * 60)
