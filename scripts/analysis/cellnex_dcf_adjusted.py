"""
Valoración DCF de Cellnex (CLNX.MC) - VERSIÓN AJUSTADA

Tasas de crecimiento personalizadas:
- Año 1: 8%
- Año 2: 10%
- Año 3: 12%
- Año 4: 15%
- Año 5: 18%

AJUSTES APLICADOS PARA REALISMO:
1. WACC ajustado al alza (beta más realista + risk premium infraestructura)
2. FCF base más conservador (mayor maintenance capex)
3. Terminal growth más conservador
"""


class CellnexDCFModel:
    """Modelo DCF simplificado para Cellnex."""

    def __init__(self, wacc, terminal_growth):
        self.wacc = wacc
        self.terminal_growth = terminal_growth

    def project_fcf(self, base_fcf, growth_rates):
        projections = []
        current_fcf = base_fcf
        for rate in growth_rates:
            current_fcf = current_fcf * (1 + rate)
            projections.append(current_fcf)
        return projections

    def calculate_present_values(self, projected_fcf):
        pv_fcf = []
        for i, fcf in enumerate(projected_fcf, start=1):
            pv = fcf / ((1 + self.wacc) ** i)
            pv_fcf.append(pv)
        return pv_fcf

    def calculate_terminal_value(self, final_fcf):
        if self.wacc <= self.terminal_growth:
            raise ValueError(f"WACC ({self.wacc:.2%}) must be > terminal growth ({self.terminal_growth:.2%})")
        tv = (final_fcf * (1 + self.terminal_growth)) / (self.wacc - self.terminal_growth)
        return tv

    def run_valuation(self, base_fcf, growth_rates, cash, debt, shares):
        projected_fcf = self.project_fcf(base_fcf, growth_rates)
        pv_fcf = self.calculate_present_values(projected_fcf)
        terminal_value = self.calculate_terminal_value(projected_fcf[-1])
        pv_terminal = terminal_value / ((1 + self.wacc) ** len(projected_fcf))
        enterprise_value = sum(pv_fcf) + pv_terminal
        equity_value = enterprise_value + cash - debt
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


def calculate_normalized_fcf(ebitda, maintenance_capex_rate=0.15, tax_rate=0.27, working_capital_adj=0.02):
    """
    Calcular FCF normalizado (versión AJUSTADA - más conservadora).

    AJUSTES:
    - Maintenance CapEx: 15% (vs 10% anterior) → Más realista para torres
    - Tax rate: 27% (vs 25%) → Tasa efectiva española más conservadora
    - Working capital: -2% EBITDA → Ajuste por crecimiento orgánico

    FCF = EBITDA × (1 - Tax) - Maintenance CapEx - ΔWC
    """
    maintenance_capex = ebitda * maintenance_capex_rate
    working_capital_investment = ebitda * working_capital_adj
    ebitda_after_tax = ebitda * (1 - tax_rate)
    fcf_normalized = ebitda_after_tax - maintenance_capex - working_capital_investment

    return fcf_normalized


def calculate_wacc_adjusted(beta_equity, market_cap, total_debt, tax_rate=0.27, country_risk_premium=0.01):
    """
    Calcular WACC AJUSTADO para Cellnex (versión más conservadora).

    AJUSTES:
    1. Beta unlevered → relevered con deuda real
    2. Country risk premium para España (+1%)
    3. Size premium para mid-cap (+0.5%)
    4. Illiquidity premium para infraestructura (+0.3%)
    5. Cost of debt ajustado al alza (refinancing risk)

    Beta unlevered (tower industry) = 0.58
    Beta levered = Beta_u × [1 + (1 - Tax) × (D/E)]
    """
    # Beta unlevered de la industria (American Tower, Crown Castle average)
    beta_unlevered = 0.58

    # Relever beta con estructura de capital de Cellnex
    debt_to_equity = total_debt / market_cap
    beta_levered = beta_unlevered * (1 + (1 - tax_rate) * debt_to_equity)

    # Risk-free rate (bonos alemanes 10Y)
    rf = 0.025  # 2.5%

    # Market risk premium Europa
    mrp = 0.065  # 6.5% (ligeramente más alto)

    # Cost of equity con ajustes
    cost_of_equity_base = rf + beta_levered * mrp
    size_premium = 0.005  # +0.5% (mid-cap)
    illiquidity_premium = 0.003  # +0.3% (infraestructura no líquida)
    cost_of_equity = cost_of_equity_base + country_risk_premium + size_premium + illiquidity_premium

    # Cost of debt AJUSTADO (considerando refinancing risk y alta deuda)
    # Cellnex BBB rating pero con alta deuda → spread más alto
    cost_of_debt = 0.045  # 4.5% (vs 3.5% anterior)

    # Weights
    equity_value = market_cap
    debt_value = total_debt
    total_value = equity_value + debt_value

    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    # WACC
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

    return wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt, beta_levered


def main():
    """Función principal con parámetros AJUSTADOS."""

    print("\n" + "="*80)
    print("VALORACIÓN DCF - CELLNEX TELECOM (VERSIÓN AJUSTADA)")
    print("Parámetros optimizados para rigor financiero")
    print("="*80)

    # =========================================================================
    # DATOS FUNDAMENTALES
    # =========================================================================

    ticker = "CLNX.MC"
    company_name = "Cellnex Telecom S.A."
    current_price = 35.50  # EUR
    shares_outstanding = 596_000_000  # 596M

    cash = 1_500_000_000  # €1.5B
    total_debt = 18_000_000_000  # €18.0B
    ebitda = 3_100_000_000  # €3.1B
    beta_equity = 0.65

    market_cap = current_price * shares_outstanding
    net_debt = total_debt - cash
    ev = market_cap + net_debt

    print(f"\n📊 DATOS FUNDAMENTALES:")
    print("─" * 80)
    print(f"   Precio actual: €{current_price:.2f}")
    print(f"   Market Cap: €{market_cap/1e9:.2f}B")
    print(f"   Debt: €{total_debt/1e9:.2f}B")
    print(f"   Cash: €{cash/1e9:.2f}B")
    print(f"   EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   EV/EBITDA (mercado): {ev/ebitda:.2f}x")

    # =========================================================================
    # NORMALIZACIÓN FCF (AJUSTADA)
    # =========================================================================

    print("\n" + "="*80)
    print("NORMALIZACIÓN FCF (AJUSTADA - MÁS CONSERVADORA)")
    print("="*80)

    maintenance_capex_rate = 0.15  # AJUSTADO: 15% (vs 10%)
    tax_rate = 0.27  # AJUSTADO: 27% (vs 25%)
    wc_adj = 0.02  # NUEVO: 2% para working capital

    base_fcf = calculate_normalized_fcf(
        ebitda=ebitda,
        maintenance_capex_rate=maintenance_capex_rate,
        tax_rate=tax_rate,
        working_capital_adj=wc_adj
    )

    print(f"\n   Cálculo AJUSTADO:")
    print(f"   ├─ EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   ├─ Tax rate: {tax_rate*100:.0f}% (↑ vs 25%)")
    print(f"   ├─ EBITDA after tax: €{ebitda * (1-tax_rate)/1e9:.2f}B")
    print(f"   ├─ Maintenance CapEx ({maintenance_capex_rate*100:.0f}%): €{ebitda * maintenance_capex_rate/1e9:.2f}B (↑ vs 10%)")
    print(f"   ├─ Working Capital: €{ebitda * wc_adj/1e9:.2f}B (NUEVO)")
    print(f"   └─ FCF Base: €{base_fcf/1e9:.3f}B")

    print(f"\n   ⚠️  AJUSTES APLICADOS:")
    print(f"   • Maintenance CapEx: 15% (más realista para torres)")
    print(f"   • Tax rate: 27% (tasa efectiva española)")
    print(f"   • Working capital: 2% (crecimiento orgánico requiere inversión)")

    # =========================================================================
    # WACC AJUSTADO
    # =========================================================================

    print("\n" + "="*80)
    print("WACC AJUSTADO (MÁS CONSERVADOR)")
    print("="*80)

    country_risk = 0.01  # +1% para España
    wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt, beta_levered = calculate_wacc_adjusted(
        beta_equity=beta_equity,
        market_cap=market_cap,
        total_debt=total_debt,
        tax_rate=tax_rate,
        country_risk_premium=country_risk
    )

    print(f"\n   📊 COST OF EQUITY (CAPM + Ajustes):")
    print(f"   ├─ Beta unlevered (industria): 0.58")
    print(f"   ├─ Debt/Equity: {total_debt/market_cap:.2f}x")
    print(f"   ├─ Beta levered: {beta_levered:.3f}")
    print(f"   ├─ Rf + β × MRP: {0.025 + beta_levered * 0.065:.2%}")
    print(f"   ├─ Country risk (España): +{country_risk:.1%}")
    print(f"   ├─ Size premium (mid-cap): +0.5%")
    print(f"   ├─ Illiquidity premium: +0.3%")
    print(f"   └─ Cost of Equity: {cost_of_equity*100:.2f}%")

    print(f"\n   📊 COST OF DEBT:")
    print(f"   ├─ Pre-tax: {cost_of_debt*100:.2f}% (↑ vs 3.5%)")
    print(f"   ├─ Razón: Alta deuda + refinancing risk")
    print(f"   └─ After-tax: {cost_of_debt*(1-tax_rate)*100:.2f}%")

    print(f"\n   📊 WACC FINAL:")
    print(f"   WACC = {wacc*100:.2f}% (↑ vs 4.66% anterior)")

    # =========================================================================
    # TASAS DE CRECIMIENTO
    # =========================================================================

    print("\n" + "="*80)
    print("TASAS DE CRECIMIENTO (PERSONALIZADAS)")
    print("="*80)

    custom_growth_rates = [0.08, 0.10, 0.12, 0.15, 0.18]
    terminal_growth = 0.020  # AJUSTADO: 2.0% (vs 2.5%)

    print(f"\n   Proyección 5 años:")
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"   Año {i}: {rate*100:.1f}%")
    print(f"   Terminal Growth: {terminal_growth*100:.1f}% (↓ vs 2.5%)")

    # =========================================================================
    # VALORACIÓN DCF
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
    # PROYECCIONES
    # =========================================================================

    print(f"\n   📊 PROYECCIONES FCF:")
    print("   ─" * 76)
    print(f"   {'Año':<8} {'FCF (€B)':<12} {'Growth':<10} {'PV (€B)'}")
    print("   ─" * 76)

    for i, (fcf, rate, pv) in enumerate(zip(result['projected_fcf'], custom_growth_rates, result['pv_fcf']), 1):
        print(f"   {i:<8} €{fcf/1e9:>10.3f} {rate*100:>8.1f}% €{pv/1e9:>10.3f}")

    # =========================================================================
    # VALORACIÓN
    # =========================================================================

    pv_fcf_total = sum(result['pv_fcf'])
    pv_fcf_pct = (pv_fcf_total / result['enterprise_value']) * 100
    tv_pv_pct = (result['pv_terminal_value'] / result['enterprise_value']) * 100

    print(f"\n   🎯 ENTERPRISE VALUE:")
    print("   ─" * 76)
    print(f"   PV de FCF (años 1-5): €{pv_fcf_total/1e9:>10.2f}B ({pv_fcf_pct:>5.1f}%)")
    print(f"   PV Terminal Value: €{result['pv_terminal_value']/1e9:>10.2f}B ({tv_pv_pct:>5.1f}%)")
    print(f"   ─────────────────────────────────────────────────────────────────────────")
    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:>10.2f}B")

    print(f"\n   🎯 EQUITY VALUE:")
    print("   ─" * 76)
    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:>10.2f}B")
    print(f"   + Cash: €{cash/1e9:>10.2f}B")
    print(f"   - Debt: €{total_debt/1e9:>10.2f}B")
    print(f"   ─────────────────────────────────────────────────────────────────────────")
    print(f"   Equity Value: €{result['equity_value']/1e9:>10.2f}B")
    print(f"   ÷ Shares: {shares_outstanding/1e6:>10.1f}M")
    print(f"   ─────────────────────────────────────────────────────────────────────────")
    print(f"   💎 VALOR INTRÍNSECO: €{result['fair_value_per_share']:>10.2f}")

    # =========================================================================
    # COMPARACIÓN
    # =========================================================================

    upside = ((result['fair_value_per_share'] - current_price) / current_price) * 100
    ev_ebitda_dcf = result['enterprise_value'] / ebitda

    print(f"\n" + "="*80)
    print("COMPARACIÓN CON MERCADO")
    print("="*80)

    print(f"\n   Valor intrínseco DCF: €{result['fair_value_per_share']:.2f}")
    print(f"   Precio actual: €{current_price:.2f}")
    print(f"   ─────────────────────────────────────────────────────────────────────────")

    if upside > 0:
        print(f"   ✅ UPSIDE: +{upside:.1f}%")
        if upside > 50:
            recommendation = "🚀 STRONG BUY"
        elif upside > 25:
            recommendation = "📈 BUY"
        elif upside > 15:
            recommendation = "👍 BUY"
        else:
            recommendation = "⚖️  HOLD"
    else:
        print(f"   ⚠️  DOWNSIDE: {upside:.1f}%")
        if upside < -25:
            recommendation = "🔻 STRONG SELL"
        elif upside < -15:
            recommendation = "📉 SELL"
        else:
            recommendation = "⚖️  HOLD"

    print(f"   Recomendación: {recommendation}")

    print(f"\n   📊 MÉTRICAS:")
    print(f"   EV/EBITDA (DCF): {ev_ebitda_dcf:.2f}x")
    print(f"   EV/EBITDA (mercado): {ev/ebitda:.2f}x")

    # =========================================================================
    # VERIFICACIÓN
    # =========================================================================

    print(f"\n" + "="*80)
    print("VERIFICACIÓN DE RIGOR FINANCIERO")
    print("="*80)

    checks_passed = 0
    checks_total = 0

    # Check 1: WACC > Terminal Growth
    checks_total += 1
    if result['wacc'] > result['terminal_growth']:
        print(f"   ✅ WACC ({result['wacc']:.2%}) > Terminal Growth ({result['terminal_growth']:.2%})")
        checks_passed += 1

    # Check 2-4: Values positivos
    checks_total += 3
    if result['enterprise_value'] > 0:
        print(f"   ✅ Enterprise Value positivo: €{result['enterprise_value']/1e9:.2f}B")
        checks_passed += 1
    if result['equity_value'] > 0:
        print(f"   ✅ Equity Value positivo: €{result['equity_value']/1e9:.2f}B")
        checks_passed += 1
    if result['fair_value_per_share'] > 0:
        print(f"   ✅ Fair Value positivo: €{result['fair_value_per_share']:.2f}")
        checks_passed += 1

    # Check 5: FCF creciente
    checks_total += 1
    fcf_growing = all(result['projected_fcf'][i] > result['projected_fcf'][i-1]
                      for i in range(1, len(result['projected_fcf'])))
    if fcf_growing:
        print(f"   ✅ FCF proyectado es creciente")
        checks_passed += 1

    # Check 6: TV ratio
    checks_total += 1
    tv_ratio = result['pv_terminal_value'] / result['enterprise_value']
    if 0.60 < tv_ratio < 0.85:
        print(f"   ✅ PV Terminal Value = {tv_ratio*100:.1f}% de EV (rango: 60-85%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  PV Terminal Value = {tv_ratio*100:.1f}% de EV")

    # Check 7: EV/EBITDA
    checks_total += 1
    if 10 < ev_ebitda_dcf < 20:
        print(f"   ✅ EV/EBITDA = {ev_ebitda_dcf:.2f}x (rango torres: 10-20x)")
        checks_passed += 1
    else:
        print(f"   ⚠️  EV/EBITDA = {ev_ebitda_dcf:.2f}x")

    # Check 8: Debt/EBITDA
    checks_total += 1
    debt_ebitda = total_debt / ebitda
    if debt_ebitda < 8:
        print(f"   ✅ Debt/EBITDA = {debt_ebitda:.2f}x (sostenible)")
        checks_passed += 1

    print(f"\n   ─────────────────────────────────────────────────────────────────────────")
    print(f"   📊 Resultado: {checks_passed}/{checks_total} checks pasados ({checks_passed/checks_total*100:.0f}%)")

    if checks_passed >= 7:
        print(f"   ✅ VALORACIÓN RIGUROSA Y CONSISTENTE")
    elif checks_passed >= 6:
        print(f"   ⚠️  Valoración razonable con advertencias menores")
    else:
        print(f"   ❌ Revisar parámetros")

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================

    print(f"\n" + "="*80)
    print("RESUMEN DE INPUTS UTILIZADOS (VERSIÓN AJUSTADA)")
    print("="*80)

    print(f"\n   📋 FCF NORMALIZADO:")
    print(f"   ├─ EBITDA: €{ebitda/1e9:.2f}B")
    print(f"   ├─ Tax rate: {tax_rate*100:.0f}%")
    print(f"   ├─ Maintenance CapEx: {maintenance_capex_rate*100:.0f}%")
    print(f"   ├─ Working Capital: {wc_adj*100:.0f}%")
    print(f"   └─ FCF Base: €{base_fcf/1e9:.3f}B")

    print(f"\n   📋 WACC:")
    print(f"   ├─ Beta levered: {beta_levered:.3f}")
    print(f"   ├─ Cost of Equity: {cost_of_equity*100:.2f}%")
    print(f"   ├─ Cost of Debt: {cost_of_debt*100:.2f}%")
    print(f"   └─ WACC: {wacc*100:.2f}%")

    print(f"\n   📋 CRECIMIENTO:")
    print(f"   ├─ Años 1-5: 8%, 10%, 12%, 15%, 18%")
    print(f"   └─ Terminal: {terminal_growth*100:.1f}%")

    print(f"\n   📋 VALORACIÓN:")
    print(f"   ├─ Enterprise Value: €{result['enterprise_value']/1e9:.2f}B")
    print(f"   ├─ Equity Value: €{result['equity_value']/1e9:.2f}B")
    print(f"   ├─ Fair Value/Share: €{result['fair_value_per_share']:.2f}")
    print(f"   ├─ Precio actual: €{current_price:.2f}")
    print(f"   └─ Upside/Downside: {upside:+.1f}%")

    print("\n" + "="*80)
    print("FIN DEL ANÁLISIS")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
