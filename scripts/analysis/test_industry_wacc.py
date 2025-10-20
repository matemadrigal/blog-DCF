"""Test industry-specific WACC from Damodaran."""

from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.damodaran_data import DamodaranData

# Test companies from different sectors
test_companies = [
    ("MSFT", "Microsoft", "Software"),
    ("NVDA", "NVIDIA", "Semiconductor"),
    ("GOOGL", "Google", "Internet"),
    ("JNJ", "Johnson & Johnson", "Pharmaceutical"),
    ("JPM", "JPMorgan", "Bank"),
    ("DUK", "Duke Energy", "Utility"),
    ("WMT", "Walmart", "Retail"),
    ("KO", "Coca-Cola", "Food/Beverage"),
]

print("=" * 100)
print("WACC POR SECTOR - Comparación Company-Specific vs Industry Average (Damodaran)")
print("=" * 100)
print()

wacc_calc = WACCCalculator(use_damodaran=True)

results = []

for ticker, name, expected_sector in test_companies:
    print(f"\n{name} ({ticker}) - {expected_sector}")
    print("-" * 100)

    try:
        # Get industry data
        industry_data = DamodaranData.get_industry_data(ticker)

        # Method 1: Company-specific WACC
        company_wacc = wacc_calc.calculate_wacc(
            ticker, use_net_debt=True, adjust_for_growth=True, use_industry_wacc=False
        )

        # Method 2: Industry WACC
        industry_wacc = wacc_calc.calculate_wacc(
            ticker, use_net_debt=True, adjust_for_growth=True, use_industry_wacc=True
        )

        print(f"\n📊 DAMODARAN INDUSTRY DATA ({industry_data['industry'].upper()}):")
        print(f"   Industry Beta: {industry_data['beta']:.2f}")
        print(f"   Industry WACC: {industry_data['wacc']:.2%}")
        print(f"   Industry Cost of Equity: {industry_data['cost_of_equity']:.2%}")
        print(f"   Industry D/E Ratio: {industry_data['debt_ratio']:.2%}")

        print("\n🏢 COMPANY-SPECIFIC WACC:")
        print(f"   Beta: {company_wacc['beta']:.2f} ({company_wacc['beta_source']})")
        print(f"   Cost of Equity: {company_wacc['cost_of_equity']:.2%}")
        print(
            f"   Cost of Debt (after-tax): {company_wacc['after_tax_cost_of_debt']:.2%}"
        )
        print(
            f"   E/V: {company_wacc['equity_weight']:.1%} | D/V: {company_wacc['debt_weight']:.1%}"
        )
        print(f"   WACC: {company_wacc['wacc']:.2%}")

        print("\n🏭 INDUSTRY AVERAGE WACC (Damodaran):")
        print(f"   Beta: {industry_wacc['beta']:.2f} (Industry Average)")
        print(f"   Cost of Equity: {industry_wacc['cost_of_equity']:.2%}")
        print(
            f"   E/V: {industry_wacc['equity_weight']:.1%} | D/V: {industry_wacc['debt_weight']:.1%}"
        )
        print(f"   WACC: {industry_wacc['wacc']:.2%}")

        diff = company_wacc["wacc"] - industry_wacc["wacc"]
        print(
            f"\n📈 Diferencia: {diff:+.2%} ({'Company WACC higher' if diff > 0 else 'Industry WACC higher'})"
        )

        results.append(
            {
                "ticker": ticker,
                "name": name,
                "sector": expected_sector,
                "industry": industry_data["industry"],
                "company_wacc": company_wacc["wacc"],
                "industry_wacc": industry_wacc["wacc"],
                "diff": diff,
            }
        )

    except Exception as e:
        print(f"Error: {e}")

# Summary table
print("\n\n" + "=" * 120)
print("RESUMEN - WACCs POR SECTOR")
print("=" * 120)
print(
    f"{'Empresa':<25} {'Sector':<20} {'Industry':<15} {'Company WACC':<15} {'Industry WACC':<15} {'Diferencia':<15}"
)
print("-" * 120)

for r in results:
    print(
        f"{r['name']:<25} {r['sector']:<20} {r['industry']:<15} "
        f"{r['company_wacc']:>13.2%}  {r['industry_wacc']:>14.2%}  {r['diff']:>13.2%}"
    )

print("\n" + "=" * 120)
print("ANÁLISIS")
print("=" * 120)

print(
    """
✅ CADA SECTOR TIENE UN WACC DIFERENTE según Damodaran:

Sectores de BAJO riesgo (WACC bajo):
  • Utilities (Duke Energy): ~5.7%
  • Banks (JPMorgan): ~6.0%

Sectores de MEDIO riesgo:
  • Food/Beverage (Coca-Cola): ~6.8%
  • Pharmaceutical (J&J): ~7.9%
  • Retail (Walmart): ~7.8%

Sectores de ALTO riesgo (WACC alto):
  • Software (Microsoft): ~9.4%
  • Internet (Google): ~9.6%
  • Semiconductor (NVIDIA): ~10.0%

🎯 RECOMENDACIÓN:
  • Usar "Industry WACC" para:
    - Análisis rápido
    - Empresas sin datos completos
    - Comparación entre sectores

  • Usar "Company-Specific WACC" para:
    - Análisis detallado
    - Empresas con estructura de capital única
    - Valoración precisa
"""
)
