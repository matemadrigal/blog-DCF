"""
Script para analizar múltiples empresas y verificar parámetros de valoración DCF.
Compara WACC y tasa de crecimiento terminal con referencias del mercado.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dcf.wacc_calculator import WACCCalculator
import pandas as pd
import yfinance as yf


def analyze_company(ticker: str, wacc_calc: WACCCalculator):
    """
    Analiza una empresa y retorna métricas clave de valoración.
    """
    try:
        print(f"\n{'='*80}")
        print(f"Analizando {ticker}...")
        print(f"{'='*80}")

        # Calculate WACC (company-specific)
        wacc_result = wacc_calc.calculate_wacc(
            ticker, use_net_debt=True, adjust_for_growth=True, use_industry_wacc=False
        )

        # Get industry WACC for comparison
        industry_wacc_result = wacc_calc.calculate_wacc(
            ticker, use_net_debt=True, adjust_for_growth=False, use_industry_wacc=True
        )

        # Calculate terminal growth (company-specific)
        terminal_result = wacc_calc.calculate_company_terminal_growth(
            ticker, use_company_specific=True
        )

        # Get company info
        stock = yf.Ticker(ticker)
        info = stock.info
        sector = info.get("sector", "Unknown")
        industry = info.get("industry", "Unknown")

        # Build result
        result = {
            "Ticker": ticker,
            "Sector": sector,
            "Industry": industry[:30],  # Truncate for display
            # WACC metrics
            "WACC_Company": wacc_result["wacc"] * 100,
            "WACC_Unadjusted": wacc_result["wacc_unadjusted"] * 100,
            "WACC_Industry": industry_wacc_result["wacc"] * 100,
            "Beta": wacc_result["beta"],
            "Cost_of_Equity": wacc_result["cost_of_equity"] * 100,
            # Terminal growth
            "Terminal_Growth": terminal_result["terminal_growth"] * 100,
            "Terminal_Method": terminal_result["method"],
            # Capital structure
            "Debt_Ratio": wacc_result["debt_weight"],
            "Equity_Ratio": wacc_result["equity_weight"],
            # Risk metrics
            "Risk_Free_Rate": wacc_result["risk_free_rate"] * 100,
            "Market_Return": wacc_result["market_return"] * 100,
            "Equity_Risk_Premium": wacc_result["equity_risk_premium"] * 100,
        }

        # Print detailed info
        print(f"\n{ticker} - {sector}")
        print(f"{'─'*80}")
        print(f"WACC (Company-Specific, Adjusted): {result['WACC_Company']:.2f}%")
        print(f"WACC (Unadjusted):                  {result['WACC_Unadjusted']:.2f}%")
        print(f"WACC (Industry Average):            {result['WACC_Industry']:.2f}%")
        print(f"Beta:                               {result['Beta']:.2f}")
        print(f"Cost of Equity (Re):                {result['Cost_of_Equity']:.2f}%")
        print(f"Terminal Growth Rate:               {result['Terminal_Growth']:.2f}%")
        print(f"Terminal Growth Method:             {result['Terminal_Method']}")
        print("\nCapital Structure:")
        print(f"  Equity Weight:                    {result['Equity_Ratio']:.2%}")
        print(f"  Debt Weight:                      {result['Debt_Ratio']:.2%}")
        print("\nMarket Parameters:")
        print(f"  Risk-Free Rate:                   {result['Risk_Free_Rate']:.2f}%")
        print(f"  Market Return:                    {result['Market_Return']:.2f}%")
        print(
            f"  Equity Risk Premium:              {result['Equity_Risk_Premium']:.2f}%"
        )

        # Analysis vs benchmarks
        print(f"\n{'─'*80}")
        print("ANÁLISIS vs BENCHMARKS:")
        print(f"{'─'*80}")

        # WACC analysis
        wacc_adjusted = result["WACC_Company"]
        wacc_industry = result["WACC_Industry"]

        if sector == "Technology":
            wacc_benchmark_low = 7.5
            wacc_benchmark_high = 9.5
        elif sector == "Healthcare":
            wacc_benchmark_low = 7.0
            wacc_benchmark_high = 9.0
        elif sector == "Financial Services":
            wacc_benchmark_low = 8.0
            wacc_benchmark_high = 10.0
        elif sector == "Consumer Defensive":
            wacc_benchmark_low = 6.5
            wacc_benchmark_high = 8.5
        else:
            wacc_benchmark_low = 7.0
            wacc_benchmark_high = 9.5

        print("\n1. WACC Analysis:")
        print(f"   Company WACC:     {wacc_adjusted:.2f}%")
        print(f"   Industry Average: {wacc_industry:.2f}%")
        print(
            f"   Benchmark Range:  {wacc_benchmark_low:.1f}% - {wacc_benchmark_high:.1f}%"
        )

        if wacc_adjusted > wacc_benchmark_high:
            print("   ⚠️  WACC ALTO - Por encima del rango recomendado")
            print(f"      Diferencia: +{wacc_adjusted - wacc_benchmark_high:.2f}pp")
        elif wacc_adjusted < wacc_benchmark_low:
            print("   ✓ WACC BAJO - Puede ser muy optimista")
        else:
            print("   ✓ WACC EN RANGO - Dentro de parámetros razonables")

        # Terminal growth analysis
        terminal_growth = result["Terminal_Growth"]
        terminal_benchmark_low = 2.0
        terminal_benchmark_high = 3.0

        print("\n2. Terminal Growth Analysis:")
        print(f"   Company Terminal Growth: {terminal_growth:.2f}%")
        print(
            f"   Benchmark Range:         {terminal_benchmark_low:.1f}% - {terminal_benchmark_high:.1f}%"
        )
        print("   GDP Long-term:           ~2.5%")

        if terminal_growth > 4.0:
            print("   ⚠️  CRECIMIENTO TERMINAL MUY ALTO")
            print(
                f"      Diferencia vs benchmark: +{terminal_growth - terminal_benchmark_high:.2f}pp"
            )
            print("      Justificación requerida para >3.5%")
        elif terminal_growth > terminal_benchmark_high:
            print("   ⚠️  CRECIMIENTO TERMINAL ALTO")
            print(
                f"      Diferencia: +{terminal_growth - terminal_benchmark_high:.2f}pp"
            )
        elif terminal_growth < terminal_benchmark_low:
            print("   ⚠️  CRECIMIENTO TERMINAL BAJO - ¿Industria en declive?")
        else:
            print("   ✓ CRECIMIENTO TERMINAL EN RANGO")

        # Spread analysis
        wacc_terminal_spread = wacc_adjusted - terminal_growth
        print("\n3. WACC - Terminal Growth Spread:")
        print(f"   Spread: {wacc_terminal_spread:.2f}pp")

        if wacc_terminal_spread < 3.0:
            print("   ⚠️  SPREAD MUY BAJO - Riesgo de valoraciones infladas")
            print("      Recomendado: >4.0pp para estabilidad")
        elif wacc_terminal_spread < 4.0:
            print("   ⚠️  SPREAD AJUSTADO - Monitorear sensibilidad")
        else:
            print("   ✓ SPREAD SALUDABLE")

        return result

    except Exception as e:
        print(f"Error analizando {ticker}: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """
    Analiza múltiples empresas de diferentes sectores.
    """
    print("=" * 80)
    print("ANÁLISIS MULTI-EMPRESA - VALIDACIÓN DE PARÁMETROS DCF")
    print("=" * 80)
    print("\nObjetivo: Verificar si WACC alto y g terminal optimista son sistemáticos")
    print(
        "Referencia: Análisis de Apple mostró WACC 8.26-11.26% (vs 7.5-9.5% recomendado)"
    )
    print("           y g terminal 2.75-4.25% (vs 2-3% recomendado)")

    # Initialize calculators
    wacc_calc = WACCCalculator(use_damodaran=True)

    # Companies to analyze
    companies = {
        "Tecnología": ["AAPL", "MSFT", "GOOGL", "META"],
        "Financiero": ["JPM", "BAC", "WFC"],
        "Healthcare": ["JNJ", "UNH", "PFE"],
        "Consumer Defensive": ["PG", "KO", "WMT"],
        "Industrial": ["CAT", "BA", "GE"],
    }

    all_results = []

    for sector, tickers in companies.items():
        print(f"\n\n{'#'*80}")
        print(f"SECTOR: {sector}")
        print(f"{'#'*80}")

        for ticker in tickers:
            result = analyze_company(ticker, wacc_calc)
            if result:
                all_results.append(result)

            # Small delay to avoid rate limits
            import time

            time.sleep(1)

    # Summary analysis
    if all_results:
        print(f"\n\n{'='*80}")
        print("RESUMEN COMPARATIVO - TODOS LOS SECTORES")
        print(f"{'='*80}\n")

        df = pd.DataFrame(all_results)

        print("WACC - Estadísticas Descriptivas:")
        print(f"  Media:              {df['WACC_Company'].mean():.2f}%")
        print(f"  Mediana:            {df['WACC_Company'].median():.2f}%")
        print(f"  Desv. Estándar:     {df['WACC_Company'].std():.2f}%")
        print(
            f"  Mínimo:             {df['WACC_Company'].min():.2f}% ({df.loc[df['WACC_Company'].idxmin(), 'Ticker']})"
        )
        print(
            f"  Máximo:             {df['WACC_Company'].max():.2f}% ({df.loc[df['WACC_Company'].idxmax(), 'Ticker']})"
        )

        print("\nTerminal Growth - Estadísticas Descriptivas:")
        print(f"  Media:              {df['Terminal_Growth'].mean():.2f}%")
        print(f"  Mediana:            {df['Terminal_Growth'].median():.2f}%")
        print(f"  Desv. Estándar:     {df['Terminal_Growth'].std():.2f}%")
        print(
            f"  Mínimo:             {df['Terminal_Growth'].min():.2f}% ({df.loc[df['Terminal_Growth'].idxmin(), 'Ticker']})"
        )
        print(
            f"  Máximo:             {df['Terminal_Growth'].max():.2f}% ({df.loc[df['Terminal_Growth'].idxmax(), 'Ticker']})"
        )

        # Key findings
        print(f"\n{'─'*80}")
        print("HALLAZGOS CLAVE:")
        print(f"{'─'*80}")

        # WACC > 9.5%
        high_wacc = df[df["WACC_Company"] > 9.5]
        if len(high_wacc) > 0:
            print("\n🔴 Empresas con WACC > 9.5% (posible sobrestimación):")
            for _, row in high_wacc.iterrows():
                print(
                    f"   {row['Ticker']:6s} - {row['WACC_Company']:6.2f}% (Sector: {row['Sector']})"
                )

        # Terminal growth > 3.5%
        high_terminal = df[df["Terminal_Growth"] > 3.5]
        if len(high_terminal) > 0:
            print("\n🔴 Empresas con g terminal > 3.5% (posible optimismo):")
            for _, row in high_terminal.iterrows():
                print(
                    f"   {row['Ticker']:6s} - {row['Terminal_Growth']:6.2f}% (Sector: {row['Sector']})"
                )

        # Good examples
        good_wacc = df[(df["WACC_Company"] >= 7.5) & (df["WACC_Company"] <= 9.5)]
        good_terminal = df[
            (df["Terminal_Growth"] >= 2.0) & (df["Terminal_Growth"] <= 3.0)
        ]
        good_both = pd.merge(good_wacc, good_terminal, how="inner")

        if len(good_both) > 0:
            print("\n✅ Empresas con parámetros dentro de rango recomendado:")
            for _, row in good_both.iterrows():
                print(
                    f"   {row['Ticker']:6s} - WACC: {row['WACC_Company']:5.2f}%, g: {row['Terminal_Growth']:5.2f}%"
                )

        # Export to CSV
        output_file = "dcf_parameters_analysis.csv"
        df.to_csv(output_file, index=False)
        print(f"\n📊 Resultados completos exportados a: {output_file}")

        # Final conclusion
        print(f"\n{'='*80}")
        print("CONCLUSIÓN:")
        print(f"{'='*80}")

        pct_high_wacc = (len(high_wacc) / len(df)) * 100
        pct_high_terminal = (len(high_terminal) / len(df)) * 100

        print(f"\n{pct_high_wacc:.1f}% de las empresas tienen WACC > 9.5%")
        print(f"{pct_high_terminal:.1f}% de las empresas tienen g terminal > 3.5%")

        if pct_high_wacc > 30 or pct_high_terminal > 30:
            print("\n⚠️  PROBLEMA SISTEMÁTICO DETECTADO")
            print(
                "El modelo tiende a sobrestimar WACC y/o tasa de crecimiento terminal."
            )
            print("\nRECOMENDACIONES:")
            print("1. Revisar ajuste por beta en wacc_calculator.py (líneas 318-334)")
            print(
                "2. Revisar cálculo de terminal growth en wacc_calculator.py (líneas 365-517)"
            )
            print("3. Considerar caps más conservadores:")
            print("   - WACC máximo: 9.5% para tech, 8.5% para otros")
            print("   - g terminal máximo: 3.0% (salvo casos excepcionales)")
        else:
            print("\n✅ PARÁMETROS GENERALMENTE RAZONABLES")
            print("Los casos fuera de rango parecen ser excepciones justificadas.")


if __name__ == "__main__":
    main()
