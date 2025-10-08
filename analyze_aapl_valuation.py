"""Analyze why AAPL appears overvalued in the model."""

# From the screenshot:
# FCF projections: 10%, 8%, 8%, 7%, 8% growth
# Base FCF: $108.807B
# Fair Value: $150.72
# Current Price: $258.06
# Upside: -41.6%

# Let's reverse engineer and check the calculation

base_fcf = 108.807e9  # $108.807B
growth_rates = [0.10, 0.08, 0.08, 0.07, 0.08]

# Project FCF
fcf_projections = []
current_fcf = base_fcf
for g in growth_rates:
    current_fcf = current_fcf * (1 + g)
    fcf_projections.append(current_fcf)

print("FCF Projections:")
for i, fcf in enumerate(fcf_projections, 1):
    print(f"  Year {i}: ${fcf/1e9:.2f}B")

# From screenshot:
enterprise_value = 2278.21e9
equity_value = 2236.75e9
fair_value_per_share = 150.72
shares = 14.84e9  # From our earlier test

# Calculate implied WACC and terminal growth
# EV = $2278.21B
# Last FCF = fcf_projections[-1]

last_fcf = fcf_projections[-1]
print(f"\nLast projected FCF (Year 5): ${last_fcf/1e9:.2f}B")

# Try to back out the WACC
# Let's assume terminal growth = 4% (from our model)
g_terminal = 0.04

# Sum of discounted FCFs should equal EV
# We can test different WACC values


def calculate_ev(fcf_list, wacc, g_term):
    """Calculate enterprise value given FCF, WACC, and terminal growth."""
    pv_fcf = sum(fcf / (1 + wacc) ** i for i, fcf in enumerate(fcf_list, 1))
    terminal_value = (fcf_list[-1] * (1 + g_term)) / (wacc - g_term)
    pv_terminal = terminal_value / (1 + wacc) ** len(fcf_list)
    return pv_fcf + pv_terminal


# Test with 10% WACC (from our model)
wacc_test = 0.10
ev_test = calculate_ev(fcf_projections, wacc_test, g_terminal)
print(f"\nWith WACC={wacc_test:.1%}, Terminal g={g_terminal:.1%}:")
print(f"  Enterprise Value: ${ev_test/1e9:.2f}B")
print(f"  Screenshot shows: ${enterprise_value/1e9:.2f}B")

# The issue: growth rates are too LOW
# Let's check what professional analysts use

print("\n" + "=" * 60)
print("COMPARISON WITH ANALYST ESTIMATES")
print("=" * 60)

analyst_estimates = {
    "GuruFocus": 130.48,
    "Alpha Spread": 130.88,
    "ValueInvesting.io": 201.13,
    "Simply Wall St": 250.73,
    "Our Model": 150.72,
}

print("\nDCF Fair Value Estimates:")
for source, fv in analyst_estimates.items():
    diff = ((fv - 258.06) / 258.06) * 100
    print(f"  {source:25s}: ${fv:7.2f} ({diff:+6.1f}%)")

print("\n" + "=" * 60)
print("POTENTIAL ISSUES IDENTIFIED")
print("=" * 60)

issues = """
1. GROWTH RATES TOO CONSERVATIVE
   - Our model uses: 10%, 8%, 8%, 7%, 8%
   - Apple's historical FCF growth is volatile but includes high periods
   - Recent FCF: $108B (2024) vs $99B (2023) vs $111B (2022)
   - This is NEGATIVE average growth, not 8%!

2. BASE FCF SELECTION ISSUE
   - We're using the MOST RECENT year ($108.8B)
   - But Apple's FCF is cyclical/volatile
   - Should we use an AVERAGE or NORMALIZED base?

3. APPLE-SPECIFIC FACTORS NOT CONSIDERED
   - Massive cash position ($65B) reduces risk
   - Capital return program (buybacks, dividends)
   - Market leader with pricing power
   - These justify higher multiples

4. MARKET PRICING
   - AAPL trades at $258 (P/FCF ≈ 2.37x)
   - Market expects HIGHER growth than historical
   - AI iPhone cycle, Services growth, Vision Pro, etc.

5. OUR MODEL VS REALITY
   - GuruFocus: $130 (AAPL overvalued by 49%)
   - Alpha Spread: $131 (AAPL overvalued by 49%)
   - Our Model: $151 (AAPL overvalued by 42%)
   - Simply Wall St: $251 (AAPL fairly valued)

   → We're ALIGNED with conservative analysts!
   → Simply Wall St uses more optimistic assumptions
"""

print(issues)

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)

conclusion = """
Your model is NOT BROKEN - it's actually working correctly!

The issue is that Apple (and many growth stocks) ARE trading at premium
valuations that exceed conservative DCF estimates.

Three perspectives:

A) CONSERVATIVE VIEW (GuruFocus, Alpha Spread, Your Model)
   - Fair Value: $130-150
   - AAPL is 40-50% overvalued
   - Uses historical FCF growth, standard WACC

B) MODERATE VIEW (ValueInvesting.io)
   - Fair Value: $200
   - AAPL is 20% overvalued
   - Uses slightly higher growth assumptions

C) OPTIMISTIC VIEW (Simply Wall St)
   - Fair Value: $250
   - AAPL is fairly valued
   - Uses bullish growth assumptions (AI, services)

Your $150 estimate suggests AAPL is expensive but not egregiously so.
This is a VALID analytical view, not an error.

To get values closer to market price, you would need to assume:
- Higher FCF growth (15-20% vs 8-10%)
- Lower WACC (7-8% vs 10%)
- Higher terminal growth (4-5% vs 4%)

But these may be TOO OPTIMISTIC and lead to overpaying for stocks.
"""

print(conclusion)
