"""
Test script for DDM (Dividend Discount Model) with major banks.
Tests: JPMorgan Chase (JPM), Citigroup (C), Goldman Sachs (GS)
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

from src.models.ddm import DDMValuation
from src.utils.ddm_data_fetcher import (
    get_dividend_data,
    calculate_dividend_growth_rate,
    get_payout_ratio,
    get_roe,
    get_cost_of_equity,
)


def test_bank(ticker: str, name: str):
    """Test DDM valuation for a bank."""
    print(f"\n{'='*80}")
    print(f"Testing DDM for {name} ({ticker})")
    print(f"{'='*80}\n")

    # 1. Get dividend data
    print("1️⃣ Fetching dividend data...")
    dividend_per_share, historical_dividends, div_metadata = get_dividend_data(
        ticker, max_years=5
    )

    print(f"   ✓ Current DPS: ${dividend_per_share:.2f}")
    print(
        f"   ✓ Historical dividends: {[f'${d:.2f}' for d in historical_dividends[:5]]}"
    )
    print(f"   ✓ Source: {div_metadata['data_source']}")
    print(f"   ✓ Years found: {div_metadata['years_found']}")

    if div_metadata.get("warnings"):
        for w in div_metadata["warnings"]:
            print(f"   ⚠️  {w}")

    if dividend_per_share <= 0:
        print(f"   ❌ No dividend data - cannot use DDM for {ticker}")
        return

    # 2. Calculate growth rate
    print("\n2️⃣ Calculating dividend growth rate...")
    if len(historical_dividends) >= 2:
        growth_rate, growth_details = calculate_dividend_growth_rate(
            historical_dividends, method="cagr"
        )
        print(f"   ✓ Growth rate (CAGR): {growth_rate:.2%}")
        if growth_details.get("warnings"):
            for w in growth_details["warnings"]:
                print(f"   ⚠️  {w}")
    else:
        growth_rate = 0.03
        print("   ⚠️  Insufficient data - using default 3% growth")

    # 3. Get additional metrics
    print("\n3️⃣ Fetching additional metrics...")
    payout_ratio, payout_meta = get_payout_ratio(ticker)
    roe, roe_meta = get_roe(ticker)
    cost_of_equity, coe_meta = get_cost_of_equity(ticker)

    print(
        f"   ✓ Payout Ratio: {payout_ratio:.1%}"
        if payout_ratio > 0
        else "   ⚠️  Payout Ratio: N/A"
    )
    print(f"   ✓ ROE: {roe:.1%}" if roe != 0 else "   ⚠️  ROE: N/A")
    print(f"   ✓ Cost of Equity: {cost_of_equity:.2%}")
    print(f"   ✓ Beta: {coe_meta['inputs'].get('beta', 'N/A')}")

    # 4. Calculate DDM valuation (Gordon Growth Model)
    print("\n4️⃣ Calculating Gordon Growth Model valuation...")
    ddm = DDMValuation(ticker)

    intrinsic_value, ddm_details = ddm.gordon_growth_model(
        dividend_per_share=dividend_per_share,
        cost_of_equity=cost_of_equity,
        growth_rate=growth_rate,
    )

    if ddm_details.get("errors"):
        print("   ❌ Errors:")
        for error in ddm_details["errors"]:
            print(f"      - {error}")
        return

    print(f"   ✓ Fair Value per Share: ${intrinsic_value:.2f}")

    if ddm_details.get("warnings"):
        for w in ddm_details["warnings"]:
            print(f"   ⚠️  {w}")

    # 5. Get current price for comparison
    print("\n5️⃣ Comparing with market price...")
    try:
        import yfinance as yf

        stock = yf.Ticker(ticker)
        current_price = stock.info.get("currentPrice", 0)

        if current_price > 0:
            upside = ((intrinsic_value - current_price) / current_price) * 100
            print(f"   ✓ Current Price: ${current_price:.2f}")
            print(f"   ✓ Fair Value: ${intrinsic_value:.2f}")
            print(f"   ✓ Upside/Downside: {upside:+.1f}%")

            if upside > 10:
                print(f"   🟢 UNDERVALUED by {upside:.1f}%")
            elif upside < -10:
                print(f"   🔴 OVERVALUED by {abs(upside):.1f}%")
            else:
                print("   🟡 FAIRLY VALUED")
        else:
            print("   ⚠️  Could not fetch current price")
    except Exception as e:
        print(f"   ⚠️  Error fetching price: {e}")

    # 6. Calculate implied growth rate
    print("\n6️⃣ Calculating implied growth rate (reverse DDM)...")
    if current_price > 0:
        implied_growth, implied_details = ddm.calculate_implied_growth_rate(
            current_price, dividend_per_share, cost_of_equity
        )
        print(f"   ✓ Implied Growth Rate: {implied_growth:.2%}")
        print(f"   ✓ Your Estimate: {growth_rate:.2%}")
        diff = (implied_growth - growth_rate) * 100
        print(f"   ✓ Difference: {diff:+.1f}pp")
        print(f"   📊 {implied_details.get('interpretation', '')}")

    print(f"\n{'='*80}")
    print(f"✅ Test completed for {name} ({ticker})")
    print(f"{'='*80}\n")


# Test the three major banks
if __name__ == "__main__":
    banks = [
        ("JPM", "JPMorgan Chase"),
        ("C", "Citigroup"),
        ("GS", "Goldman Sachs"),
    ]

    print("\n" + "=" * 80)
    print("DDM VALUATION TEST - MAJOR US BANKS")
    print("=" * 80)

    for ticker, name in banks:
        try:
            test_bank(ticker, name)
        except Exception as e:
            print(f"\n❌ Error testing {name} ({ticker}): {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80 + "\n")
