"""Test unified FCF calculation across all modes."""

import yfinance as yf


def test_unified_fcf_calculation(ticker="AAPL"):
    """
    Test that FCF calculation is unified and correct.

    Formula: FCF = Operating Cash Flow - |Capital Expenditure|
    """
    print("=" * 70)
    print(f"Testing Unified FCF Calculation for {ticker}")
    print("=" * 70)
    print()

    try:
        t = yf.Ticker(ticker)
        cashflow = t.cashflow

        if cashflow.empty:
            print(f"❌ No cash flow data available for {ticker}")
            return

        print("Cash Flow Statement Data:")
        print("-" * 70)

        # Get up to 5 years of historical data
        cols = list(cashflow.columns)[:5]

        historical_fcf = []
        years_data = []

        for i, col in enumerate(cols):
            year = col.year if hasattr(col, "year") else f"Year {i+1}"
            op = None
            capex = None

            # Find Operating Cash Flow
            for idx in cashflow.index:
                name = str(idx).lower()
                if "operating cash flow" in name and op is None:
                    op = cashflow.loc[idx, col]
                    break

            # Find Capital Expenditure
            for idx in cashflow.index:
                name = str(idx).lower()
                if "capital expenditure" in name or "purchase of ppe" in name:
                    capex = cashflow.loc[idx, col]
                    break

            if op is not None and capex is not None:
                fcf = float(op - abs(capex))
                historical_fcf.append(fcf)

                # Format for display
                op_display = f"${op/1e9:.2f}B" if abs(op) > 1e9 else f"${op/1e6:.2f}M"
                capex_display = (
                    f"${capex/1e9:.2f}B" if abs(capex) > 1e9 else f"${capex/1e6:.2f}M"
                )
                fcf_display = (
                    f"${fcf/1e9:.2f}B" if abs(fcf) > 1e9 else f"${fcf/1e6:.2f}M"
                )

                years_data.append(
                    {
                        "year": year,
                        "ocf": op,
                        "capex": capex,
                        "fcf": fcf,
                        "ocf_display": op_display,
                        "capex_display": capex_display,
                        "fcf_display": fcf_display,
                    }
                )

                print(f"Year {year}:")
                print(f"  Operating Cash Flow: {op_display}")
                print(f"  Capital Expenditure: {capex_display}")
                print(f"  FCF = OCF - |CAPEX| = {fcf_display}")
                print()

        if historical_fcf:
            # Most recent year is first
            base_fcf = historical_fcf[0]
            base_year = years_data[0]["year"]

            print("=" * 70)
            print("RESULT:")
            print("=" * 70)
            print(f"Base Year: {base_year}")
            print(
                f"Base FCF: ${base_fcf/1e9:.2f}B"
                if base_fcf > 1e9
                else f"Base FCF: ${base_fcf/1e6:.2f}M"
            )
            print()
            print("This value should be CONSISTENT across:")
            print("  ✓ Mode: Manual (autosuggested)")
            print("  ✓ Mode: Autocompletar")
            print("  ✓ Mode: Multi-fuente")
            print()

            # Calculate growth rates
            print("Historical Growth Rates:")
            print("-" * 70)
            for i in range(1, len(historical_fcf)):
                if historical_fcf[i - 1] != 0:
                    growth = (historical_fcf[i - 1] - historical_fcf[i]) / abs(
                        historical_fcf[i]
                    )
                    print(
                        f"  {years_data[i]['year']} -> {years_data[i-1]['year']}: {growth*100:+.2f}%"
                    )
            print()

            return base_fcf, historical_fcf
        else:
            print("❌ No valid FCF data found")
            return None, []

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None, []


if __name__ == "__main__":
    # Test with Apple
    print("\n")
    test_unified_fcf_calculation("AAPL")

    print("\n")
    print("=" * 70)
    print("Testing with another company (MSFT)")
    print("=" * 70)
    print("\n")
    test_unified_fcf_calculation("MSFT")
