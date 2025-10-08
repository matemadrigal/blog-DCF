"""
Test company-specific terminal growth calculation.

This script demonstrates how terminal growth is calculated for each
individual company based on their specific fundamentals:
- ROE (sustainable profitability)
- Operating margins (efficiency)
- Revenue growth (momentum)
- Beta (risk/volatility)
"""

from src.dcf.wacc_calculator import WACCCalculator


def test_terminal_growth():
    """Test terminal growth calculation for various companies."""

    print("=" * 100)
    print("TERMINAL GROWTH - Cálculo Específico por Empresa (Metodología Damodaran)")
    print("=" * 100)
    print()

    print("📚 METODOLOGÍA:")
    print(
        "   g_terminal = GDP_base + ROE_premium + margin_premium + growth_premium - risk_adjustment"
    )
    print()
    print("   • GDP base: 2.5% (crecimiento de largo plazo EE.UU.)")
    print("   • ROE premium: +0.5% si ROE > 15%, 0% si 10-15%, -0.5% si < 10%")
    print("   • Margin premium: +0.5% si >20%, +0.25% si >10%, 0% si >5%, -0.5% si <5%")
    print(
        "   • Growth premium: +0.5% si >15%, +0.25% si >5%, 0% si <5%, -0.5% si negativo"
    )
    print("   • Risk adjustment: +0.5% si β>1.5, +0.25% si β>1.2, -0.25% si β<0.8")
    print()
    print("   Constraints: Min 1.5%, Max 4.5%")
    print()
    print("=" * 100)
    print()

    # Test companies from different sectors
    tickers = [
        "AAPL",  # Tech - high margins, high ROE
        "MSFT",  # Tech - excellent fundamentals
        "NVDA",  # Tech - high growth, high volatility
        "GOOGL",  # Tech - strong margins
        "JNJ",  # Healthcare - stable, mature
        "PFE",  # Healthcare - pharma
        "JPM",  # Financial - bank
        "BAC",  # Financial - bank
        "KO",  # Consumer - mature, stable
        "WMT",  # Retail - low margins
        "DUK",  # Utility - very stable, low growth
        "XOM",  # Energy - cyclical
    ]

    wacc_calc = WACCCalculator(use_damodaran=True)

    print(
        f"{'Ticker':<10} {'ROE':<8} {'Op.Margin':<12} {'Rev.Growth':<12} {'Beta':<8} {'g_terminal':<12} {'Método':<20}"
    )
    print("-" * 100)

    results = []
    for ticker in tickers:
        try:
            result = wacc_calc.calculate_company_terminal_growth(
                ticker, use_company_specific=True
            )

            g = result["terminal_growth"]
            method = result["method"]

            if method == "company_specific":
                comp = result["components"]
                roe = comp.get("roe", 0)
                op_margin = comp.get("operating_margin", 0)
                rev_growth = comp.get("revenue_growth", 0)
                beta = comp.get("beta", 1.0)

                print(
                    f"{ticker:<10} {roe*100:>6.1f}% {op_margin*100:>10.1f}% {rev_growth*100:>10.1f}% {beta:>6.2f}  {g*100:>10.2f}%  {method:<20}"
                )

                results.append(
                    {
                        "ticker": ticker,
                        "g": g,
                        "roe": roe,
                        "margin": op_margin,
                        "growth": rev_growth,
                        "beta": beta,
                        "justification": result["justification"],
                    }
                )
            else:
                print(
                    f"{ticker:<10} {'N/A':<8} {'N/A':<12} {'N/A':<12} {'N/A':<8} {g*100:>10.2f}%  {method:<20}"
                )

        except Exception as e:
            print(f"{ticker:<10} Error: {str(e)}")

    print()
    print("=" * 100)
    print("ANÁLISIS DETALLADO POR EMPRESA")
    print("=" * 100)
    print()

    for r in results:
        print(f"\n📊 **{r['ticker']}**")
        print("-" * 50)
        print(r["justification"])
        print()

    print()
    print("=" * 100)
    print("CONCLUSIONES")
    print("=" * 100)
    print()
    print("✅ DIFERENCIAS CLAVE vs CÁLCULO POR SECTOR:")
    print()
    print(
        "1. **Personalización**: Cada empresa tiene su propio g_terminal basado en fundamentales"
    )
    print("2. **ROE**: Empresas con ROE >15% (AAPL, MSFT) obtienen premium de +0.5%")
    print(
        "3. **Márgenes**: Tech con márgenes >20% obtienen +0.5%, retail con <10% pierden -0.5%"
    )
    print("4. **Crecimiento**: Empresas con revenue growth >15% obtienen +0.5%")
    print("5. **Riesgo**: Alta volatilidad (β>1.5) reduce terminal growth en -0.5%")
    print()
    print("🎯 EJEMPLOS:")
    print()
    print("• **AAPL**: ROE alto (1.5) + márgenes excelentes (30%+) → g_terminal ~4.0%")
    print(
        "• **NVDA**: Crecimiento explosivo pero alta volatilidad → g_terminal ~3.5-4.0%"
    )
    print(
        "• **KO**: Empresa madura, márgenes buenos pero crecimiento bajo → g_terminal ~2.5%"
    )
    print("• **DUK**: Utility estable, bajo crecimiento, regulado → g_terminal ~2.0%")
    print()
    print("📈 VENTAJAS:")
    print()
    print("✓ Refleja calidad de la empresa (ROE, márgenes)")
    print("✓ Captura momentum de crecimiento")
    print("✓ Ajusta por riesgo/volatilidad")
    print("✓ Más preciso que usar promedio sectorial")
    print()
    print("=" * 100)


if __name__ == "__main__":
    test_terminal_growth()
