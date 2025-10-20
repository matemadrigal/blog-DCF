"""
MARKET VALIDATION - Cross-Check Against Professional Analysts
==============================================================

Compara nuestras valoraciones DCF/DDM con:
1. Consensus de analistas de Wall Street (price targets)
2. Valoraciones de servicios profesionales
3. Fair values publicados en reportes

Empresas a testear (múltiples sectores):
- Technology: AAPL, MSFT, GOOGL
- Banks: JPM, BAC, GS
- Consumer: KO, PEP, WMT
- Healthcare: JNJ, PFE, UNH
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

import yfinance as yf
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
from src.models.ddm import DDMValuation
from src.utils.ddm_data_fetcher import (
    get_dividend_data,
    calculate_dividend_growth_rate,
    get_cost_of_equity,
)


# Simple standalone functions without streamlit dependencies
def get_fcf_simple(ticker, years=5):
    """Get FCF without aggregator."""
    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow

        if cashflow.empty:
            return None

        # Get operating cash flow
        ocf_row = None
        for idx in cashflow.index:
            if (
                "operating cash flow" in str(idx).lower()
                or "total cash from operating" in str(idx).lower()
            ):
                ocf_row = idx
                break

        # Get capex
        capex_row = None
        for idx in cashflow.index:
            if (
                "capital expenditure" in str(idx).lower()
                or "purchase of ppe" in str(idx).lower()
            ):
                capex_row = idx
                break

        if ocf_row is None or capex_row is None:
            return None

        # Get most recent values
        col = cashflow.columns[0]
        ocf = float(cashflow.loc[ocf_row, col])
        capex = abs(float(cashflow.loc[capex_row, col]))  # Make positive

        fcf = ocf - capex

        # Get historical
        historical_fcf = []
        for col in cashflow.columns[: min(years, len(cashflow.columns))]:
            try:
                ocf_hist = float(cashflow.loc[ocf_row, col])
                capex_hist = abs(float(cashflow.loc[capex_row, col]))
                fcf_hist = ocf_hist - capex_hist
                historical_fcf.append(fcf_hist)
            except Exception:
                pass

        return {
            "success": True,
            "fcf": fcf,
            "historical_fcf": historical_fcf if historical_fcf else [fcf],
        }
    except Exception as e:
        print(f"    Error getting FCF: {e}")
        return None


def get_balance_sheet_simple(ticker):
    """Get cash and debt without aggregator."""
    try:
        stock = yf.Ticker(ticker)
        balance_sheet = stock.balance_sheet

        if balance_sheet.empty:
            return 0, 0

        col = balance_sheet.columns[0]

        # Get cash
        cash = 0
        for idx in balance_sheet.index:
            if "cash" in str(idx).lower() and "equivalents" in str(idx).lower():
                cash = abs(float(balance_sheet.loc[idx, col]))
                break

        # Get debt
        debt = 0
        for idx in balance_sheet.index:
            if "total debt" in str(idx).lower() or "long term debt" in str(idx).lower():
                debt = abs(float(balance_sheet.loc[idx, col]))
                break

        return cash, debt
    except Exception as e:
        print(f"    Error getting balance sheet: {e}")
        return 0, 0


def get_shares_simple(ticker):
    """Get shares outstanding without aggregator."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        shares = info.get("sharesOutstanding", 0)
        return shares
    except Exception as e:
        print(f"    Error getting shares: {e}")
        return 0


def get_analyst_consensus(ticker):
    """Get analyst consensus price target from Yahoo Finance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        target_mean = info.get("targetMeanPrice", None)
        target_high = info.get("targetHighPrice", None)
        target_low = info.get("targetLowPrice", None)
        num_analysts = info.get("numberOfAnalystOpinions", None)
        current_price = info.get("currentPrice", info.get("regularMarketPrice", None))

        return {
            "target_mean": target_mean,
            "target_high": target_high,
            "target_low": target_low,
            "num_analysts": num_analysts,
            "current_price": current_price,
        }
    except Exception as e:
        print(f"Error getting analyst data for {ticker}: {e}")
        return None


def calculate_our_dcf(ticker):
    """Calculate our DCF valuation."""
    try:
        print(f"\n  📊 Calculating DCF for {ticker}...")

        # Get data using simple functions
        fcf_result = get_fcf_simple(ticker, years=5)

        if not fcf_result or not fcf_result.get("success"):
            print("  ⚠️  Could not get FCF data")
            return None

        base_fcf = fcf_result["fcf"]
        historical_fcf = fcf_result.get("historical_fcf", [base_fcf])

        # Get balance sheet data
        cash, debt = get_balance_sheet_simple(ticker)
        shares = get_shares_simple(ticker)

        if shares == 0:
            print("  ⚠️  Could not get shares outstanding")
            return None

        # Calculate WACC
        wacc_calc = WACCCalculator()
        wacc_components = wacc_calc.calculate_wacc(
            ticker,
            use_net_debt=True,
            adjust_for_growth=True,
            use_industry_wacc=False,
        )

        wacc = wacc_components["wacc"]

        # Terminal growth
        terminal_growth_info = wacc_calc.calculate_company_terminal_growth(
            ticker,
            use_company_specific=True,
            wacc=wacc,
            validate_spread=True,
        )
        terminal_growth = terminal_growth_info["terminal_growth"]

        # Run DCF
        model = EnhancedDCFModel(wacc=wacc, terminal_growth=terminal_growth)
        result = model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf,
            cash=cash,
            debt=debt,
            diluted_shares=shares,
            years=5,
            custom_growth_rates=None,  # Let model calculate
        )

        fair_value_per_share = result["fair_value_per_share"]

        return {
            "fair_value": fair_value_per_share,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "base_fcf": base_fcf / 1e9,  # in billions
            "method": "DCF",
        }

    except Exception as e:
        print(f"  ❌ Error in DCF calculation: {e}")
        return None


def calculate_our_ddm(ticker):
    """Calculate our DDM valuation (for financials)."""
    try:
        print(f"\n  💰 Calculating DDM for {ticker}...")

        # Get dividend data
        dividend_per_share, historical_dividends, div_metadata = get_dividend_data(
            ticker, max_years=5
        )

        if dividend_per_share <= 0:
            print("  ⚠️  No dividend data")
            return None

        # Get growth rate
        if len(historical_dividends) >= 2:
            growth_rate, _ = calculate_dividend_growth_rate(
                historical_dividends, method="cagr"
            )
            # Cap growth at 8% for Gordon Model (raised from 5% based on market validation)
            growth_rate = min(growth_rate, 0.08)
            growth_rate = max(growth_rate, 0.03)  # Floor raised from 1% to 3%
        else:
            growth_rate = 0.03

        # Get cost of equity
        cost_of_equity, _ = get_cost_of_equity(ticker)

        # Calculate DDM
        ddm = DDMValuation(ticker)
        fair_value, details = ddm.gordon_growth_model(
            dividend_per_share=dividend_per_share,
            cost_of_equity=cost_of_equity,
            growth_rate=growth_rate,
        )

        if details.get("errors"):
            print(f"  ❌ DDM errors: {details['errors']}")
            return None

        return {
            "fair_value": fair_value,
            "cost_of_equity": cost_of_equity,
            "growth_rate": growth_rate,
            "dividend": dividend_per_share,
            "method": "DDM",
        }

    except Exception as e:
        print(f"  ❌ Error in DDM calculation: {e}")
        return None


def compare_company(ticker, name, sector, use_ddm=False):
    """Compare our valuation vs analyst consensus."""
    print(f"\n{'='*80}")
    print(f"🏢 {name} ({ticker}) - {sector}")
    print(f"{'='*80}")

    # Get analyst consensus
    print("\n📈 Getting analyst consensus...")
    analyst_data = get_analyst_consensus(ticker)

    if not analyst_data or analyst_data["target_mean"] is None:
        print("  ⚠️  No analyst data available")
        return None

    print(f"  ✓ Analyst Mean Target: ${analyst_data['target_mean']:.2f}")
    print(
        f"  ✓ Analyst Range: ${analyst_data['target_low']:.2f} - ${analyst_data['target_high']:.2f}"
    )
    print(f"  ✓ Number of Analysts: {analyst_data['num_analysts']}")
    print(f"  ✓ Current Price: ${analyst_data['current_price']:.2f}")

    # Calculate our valuation
    if use_ddm:
        our_valuation = calculate_our_ddm(ticker)
    else:
        our_valuation = calculate_our_dcf(ticker)

    if not our_valuation:
        print("\n  ❌ Could not calculate our valuation")
        return None

    # Display our results
    print(f"\n💡 Our Valuation ({our_valuation['method']}):")
    print(f"  ✓ Fair Value: ${our_valuation['fair_value']:.2f}")

    if our_valuation["method"] == "DCF":
        print(f"  ✓ WACC: {our_valuation['wacc']:.2%}")
        print(f"  ✓ Terminal Growth: {our_valuation['terminal_growth']:.2%}")
        print(f"  ✓ Base FCF: ${our_valuation['base_fcf']:.2f}B")
    else:  # DDM
        print(f"  ✓ Cost of Equity: {our_valuation['cost_of_equity']:.2%}")
        print(f"  ✓ Growth Rate: {our_valuation['growth_rate']:.2%}")
        print(f"  ✓ Dividend: ${our_valuation['dividend']:.2f}")

    # Comparison
    print("\n📊 Comparison:")
    our_fv = our_valuation["fair_value"]
    analyst_target = analyst_data["target_mean"]
    current_price = analyst_data["current_price"]

    # Our valuation vs analyst consensus
    diff_vs_analyst = ((our_fv - analyst_target) / analyst_target) * 100

    # Our valuation vs current price
    our_upside = ((our_fv - current_price) / current_price) * 100

    # Analyst consensus vs current price
    analyst_upside = ((analyst_target - current_price) / current_price) * 100

    print(f"  • Current Price:        ${current_price:.2f}")
    print(
        f"  • Analyst Target:       ${analyst_target:.2f} ({analyst_upside:+.1f}% upside)"
    )
    print(f"  • Our Fair Value:       ${our_fv:.2f} ({our_upside:+.1f}% upside)")
    print(f"  • Difference:           {diff_vs_analyst:+.1f}% vs analysts")

    # Interpretation
    print("\n🔍 Interpretation:")
    if abs(diff_vs_analyst) < 10:
        print("  ✅ STRONG ALIGNMENT - Our model agrees with analysts (within 10%)")
    elif abs(diff_vs_analyst) < 20:
        print("  ✓ GOOD ALIGNMENT - Reasonable agreement with analysts (within 20%)")
    elif abs(diff_vs_analyst) < 30:
        print("  ⚠️  MODERATE DIVERGENCE - Some disagreement with analysts (20-30%)")
    else:
        print("  ⚠️  SIGNIFICANT DIVERGENCE - Major disagreement with analysts (>30%)")

    if our_upside > 0 and analyst_upside > 0:
        print("  📈 Both our model and analysts see UPSIDE potential")
    elif our_upside < 0 and analyst_upside < 0:
        print("  📉 Both our model and analysts see DOWNSIDE risk")
    else:
        print("  🔀 DIVERGENCE: Our model and analysts disagree on direction")

    return {
        "ticker": ticker,
        "name": name,
        "sector": sector,
        "current_price": current_price,
        "analyst_target": analyst_target,
        "our_fair_value": our_fv,
        "diff_vs_analyst_pct": diff_vs_analyst,
        "our_upside_pct": our_upside,
        "analyst_upside_pct": analyst_upside,
        "method": our_valuation["method"],
    }


# Test companies
companies = [
    # Technology
    ("AAPL", "Apple Inc.", "Technology", False),
    ("MSFT", "Microsoft", "Technology", False),
    ("GOOGL", "Alphabet (Google)", "Technology", False),
    # Banks (use DDM)
    ("JPM", "JPMorgan Chase", "Banks", True),
    ("BAC", "Bank of America", "Banks", True),
    ("GS", "Goldman Sachs", "Banks", True),
    # Consumer
    ("KO", "Coca-Cola", "Consumer Staples", False),
    ("PEP", "PepsiCo", "Consumer Staples", False),
    ("WMT", "Walmart", "Consumer Discretionary", False),
    # Healthcare
    ("JNJ", "Johnson & Johnson", "Healthcare", False),
    ("PFE", "Pfizer", "Healthcare", False),
]

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("MARKET VALIDATION - CROSS-CHECK AGAINST PROFESSIONAL ANALYSTS")
    print("=" * 80)
    print("\nComparing our DCF/DDM valuations with Wall Street analyst consensus")
    print(f"Testing {len(companies)} companies across multiple sectors")

    results = []

    for ticker, name, sector, use_ddm in companies:
        try:
            result = compare_company(ticker, name, sector, use_ddm)
            if result:
                results.append(result)
        except Exception as e:
            print(f"\n❌ Error processing {ticker}: {e}")
            import traceback

            traceback.print_exc()

    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY - MODEL VALIDATION")
    print("=" * 80)

    if results:
        print(f"\nSuccessfully validated {len(results)} companies:\n")

        # Create comparison table
        print(
            f"{'Ticker':<8} {'Current':<10} {'Analyst':<10} {'Our FV':<10} {'Diff':<10} {'Agreement':<20}"
        )
        print("-" * 80)

        strong_alignment = 0
        good_alignment = 0
        moderate_divergence = 0
        significant_divergence = 0

        for r in results:
            diff_pct = r["diff_vs_analyst_pct"]

            if abs(diff_pct) < 10:
                agreement = "✅ Strong"
                strong_alignment += 1
            elif abs(diff_pct) < 20:
                agreement = "✓ Good"
                good_alignment += 1
            elif abs(diff_pct) < 30:
                agreement = "⚠️  Moderate"
                moderate_divergence += 1
            else:
                agreement = "⚠️  Divergent"
                significant_divergence += 1

            print(
                f"{r['ticker']:<8} ${r['current_price']:<9.2f} ${r['analyst_target']:<9.2f} "
                f"${r['our_fair_value']:<9.2f} {diff_pct:>+6.1f}%  {agreement:<20}"
            )

        # Statistics
        total = len(results)
        print("\n" + "=" * 80)
        print("📈 VALIDATION STATISTICS:")
        print(
            f"  ✅ Strong Alignment (<10% diff):      {strong_alignment}/{total} ({strong_alignment/total*100:.1f}%)"
        )
        print(
            f"  ✓  Good Alignment (10-20% diff):      {good_alignment}/{total} ({good_alignment/total*100:.1f}%)"
        )
        print(
            f"  ⚠️  Moderate Divergence (20-30%):      {moderate_divergence}/{total} ({moderate_divergence/total*100:.1f}%)"
        )
        print(
            f"  ⚠️  Significant Divergence (>30%):     {significant_divergence}/{total} ({significant_divergence/total*100:.1f}%)"
        )

        alignment_rate = (strong_alignment + good_alignment) / total * 100
        print(f"\n  🎯 Overall Alignment Rate: {alignment_rate:.1f}%")

        if alignment_rate >= 70:
            print(
                "\n  ✅ EXCELLENT - Our model shows strong agreement with professional analysts"
            )
        elif alignment_rate >= 50:
            print(
                "\n  ✓  GOOD - Our model is reasonably aligned with professional analysts"
            )
        else:
            print(
                "\n  ⚠️  REVIEW NEEDED - Significant divergence from professional analysts"
            )

        # Average absolute difference
        avg_diff = sum(abs(r["diff_vs_analyst_pct"]) for r in results) / len(results)
        print(f"\n  📊 Average Absolute Difference: {avg_diff:.1f}%")

    else:
        print("\n❌ No results to analyze")

    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80 + "\n")
