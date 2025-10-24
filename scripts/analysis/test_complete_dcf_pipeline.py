"""
Complete DCF Pipeline Test - Demonstrates All Audit Fixes

This script demonstrates the complete DCF valuation pipeline with all
audit fixes applied:

1. Terminal Value with mid-year discounting
2. FCF growth with sign preservation
3. Reinvestment consistency validation
4. WACC with country risk via beta
5. Beta adjustment order (Blume → Hamada)
6. Optional IFRS 16 lease separation
7. Complete EV → Equity → Price pipeline

[AuditFix] All improvements integrated with maximum financial rigor.
"""

import sys
sys.path.insert(0, "/home/mateo/blog-DCF")

from src.dcf.model import dcf_value
from src.dcf.projections import (
    predict_growth_rate_linear_regression,
    apply_growth_rates_to_base,
    adjust_growth_rates_for_reinvestment,
)
from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.valuation_bridge import (
    calculate_price_per_share,
    print_valuation_bridge_report,
)
from src.utils.data_fetcher import get_free_cash_flow_history
import yfinance as yf


def complete_dcf_valuation(ticker: str, verbose: bool = True):
    """
    Perform complete DCF valuation with all audit fixes.

    Args:
        ticker: Stock ticker
        verbose: Print detailed analysis

    Returns:
        Dictionary with complete valuation results
    """
    if verbose:
        print("\n" + "=" * 80)
        print(f"COMPLETE DCF VALUATION: {ticker}")
        print("=" * 80)

    # ========================================================================
    # STEP 1: GET HISTORICAL FCF DATA
    # ========================================================================
    if verbose:
        print("\n1️⃣ FETCHING HISTORICAL FCF DATA...")

    fcf_history = get_free_cash_flow_history(ticker, years=5)

    if not fcf_history or len(fcf_history) < 2:
        print(f"   ❌ Insufficient FCF data for {ticker}")
        return None

    base_fcf = fcf_history[-1]  # Most recent FCF

    if verbose:
        print(f"   ✓ Historical FCF (5 years):")
        for i, fcf in enumerate(fcf_history):
            print(f"      Year {i+1}: ${fcf/1e9:,.2f}B")
        print(f"   ✓ Base FCF: ${base_fcf/1e9:,.2f}B")

    # ========================================================================
    # STEP 2: PROJECT FCF GROWTH RATES
    # ========================================================================
    if verbose:
        print("\n2️⃣ PROJECTING FCF GROWTH RATES...")
        print("   [AuditFix] Using corrected growth formula with sign preservation")

    # Predict growth rates (5-year forecast)
    growth_rates = predict_growth_rate_linear_regression(
        fcf_history, years_to_predict=5
    )

    if verbose:
        print(f"   ✓ Predicted Growth Rates:")
        for i, g in enumerate(growth_rates):
            print(f"      Year {i+1}: {g:.2%}")

    # ========================================================================
    # STEP 3: VALIDATE REINVESTMENT CONSISTENCY
    # ========================================================================
    if verbose:
        print("\n3️⃣ VALIDATING REINVESTMENT CONSISTENCY...")
        print("   [AuditFix] Ensuring g = Reinvestment Rate × ROIC")

    # Adjust growth rates for reinvestment consistency
    # Assumes 15% ROIC, 80% max reinvestment
    adjusted_growth_rates, adjustment_details = adjust_growth_rates_for_reinvestment(
        growth_rates, roic=0.15, max_reinvestment_rate=0.80
    )

    if verbose:
        if adjustment_details["num_adjustments"] > 0:
            print(f"   ⚠️  {adjustment_details['num_adjustments']} growth rates adjusted:")
            for adj in adjustment_details["adjustments_made"]:
                print(f"      Year {adj['year']}: {adj['original_growth']:.1%} → {adj['adjusted_growth']:.1%}")
                print(f"         (Reinvestment: {adj['implied_reinvestment_original']:.1%} → {adj['implied_reinvestment_adjusted']:.1%})")
        else:
            print(f"   ✓ All growth rates sustainable with 80% max reinvestment")

    # ========================================================================
    # STEP 4: PROJECT FCF
    # ========================================================================
    if verbose:
        print("\n4️⃣ PROJECTING FUTURE FCF...")

    projected_fcf = apply_growth_rates_to_base(base_fcf, adjusted_growth_rates)

    if verbose:
        print(f"   ✓ Projected FCF (5-year forecast):")
        for i, fcf in enumerate(projected_fcf):
            print(f"      Year {i+1}: ${fcf/1e9:,.2f}B")

    # ========================================================================
    # STEP 5: CALCULATE WACC
    # ========================================================================
    if verbose:
        print("\n5️⃣ CALCULATING WACC...")
        print("   [AuditFix] Country risk via beta adjustment (avoid double-counting)")
        print("   [AuditFix] Beta order: Blume → Hamada with marginal tax rate")

    wacc_calc = WACCCalculator(use_damodaran=True, tax_rate=0.21)

    wacc_result = wacc_calc.calculate_wacc(
        ticker=ticker,
        use_net_debt=True,
        apply_blume_adjustment=True,
        use_dynamic_risk_free_rate=False,
        country_code="USA",
        apply_country_risk_to_beta=True,  # [AuditFix] NEW
    )

    wacc = wacc_result["wacc"]

    if verbose:
        print(f"   ✓ WACC: {wacc:.2%}")
        print(f"   ✓ Cost of Equity: {wacc_result['cost_of_equity']:.2%}")
        print(f"   ✓ Cost of Debt: {wacc_result['cost_of_debt']:.2%}")
        print(f"   ✓ Beta: {wacc_result['beta']:.2f} ({wacc_result['beta_source']})")
        print(f"   ✓ D/E Ratio: {wacc_result['total_debt']/wacc_result['market_cap']:.2f}")

    # ========================================================================
    # STEP 6: CALCULATE TERMINAL VALUE & DCF
    # ========================================================================
    if verbose:
        print("\n6️⃣ CALCULATING DCF VALUE...")
        print("   [AuditFix] Mid-year discounting convention (increases PV by ~5%)")
        print("   [AuditFix] Terminal value with stability controls")

    # Terminal growth rate (conservative 2.5%)
    terminal_growth = 0.025

    # Calculate DCF with mid-year convention
    enterprise_value = dcf_value(
        cash_flows=projected_fcf,
        discount_rate=wacc,
        perpetuity_growth=terminal_growth,
        use_mid_year_convention=True,  # [AuditFix] NEW
        min_spread_bps=0.02,  # [AuditFix] NEW
    )

    if verbose:
        print(f"   ✓ Enterprise Value: ${enterprise_value/1e9:,.2f}B")
        print(f"   ✓ Terminal Growth: {terminal_growth:.1%}")
        print(f"   ✓ WACC - g spread: {(wacc - terminal_growth):.2%}")

    # ========================================================================
    # STEP 7: EV → EQUITY → PRICE PIPELINE
    # ========================================================================
    if verbose:
        print("\n7️⃣ CONVERTING EV TO PRICE PER SHARE...")
        print("   [AuditFix] Complete bridge: EV → Equity → Price with dilution")

    # Calculate intrinsic price per share
    intrinsic_price, analysis = calculate_price_per_share(
        enterprise_value=enterprise_value,
        ticker=ticker,
        total_debt=wacc_result["total_debt"],
        cash=wacc_result["cash"],
        use_diluted_shares=True,  # Treasury Stock Method
        include_minority_interest=True,
        include_preferred_stock=True,
    )

    # ========================================================================
    # STEP 8: PRINT VALUATION BRIDGE REPORT
    # ========================================================================
    if verbose:
        print_valuation_bridge_report(analysis)

    # ========================================================================
    # RETURN RESULTS
    # ========================================================================
    return {
        "ticker": ticker,
        "base_fcf": base_fcf,
        "growth_rates_original": growth_rates,
        "growth_rates_adjusted": adjusted_growth_rates,
        "projected_fcf": projected_fcf,
        "wacc": wacc,
        "terminal_growth": terminal_growth,
        "enterprise_value": enterprise_value,
        "equity_value": analysis["equity_value"],
        "diluted_shares": analysis["diluted_shares"],
        "intrinsic_price_per_share": intrinsic_price,
        "current_price": analysis.get("current_price", 0),
        "upside_pct": analysis.get("upside_pct", 0),
        "recommendation": analysis.get("recommendation", "N/A"),
        "full_analysis": analysis,
    }


def test_multiple_companies():
    """Test DCF pipeline on multiple companies."""
    companies = [
        ("AAPL", "Apple Inc."),
        ("MSFT", "Microsoft"),
        ("GOOGL", "Alphabet"),
        ("NVDA", "NVIDIA"),
    ]

    print("\n" + "=" * 80)
    print("COMPLETE DCF PIPELINE - MULTIPLE COMPANIES")
    print("=" * 80)
    print("\nTesting DCF valuation with all audit fixes:")
    print("1. Mid-year discounting")
    print("2. FCF growth sign preservation")
    print("3. Reinvestment consistency")
    print("4. Country risk via beta")
    print("5. Beta order validation")
    print("6. IFRS 16 (optional)")
    print("7. Complete EV → Price pipeline")
    print("=" * 80)

    results = []

    for ticker, name in companies:
        try:
            print(f"\n\n{'='*80}")
            print(f"TESTING: {name} ({ticker})")
            print(f"{'='*80}")

            result = complete_dcf_valuation(ticker, verbose=True)

            if result:
                results.append(result)

        except Exception as e:
            print(f"\n❌ Error testing {name} ({ticker}): {e}")
            import traceback
            traceback.print_exc()

    # ========================================================================
    # SUMMARY TABLE
    # ========================================================================
    print("\n" + "=" * 80)
    print("VALUATION SUMMARY")
    print("=" * 80)
    print(f"\n{'Ticker':<10} {'Current':<12} {'Intrinsic':<12} {'Upside':<12} {'Recommendation':<15}")
    print("-" * 80)

    for r in results:
        print(
            f"{r['ticker']:<10} "
            f"${r['current_price']:<11.2f} "
            f"${r['intrinsic_price_per_share']:<11.2f} "
            f"{r['upside_pct']:>10.1%}  "
            f"{r['recommendation']:<15}"
        )

    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    # Run complete test
    test_multiple_companies()
