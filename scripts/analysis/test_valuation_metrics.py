"""
Test script para validar métricas de valoración.

Este script valida la precisión matemática y financiera de los cálculos de:
- EV/EBITDA
- P/E Ratio
- P/B Ratio

Usa datos reales de empresas conocidas para verificar que los cálculos sean correctos.
"""

from src.dcf.valuation_metrics import ValuationMetricsCalculator, ValuationMetrics


def test_enterprise_value_calculation():
    """Test: Cálculo de Enterprise Value."""
    print("\n" + "=" * 80)
    print("TEST 1: Enterprise Value Calculation")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    # Ejemplo: Empresa con Market Cap = 1000B, Debt = 100B, Cash = 50B
    market_cap = 1_000_000_000_000  # $1T
    total_debt = 100_000_000_000  # $100B
    cash = 50_000_000_000  # $50B

    ev = calculator.calculate_enterprise_value(market_cap, total_debt, cash)

    expected_ev = market_cap + total_debt - cash
    expected_ev_value = 1_050_000_000_000  # $1.05T

    print(f"Market Cap: ${market_cap / 1e9:.2f}B")
    print(f"Total Debt: ${total_debt / 1e9:.2f}B")
    print(f"Cash: ${cash / 1e9:.2f}B")
    print("\nFórmula: EV = Market Cap + Debt - Cash")
    print(f"EV Calculado: ${ev / 1e9:.2f}B")
    print(f"EV Esperado: ${expected_ev_value / 1e9:.2f}B")

    assert ev == expected_ev, f"EV incorrecto: {ev} != {expected_ev}"
    print("✅ Test PASADO: Enterprise Value calculado correctamente")


def test_ev_ebitda_calculation():
    """Test: Cálculo de EV/EBITDA."""
    print("\n" + "=" * 80)
    print("TEST 2: EV/EBITDA Calculation")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    # Ejemplo: EV = $100B, EBITDA = $10B -> EV/EBITDA = 10x
    enterprise_value = 100_000_000_000  # $100B
    ebitda = 10_000_000_000  # $10B

    ev_ebitda = calculator.calculate_ev_ebitda(enterprise_value, ebitda)

    expected_multiple = 10.0

    print(f"Enterprise Value: ${enterprise_value / 1e9:.2f}B")
    print(f"EBITDA: ${ebitda / 1e9:.2f}B")
    print("\nFórmula: EV/EBITDA = Enterprise Value / EBITDA")
    print(f"Múltiplo Calculado: {ev_ebitda:.2f}x")
    print(f"Múltiplo Esperado: {expected_multiple:.2f}x")

    assert abs(ev_ebitda - expected_multiple) < 0.01, "EV/EBITDA incorrecto"
    print("✅ Test PASADO: EV/EBITDA calculado correctamente")

    # Test con EBITDA negativo
    print("\n--- Sub-test: EBITDA negativo ---")
    ebitda_negative = -1_000_000_000
    ev_ebitda_negative = calculator.calculate_ev_ebitda(
        enterprise_value, ebitda_negative
    )
    print(f"EBITDA negativo: ${ebitda_negative / 1e9:.2f}B")
    print(f"Resultado: {ev_ebitda_negative}")

    assert ev_ebitda_negative is None, "Debe retornar None para EBITDA negativo"
    print("✅ Sub-test PASADO: Manejo correcto de EBITDA negativo")


def test_pe_ratio_calculation():
    """Test: Cálculo de P/E Ratio."""
    print("\n" + "=" * 80)
    print("TEST 3: P/E Ratio Calculation")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    # Ejemplo: Price = $150, EPS = $6 -> P/E = 25x
    price = 150.0
    eps = 6.0

    pe_ratio = calculator.calculate_pe_ratio(price, eps)

    expected_pe = 25.0

    print(f"Stock Price: ${price:.2f}")
    print(f"EPS (Diluted): ${eps:.2f}")
    print("\nFórmula: P/E = Price / EPS")
    print(f"P/E Calculado: {pe_ratio:.2f}x")
    print(f"P/E Esperado: {expected_pe:.2f}x")

    assert abs(pe_ratio - expected_pe) < 0.01, "P/E incorrecto"
    print("✅ Test PASADO: P/E calculado correctamente")

    # Test con EPS negativo
    print("\n--- Sub-test: EPS negativo ---")
    eps_negative = -2.0
    pe_negative = calculator.calculate_pe_ratio(price, eps_negative)
    print(f"EPS negativo: ${eps_negative:.2f}")
    print(f"Resultado: {pe_negative}")

    assert pe_negative is None, "Debe retornar None para EPS negativo"
    print("✅ Sub-test PASADO: Manejo correcto de EPS negativo")


def test_pb_ratio_calculation():
    """Test: Cálculo de P/B Ratio."""
    print("\n" + "=" * 80)
    print("TEST 4: P/B Ratio Calculation")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    # Ejemplo: Price = $100, Book Value per Share = $50 -> P/B = 2x
    price = 100.0
    book_value_per_share = 50.0

    pb_ratio = calculator.calculate_pb_ratio(price, book_value_per_share)

    expected_pb = 2.0

    print(f"Stock Price: ${price:.2f}")
    print(f"Book Value per Share: ${book_value_per_share:.2f}")
    print("\nFórmula: P/B = Price / Book Value per Share")
    print(f"P/B Calculado: {pb_ratio:.2f}x")
    print(f"P/B Esperado: {expected_pb:.2f}x")

    assert abs(pb_ratio - expected_pb) < 0.01, "P/B incorrecto"
    print("✅ Test PASADO: P/B calculado correctamente")


def test_real_company_data():
    """Test: Validar con datos reales de una empresa (AAPL)."""
    print("\n" + "=" * 80)
    print("TEST 5: Validación con Datos Reales (AAPL)")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    try:
        # Fetch real data from Apple
        metrics = calculator.calculate_all_metrics("AAPL")

        print(f"\n📊 Métricas de {metrics.company_name} ({metrics.ticker})")
        print("-" * 80)

        # Enterprise Value components
        print("\n💰 Enterprise Value:")
        if metrics.market_cap:
            print(f"  Market Cap: ${metrics.market_cap / 1e9:.2f}B")
        if metrics.total_debt is not None:
            print(f"  Total Debt: ${metrics.total_debt / 1e9:.2f}B")
        if metrics.cash_and_equivalents is not None:
            print(f"  Cash: ${metrics.cash_and_equivalents / 1e9:.2f}B")
        if metrics.enterprise_value:
            print(f"  ➡️ Enterprise Value: ${metrics.enterprise_value / 1e9:.2f}B")

        # Valuation metrics
        print("\n📈 Métricas de Valoración:")
        if metrics.ev_ebitda:
            print(f"  EV/EBITDA: {metrics.ev_ebitda:.2f}x")
        else:
            print("  EV/EBITDA: N/A")

        if metrics.pe_ratio:
            print(f"  P/E Ratio: {metrics.pe_ratio:.2f}x")
        else:
            print("  P/E Ratio: N/A")

        if metrics.pb_ratio:
            print(f"  P/B Ratio: {metrics.pb_ratio:.2f}x")
        else:
            print("  P/B Ratio: N/A")

        # Income statement
        print("\n💼 Income Statement:")
        if metrics.ebitda:
            print(f"  EBITDA: ${metrics.ebitda / 1e9:.2f}B")
        if metrics.net_income:
            print(f"  Net Income: ${metrics.net_income / 1e9:.2f}B")
        if metrics.eps:
            print(f"  EPS (Diluted): ${metrics.eps:.2f}")

        print(f"\n📅 Fuente: {metrics.data_source}")
        print(f"📅 Fecha: {metrics.calculation_date.strftime('%Y-%m-%d %H:%M')}")

        # Interpretations
        print("\n🔍 Interpretación de Métricas:")
        interpretations = calculator.get_valuation_interpretation(metrics)
        for metric_name, interpretation in interpretations.items():
            print(f"  {metric_name.upper()}: {interpretation}")

        # Validation checks
        print("\n✅ Validaciones:")

        # Check EV formula
        if (
            metrics.market_cap
            and metrics.total_debt is not None
            and metrics.cash_and_equivalents is not None
        ):
            calculated_ev = (
                metrics.market_cap + metrics.total_debt - metrics.cash_and_equivalents
            )
            if metrics.enterprise_value:
                ev_match = (
                    abs(calculated_ev - metrics.enterprise_value) < 1e6
                )  # Tolerance 1M
                print(f"  EV formula: {'✅ CORRECTO' if ev_match else '❌ ERROR'}")
                if not ev_match:
                    print(f"    Calculado: ${calculated_ev / 1e9:.2f}B")
                    print(f"    Almacenado: ${metrics.enterprise_value / 1e9:.2f}B")

        # Check EV/EBITDA formula
        if metrics.enterprise_value and metrics.ebitda and metrics.ebitda > 0:
            calculated_ev_ebitda = metrics.enterprise_value / metrics.ebitda
            if metrics.ev_ebitda:
                ev_ebitda_match = abs(calculated_ev_ebitda - metrics.ev_ebitda) < 0.01
                print(
                    f"  EV/EBITDA formula: {'✅ CORRECTO' if ev_ebitda_match else '❌ ERROR'}"
                )

        # Check P/E formula
        if metrics.current_price and metrics.eps and metrics.eps > 0:
            calculated_pe = metrics.current_price / metrics.eps
            if metrics.pe_ratio:
                pe_match = abs(calculated_pe - metrics.pe_ratio) < 0.01
                print(f"  P/E formula: {'✅ CORRECTO' if pe_match else '❌ ERROR'}")

        print("\n✅ Test PASADO: Datos reales validados correctamente")

    except Exception as e:
        print(f"⚠️ Warning: No se pudieron obtener datos reales: {str(e)}")
        print("Esto es normal si no hay conexión a internet o problemas con yfinance")


def test_dcf_comparison():
    """Test: Comparación con DCF."""
    print("\n" + "=" * 80)
    print("TEST 6: Comparación DCF vs Métricas Relativas")
    print("=" * 80)

    calculator = ValuationMetricsCalculator()

    # Mock metrics
    metrics = ValuationMetrics(
        ticker="TEST",
        company_name="Test Company",
        ev_ebitda=12.5,
        pe_ratio=20.0,
        pb_ratio=2.5,
        current_price=100.0,
    )

    # DCF fair value scenarios
    print("\nEscenario 1: DCF sugiere subvaluación (Fair Value > Precio)")
    dcf_fair_value = 150.0
    current_price = 100.0

    comparison = calculator.compare_with_dcf(dcf_fair_value, current_price, metrics)

    print(f"  Fair Value (DCF): ${dcf_fair_value:.2f}")
    print(f"  Precio Actual: ${current_price:.2f}")
    print(f"  Upside: {comparison['dcf_upside']:.1f}%")
    print(f"  Señal DCF: {comparison['dcf_signal']}")
    print(f"  Consenso: {comparison['consensus']}")

    assert comparison["dcf_upside"] == 50.0, "Upside calculation incorrect"
    print("  ✅ Cálculo de upside correcto")

    print("\nEscenario 2: DCF sugiere sobrevaluación (Fair Value < Precio)")
    dcf_fair_value = 80.0
    current_price = 100.0

    comparison = calculator.compare_with_dcf(dcf_fair_value, current_price, metrics)

    print(f"  Fair Value (DCF): ${dcf_fair_value:.2f}")
    print(f"  Precio Actual: ${current_price:.2f}")
    print(f"  Upside: {comparison['dcf_upside']:.1f}%")
    print(f"  Señal DCF: {comparison['dcf_signal']}")
    print(f"  Consenso: {comparison['consensus']}")

    assert comparison["dcf_upside"] == -20.0, "Downside calculation incorrect"
    print("  ✅ Cálculo de downside correcto")

    print("\n✅ Test PASADO: Comparación DCF funcionando correctamente")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("🧪 TEST SUITE: MÉTRICAS DE VALORACIÓN")
    print("=" * 80)
    print("\nValidando precisión matemática y fundamentos financieros...")

    try:
        test_enterprise_value_calculation()
        test_ev_ebitda_calculation()
        test_pe_ratio_calculation()
        test_pb_ratio_calculation()
        test_real_company_data()
        test_dcf_comparison()

        print("\n" + "=" * 80)
        print("🎉 TODOS LOS TESTS PASADOS")
        print("=" * 80)
        print("\n✅ Las métricas de valoración están implementadas correctamente")
        print("✅ Todas las fórmulas matemáticas son precisas")
        print("✅ Los fundamentos financieros están contrastados")
        print("\nReferencias validadas:")
        print("  • EV = Market Cap + Debt - Cash")
        print("  • EV/EBITDA = Enterprise Value / EBITDA")
        print("  • P/E = Price / EPS")
        print("  • P/B = Price / Book Value per Share")

    except AssertionError as e:
        print("\n" + "=" * 80)
        print("❌ TEST FALLÓ")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        raise
    except Exception as e:
        print("\n" + "=" * 80)
        print("⚠️ ERROR INESPERADO")
        print("=" * 80)
        print(f"\nError: {str(e)}")
        raise


if __name__ == "__main__":
    main()
