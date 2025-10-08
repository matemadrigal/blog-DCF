"""Test terminal growth calculation by industry."""

from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.damodaran_data import DamodaranData
import yfinance as yf

# Test companies from different sectors
test_companies = [
    ("MSFT", "Microsoft"),
    ("NVDA", "NVIDIA"),
    ("GOOGL", "Google"),
    ("AAPL", "Apple"),
    ("JNJ", "Johnson & Johnson"),
    ("PFE", "Pfizer"),
    ("JPM", "JPMorgan"),
    ("BAC", "Bank of America"),
    ("DUK", "Duke Energy"),
    ("NEE", "NextEra Energy"),
    ("KO", "Coca-Cola"),
    ("WMT", "Walmart"),
    ("XOM", "Exxon Mobil"),
]

print("=" * 100)
print("TERMINAL GROWTH RATE - Metodología Damodaran vs Cálculo Simple")
print("=" * 100)
print()
print("📚 FRAMEWORK DE DAMODARAN:")
print("   • Terminal growth debe ≤ GDP de largo plazo + pequeña prima")
print("   • GDP EE.UU. largo plazo: ~2.5%")
print("   • Inflación objetivo: ~2%")
print("   • Máximo teórico: ~4.5%, pero conservador: 2-3.5%")
print()
print("=" * 100)
print()

# Create calculators
calc_damodaran = WACCCalculator(use_damodaran=True)
calc_simple = WACCCalculator(use_damodaran=False)

results = []

print(
    f"{'Empresa':<25} {'Sector':<25} {'Industria':<18} {'Simple':<10} {'Damodaran':<10} {'Justificación':<30}"
)
print("-" * 130)

for ticker, name in test_companies:
    try:
        # Get sector info
        stock = yf.Ticker(ticker)
        sector = stock.info.get("sector", "Unknown")

        # Get industry from Damodaran
        industry_key = DamodaranData.get_industry_key(ticker)

        # Get terminal growth from both methods
        g_simple = calc_simple.get_sector_terminal_growth(ticker)
        g_damodaran = calc_damodaran.get_sector_terminal_growth(ticker)

        # Justification based on industry
        justifications = {
            "software": "GDP + innovación",
            "semiconductor": "GDP + tecnología",
            "internet": "GDP + network effects",
            "pharmaceutical": "GDP + demografía",
            "healthcare": "GDP + demografía",
            "bank": "GDP (regulado)",
            "utility": "Sub-GDP (maduro)",
            "retail": "GDP (competitivo)",
            "beverage": "GDP (maduro)",
            "food_processing": "GDP (maduro)",
            "oil_gas": "Sub-GDP (transición)",
            "market": "GDP promedio",
        }

        justification = justifications.get(industry_key, "GDP promedio")

        print(
            f"{name:<25} {sector:<25} {industry_key:<18} "
            f"{g_simple:>8.2%}  {g_damodaran:>8.2%}  {justification:<30}"
        )

        results.append(
            {
                "ticker": ticker,
                "name": name,
                "sector": sector,
                "industry": industry_key,
                "simple": g_simple,
                "damodaran": g_damodaran,
                "diff": g_damodaran - g_simple,
            }
        )

    except Exception as e:
        print(f"{name:<25} Error: {e}")

# Summary statistics
print("\n" + "=" * 100)
print("RESUMEN POR CATEGORÍA")
print("=" * 100)

categories = {
    "Tech Alto Crecimiento": ["software", "semiconductor", "internet"],
    "Healthcare": ["pharmaceutical", "healthcare", "biotechnology"],
    "Financials": ["bank", "insurance"],
    "Utilities/Energy": ["utility", "oil_gas"],
    "Consumer": ["retail", "beverage", "food_processing"],
}

print(f"\n{'Categoría':<25} {'Terminal Growth':<20} {'Razón':<50}")
print("-" * 100)

for category, industries in categories.items():
    # Get unique terminal growth values for this category
    g_values = set()
    for industry in industries:
        if industry in DamodaranData.INDUSTRY_DATA:
            # Use the get_terminal_growth method
            for ticker, _, _, industry_key, _, g_dam, _ in [
                (
                    r["ticker"],
                    r["name"],
                    r["sector"],
                    r["industry"],
                    r["simple"],
                    r["damodaran"],
                    r["diff"],
                )
                for r in results
            ]:
                if industry_key == industry:
                    g_values.add(g_dam)
                    break

    if g_values:
        g_range = (
            f"{min(g_values):.1%} - {max(g_values):.1%}"
            if len(g_values) > 1
            else f"{list(g_values)[0]:.1%}"
        )

        reasons = {
            "Tech Alto Crecimiento": "Innovación y crecimiento por encima de GDP",
            "Healthcare": "Demografía envejecida + crecimiento GDP",
            "Financials": "Crecimiento vinculado a GDP",
            "Utilities/Energy": "Maduro, regulado, por debajo de GDP",
            "Consumer": "Maduro, crecimiento = GDP",
        }

        print(f"{category:<25} {g_range:<20} {reasons[category]:<50}")

print("\n" + "=" * 100)
print("DIFERENCIAS CLAVE: Damodaran vs Simple")
print("=" * 100)

# Find biggest differences
sorted_results = sorted(results, key=lambda x: abs(x["diff"]), reverse=True)

print(
    f"\n{'Empresa':<25} {'Diferencia':<15} {'Simple → Damodaran':<25} {'Impacto':<30}"
)
print("-" * 100)

for r in sorted_results[:8]:
    diff_pct = r["diff"] * 100
    transition = f"{r['simple']:.1%} → {r['damodaran']:.1%}"

    if abs(diff_pct) < 0.1:
        impact = "Sin cambio"
    elif diff_pct < 0:
        impact = "Más conservador (↓ Fair Value)"
    else:
        impact = "Más optimista (↑ Fair Value)"

    print(f"{r['name']:<25} {diff_pct:>+13.1f}bp  {transition:<25} {impact:<30}")

print("\n" + "=" * 100)
print("CONCLUSIONES")
print("=" * 100)

print(
    """
✅ DAMODARAN ES MÁS GRANULAR Y CONSERVADOR:

1. **Tech (3.5%)** vs Simple (4%):
   - Damodaran: Más conservador para tech
   - Razón: Terminal phase = empresa madura, no puede crecer 4% perpetuamente

2. **Healthcare (3%)** vs Simple (3.5%):
   - Damodaran: Vinculado a GDP + demografía
   - Razón: Crecimiento sostenible a largo plazo

3. **Utilities (2%)** vs Simple (2.5%):
   - Damodaran: Más conservador
   - Razón: Sector maduro, regulado, crecimiento limitado

4. **Banks (2.5%)** vs Simple (3%):
   - Damodaran: Vinculado estrictamente a GDP
   - Razón: Sector financiero crece con economía

📊 REGLA DE DAMODARAN:
   "Terminal growth debe reflejar el crecimiento perpetuo sostenible.
    Ninguna empresa puede crecer por encima de GDP + inflación forever."

🎯 RECOMENDACIÓN:
   Usar terminal growth de Damodaran para:
   - Valoraciones conservadoras y defendibles
   - Análisis académico riguroso
   - Comparación justa entre sectores
"""
)
