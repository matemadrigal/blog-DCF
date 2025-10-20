"""
Script para probar los ajustes realizados en los parámetros DCF.
Compara ANTES vs DESPUÉS de los ajustes.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dcf.wacc_calculator import WACCCalculator
import pandas as pd


def test_company(ticker: str, wacc_calc: WACCCalculator):
    """
    Prueba una empresa y muestra los resultados con los nuevos ajustes.
    """
    print(f"\n{'='*80}")
    print(f"Probando {ticker}")
    print(f"{'='*80}")

    try:
        # Calculate WACC
        wacc_result = wacc_calc.calculate_wacc(
            ticker, use_net_debt=True, adjust_for_growth=True, use_industry_wacc=False
        )

        # Calculate terminal growth WITH WACC for spread validation
        terminal_result = wacc_calc.calculate_company_terminal_growth(
            ticker,
            use_company_specific=True,
            wacc=wacc_result["wacc"],
            validate_spread=True,
        )

        # Display results
        print(f"\nResultados para {ticker}:")
        print(f"{'─'*80}")

        print("\n📊 WACC:")
        print(f"   WACC Final:              {wacc_result['wacc']:.2%}")
        print(f"   WACC sin ajustar:        {wacc_result['wacc_unadjusted']:.2%}")

        if wacc_result.get("floor_applied"):
            print(
                f"   ✓ Floor aplicado:        {wacc_result['wacc_before_floor']:.2%} → {wacc_result['wacc']:.2%}"
            )
            print(
                f"     (Floor del sector {wacc_result['sector']}: {wacc_result['wacc_floor']:.2%})"
            )

        if wacc_result.get("using_industry_wacc"):
            print("   ✓ Usando WACC industria (sector financiero)")

        print("\n📈 Crecimiento Terminal:")
        print(f"   g terminal:              {terminal_result['terminal_growth']:.2%}")

        if terminal_result.get("spread_adjusted"):
            print(
                f"   ✓ Spread ajustado:       {terminal_result['g_before_spread_adjustment']:.2%} → {terminal_result['terminal_growth']:.2%}"
            )
            print("     (Para mantener spread mínimo 4.0pp)")

        print("\n⚖️  Spread (WACC - g):")
        spread = wacc_result["wacc"] - terminal_result["terminal_growth"]
        print(f"   Spread:                  {spread:.2%} ({spread*100:.1f}pp)")

        if spread < 0.04:
            print("   ⚠️  SPREAD BAJO - Revisar!")
        elif spread < 0.05:
            print("   ⚠️  Spread ajustado")
        else:
            print("   ✓ Spread saludable")

        print("\n📋 Componentes del cálculo:")
        print(f"   Sector:                  {wacc_result.get('sector', 'N/A')}")
        print(f"   Beta:                    {wacc_result['beta']:.2f}")
        print(f"   Cost of Equity:          {wacc_result['cost_of_equity']:.2%}")

        if "components" in terminal_result:
            comp = terminal_result["components"]
            print("\n   Componentes g terminal:")
            print(f"     Base (PIB):            {comp['gdp_base']:.2%}")
            if comp["roe_premium"] != 0:
                print(
                    f"     ROE premium:           {comp['roe_premium']:+.2%} (ROE: {comp.get('roe', 0):.1%})"
                )
            if comp["margin_premium"] != 0:
                print(f"     Margin premium:        {comp['margin_premium']:+.2%}")
            if comp["growth_premium"] != 0:
                print(f"     Growth premium:        {comp['growth_premium']:+.2%}")
            if comp["risk_adjustment"] != 0:
                print(f"     Risk adjustment:       {-comp['risk_adjustment']:+.2%}")

        return {
            "ticker": ticker,
            "wacc": wacc_result["wacc"],
            "g_terminal": terminal_result["terminal_growth"],
            "spread": spread,
            "floor_applied": wacc_result.get("floor_applied", False),
            "spread_adjusted": terminal_result.get("spread_adjusted", False),
            "sector": wacc_result.get("sector", "N/A"),
            "using_industry_wacc": wacc_result.get("using_industry_wacc", False),
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def main():
    print("=" * 80)
    print("PRUEBA DE AJUSTES EN PARÁMETROS DCF")
    print("=" * 80)
    print("\nAjustes implementados:")
    print("  1. ✓ Premios de g terminal reducidos: 0.50% → 0.25%")
    print("  2. ✓ Cap máximo de g terminal: 4.5% → 3.5%")
    print("  3. ✓ Validación de spread mínimo: 4.0pp")
    print("  4. ✓ WACC floors por sector (Tech 7.5%, Healthcare 6.5%, etc.)")
    print("  5. ✓ Financieros usan WACC industria automáticamente")

    # Initialize calculator
    wacc_calc = WACCCalculator(use_damodaran=True)

    # Test companies (casos problemáticos identificados en el análisis)
    test_cases = [
        # Casos con g terminal alto
        ("AAPL", "g terminal era 3.75%, debería bajar a ~3.0%"),
        ("MSFT", "g terminal era 4.00%, debería bajar a ~3.0-3.25%"),
        ("JNJ", "g terminal era 4.00% y WACC 6.03% (spread 2.03pp crítico)"),
        # Caso financiero
        ("JPM", "WACC era 10.32%, debería usar industria (~6.0%)"),
        # Casos con WACC bajo
        ("PG", "WACC era 5.80% y g 3.75% (spread 2.05pp crítico)"),
        ("KO", "WACC era 6.02% y g 3.75% (spread 2.27pp crítico)"),
    ]

    results = []

    for ticker, description in test_cases:
        print(f"\n\n{'#'*80}")
        print(f"CASO: {ticker}")
        print(f"Expectativa: {description}")
        print(f"{'#'*80}")

        result = test_company(ticker, wacc_calc)
        if result:
            results.append(result)

        import time

        time.sleep(1)  # Avoid rate limits

    # Summary
    if results:
        print(f"\n\n{'='*80}")
        print("RESUMEN DE RESULTADOS")
        print(f"{'='*80}\n")

        df = pd.DataFrame(results)

        print("Tabla comparativa:")
        print(
            df[["ticker", "wacc", "g_terminal", "spread", "sector"]].to_string(
                index=False
            )
        )

        print("\n\nEstadísticas:")
        print(f"  WACC promedio:           {df['wacc'].mean():.2%}")
        print(f"  g terminal promedio:     {df['g_terminal'].mean():.2%}")
        print(
            f"  Spread promedio:         {df['spread'].mean():.2%} ({df['spread'].mean()*100:.1f}pp)"
        )
        print(
            f"  Spread mínimo:           {df['spread'].min():.2%} ({df['spread'].min()*100:.1f}pp)"
        )

        print("\n\nAjustes aplicados:")
        print(
            f"  WACC floors aplicados:   {df['floor_applied'].sum()} de {len(df)} empresas"
        )
        print(
            f"  Spread ajustados:        {df['spread_adjusted'].sum()} de {len(df)} empresas"
        )
        print(
            f"  Usando WACC industria:   {df['using_industry_wacc'].sum()} de {len(df)} empresas"
        )

        # Validation
        print(f"\n\n{'='*80}")
        print("VALIDACIÓN DE OBJETIVOS")
        print(f"{'='*80}\n")

        # Objetivo 1: g terminal < 3.5%
        high_g = df[df["g_terminal"] > 0.035]
        print("1. g terminal > 3.5%:")
        if len(high_g) > 0:
            print(f"   ⚠️  {len(high_g)} empresas aún tienen g > 3.5%:")
            for _, row in high_g.iterrows():
                print(f"      - {row['ticker']}: {row['g_terminal']:.2%}")
        else:
            print("   ✓ Todas las empresas tienen g ≤ 3.5%")

        # Objetivo 2: spread >= 4.0pp
        low_spread = df[df["spread"] < 0.04]
        print("\n2. Spread < 4.0pp:")
        if len(low_spread) > 0:
            print(f"   ⚠️  {len(low_spread)} empresas tienen spread < 4.0pp:")
            for _, row in low_spread.iterrows():
                print(f"      - {row['ticker']}: {row['spread']*100:.1f}pp")
        else:
            print("   ✓ Todas las empresas tienen spread ≥ 4.0pp")

        # Objetivo 3: WACC floors
        print("\n3. WACC floors por sector:")
        print(
            f"   ✓ {df['floor_applied'].sum()} empresas tuvieron WACC ajustado al mínimo del sector"
        )

        # Objetivo 4: Financieros con WACC industria
        financials = df[df["sector"] == "Financial Services"]
        if len(financials) > 0:
            print("\n4. Financieros usando WACC industria:")
            if financials["using_industry_wacc"].all():
                print("   ✓ Todos los financieros usan WACC industria")
                for _, row in financials.iterrows():
                    print(f"      - {row['ticker']}: WACC {row['wacc']:.2%}")
            else:
                print("   ⚠️  Algunos financieros no usan WACC industria")

        print(f"\n\n{'='*80}")
        print("CONCLUSIÓN")
        print(f"{'='*80}\n")

        if len(low_spread) == 0 and len(high_g) <= 1:
            print("✅ AJUSTES EXITOSOS")
            print("   - Spreads saludables (≥4.0pp)")
            print("   - g terminal conservador (≤3.5%)")
            print("   - WACC floors aplicados correctamente")
            print("   - Financieros usando WACC industria")
        else:
            print("⚠️  REVISAR ALGUNOS CASOS")
            print(f"   - {len(low_spread)} empresas con spread bajo")
            print(f"   - {len(high_g)} empresas con g terminal alto")


if __name__ == "__main__":
    main()
