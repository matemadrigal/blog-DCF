"""
Valoración DCF de Cellnex (CLNX.MC) - Versión Standalone

Tasas de crecimiento personalizadas:
- Año 1: 8%
- Año 2: 10%
- Año 3: 12%
- Año 4: 15%
- Año 5: 18%

Metodología forward-looking para empresas de infraestructura en expansión.
No requiere dependencias externas (solo Python stdlib).
"""


class CellnexDCFModel:
    """Modelo DCF simplificado para Cellnex."""

    def __init__(self, wacc, terminal_growth):
        """
        Inicializar modelo DCF.

        Args:
            wacc: Weighted Average Cost of Capital
            terminal_growth: Tasa de crecimiento perpetuo
        """
        self.wacc = wacc
        self.terminal_growth = terminal_growth

    def project_fcf(self, base_fcf, growth_rates):
        """
        Proyectar FCF futuros con tasas de crecimiento.

        Args:
            base_fcf: FCF base
            growth_rates: Lista de tasas de crecimiento

        Returns:
            Lista de FCF proyectados
        """
        projections = []
        current_fcf = base_fcf

        for rate in growth_rates:
            current_fcf = current_fcf * (1 + rate)
            projections.append(current_fcf)

        return projections

    def calculate_present_values(self, projected_fcf):
        """
        Calcular valor presente de FCF proyectados.

        Args:
            projected_fcf: Lista de FCF proyectados

        Returns:
            Lista de valores presentes
        """
        pv_fcf = []
        for i, fcf in enumerate(projected_fcf, start=1):
            pv = fcf / ((1 + self.wacc) ** i)
            pv_fcf.append(pv)

        return pv_fcf

    def calculate_terminal_value(self, final_fcf):
        """
        Calcular Terminal Value usando Gordon Growth Model.

        Args:
            final_fcf: FCF del año final

        Returns:
            Terminal Value
        """
        if self.wacc <= self.terminal_growth:
            raise ValueError(f"WACC ({self.wacc:.2%}) must be > terminal growth ({self.terminal_growth:.2%})")

        tv = (final_fcf * (1 + self.terminal_growth)) / (self.wacc - self.terminal_growth)
        return tv

    def run_valuation(self, base_fcf, growth_rates, cash, debt, shares):
        """
        Ejecutar valoración DCF completa.

        Args:
            base_fcf: FCF base normalizado
            growth_rates: Tasas de crecimiento
            cash: Efectivo
            debt: Deuda total
            shares: Acciones en circulación

        Returns:
            Diccionario con resultados
        """
        # Proyectar FCF
        projected_fcf = self.project_fcf(base_fcf, growth_rates)

        # Calcular PV
        pv_fcf = self.calculate_present_values(projected_fcf)

        # Terminal Value
        terminal_value = self.calculate_terminal_value(projected_fcf[-1])

        # PV Terminal Value
        pv_terminal = terminal_value / ((1 + self.wacc) ** len(projected_fcf))

        # Enterprise Value
        enterprise_value = sum(pv_fcf) + pv_terminal

        # Equity Value
        equity_value = enterprise_value + cash - debt

        # Fair Value per Share
        fair_value_per_share = equity_value / shares

        return {
            'base_fcf': base_fcf,
            'projected_fcf': projected_fcf,
            'pv_fcf': pv_fcf,
            'terminal_value': terminal_value,
            'pv_terminal_value': pv_terminal,
            'enterprise_value': enterprise_value,
            'equity_value': equity_value,
            'fair_value_per_share': fair_value_per_share,
            'wacc': self.wacc,
            'terminal_growth': self.terminal_growth,
        }


def calculate_normalized_fcf(ebitda, maintenance_capex_rate=0.10, tax_rate=0.25):
    """
    Calcular FCF normalizado desde EBITDA (método forward-looking).

    FCF = EBITDA × (1 - Tax) - Maintenance CapEx

    Args:
        ebitda: EBITDA
        maintenance_capex_rate: Capex mantenimiento como % de EBITDA
        tax_rate: Tasa impositiva

    Returns:
        FCF normalizado
    """
    maintenance_capex = ebitda * maintenance_capex_rate
    ebitda_after_tax = ebitda * (1 - tax_rate)
    fcf_normalized = ebitda_after_tax - maintenance_capex

    return fcf_normalized


def calculate_wacc(beta, market_cap, total_debt, tax_rate=0.25):
    """
    Calcular WACC para empresa de infraestructura europea.

    Args:
        beta: Beta de mercado
        market_cap: Capitalización bursátil
        total_debt: Deuda total
        tax_rate: Tasa impositiva

    Returns:
        (wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt)
    """
    # Risk-free rate (bonos alemanes 10Y)
    rf = 0.025  # 2.5%

    # Market risk premium Europa
    mrp = 0.06  # 6%

    # Cost of equity (CAPM)
    cost_of_equity = rf + beta * mrp

    # Cost of debt (Cellnex BBB rating)
    cost_of_debt = 0.035  # 3.5%

    # Weights
    equity_value = market_cap
    debt_value = total_debt
    total_value = equity_value + debt_value

    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    # WACC
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

    return wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt


def main():
    """Función principal."""

    print("\n" + "="*80)
    print("VALORACIÓN DCF - CELLNEX TELECOM (CLNX.MC)")
    print("Infraestructura de Torres de Telecomunicaciones")
    print("="*80)

    # =========================================================================
    # DATOS FUNDAMENTALES DE CELLNEX
    # =========================================================================

    print("\n📊 DATOS FUNDAMENTALES (Q3 2024):")
    print("─" * 80)

    # Datos de mercado
    ticker = "CLNX.MC"
    company_name = "Cellnex Telecom S.A."
    current_price = 35.50  # EUR
    shares_outstanding = 596_000_000  # 596M acciones

    # Balance
    cash = 1_500_000_000  # €1.5B
    total_debt = 18_000_000_000  # €18.0B
    net_debt = total_debt - cash

    # Operating
    ebitda = 3_100_000_000  # €3.1B EBITDA recurrente

    # Risk
    beta = 0.65  # Beta bajo (infraestructura regulada)

    # Cálculos derivados
    market_cap = current_price * shares_outstanding
    ev = market_cap + net_debt

    print(f"   Ticker: {ticker}")
    print(f"   Nombre: {company_name}")
    print(f"   Precio actual: €{current_price:.2f}")
    print(f"   Shares outstanding: {shares_outstanding/1e6:.1f}M")
    print(f"   Market Cap: €{market_cap/1e9:.2f}B")
    print(f"\n   Cash: €{cash/1e9:.2f}B")
    print(f"   Debt: €{total_debt/1e9:.2f}B")
    print(f"   Net Debt: €{net_debt/1e9:.2f}B")
    print(f"   Enterprise Value: €{ev/1e9:.2f}B")
    print(f"\n   EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   EV/EBITDA: {ev/ebitda:.2f}x")
    print(f"   Debt/EBITDA: {total_debt/ebitda:.2f}x")
    print(f"   Beta: {beta:.3f}")

    # =========================================================================
    # CÁLCULO DE FCF NORMALIZADO (FORWARD-LOOKING)
    # =========================================================================

    print("\n" + "="*80)
    print("NORMALIZACIÓN DE FCF (MÉTODO FORWARD-LOOKING)")
    print("="*80)

    print("\n⚠️  PROBLEMA CON FCF HISTÓRICO:")
    print("─" * 80)
    print("   FCF histórico negativo debido a:")
    print("   • Alta inversión en M&A (adquisiciones de torres)")
    print("   • Growth CapEx (construcción de nuevas torres)")
    print("   • Expansion activities (nuevos mercados)")
    print("\n   ❌ No se puede usar FCF histórico como base para proyecciones")

    print("\n✅ SOLUCIÓN: MÉTODO FORWARD-LOOKING (EBITDA-BASED)")
    print("─" * 80)

    maintenance_capex_rate = 0.10  # 10% de EBITDA
    tax_rate = 0.25  # 25% tasa efectiva

    base_fcf = calculate_normalized_fcf(
        ebitda=ebitda,
        maintenance_capex_rate=maintenance_capex_rate,
        tax_rate=tax_rate
    )

    print(f"   FCF Base = EBITDA × (1 - Tax) - Maintenance CapEx")
    print(f"\n   Cálculo detallado:")
    print(f"   ├─ EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   ├─ Tax rate: {tax_rate*100:.0f}%")
    print(f"   ├─ EBITDA after tax: €{ebitda * (1-tax_rate)/1e9:.2f}B")
    print(f"   ├─ Maintenance CapEx ({maintenance_capex_rate*100:.0f}%): €{ebitda * maintenance_capex_rate/1e9:.2f}B")
    print(f"   └─ FCF Base: €{base_fcf/1e9:.3f}B")

    print(f"\n   ℹ️  Este método:")
    print(f"   • Usa EBITDA como proxy de generación operativa")
    print(f"   • Solo deduce capex de mantenimiento (no growth)")
    print(f"   • Asume tasa impositiva normalizada")
    print(f"   • Es apropiado para infraestructura en expansión")

    # =========================================================================
    # CÁLCULO DE WACC
    # =========================================================================

    print("\n" + "="*80)
    print("CÁLCULO DE WACC (WEIGHTED AVERAGE COST OF CAPITAL)")
    print("="*80)

    wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt = calculate_wacc(
        beta=beta,
        market_cap=market_cap,
        total_debt=total_debt,
        tax_rate=tax_rate
    )

    print("\n📊 COST OF EQUITY (CAPM):")
    print("─" * 80)
    rf = 0.025
    mrp = 0.06
    print(f"   Re = Rf + β × MRP")
    print(f"   Re = {rf*100:.1f}% + {beta:.3f} × {mrp*100:.1f}%")
    print(f"   Re = {cost_of_equity*100:.2f}%")

    print("\n📊 COST OF DEBT:")
    print("─" * 80)
    print(f"   Rd (pre-tax): {cost_of_debt*100:.2f}%")
    print(f"   Rd (after-tax): {cost_of_debt*(1-tax_rate)*100:.2f}%")
    print(f"   Rating: BBB (investment grade)")

    print("\n📊 CAPITAL STRUCTURE:")
    print("─" * 80)
    print(f"   Equity: €{market_cap/1e9:.2f}B ({weight_equity*100:.1f}%)")
    print(f"   Debt: €{total_debt/1e9:.2f}B ({weight_debt*100:.1f}%)")

    print("\n📊 WACC FINAL:")
    print("─" * 80)
    print(f"   WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)")
    print(f"   WACC = {weight_equity:.3f} × {cost_of_equity:.4f} + {weight_debt:.3f} × {cost_of_debt:.4f} × {1-tax_rate:.2f}")
    print(f"   WACC = {wacc*100:.2f}%")

    # =========================================================================
    # TASAS DE CRECIMIENTO PERSONALIZADAS
    # =========================================================================

    print("\n" + "="*80)
    print("TASAS DE CRECIMIENTO PERSONALIZADAS")
    print("="*80)

    custom_growth_rates = [0.08, 0.10, 0.12, 0.15, 0.18]
    terminal_growth = 0.025  # 2.5%

    print("\n📈 PROYECCIÓN 5 AÑOS:")
    print("─" * 80)
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"   Año {i}: {rate*100:.1f}%")

    print(f"\n   Terminal Growth (perpetuidad): {terminal_growth*100:.1f}%")

    print("\n💡 RAZONAMIENTO:")
    print("─" * 80)
    print("   Años 1-2 (8-10%): Expansión moderada")
    print("      • Estabilización post-adquisiciones")
    print("      • Mejora gradual en conversión EBITDA → FCF")
    print("   Años 3-4 (12-15%): Aceleración")
    print("      • Sinergias operativas materializadas")
    print("      • Reducción de growth capex")
    print("   Año 5 (18%): Peak conversion")
    print("      • Máxima eficiencia operativa")
    print("      • Portfolio optimizado")
    print("   Perpetuidad (2.5%): Crecimiento maduro")
    print("      • Inflación + crecimiento PIB Europa")

    # =========================================================================
    # EJECUCIÓN DE VALORACIÓN DCF
    # =========================================================================

    print("\n" + "="*80)
    print("VALORACIÓN DCF")
    print("="*80)

    model = CellnexDCFModel(wacc=wacc, terminal_growth=terminal_growth)

    result = model.run_valuation(
        base_fcf=base_fcf,
        growth_rates=custom_growth_rates,
        cash=cash,
        debt=total_debt,
        shares=shares_outstanding
    )

    # =========================================================================
    # PROYECCIONES FCF
    # =========================================================================

    print("\n📊 PROYECCIONES FCF (5 años):")
    print("─" * 80)
    print(f"   {'Año':<8} {'FCF (€B)':<12} {'Growth':<10} {'Disc. Factor':<14} {'PV (€B)'}")
    print("─" * 80)

    for i, (fcf, rate, pv) in enumerate(zip(result['projected_fcf'], custom_growth_rates, result['pv_fcf']), 1):
        discount_factor = 1 / ((1 + wacc) ** i)
        print(f"   {i:<8} €{fcf/1e9:>10.3f} {rate*100:>8.1f}% {discount_factor:>12.4f} €{pv/1e9:>10.3f}")

    # =========================================================================
    # ENTERPRISE VALUE
    # =========================================================================

    print("\n🎯 VALORACIÓN - ENTERPRISE VALUE:")
    print("─" * 80)

    pv_fcf_total = sum(result['pv_fcf'])
    pv_fcf_pct = (pv_fcf_total / result['enterprise_value']) * 100
    tv_pv_pct = (result['pv_terminal_value'] / result['enterprise_value']) * 100

    print(f"   PV de FCF (años 1-5): €{pv_fcf_total/1e9:>10.2f}B ({pv_fcf_pct:>5.1f}%)")
    print(f"   PV Terminal Value: €{result['pv_terminal_value']/1e9:>10.2f}B ({tv_pv_pct:>5.1f}%)")
    print(f"   {'─'*76}")
    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:>10.2f}B")

    # =========================================================================
    # EQUITY VALUE
    # =========================================================================

    print("\n🎯 VALORACIÓN - EQUITY VALUE:")
    print("─" * 80)

    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:>10.2f}B")
    print(f"   + Cash: €{cash/1e9:>10.2f}B")
    print(f"   - Debt: €{total_debt/1e9:>10.2f}B")
    print(f"   {'─'*76}")
    print(f"   Equity Value: €{result['equity_value']/1e9:>10.2f}B")
    print(f"   ÷ Shares: {shares_outstanding/1e6:>10.1f}M")
    print(f"   {'─'*76}")
    print(f"   💎 VALOR INTRÍNSECO: €{result['fair_value_per_share']:>10.2f}")

    # =========================================================================
    # COMPARACIÓN CON PRECIO DE MERCADO
    # =========================================================================

    print("\n📈 COMPARACIÓN CON MERCADO:")
    print("─" * 80)

    upside = ((result['fair_value_per_share'] - current_price) / current_price) * 100

    print(f"   Valor intrínseco: €{result['fair_value_per_share']:.2f}")
    print(f"   Precio actual: €{current_price:.2f}")
    print(f"   {'─'*76}")

    if upside > 0:
        print(f"   ✅ UPSIDE: +{upside:.1f}%")
        if upside > 50:
            recommendation = "🚀 STRONG BUY"
            confidence = "Alta"
        elif upside > 25:
            recommendation = "📈 BUY"
            confidence = "Alta"
        elif upside > 15:
            recommendation = "👍 BUY"
            confidence = "Media"
        else:
            recommendation = "⚖️  HOLD (sesgo alcista)"
            confidence = "Media"
    else:
        print(f"   ⚠️  DOWNSIDE: {upside:.1f}%")
        if upside < -25:
            recommendation = "🔻 STRONG SELL"
            confidence = "Alta"
        elif upside < -15:
            recommendation = "📉 SELL"
            confidence = "Media"
        else:
            recommendation = "⚖️  HOLD (sesgo bajista)"
            confidence = "Baja"

    print(f"\n   Recomendación: {recommendation}")
    print(f"   Confianza: {confidence}")

    # =========================================================================
    # MÉTRICAS DE VALORACIÓN
    # =========================================================================

    print("\n📊 MÉTRICAS DE VALORACIÓN:")
    print("─" * 80)

    ev_ebitda_dcf = result['enterprise_value'] / ebitda
    ev_ebitda_market = ev / ebitda
    pe_implied = (result['equity_value'] / shares_outstanding) / current_price

    print(f"   EV/EBITDA (DCF): {ev_ebitda_dcf:.2f}x")
    print(f"   EV/EBITDA (mercado): {ev_ebitda_market:.2f}x")
    print(f"   P/E implícito: {pe_implied:.2f}x")

    # =========================================================================
    # VERIFICACIÓN DE RIGOR FINANCIERO
    # =========================================================================

    print("\n" + "="*80)
    print("VERIFICACIÓN DE RIGOR FINANCIERO")
    print("="*80)

    checks_passed = 0
    checks_total = 0

    print("\n🔍 CHECKS:")
    print("─" * 80)

    # Check 1: WACC > Terminal Growth
    checks_total += 1
    if result['wacc'] > result['terminal_growth']:
        print(f"   ✅ WACC ({result['wacc']:.2%}) > Terminal Growth ({result['terminal_growth']:.2%})")
        checks_passed += 1
    else:
        print(f"   ❌ WACC debe ser > Terminal Growth")

    # Check 2: Enterprise Value > 0
    checks_total += 1
    if result['enterprise_value'] > 0:
        print(f"   ✅ Enterprise Value positivo: €{result['enterprise_value']/1e9:.2f}B")
        checks_passed += 1
    else:
        print(f"   ❌ Enterprise Value debe ser positivo")

    # Check 3: Equity Value > 0
    checks_total += 1
    if result['equity_value'] > 0:
        print(f"   ✅ Equity Value positivo: €{result['equity_value']/1e9:.2f}B")
        checks_passed += 1
    else:
        print(f"   ❌ Equity Value negativo (exceso de deuda)")

    # Check 4: Fair Value > 0
    checks_total += 1
    if result['fair_value_per_share'] > 0:
        print(f"   ✅ Fair Value positivo: €{result['fair_value_per_share']:.2f}")
        checks_passed += 1
    else:
        print(f"   ❌ Fair Value debe ser positivo")

    # Check 5: FCF creciente
    checks_total += 1
    fcf_growing = all(result['projected_fcf'][i] > result['projected_fcf'][i-1]
                      for i in range(1, len(result['projected_fcf'])))
    if fcf_growing:
        print(f"   ✅ FCF proyectado es estrictamente creciente")
        checks_passed += 1
    else:
        print(f"   ⚠️  FCF proyectado no es creciente")

    # Check 6: TV razonable (60-85% de EV)
    checks_total += 1
    tv_ratio = result['pv_terminal_value'] / result['enterprise_value']
    if 0.60 < tv_ratio < 0.85:
        print(f"   ✅ PV Terminal Value es {tv_ratio*100:.1f}% de EV (rango: 60-85%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  PV Terminal Value es {tv_ratio*100:.1f}% de EV")

    # Check 7: EV/EBITDA razonable (12-18x para torres)
    checks_total += 1
    if 10 < ev_ebitda_dcf < 20:
        print(f"   ✅ EV/EBITDA = {ev_ebitda_dcf:.2f}x (rango torres: 10-20x)")
        checks_passed += 1
    else:
        print(f"   ⚠️  EV/EBITDA = {ev_ebitda_dcf:.2f}x (fuera de rango)")

    # Check 8: Debt/EBITDA sostenible (< 8x)
    checks_total += 1
    debt_ebitda = total_debt / ebitda
    if debt_ebitda < 8:
        print(f"   ✅ Debt/EBITDA = {debt_ebitda:.2f}x (sostenible < 8x)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Debt/EBITDA = {debt_ebitda:.2f}x (alto)")

    print(f"\n   {'─'*76}")
    print(f"   📊 Resultado: {checks_passed}/{checks_total} checks pasados ({checks_passed/checks_total*100:.0f}%)")

    if checks_passed == checks_total:
        print(f"   ✅ TODOS LOS CHECKS PASADOS - Valoración rigurosa")
    elif checks_passed >= checks_total * 0.8:
        print(f"   ⚠️  Mayoría de checks pasados - Revisar advertencias")
    else:
        print(f"   ❌ Múltiples checks fallidos - Revisar inputs")

    # =========================================================================
    # RESUMEN FINAL DE INPUTS
    # =========================================================================

    print("\n" + "="*80)
    print("RESUMEN DE INPUTS UTILIZADOS")
    print("="*80)

    print("\n📋 DATOS FUNDAMENTALES:")
    print("─" * 80)
    print(f"   Ticker: {ticker}")
    print(f"   Precio actual: €{current_price:.2f}")
    print(f"   Shares: {shares_outstanding/1e6:.1f}M")
    print(f"   Market Cap: €{market_cap/1e9:.2f}B")
    print(f"   Cash: €{cash/1e9:.2f}B")
    print(f"   Debt: €{total_debt/1e9:.2f}B")
    print(f"   EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   Beta: {beta:.3f}")

    print("\n📋 NORMALIZACIÓN FCF:")
    print("─" * 80)
    print(f"   Método: Forward-looking (EBITDA-based)")
    print(f"   EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   Tax rate: {tax_rate*100:.0f}%")
    print(f"   Maintenance CapEx: {maintenance_capex_rate*100:.0f}% EBITDA")
    print(f"   FCF Base: €{base_fcf/1e9:.3f}B")

    print("\n📋 PARÁMETROS DCF:")
    print("─" * 80)
    print(f"   WACC: {wacc*100:.2f}%")
    print(f"      ├─ Cost of Equity: {cost_of_equity*100:.2f}%")
    print(f"      ├─ Cost of Debt (after-tax): {cost_of_debt*(1-tax_rate)*100:.2f}%")
    print(f"      ├─ Weight Equity: {weight_equity*100:.1f}%")
    print(f"      └─ Weight Debt: {weight_debt*100:.1f}%")
    print(f"   Terminal Growth: {terminal_growth*100:.1f}%")

    print("\n📋 TASAS DE CRECIMIENTO:")
    print("─" * 80)
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"   Año {i}: {rate*100:.1f}%")
    print(f"   Perpetuidad: {terminal_growth*100:.1f}%")

    print("\n" + "="*80)
    print("FIN DEL ANÁLISIS")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
