"""Test improved DCF model with dynamic WACC and realistic growth rates."""

from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
import yfinance as yf


def test_company_valuation(ticker: str):
    """Test valuation for a company with both old and new parameters."""
    print(f"\n{'=' * 80}")
    print(f"Testing {ticker}")
    print(f"{'=' * 80}\n")

    # Get company data
    stock = yf.Ticker(ticker)
    info = stock.info
    cashflow = stock.cashflow

    company_name = info.get("longName", ticker)
    current_price = info.get("currentPrice", 0)
    shares = info.get("sharesOutstanding", 0)

    print(f"Company: {company_name}")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Shares Outstanding: {shares/1e9:.2f}B\n")

    # Get FCF data
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

    if not historical_fcf:
        print(f"⚠️  No FCF data available for {ticker}")
        return

    base_fcf = historical_fcf[0]
    print(f"Base FCF: ${base_fcf/1e9:.2f}B")
    print(f"Historical FCF (5 years): {[f'{f/1e9:.2f}B' for f in historical_fcf]}\n")

    # Get balance sheet data
    cash = info.get("totalCash", 0)
    debt = info.get("totalDebt", 0)

    print(f"Cash: ${cash/1e9:.2f}B")
    print(f"Debt: ${debt/1e9:.2f}B")
    print(f"Net Debt: ${(debt-cash)/1e9:.2f}B\n")

    # Test 1: Old model (fixed WACC 8.5%, terminal growth 3%)
    print("=" * 80)
    print("OLD MODEL (Fixed Parameters)")
    print("=" * 80)

    old_model = EnhancedDCFModel(wacc=0.085, terminal_growth=0.03)
    old_model.terminal_growth = 0.03  # Force old terminal growth

    # Manually set old growth rates (conservative)
    old_growth_rates = [0.15, 0.12, 0.10, 0.08, 0.05]

    old_result = old_model.full_dcf_valuation(
        base_fcf=base_fcf,
        historical_fcf=historical_fcf,
        cash=cash,
        debt=debt,
        diluted_shares=shares,
        years=5,
        custom_growth_rates=old_growth_rates,
    )

    print(f"WACC: {old_result['wacc']:.2%}")
    print(f"Terminal Growth: {old_result['terminal_growth']:.2%}")
    print(f"Growth Rates: {[f'{g:.1%}' for g in old_result['growth_rates']]}")
    print(f"Enterprise Value: ${old_result['enterprise_value']/1e9:.2f}B")
    print(f"Equity Value: ${old_result['equity_value']/1e9:.2f}B")
    print(f"Fair Value per Share: ${old_result['fair_value_per_share']:.2f}")
    print(f"Current Price: ${current_price:.2f}")

    old_upside = (
        (old_result["fair_value_per_share"] - current_price) / current_price
    ) * 100
    print(f"Upside/Downside: {old_upside:+.1f}%\n")

    # Test 2: New model with dynamic WACC
    print("=" * 80)
    print("NEW MODEL (Dynamic WACC + Realistic Growth)")
    print("=" * 80)

    wacc_calc = WACCCalculator()
    wacc_components = wacc_calc.calculate_wacc(
        ticker, use_net_debt=True, adjust_for_growth=True
    )
    dynamic_wacc = wacc_components["wacc"]
    sector_terminal_g = wacc_calc.get_sector_terminal_growth(ticker)

    print(f"Beta: {wacc_components['beta']:.2f}")
    print(f"Cost of Equity (CAPM): {wacc_components['cost_of_equity']:.2%}")
    print(f"Cost of Debt (after-tax): {wacc_components['after_tax_cost_of_debt']:.2%}")
    print(
        f"E/V: {wacc_components['equity_weight']:.1%} | D/V: {wacc_components['debt_weight']:.1%}"
    )
    print(f"Dynamic WACC: {dynamic_wacc:.2%}")
    print(f"Sector Terminal Growth: {sector_terminal_g:.2%}\n")

    new_model = EnhancedDCFModel(wacc=dynamic_wacc, terminal_growth=sector_terminal_g)

    new_result = new_model.full_dcf_valuation(
        base_fcf=base_fcf,
        historical_fcf=historical_fcf,
        cash=cash,
        debt=debt,
        diluted_shares=shares,
        years=5,
        custom_growth_rates=None,  # Let model calculate
    )

    print(f"WACC: {new_result['wacc']:.2%}")
    print(f"Terminal Growth: {new_result['terminal_growth']:.2%}")
    print(f"Growth Rates: {[f'{g:.1%}' for g in new_result['growth_rates']]}")
    print(f"Enterprise Value: ${new_result['enterprise_value']/1e9:.2f}B")
    print(f"Equity Value: ${new_result['equity_value']/1e9:.2f}B")
    print(f"Fair Value per Share: ${new_result['fair_value_per_share']:.2f}")
    print(f"Current Price: ${current_price:.2f}")

    new_upside = (
        (new_result["fair_value_per_share"] - current_price) / current_price
    ) * 100
    print(f"Upside/Downside: {new_upside:+.1f}%\n")

    # Comparison
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)

    fair_value_change = (
        (new_result["fair_value_per_share"] - old_result["fair_value_per_share"])
        / old_result["fair_value_per_share"]
    ) * 100
    print(f"Fair Value Change: {fair_value_change:+.1f}%")
    print(f"Old Model Fair Value: ${old_result['fair_value_per_share']:.2f}")
    print(f"New Model Fair Value: ${new_result['fair_value_per_share']:.2f}")
    print(f"Old Model Upside: {old_upside:+.1f}%")
    print(f"New Model Upside: {new_upside:+.1f}%")
    print(f"Change in Assessment: {new_upside - old_upside:+.1f} percentage points\n")


if __name__ == "__main__":
    # Test with different types of companies
    test_companies = [
        "AAPL",  # Large cap tech
        "MSFT",  # Large cap tech
        "NVDA",  # High growth tech
        "JNJ",  # Healthcare
        "KO",  # Consumer staples
    ]

    for ticker in test_companies:
        try:
            test_company_valuation(ticker)
        except Exception as e:
            print(f"Error testing {ticker}: {e}\n")
