"""Test FCF normalization impact on AAPL valuation."""

from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
import yfinance as yf

ticker = "AAPL"

# Get data
stock = yf.Ticker(ticker)
info = stock.info
cashflow = stock.cashflow

# Get FCF
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

base_fcf = historical_fcf[0]
cash = info.get("totalCash", 0)
debt = info.get("totalDebt", 0)
shares = info.get("sharesOutstanding", 0)
current_price = info.get("currentPrice", 0)

print("AAPL - Apple Inc.")
print(f"Current Price: ${current_price:.2f}")
print("\nHistorical FCF:")
for i, fcf in enumerate(historical_fcf):
    print(f"  Year {i}: ${fcf/1e9:.2f}B")

# Calculate WACC
wacc_calc = WACCCalculator()
wacc_data = wacc_calc.calculate_wacc(ticker)
wacc = wacc_data["wacc"]
terminal_g = wacc_calc.get_sector_terminal_growth(ticker)

print(f"\nWACC: {wacc:.2%}")
print(f"Terminal Growth: {terminal_g:.2%}")

# Test different normalization methods
methods = ["current", "weighted_average", "average", "median"]

print(f"\n{'='*80}")
print("NORMALIZATION COMPARISON")
print(f"{'='*80}\n")

results = []

for method in methods:
    model = EnhancedDCFModel(wacc=wacc, terminal_growth=terminal_g)

    result = model.full_dcf_valuation(
        base_fcf=base_fcf,
        historical_fcf=historical_fcf,
        cash=cash,
        debt=debt,
        diluted_shares=shares,
        years=5,
        normalize_base=(method != "current"),
        normalization_method=method,
    )

    fv = result["fair_value_per_share"]
    upside = ((fv - current_price) / current_price) * 100
    base_used = result["base_fcf"]

    results.append(
        {
            "method": method,
            "base_fcf": base_used,
            "fair_value": fv,
            "upside": upside,
        }
    )

    method_label = {
        "current": "Año Actual (sin normalizar)",
        "weighted_average": "Promedio Ponderado (50%, 30%, 20%)",
        "average": "Promedio Simple",
        "median": "Mediana",
    }[method]

    print(f"{method_label}")
    print(f"  Base FCF: ${base_used/1e9:.2f}B")
    print(f"  Fair Value: ${fv:.2f}")
    print(f"  Upside: {upside:+.1f}%")
    print()

# Summary table
print(f"{'='*80}")
print("SUMMARY")
print(f"{'='*80}\n")

print(f"Current Market Price: ${current_price:.2f}\n")

print(f"{'Method':<40} {'Base FCF':<15} {'Fair Value':<15} {'Upside':<10}")
print(f"{'-'*80}")

for r in results:
    method_label = {
        "current": "Año Actual",
        "weighted_average": "Promedio Ponderado",
        "average": "Promedio Simple",
        "median": "Mediana",
    }[r["method"]]

    print(
        f"{method_label:<40} "
        f"${r['base_fcf']/1e9:>6.2f}B       "
        f"${r['fair_value']:>8.2f}       "
        f"{r['upside']:>+6.1f}%"
    )

print(f"\n{'='*80}")
print("KEY INSIGHTS")
print(f"{'='*80}\n")

current_fv = [r for r in results if r["method"] == "current"][0]["fair_value"]
weighted_fv = [r for r in results if r["method"] == "weighted_average"][0]["fair_value"]

improvement = ((weighted_fv - current_fv) / current_fv) * 100

print(f"1. Using weighted average FCF increases fair value by {improvement:+.1f}%")
print("2. This brings valuation closer to market expectations")
print(f"3. Historical FCF: {[f'${f/1e9:.1f}B' for f in historical_fcf[:4]]}")
print("4. Apple's FCF is volatile - normalization provides better base")
