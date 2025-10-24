"""
Enhanced DDM test for financial institutions using Two-Stage Model.

This script demonstrates the proper use of DDM for banks:
1. Gordon Growth for mature/stable banks
2. Two-Stage DDM for growing banks
3. Comparison and recommendation
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


def test_bank_enhanced(ticker: str, name: str):
    """Enhanced DDM test using both Gordon and Two-Stage models."""
    print(f"\n{'='*80}")
    print(f"ENHANCED DDM VALUATION: {name} ({ticker})")
    print(f"{'='*80}\n")

    # 1. Get dividend data
    print("1️⃣ Fetching dividend data...")
    dividend_per_share, historical_dividends, div_metadata = get_dividend_data(
        ticker, max_years=5
    )

    print(f"   ✓ Current DPS: ${dividend_per_share:.2f}")
    print(f"   ✓ Years of data: {div_metadata['years_found']}")

    if dividend_per_share <= 0:
        print(f"   ❌ No dividend data - cannot use DDM")
        return

    # 2. Historical growth
    print("\n2️⃣ Analyzing dividend growth...")
    if len(historical_dividends) >= 2:
        historical_growth, _ = calculate_dividend_growth_rate(
            historical_dividends, method="cagr"
        )
        print(f"   ✓ Historical Growth (5Y CAGR): {historical_growth:.2%}")
    else:
        historical_growth = 0.03

    # 3. Get metrics
    print("\n3️⃣ Fetching fundamental metrics...")
    payout_ratio, _ = get_payout_ratio(ticker)
    roe, _ = get_roe(ticker)
    cost_of_equity, coe_meta = get_cost_of_equity(ticker)

    print(f"   ✓ Payout Ratio: {payout_ratio:.1%}")
    print(f"   ✓ ROE: {roe:.1%}")
    print(f"   ✓ Cost of Equity: {cost_of_equity:.2%}")
    print(f"   ✓ Beta: {coe_meta['inputs'].get('beta', 'N/A'):.2f}")

    # 4. Calculate sustainable growth
    ddm = DDMValuation(ticker)

    if roe > 0 and payout_ratio > 0:
        sustainable_growth = ddm.calculate_sustainable_growth_rate(roe, payout_ratio)
        print(f"   ✓ Sustainable Growth (ROE × retention): {sustainable_growth:.2%}")
    else:
        sustainable_growth = 0.03

    # 5. Normalize for perpetuity
    print("\n4️⃣ Normalizing growth for perpetuity...")
    normalized_growth, norm_details = ddm.normalize_growth_for_perpetuity(
        historical_growth=historical_growth,
        sustainable_growth=sustainable_growth,
        cost_of_equity=cost_of_equity,
        weight_historical=0.30,
    )

    print(f"   ✓ Perpetual Growth (normalized): {normalized_growth:.2%}")

    # 6. Gordon Growth Model (BASELINE)
    print("\n5️⃣ GORDON GROWTH MODEL (Conservative Baseline)")
    print("   " + "-" * 70)

    gordon_value, gordon_details = ddm.gordon_growth_model(
        dividend_per_share=dividend_per_share,
        cost_of_equity=cost_of_equity,
        growth_rate=normalized_growth,
    )

    if gordon_details.get("errors"):
        print("   ❌ Gordon Model Failed:")
        for err in gordon_details["errors"]:
            print(f"      {err}")
    else:
        print(f"   ✓ Fair Value: ${gordon_value:.2f}")
        print(f"   ✓ P/D Ratio: {gordon_value/dividend_per_share:.1f}x")

    # 7. Two-Stage DDM (REALISTIC FOR GROWING BANKS)
    print("\n6️⃣ TWO-STAGE DDM (Realistic for Growing Banks)")
    print("   " + "-" * 70)

    # Use historical growth for near term (capped at reasonable levels)
    high_growth = min(historical_growth, 0.08)  # Cap at 8%
    stable_growth = normalized_growth  # Use normalized for terminal
    high_growth_years = 5  # 5-year high growth period

    print(f"   Stage 1 (Years 1-5): {high_growth:.2%} growth")
    print(f"   Stage 2 (Perpetual): {stable_growth:.2%} growth")

    two_stage_value, two_stage_details = ddm.two_stage_ddm(
        dividend_per_share=dividend_per_share,
        cost_of_equity=cost_of_equity,
        high_growth_rate=high_growth,
        stable_growth_rate=stable_growth,
        high_growth_years=high_growth_years,
    )

    if two_stage_details.get("errors"):
        print("   ❌ Two-Stage Model Failed:")
        for err in two_stage_details["errors"]:
            print(f"      {err}")
    else:
        print(f"   ✓ Fair Value: ${two_stage_value:.2f}")
        print(f"   ✓ Stage 1 PV: ${two_stage_details['calculations']['PV(High Growth Dividends)']:.2f}")
        print(f"   ✓ Stage 2 PV: ${two_stage_details['calculations']['PV(Terminal Value)']:.2f}")

    # 8. Compare with market
    print("\n7️⃣ MARKET COMPARISON")
    print("   " + "-" * 70)

    import yfinance as yf

    stock = yf.Ticker(ticker)
    current_price = stock.info.get("currentPrice", 0)

    if current_price > 0:
        print(f"   📊 Current Market Price: ${current_price:.2f}\n")

        # Gordon comparison
        gordon_upside = ((gordon_value - current_price) / current_price) * 100
        print(f"   Gordon Growth Model:")
        print(f"      Fair Value: ${gordon_value:.2f}")
        print(f"      Upside: {gordon_upside:+.1f}%")

        # Two-stage comparison
        two_stage_upside = ((two_stage_value - current_price) / current_price) * 100
        print(f"\n   Two-Stage DDM:")
        print(f"      Fair Value: ${two_stage_value:.2f}")
        print(f"      Upside: {two_stage_upside:+.1f}%")

        # Recommendation
        print(f"\n   📈 RECOMMENDATION:")
        if two_stage_upside > 20:
            print(f"      🟢 STRONG BUY - Undervalued by {two_stage_upside:.1f}%")
        elif two_stage_upside > 10:
            print(f"      🟢 BUY - Undervalued by {two_stage_upside:.1f}%")
        elif two_stage_upside > -10:
            print(f"      🟡 HOLD - Fairly valued ({two_stage_upside:+.1f}%)")
        elif two_stage_upside > -20:
            print(f"      🔴 SELL - Overvalued by {abs(two_stage_upside):.1f}%")
        else:
            print(f"      🔴 STRONG SELL - Overvalued by {abs(two_stage_upside):.1f}%")

        # Implied growth
        implied_growth, _ = ddm.calculate_implied_growth_rate(
            current_price, dividend_per_share, cost_of_equity
        )
        print(f"\n   🔍 Market Implied Perpetual Growth: {implied_growth:.2%}")
        print(f"      (Market prices imply {implied_growth:.2%} dividend growth forever)")

        if implied_growth > 0.08:
            print(f"      ⚠️  Market expectations may be too optimistic")
        elif implied_growth < 0.02:
            print(f"      💡 Market may be undervaluing dividend growth potential")

    print(f"\n{'='*80}")
    print(f"✅ Enhanced analysis completed for {name}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    banks = [
        ("JPM", "JPMorgan Chase"),
        ("C", "Citigroup"),
        ("GS", "Goldman Sachs"),
        ("BAC", "Bank of America"),
        ("WFC", "Wells Fargo"),
    ]

    print("\n" + "=" * 80)
    print("ENHANCED DDM VALUATION - US BANKS (Two-Stage Model)")
    print("=" * 80)

    for ticker, name in banks:
        try:
            test_bank_enhanced(ticker, name)
        except Exception as e:
            print(f"\n❌ Error testing {name} ({ticker}): {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80 + "\n")
