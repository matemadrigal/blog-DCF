"""Test Damodaran WACC improvements vs old model."""

from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.damodaran_data import DamodaranData
from src.dcf.enhanced_model import EnhancedDCFModel
import yfinance as yf


def test_company(ticker: str):
    """Test WACC calculation with old vs new (Damodaran) method."""
    print(f"\n{'='*80}")
    print(f"Testing {ticker}")
    print(f"{'='*80}\n")

    # Get company data
    stock = yf.Ticker(ticker)
    info = stock.info
    company_name = info.get("longName", ticker)
    sector = info.get("sector", "Unknown")
    current_price = info.get("currentPrice", 0)

    print(f"Company: {company_name}")
    print(f"Sector: {sector}")
    print(f"Current Price: ${current_price:.2f}\n")

    # Get FCF and balance sheet
    cashflow = stock.cashflow
    historical_fcf = []
    if not cashflow.empty:
        cols = list(cashflow.columns)[:5]
        for c in cols:
            op = None
            capex = None
            for idx in cashflow.index:
                name = str(idx).lower()
                if "operating cash flow" in name and op is None:
                    op = cashflow.loc[idx, c]
                if (
                    "capital expenditure" in name or "purchase of ppe" in name
                ) and capex is None:
                    capex = cashflow.loc[idx, c]

            if op is not None and capex is not None:
                fcf = float(op - abs(capex))
                historical_fcf.append(fcf)

    base_fcf = historical_fcf[0] if historical_fcf else 0
    cash = info.get("totalCash", 0)
    debt = info.get("totalDebt", 0)
    shares = info.get("sharesOutstanding", 0)

    print(f"Base FCF: ${base_fcf/1e9:.2f}B")
    print(f"Cash: ${cash/1e9:.2f}B")
    print(f"Debt: ${debt/1e9:.2f}B")
    print(f"Net Debt: ${(debt-cash)/1e9:.2f}B\n")

    # TEST 1: Old Model (no Damodaran)
    print("=" * 80)
    print("OLD MODEL (Pre-Damodaran)")
    print("=" * 80)

    old_wacc_calc = WACCCalculator(use_damodaran=False)
    old_wacc_data = old_wacc_calc.calculate_wacc(
        ticker, use_net_debt=True, adjust_for_growth=True
    )

    print(f"Risk-free rate: {old_wacc_data['risk_free_rate']:.2%}")
    print(f"Market return: {old_wacc_data['market_return']:.2%}")
    print(f"ERP: {old_wacc_data['equity_risk_premium']:.2%}")
    print(f"Beta: {old_wacc_data['beta']:.2f}")
    print(f"Cost of Equity: {old_wacc_data['cost_of_equity']:.2%}")
    print(f"Cost of Debt (after-tax): {old_wacc_data['after_tax_cost_of_debt']:.2%}")
    print(f"E/V: {old_wacc_data['equity_weight']:.1%}")
    print(f"D/V: {old_wacc_data['debt_weight']:.1%}")
    print(f"WACC: {old_wacc_data['wacc']:.2%}\n")

    # Run DCF with old WACC
    old_model = EnhancedDCFModel(
        wacc=old_wacc_data["wacc"],
        terminal_growth=old_wacc_calc.get_sector_terminal_growth(ticker),
    )
    old_result = old_model.full_dcf_valuation(
        base_fcf=base_fcf,
        historical_fcf=historical_fcf,
        cash=cash,
        debt=debt,
        diluted_shares=shares,
        years=5,
    )

    old_fv = old_result["fair_value_per_share"]
    old_upside = ((old_fv - current_price) / current_price) * 100

    print(f"Fair Value: ${old_fv:.2f}")
    print(f"Upside: {old_upside:+.1f}%")

    # TEST 2: New Model (Damodaran)
    print("\n" + "=" * 80)
    print("NEW MODEL (With Damodaran)")
    print("=" * 80)

    # Show Damodaran industry data
    industry_data = DamodaranData.get_industry_data(ticker)
    print(f"\nDamodaran Industry Data ({industry_data['industry']}):")
    print(f"  Industry Beta: {industry_data['beta']:.2f}")
    print(f"  Industry Unlevered Beta: {industry_data['unlevered_beta']:.2f}")
    print(f"  Industry Debt Ratio: {industry_data['debt_ratio']:.2%}")
    print(f"  Industry Tax Rate: {industry_data['tax_rate']:.2%}")
    print(f"  Industry Cost of Equity: {industry_data['cost_of_equity']:.2%}")
    print(f"  Industry WACC: {industry_data['wacc']:.2%}\n")

    new_wacc_calc = WACCCalculator(use_damodaran=True)
    new_wacc_data = new_wacc_calc.calculate_wacc(
        ticker, use_net_debt=True, adjust_for_growth=True
    )

    print(f"Risk-free rate: {new_wacc_data['risk_free_rate']:.2%} (Damodaran 2025)")
    print(f"Market return: {new_wacc_data['market_return']:.2%} (Damodaran 2025)")
    print(f"ERP: {new_wacc_data['equity_risk_premium']:.2%}")
    print(f"Beta: {new_wacc_data['beta']:.2f} (Source: {new_wacc_data['beta_source']})")
    print(f"Cost of Equity: {new_wacc_data['cost_of_equity']:.2%}")
    print(f"Cost of Debt (after-tax): {new_wacc_data['after_tax_cost_of_debt']:.2%}")
    print(f"E/V: {new_wacc_data['equity_weight']:.1%}")
    print(f"D/V: {new_wacc_data['debt_weight']:.1%}")

    if new_wacc_data.get("using_gross_debt"):
        print("⚠️  Using GROSS debt for WACC (company has net cash but meaningful debt)")
        print(f"   Gross Debt: ${new_wacc_data['total_debt']/1e9:.2f}B")
        print(f"   Net Debt: ${new_wacc_data['net_debt']/1e9:.2f}B")
        print(
            f"   Debt for WACC: ${new_wacc_data['debt_for_wacc']/1e9:.2f}B (capturing tax shield)"
        )

    print(f"WACC: {new_wacc_data['wacc']:.2%}\n")

    # Run DCF with new WACC
    new_model = EnhancedDCFModel(
        wacc=new_wacc_data["wacc"],
        terminal_growth=new_wacc_calc.get_sector_terminal_growth(ticker),
    )
    new_result = new_model.full_dcf_valuation(
        base_fcf=base_fcf,
        historical_fcf=historical_fcf,
        cash=cash,
        debt=debt,
        diluted_shares=shares,
        years=5,
    )

    new_fv = new_result["fair_value_per_share"]
    new_upside = ((new_fv - current_price) / current_price) * 100

    print(f"Fair Value: ${new_fv:.2f}")
    print(f"Upside: {new_upside:+.1f}%")

    # COMPARISON
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)

    wacc_change = new_wacc_data["wacc"] - old_wacc_data["wacc"]
    fv_change = ((new_fv - old_fv) / old_fv) * 100

    print(
        f"\nWACC Change: {old_wacc_data['wacc']:.2%} → {new_wacc_data['wacc']:.2%} ({wacc_change:+.2%})"
    )
    print(f"Fair Value Change: ${old_fv:.2f} → ${new_fv:.2f} ({fv_change:+.1f}%)")
    print(f"Old Upside: {old_upside:+.1f}%")
    print(f"New Upside: {new_upside:+.1f}%")
    print(f"Change in Assessment: {new_upside - old_upside:+.1f} percentage points")

    return {
        "ticker": ticker,
        "old_wacc": old_wacc_data["wacc"],
        "new_wacc": new_wacc_data["wacc"],
        "old_fv": old_fv,
        "new_fv": new_fv,
        "old_upside": old_upside,
        "new_upside": new_upside,
    }


if __name__ == "__main__":
    # Test with key companies
    companies = ["MSFT", "AAPL", "NVDA", "JNJ", "KO"]

    results = []
    for ticker in companies:
        try:
            result = test_company(ticker)
            results.append(result)
        except Exception as e:
            print(f"\nError testing {ticker}: {e}")

    # Summary table
    print("\n\n" + "=" * 100)
    print("SUMMARY TABLE")
    print("=" * 100)
    print(
        f"{'Ticker':<8} {'Old WACC':<12} {'New WACC':<12} {'Old FV':<12} {'New FV':<12} {'Old Upside':<12} {'New Upside':<12}"
    )
    print("-" * 100)

    for r in results:
        print(
            f"{r['ticker']:<8} {r['old_wacc']:>10.2%}  {r['new_wacc']:>10.2%}  "
            f"${r['old_fv']:>9.2f}  ${r['new_fv']:>9.2f}  "
            f"{r['old_upside']:>+10.1f}%  {r['new_upside']:>+10.1f}%"
        )
