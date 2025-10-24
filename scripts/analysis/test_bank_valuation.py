"""
Test Bank Valuation Models - Compare RIM, P/B, DDM, and Hybrid.

This script demonstrates the proper way to value banks using:
1. Residual Income Model (RIM) - Industry standard
2. P/B × ROE Model - Simple and effective
3. Hybrid Model - Weighted combination

Shows realistic fair values compared to conservative DDM.
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

from src.models.bank_valuation import BankValuation, get_fair_value_bank
from src.utils.ddm_data_fetcher import get_cost_of_equity
import yfinance as yf


def get_bank_fundamentals(ticker: str) -> dict:
    """Fetch fundamental data for a bank."""
    stock = yf.Ticker(ticker)
    info = stock.info

    # Get book value per share
    book_value = info.get("bookValue", 0)

    # Get ROE
    roe = info.get("returnOnEquity", 0)

    # Get dividend
    dividend = info.get("trailingAnnualDividendRate", 0)

    # Get current price
    current_price = info.get("currentPrice", 0)

    # Get cost of equity
    cost_of_equity, coe_meta = get_cost_of_equity(ticker)

    # Get P/B ratio
    pb_ratio = info.get("priceToBook", 0)

    return {
        "book_value_per_share": book_value,
        "roe": roe,
        "dividend_per_share": dividend,
        "current_price": current_price,
        "cost_of_equity": cost_of_equity,
        "beta": coe_meta["inputs"].get("beta", 0),
        "pb_ratio": pb_ratio,
    }


def test_bank_valuation(ticker: str, name: str):
    """Test all valuation methods for a bank."""
    print(f"\n{'='*80}")
    print(f"BANK VALUATION: {name} ({ticker})")
    print(f"{'='*80}\n")

    # 1. Get fundamentals
    print("1️⃣ Fetching fundamental data...")
    try:
        data = get_bank_fundamentals(ticker)
    except Exception as e:
        print(f"   ❌ Error fetching data: {e}")
        return

    print(f"   ✓ Book Value: ${data['book_value_per_share']:.2f}")
    print(f"   ✓ ROE: {data['roe']:.2%}")
    print(f"   ✓ Dividend: ${data['dividend_per_share']:.2f}")
    print(f"   ✓ Cost of Equity: {data['cost_of_equity']:.2%}")
    print(f"   ✓ Beta: {data['beta']:.2f}")
    print(f"   ✓ Current Price: ${data['current_price']:.2f}")
    print(f"   ✓ Current P/B: {data['pb_ratio']:.2f}x")

    if data['book_value_per_share'] <= 0 or data['roe'] <= 0:
        print("   ❌ Insufficient data for valuation")
        return

    # 2. Method 1: Residual Income Model (RIM)
    print("\n2️⃣ RESIDUAL INCOME MODEL (RIM) - Industry Standard")
    print("   " + "-" * 70)

    rim_value, rim_details = get_fair_value_bank(
        ticker=ticker,
        book_value_per_share=data['book_value_per_share'],
        roe=data['roe'],
        cost_of_equity=data['cost_of_equity'],
        method="rim",
    )

    print(f"   ✓ Fair Value: ${rim_value:.2f}")
    print(f"   ✓ Implied P/B: {rim_details['implied_pb_ratio']:.2f}x")
    print(f"   ✓ Excess Return: {rim_details['calculations']['excess_return']:.2%}")
    print(f"   📊 {rim_details['interpretation']}")

    # 3. Method 2: P/B × ROE Model
    print("\n3️⃣ P/B × ROE MODEL - Simple & Effective")
    print("   " + "-" * 70)

    pb_value, pb_details = get_fair_value_bank(
        ticker=ticker,
        book_value_per_share=data['book_value_per_share'],
        roe=data['roe'],
        cost_of_equity=data['cost_of_equity'],
        growth_rate=0.03,
        method="pb_roe",
    )

    print(f"   ✓ Fair Value: ${pb_value:.2f}")
    print(f"   ✓ Fair P/B Ratio: {pb_details['calculations']['fair_pb_ratio']:.2f}x")
    print(f"   📊 {pb_details['interpretation']}")

    # 4. Method 3: Hybrid Model (RECOMMENDED)
    print("\n4️⃣ HYBRID MODEL - Weighted Combination (RECOMMENDED)")
    print("   " + "-" * 70)

    hybrid_value, hybrid_details = get_fair_value_bank(
        ticker=ticker,
        book_value_per_share=data['book_value_per_share'],
        roe=data['roe'],
        cost_of_equity=data['cost_of_equity'],
        dividend_per_share=data['dividend_per_share'],
        growth_rate=0.03,
        method="hybrid",
    )

    print(f"   ✓ Fair Value: ${hybrid_value:.2f}")
    print(f"\n   Component Values:")
    print(f"      RIM:    ${hybrid_details['component_values']['rim']:.2f} (weight: {hybrid_details['final_weights']['rim']:.0%})")
    print(f"      P/B:    ${hybrid_details['component_values']['pb_roe']:.2f} (weight: {hybrid_details['final_weights']['pb_roe']:.0%})")
    if 'ddm' in hybrid_details['component_values'] and hybrid_details['component_values']['ddm'] > 0:
        print(f"      DDM:    ${hybrid_details['component_values']['ddm']:.2f} (weight: {hybrid_details['final_weights']['ddm']:.0%})")

    if 'value_range' in hybrid_details:
        vr = hybrid_details['value_range']
        print(f"\n   Value Range: ${vr['min']:.2f} - ${vr['max']:.2f} (±{vr['range_pct']:.1f}%)")

    # 5. Market Comparison
    print("\n5️⃣ MARKET COMPARISON")
    print("   " + "-" * 70)

    current_price = data['current_price']

    print(f"\n   📊 Current Market Price: ${current_price:.2f}")
    print(f"   📊 Current P/B Ratio: {data['pb_ratio']:.2f}x\n")

    # Compare all methods
    methods = {
        "RIM (Industry Standard)": rim_value,
        "P/B × ROE (Simple)": pb_value,
        "Hybrid (Recommended)": hybrid_value,
    }

    print("   Method Comparison:")
    for method_name, fair_value in methods.items():
        upside = ((fair_value - current_price) / current_price) * 100
        print(f"      {method_name:25s}: ${fair_value:6.2f}  ({upside:+6.1f}%)")

    # Overall recommendation (using Hybrid)
    hybrid_upside = ((hybrid_value - current_price) / current_price) * 100

    print(f"\n   📈 RECOMMENDATION (based on Hybrid Model):")
    if hybrid_upside > 20:
        print(f"      🟢 STRONG BUY - Undervalued by {hybrid_upside:.1f}%")
    elif hybrid_upside > 10:
        print(f"      🟢 BUY - Undervalued by {hybrid_upside:.1f}%")
    elif hybrid_upside > -10:
        print(f"      🟡 HOLD - Fairly valued ({hybrid_upside:+.1f}%)")
    elif hybrid_upside > -20:
        print(f"      🔴 SELL - Overvalued by {abs(hybrid_upside):.1f}%")
    else:
        print(f"      🔴 STRONG SELL - Overvalued by {abs(hybrid_upside):.1f}%")

    # Implied P/B comparison
    print(f"\n   P/B Analysis:")
    print(f"      Current P/B: {data['pb_ratio']:.2f}x")
    print(f"      Fair P/B (RIM): {rim_details['implied_pb_ratio']:.2f}x")
    print(f"      Fair P/B (P/B Model): {pb_details['calculations']['fair_pb_ratio']:.2f}x")

    print(f"\n{'='*80}")
    print(f"✅ Valuation completed for {name}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    banks = [
        ("JPM", "JPMorgan Chase"),
        ("BAC", "Bank of America"),
        ("C", "Citigroup"),
        ("GS", "Goldman Sachs"),
        ("WFC", "Wells Fargo"),
    ]

    print("\n" + "=" * 80)
    print("BANK VALUATION - Comparing RIM, P/B, and Hybrid Models")
    print("=" * 80)
    print("\nThese models are specifically designed for financial institutions")
    print("and provide more realistic valuations than conservative DDM.\n")

    for ticker, name in banks:
        try:
            test_bank_valuation(ticker, name)
        except Exception as e:
            print(f"\n❌ Error testing {name} ({ticker}): {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("KEY TAKEAWAYS:")
    print("=" * 80)
    print("""
1. RIM (Residual Income Model) is the industry standard for banks
2. P/B × ROE is simple and effective for quick valuation
3. Hybrid model combines strengths of multiple approaches
4. These models are more realistic than DDM for banks
5. Banks create value when ROE > Cost of Equity
    """)
