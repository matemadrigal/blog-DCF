"""Debug growth rate calculation."""

import yfinance as yf
import numpy as np


def analyze_fcf_growth(ticker: str):
    """Analyze FCF growth patterns."""
    print(f"\n{'=' * 60}")
    print(f"Analyzing {ticker}")
    print(f"{'=' * 60}\n")

    stock = yf.Ticker(ticker)
    cashflow = stock.cashflow

    if cashflow.empty:
        print("No cashflow data")
        return

    historical_fcf = []
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

    print(f"Historical FCF: {[f'{f/1e9:.2f}B' for f in historical_fcf]}")

    # Calculate YoY growth
    hist_growth = []
    for i in range(1, len(historical_fcf)):
        if historical_fcf[i - 1] != 0:
            growth = (historical_fcf[i] - historical_fcf[i - 1]) / abs(
                historical_fcf[i - 1]
            )
            hist_growth.append(growth)
            print(f"Year {i}: {growth:.1%} growth")

    if not hist_growth:
        return

    print(f"\nMean growth: {np.mean(hist_growth):.1%}")
    print(f"Median growth: {np.median(hist_growth):.1%}")
    print(f"Std deviation: {np.std(hist_growth):.1%}")
    print(f"Min: {np.min(hist_growth):.1%}, Max: {np.max(hist_growth):.1%}")


if __name__ == "__main__":
    for ticker in ["AAPL", "MSFT", "NVDA", "JNJ", "KO"]:
        analyze_fcf_growth(ticker)
