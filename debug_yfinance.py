"""Debug Yahoo Finance data fetching."""

import yfinance as yf

ticker = "AAPL"
years = 5

print(f"Testing Yahoo Finance for {ticker}")
print("=" * 60)

try:
    t = yf.Ticker(ticker)
    cashflow = t.cashflow

    print(f"\nCashflow DataFrame shape: {cashflow.shape}")
    print(f"Cashflow empty: {cashflow.empty}")

    if not cashflow.empty:
        print(f"\nColumns (dates): {list(cashflow.columns)}")
        print("\nIndex (metrics):")
        for idx in cashflow.index:
            print(f"  - {idx}")

        print(f"\n{'='*60}")
        print("Searching for Operating Cash Flow and CAPEX...")
        print(f"{'='*60}\n")

        autofill = []
        cols = list(cashflow.columns)[:years]

        for i, c in enumerate(cols):
            print(f"\n--- Year {i+1}: {c.year if hasattr(c, 'year') else c} ---")

            op = None
            capex = None

            for idx in cashflow.index:
                name = str(idx).lower()

                # Look for Operating Cash Flow
                if "operating cash flow" in name and op is None:
                    op = cashflow.loc[idx, c]
                    print(f"  ✅ Found Operating CF: {idx} = {op:,.0f}")

                # Look for CAPEX (not stock repurchase!)
                if (
                    "capital expenditure" in name or "purchase of ppe" in name
                ) and capex is None:
                    capex = cashflow.loc[idx, c]
                    print(f"  ✅ Found CAPEX: {idx} = {capex:,.0f}")

            if op is not None and capex is not None:
                # CAPEX is usually negative, so we use abs
                fcf = float(op - abs(capex))
                autofill.append(fcf)
                print(f"  ➡️  FCF = Operating CF - abs(CAPEX) = {fcf:,.0f}")
            else:
                print(f"  ❌ Missing data: op={op}, capex={capex}")

        print(f"\n{'='*60}")
        print(f"RESULT: Found {len(autofill)} years of FCF data")
        print(f"{'='*60}")

        if autofill:
            print("\nFCF Values:")
            for i, fcf in enumerate(autofill):
                print(f"  Year {i+1}: ${fcf/1e9:.2f}B")

    else:
        print("ERROR: Cashflow DataFrame is empty!")

except Exception as e:
    print(f"\nERROR: {type(e).__name__}: {str(e)}")
    import traceback

    traceback.print_exc()
