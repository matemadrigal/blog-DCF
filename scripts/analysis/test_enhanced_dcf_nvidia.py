"""Test Enhanced DCF Model with NVIDIA."""

import yfinance as yf
from src.dcf.enhanced_model import EnhancedDCFModel

print("=" * 80)
print("TESTING ENHANCED DCF MODEL WITH NVIDIA (NVDA)")
print("=" * 80)
print()

# Get NVIDIA data
ticker = "NVDA"
print(f"Fetching data for {ticker}...")
nvda = yf.Ticker(ticker)
info = nvda.info
cashflow = nvda.cashflow
balance_sheet = nvda.balance_sheet

# Get current price and shares
current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
shares_outstanding = info.get("sharesOutstanding", 0)

print(f"Current Price: ${current_price:.2f}")
print(f"Shares Outstanding: {shares_outstanding/1e9:.2f}B")
print()

# Extract historical FCF
print("Extracting Historical FCF...")
historical_fcf = []
if not cashflow.empty:
    cols = list(cashflow.columns)[:5]
    for col in cols:
        op = None
        capex = None
        for idx in cashflow.index:
            name = str(idx).lower()
            if "operating cash flow" in name and op is None:
                op = cashflow.loc[idx, col]
            if (
                "capital expenditure" in name or "purchase of ppe" in name
            ) and capex is None:
                capex = cashflow.loc[idx, col]
        if op is not None and capex is not None:
            fcf = float(op - abs(capex))
            historical_fcf.append(fcf)

# Reverse to get chronological order (oldest to newest)
historical_fcf = list(reversed(historical_fcf))
base_fcf = historical_fcf[-1] if historical_fcf else 0

print("Historical FCF (last 5 years):")
for i, fcf in enumerate(historical_fcf):
    print(f"  Year {i+1}: ${fcf/1e9:.2f}B")
print(f"Base FCF: ${base_fcf/1e9:.2f}B")
print()

# Get balance sheet data
print("Extracting Balance Sheet Data...")
cash = 0.0
total_debt = 0.0

if not balance_sheet.empty:
    col = balance_sheet.columns[0]
    for idx in balance_sheet.index:
        name = str(idx).lower()
        if "cash and cash equivalents" in name or ("cash" in name and "short" in name):
            val = balance_sheet.loc[idx, col]
            if val is not None and str(val).lower() != "nan":
                cash = float(val)
        if "total debt" in name or "long term debt" in name:
            val = balance_sheet.loc[idx, col]
            if val is not None and str(val).lower() != "nan":
                total_debt = float(val)

# Fallback to info
if cash == 0:
    cash = info.get("totalCash", 0.0)
if total_debt == 0:
    total_debt = info.get("totalDebt", 0.0)

print(f"Cash: ${cash/1e9:.2f}B")
print(f"Total Debt: ${total_debt/1e9:.2f}B")
print(f"Net Cash/(Debt): ${(cash - total_debt)/1e9:.2f}B")
print()

# Test Enhanced DCF Model
print("=" * 80)
print("RUNNING ENHANCED DCF MODEL")
print("=" * 80)
print()

model = EnhancedDCFModel(wacc=0.085, terminal_growth=0.03)

result = model.full_dcf_valuation(
    base_fcf=base_fcf,
    historical_fcf=historical_fcf,
    cash=cash,
    debt=total_debt,
    diluted_shares=shares_outstanding,
    years=5,
)

print(f"WACC: {result['wacc']:.2%}")
print(f"Terminal Growth: {result['terminal_growth']:.2%}")
print()

print("Growth Rates (Tiered):")
for i, rate in enumerate(result["growth_rates"], 1):
    print(f"  Year {i}: {rate*100:+.2f}%")
print()

print("Projected FCF:")
for i, fcf in enumerate(result["projected_fcf"], 1):
    print(f"  Year {i}: ${fcf/1e9:.2f}B")
print()

print("Present Value of FCF:")
for i, pv in enumerate(result["pv_fcf"], 1):
    pct = (pv / result["enterprise_value"]) * 100
    print(f"  Year {i}: ${pv/1e9:.2f}B ({pct:.1f}% of EV)")
print()

print(f"Terminal Value (undiscounted): ${result['terminal_value']/1e9:.2f}B")
print(
    f"PV of Terminal Value: ${result['pv_terminal_value']/1e9:.2f}B ({(result['pv_terminal_value']/result['enterprise_value'])*100:.1f}% of EV)"
)
print()

print("=" * 80)
print("VALUATION RESULTS")
print("=" * 80)
print()

print(f"Enterprise Value (EV): ${result['enterprise_value']/1e9:.2f}B")
print(f"+ Cash:                ${result['cash']/1e9:.2f}B")
print(f"- Debt:                ${result['debt']/1e9:.2f}B")
print("─" * 40)
print(f"Equity Value:          ${result['equity_value']/1e9:.2f}B")
print()
print(f"Diluted Shares:        {result['diluted_shares']/1e9:.2f}B")
print("─" * 40)
print(f"Fair Value per Share:  ${result['fair_value_per_share']:.2f}")
print()
print(f"Current Market Price:  ${current_price:.2f}")
print("─" * 40)
upside = ((result["fair_value_per_share"] - current_price) / current_price) * 100
print(f"Upside/(Downside):     {upside:+.1f}%")
print()

if upside > 20:
    print("✅ UNDERVALUED - Strong Buy")
elif upside > 0:
    print("✓ UNDERVALUED - Buy")
elif upside > -20:
    print("≈ FAIRLY VALUED - Hold")
else:
    print("⚠️ OVERVALUED - Avoid/Sell")

print()
print("=" * 80)
print("TEST COMPLETED")
print("=" * 80)
