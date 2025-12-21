"""
Valoración DCF de Cellnex (CLNX.MC) con tasas de crecimiento personalizadas.

Tasas de crecimiento especificadas:
- Año 1: 8%
- Año 2: 10%
- Año 3: 12%
- Año 4: 15%
- Año 5: 18%

Este script usa datos realistas de Cellnex (Q3 2024) y aplica
metodología forward-looking para empresas de infraestructura.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.dcf.enhanced_model import EnhancedDCFModel


def get_cellnex_data_hardcoded():
    """
    Datos fundamentales de Cellnex Telecom (CLNX.MC)
    Fuente: Informes financieros Q3 2024 y estimaciones de mercado

    Cellnex es una empresa líder europea en infraestructura de telecomunicaciones
    con torres en España, Italia, Francia, Reino Unido, Países Bajos, Portugal,
    Austria, Irlanda, Suiza y Polonia.
    """

    # Datos de mercado (Diciembre 2024)
    current_price = 35.50  # EUR (precio aproximado)
    shares_outstanding = 596_000_000  # ~596M acciones

    # Market cap
    market_cap = current_price * shares_outstanding  # ~€21.2B

    # Datos del balance (en EUR millones)
    # Cellnex tiene alta deuda debido a adquisiciones de torres
    cash = 1_500_000_000  # €1.5B efectivo
    total_debt = 18_000_000_000  # €18B deuda total (alta por adquisiciones)

    # EBITDA recurrente (estimado 2024)
    # Cellnex reporta EBITDA recurrente de ~€3.0-3.2B
    ebitda = 3_100_000_000  # €3.1B EBITDA

    # Free Cash Flow histórico (últimos 3 años, negativo por expansión)
    # Cellnex ha tenido FCF negativo por altas inversiones en M&A y construcción
    fcf_2021 = -500_000_000  # -€500M
    fcf_2022 = -800_000_000  # -€800M
    fcf_2023 = -300_000_000  # -€300M

    fcf_history = [fcf_2023, fcf_2022, fcf_2021]  # Más reciente primero

    # Beta
    # Tower companies tienen beta bajo (ingresos contractuales, regulados)
    beta = 0.65  # Beta típico de infraestructura telecom

    return {
        'ticker': 'CLNX.MC',
        'name': 'Cellnex Telecom S.A.',
        'sector': 'Communication Services',
        'industry': 'Telecom Infrastructure / Tower REITs',
        'current_price': current_price,
        'shares': shares_outstanding,
        'market_cap': market_cap,
        'cash': cash,
        'debt': total_debt,
        'ebitda': ebitda,
        'fcf_history': fcf_history,
        'beta': beta,
    }


def calculate_normalized_fcf_forward_looking(ebitda, maintenance_capex_rate=0.10, tax_rate=0.25):
    """
    Calcula FCF normalizado usando método forward-looking para infraestructura.

    Para empresas de infraestructura en expansión:
    - Base = EBITDA (no FCF histórico negativo)
    - Capex de mantenimiento solamente (no growth capex)
    - Impuestos normalizados
    - No cambios en working capital (contratos largos)

    Fórmula:
    FCF = EBITDA × (1 - Tax Rate) - Maintenance CapEx

    Donde:
    - EBITDA: Earnings Before Interest, Taxes, Depreciation & Amortization
    - Tax Rate: 25% (tasa efectiva española)
    - Maintenance CapEx: 10% de EBITDA (industria estándar para towers)

    Args:
        ebitda: EBITDA más reciente
        maintenance_capex_rate: Capex de mantenimiento como % de EBITDA (default 10%)
        tax_rate: Tasa impositiva normalizada (default 25%)

    Returns:
        float: FCF normalizado base para proyecciones
    """
    maintenance_capex = ebitda * maintenance_capex_rate
    ebitda_after_tax = ebitda * (1 - tax_rate)
    fcf_normalized = ebitda_after_tax - maintenance_capex

    return fcf_normalized


def calculate_wacc_infrastructure(base_beta=0.65, market_cap=21e9, total_debt=18e9, tax_rate=0.25):
    """
    Calcula WACC ajustado para empresa de infraestructura europea.

    Cellnex / Tower companies tienen:
    - Beta bajo (0.5-0.8): ingresos contractuales de largo plazo (8-15 años)
    - Alta deuda (50-70% de capital): flujos predecibles permiten apalancamiento
    - Costo de deuda bajo (2-4%): deuda investment-grade (BBB/BBB+)

    Fórmula WACC:
    WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)

    Donde:
    - Re = Cost of Equity (CAPM) = Rf + β × MRP
    - Rd = Cost of Debt
    - E = Market value of Equity
    - D = Market value of Debt
    - V = E + D
    - Tc = Corporate tax rate

    Args:
        base_beta: Beta de mercado (default 0.65)
        market_cap: Capitalización bursátil (equity value)
        total_debt: Deuda total
        tax_rate: Tasa impositiva (default 25%)

    Returns:
        float: WACC
    """
    # Risk-free rate: Bonos alemanes a 10 años (proxy para Europa)
    rf = 0.025  # 2.5%

    # Market risk premium Europa
    mrp = 0.06  # 6%

    # Cost of equity (CAPM)
    cost_of_equity = rf + base_beta * mrp
    # Re = 2.5% + 0.65 × 6% = 2.5% + 3.9% = 6.4%

    # Cost of debt (Cellnex tiene rating BBB, deuda a ~3-3.5%)
    cost_of_debt = 0.035  # 3.5%

    # Market values
    equity_value = market_cap
    debt_value = total_debt

    # Total value
    total_value = equity_value + debt_value

    # Weights
    weight_equity = equity_value / total_value
    weight_debt = debt_value / total_value

    # WACC
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

    return wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt


def print_data_summary(data):
    """Imprime resumen de datos de la empresa."""
    print("\n" + "="*80)
    print("DATOS FUNDAMENTALES DE CELLNEX (CLNX.MC)")
    print("="*80)

    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"   {'─'*76}")
    print(f"   Nombre: {data['name']}")
    print(f"   Ticker: {data['ticker']}")
    print(f"   Sector: {data['sector']}")
    print(f"   Industria: {data['industry']}")

    print(f"\n💰 DATOS DE MERCADO:")
    print(f"   {'─'*76}")
    print(f"   Precio actual: €{data['current_price']:.2f}")
    print(f"   Shares outstanding: {data['shares']:,.0f} ({data['shares']/1e6:.1f}M)")
    print(f"   Market Cap: €{data['market_cap']/1e9:.2f}B")

    print(f"\n🏦 BALANCE SHEET:")
    print(f"   {'─'*76}")
    print(f"   Cash & Equivalents: €{data['cash']/1e9:.2f}B")
    print(f"   Total Debt: €{data['debt']/1e9:.2f}B")
    print(f"   Net Debt: €{(data['debt']-data['cash'])/1e9:.2f}B")

    # Enterprise Value
    ev = data['market_cap'] + data['debt'] - data['cash']
    print(f"   Enterprise Value: €{ev/1e9:.2f}B")

    # Debt metrics
    debt_to_equity = data['debt'] / data['market_cap']
    debt_to_ebitda = data['debt'] / data['ebitda']
    print(f"   Debt/Equity: {debt_to_equity:.2f}x")
    print(f"   Debt/EBITDA: {debt_to_ebitda:.2f}x")

    print(f"\n📈 OPERATING METRICS:")
    print(f"   {'─'*76}")
    print(f"   EBITDA (recurrente): €{data['ebitda']/1e9:.2f}B")
    print(f"   EV/EBITDA: {ev/data['ebitda']:.2f}x")

    print(f"\n💸 FREE CASH FLOW HISTÓRICO:")
    print(f"   {'─'*76}")
    print(f"   ⚠️  FCF negativo por fase de expansión (M&A + growth capex)")
    for i, fcf in enumerate(data['fcf_history']):
        year = 2023 - i
        print(f"   {year}: €{fcf/1e9:.2f}B")

    print(f"\n📊 RIESGO:")
    print(f"   {'─'*76}")
    print(f"   Beta: {data['beta']:.3f} (bajo - típico de infraestructura regulada)")

    print("\n" + "="*80)


def print_valuation_summary(result, data, custom_growth_rates, wacc_details):
    """Imprime resumen detallado de la valoración."""

    cost_of_equity, cost_of_debt, weight_equity, weight_debt = wacc_details

    print("\n" + "="*80)
    print("VALORACIÓN DCF - CELLNEX TELECOM")
    print("="*80)

    print(f"\n📋 INPUTS UTILIZADOS:")
    print(f"   {'─'*76}")
    print(f"   💰 FCF Base (normalizado): €{result['base_fcf']/1e9:.3f}B")
    print(f"   📊 Método: Forward-looking (EBITDA-based)")
    print(f"      └─ EBITDA: €{data['ebitda']/1e9:.2f}B")
    print(f"      └─ EBITDA × (1 - 25% tax) = €{data['ebitda']*0.75/1e9:.2f}B")
    print(f"      └─ Maintenance CapEx (10%): €{data['ebitda']*0.10/1e9:.2f}B")
    print(f"      └─ FCF Base = €{result['base_fcf']/1e9:.3f}B")
    print(f"   ℹ️  Excluye: Growth CapEx, M&A, expansion activities")

    print(f"\n   🏦 Balance Sheet:")
    print(f"   {'─'*76}")
    print(f"   Cash & Equivalents: €{data['cash']/1e9:.2f}B")
    print(f"   Total Debt: €{data['debt']/1e9:.2f}B")
    print(f"   Net Debt: €{(data['debt']-data['cash'])/1e9:.2f}B")
    print(f"   Shares Outstanding: {data['shares']/1e6:.1f}M")

    print(f"\n   📊 Parámetros DCF:")
    print(f"   {'─'*76}")
    print(f"   WACC: {result['wacc']*100:.2f}%")
    print(f"      ├─ Cost of Equity: {cost_of_equity*100:.2f}%")
    print(f"      │  └─ CAPM: Rf (2.5%) + β ({data['beta']}) × MRP (6.0%)")
    print(f"      ├─ Cost of Debt: {cost_of_debt*100:.2f}% (pre-tax)")
    print(f"      │  └─ After-tax: {cost_of_debt*(1-0.25)*100:.2f}%")
    print(f"      ├─ Weight Equity: {weight_equity*100:.1f}%")
    print(f"      └─ Weight Debt: {weight_debt*100:.1f}%")
    print(f"   Terminal Growth: {result['terminal_growth']*100:.2f}%")
    print(f"   Tax Rate: 25.0%")

    print(f"\n   📈 Tasas de Crecimiento (Personalizadas):")
    print(f"   {'─'*76}")
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"   Año {i}: {rate*100:.1f}%")
    print(f"   ℹ️  Perpetuidad: {result['terminal_growth']*100:.1f}%")

    print(f"\n📊 PROYECCIONES FCF (5 años):")
    print(f"   {'─'*76}")
    print(f"   {'Año':<8} {'FCF (€B)':<12} {'Growth':<10} {'PV (€B)':<12} {'Discount Factor'}")
    print(f"   {'─'*76}")

    base_fcf = result['base_fcf']
    for i, (fcf, pv, growth) in enumerate(zip(result['projected_fcf'], result['pv_fcf'], custom_growth_rates), 1):
        discount_factor = 1 / ((1 + result['wacc']) ** i)
        print(f"   {i:<8} €{fcf/1e9:>10.3f} {growth*100:>8.1f}% €{pv/1e9:>10.3f} {discount_factor:>14.4f}")

    print(f"\n🎯 VALORACIÓN:")
    print(f"   {'─'*76}")
    pv_fcf_total = sum(result['pv_fcf'])
    print(f"   PV de FCF (años 1-5): €{pv_fcf_total/1e9:>10.2f}B")
    print(f"   Terminal Value: €{result['terminal_value']/1e9:>10.2f}B")
    print(f"      └─ FCF Año 5: €{result['projected_fcf'][-1]/1e9:.3f}B")
    print(f"      └─ TV = FCF₅ × (1 + g) / (WACC - g)")
    print(f"      └─ TV = €{result['projected_fcf'][-1]/1e9:.3f}B × 1.025 / ({result['wacc']:.3f} - 0.025)")
    print(f"   PV Terminal Value: €{result['pv_terminal_value']/1e9:>10.2f}B")
    print(f"   {'─'*76}")
    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:>10.2f}B")

    # Breakdown of EV
    pv_fcf_pct = (pv_fcf_total / result['enterprise_value']) * 100
    tv_pv_pct = (result['pv_terminal_value'] / result['enterprise_value']) * 100
    print(f"      ├─ PV FCF: {pv_fcf_pct:.1f}%")
    print(f"      └─ PV TV: {tv_pv_pct:.1f}%")

    print(f"   + Cash: €{data['cash']/1e9:>10.2f}B")
    print(f"   - Debt: €{data['debt']/1e9:>10.2f}B")
    print(f"   {'─'*76}")
    print(f"   Equity Value: €{result['equity_value']/1e9:>10.2f}B")
    print(f"   ÷ Shares: {data['shares']/1e6:>10.1f}M")
    print(f"   {'─'*76}")
    print(f"   💎 VALOR INTRÍNSECO: €{result['fair_value_per_share']:>10.2f}")
    print(f"   📈 Precio Actual: €{data['current_price']:>10.2f}")

    # Upside/Downside
    upside = ((result['fair_value_per_share'] - data['current_price']) / data['current_price']) * 100

    print(f"\n🎲 ANÁLISIS DE INVERSIÓN:")
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
        elif upside > 10:
            recommendation = "⚖️  HOLD (sesgo alcista)"
            confidence = "Media"
        else:
            recommendation = "⚖️  HOLD"
            confidence = "Baja"
    else:
        print(f"   ⚠️  DOWNSIDE: {upside:.1f}%")
        if upside < -25:
            recommendation = "🔻 STRONG SELL"
            confidence = "Alta"
        elif upside < -15:
            recommendation = "📉 SELL"
            confidence = "Media"
        elif upside < -10:
            recommendation = "📉 SELL"
            confidence = "Media"
        else:
            recommendation = "⚖️  HOLD (sesgo bajista)"
            confidence = "Baja"

    print(f"   Recomendación: {recommendation}")
    print(f"   Confianza: {confidence}")

    # Sensibilidad implícita
    print(f"\n   📊 Métricas de valoración:")
    ev = result['enterprise_value']
    print(f"   EV/EBITDA implícito: {ev/data['ebitda']:.2f}x")
    print(f"   P/E implícito (vs precio actual): {(result['equity_value']/data['shares'])/data['current_price']:.2f}x")

    print(f"\n💡 NOTAS METODOLÓGICAS:")
    print(f"   {'─'*76}")
    print(f"   ✓ Empresa de infraestructura en fase de expansión")
    print(f"   ✓ FCF histórico negativo → Usado EBITDA forward-looking")
    print(f"   ✓ Solo capex de mantenimiento (10% EBITDA) excluye growth capex")
    print(f"   ✓ WACC ajustado para beta bajo de tower companies ({data['beta']})")
    print(f"   ✓ Tasas de crecimiento personalizadas reflejan rampa de generación FCF")
    print(f"   ✓ Terminal growth conservador ({result['terminal_growth']:.1%}) apropiado para infraestructura")
    print(f"   ✓ Alta deuda ({data['debt']/1e9:.1f}B) consistente con modelo de negocio")

    print("\n" + "="*80)


def verify_financial_rigor(result, data):
    """Verifica el rigor financiero de la valoración."""

    print("\n🔍 VERIFICACIÓN DE RIGOR FINANCIERO:")
    print(f"   {'─'*76}")

    checks_passed = 0
    checks_total = 0
    warnings = []

    # Check 1: WACC > Terminal Growth
    checks_total += 1
    if result['wacc'] > result['terminal_growth']:
        print(f"   ✅ WACC ({result['wacc']:.2%}) > Terminal Growth ({result['terminal_growth']:.2%})")
        checks_passed += 1
    else:
        print(f"   ❌ WACC debe ser > Terminal Growth")
        warnings.append("WACC <= Terminal Growth: Gordon Growth no válido")

    # Check 2: Enterprise Value > 0
    checks_total += 1
    if result['enterprise_value'] > 0:
        print(f"   ✅ Enterprise Value positivo: €{result['enterprise_value']/1e9:.2f}B")
        checks_passed += 1
    else:
        print(f"   ❌ Enterprise Value debe ser positivo")
        warnings.append("Enterprise Value negativo")

    # Check 3: Equity Value > 0
    checks_total += 1
    if result['equity_value'] > 0:
        print(f"   ✅ Equity Value positivo: €{result['equity_value']/1e9:.2f}B")
        checks_passed += 1
    else:
        print(f"   ❌ Equity Value debe ser positivo")
        warnings.append("Equity Value negativo: exceso de deuda vs EV")

    # Check 4: Fair Value > 0
    checks_total += 1
    if result['fair_value_per_share'] > 0:
        print(f"   ✅ Fair Value positivo: €{result['fair_value_per_share']:.2f}")
        checks_passed += 1
    else:
        print(f"   ❌ Fair Value debe ser positivo")
        warnings.append("Fair Value negativo")

    # Check 5: FCF creciente
    checks_total += 1
    fcf_growing = all(result['projected_fcf'][i] > result['projected_fcf'][i-1]
                      for i in range(1, len(result['projected_fcf'])))
    if fcf_growing:
        print(f"   ✅ FCF proyectado es creciente (coherente con tasas de crecimiento)")
        checks_passed += 1
    else:
        print(f"   ⚠️  FCF proyectado no es estrictamente creciente")
        warnings.append("FCF no creciente: revisar growth rates")

    # Check 6: Terminal Value razonable (60-80% de EV es típico)
    checks_total += 1
    tv_to_ev_ratio = result['pv_terminal_value'] / result['enterprise_value']
    if 0.60 < tv_to_ev_ratio < 0.85:
        print(f"   ✅ PV Terminal Value es {tv_to_ev_ratio*100:.1f}% de EV (rango: 60-85%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  PV Terminal Value es {tv_to_ev_ratio*100:.1f}% de EV")
        if tv_to_ev_ratio > 0.85:
            warnings.append(f"TV muy alto ({tv_to_ev_ratio:.1%}): modelo muy sensible a perpetuidad")
        else:
            warnings.append(f"TV muy bajo ({tv_to_ev_ratio:.1%}): growth rates quizás demasiado altos")

    # Check 7: Base FCF positivo
    checks_total += 1
    if result['base_fcf'] > 0:
        print(f"   ✅ Base FCF positivo: €{result['base_fcf']/1e9:.3f}B")
        checks_passed += 1
    else:
        print(f"   ❌ Base FCF debe ser positivo")
        warnings.append("Base FCF negativo: revisar normalización")

    # Check 8: EV/EBITDA razonable (tower companies: 12-18x típico)
    checks_total += 1
    ev_ebitda = result['enterprise_value'] / data['ebitda']
    if 10 < ev_ebitda < 20:
        print(f"   ✅ EV/EBITDA = {ev_ebitda:.2f}x (rango torre: 10-20x)")
        checks_passed += 1
    else:
        print(f"   ⚠️  EV/EBITDA = {ev_ebitda:.2f}x (fuera de rango típico 10-20x)")
        warnings.append(f"EV/EBITDA {ev_ebitda:.1f}x inusual para torres")

    # Check 9: Debt/EBITDA razonable (torres pueden tener 5-7x)
    checks_total += 1
    debt_ebitda = data['debt'] / data['ebitda']
    if debt_ebitda < 8:
        print(f"   ✅ Debt/EBITDA = {debt_ebitda:.2f}x (torres pueden soportar 5-7x)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Debt/EBITDA = {debt_ebitda:.2f}x (muy alto, riesgo de refinanciación)")
        warnings.append(f"Debt/EBITDA {debt_ebitda:.1f}x muy alto")

    print(f"\n   {'─'*76}")
    print(f"   📊 Checks Passed: {checks_passed}/{checks_total} ({checks_passed/checks_total*100:.0f}%)")

    if checks_passed == checks_total:
        print(f"   ✅ TODOS LOS CHECKS PASADOS - Valoración rigurosa")
    elif checks_passed >= checks_total * 0.8:
        print(f"   ⚠️  {checks_total - checks_passed} warnings - Revisar notas")
    else:
        print(f"   ❌ {checks_total - checks_passed} checks fallidos - Revisar inputs")

    if warnings:
        print(f"\n   ⚠️  ADVERTENCIAS:")
        for w in warnings:
            print(f"      • {w}")

    print(f"\n   {'─'*76}")

    return checks_passed, checks_total, warnings


def main():
    """Función principal de valoración."""

    print("\n" + "="*80)
    print("VALORACIÓN DCF DE CELLNEX TELECOM (CLNX.MC)")
    print("Infraestructura de Torres de Telecomunicaciones - Europa")
    print("="*80)

    # Paso 1: Obtener datos
    print("\n[1/4] Cargando datos fundamentales...")
    data = get_cellnex_data_hardcoded()

    # Imprimir resumen de datos
    print_data_summary(data)

    # Paso 2: Calcular FCF normalizado (forward-looking)
    print("\n[2/4] Calculando FCF normalizado (método forward-looking)...")
    print(f"   {'─'*76}")

    base_fcf_normalized = calculate_normalized_fcf_forward_looking(
        ebitda=data['ebitda'],
        maintenance_capex_rate=0.10,  # 10% mantenimiento
        tax_rate=0.25  # 25% tasa efectiva
    )

    print(f"   ✓ FCF Base Normalizado: €{base_fcf_normalized/1e9:.3f}B")
    print(f"   ✓ Método: EBITDA × (1 - tax) - Maintenance CapEx")
    print(f"   ✓ Desglose:")
    print(f"      - EBITDA: €{data['ebitda']/1e9:.2f}B")
    print(f"      - EBITDA after tax (25%): €{data['ebitda']*0.75/1e9:.2f}B")
    print(f"      - Maintenance CapEx (10%): €{data['ebitda']*0.10/1e9:.2f}B")
    print(f"      - FCF Normalized: €{base_fcf_normalized/1e9:.3f}B")
    print(f"   ✓ Excluye: Growth CapEx, M&A, expansion activities")
    print(f"   ✓ Razonamiento: FCF histórico negativo por inversiones en crecimiento")

    # Paso 3: Configurar modelo DCF
    print("\n[3/4] Configurando modelo DCF...")
    print(f"   {'─'*76}")

    # WACC ajustado para infraestructura
    wacc, cost_of_equity, cost_of_debt, weight_equity, weight_debt = calculate_wacc_infrastructure(
        base_beta=data['beta'],
        market_cap=data['market_cap'],
        total_debt=data['debt'],
        tax_rate=0.25
    )

    print(f"   ✓ WACC calculado: {wacc*100:.2f}%")
    print(f"      ├─ Cost of Equity (CAPM): {cost_of_equity*100:.2f}%")
    print(f"      │  └─ Rf (2.5%) + β ({data['beta']}) × MRP (6.0%)")
    print(f"      ├─ Cost of Debt (pre-tax): {cost_of_debt*100:.2f}%")
    print(f"      │  └─ After-tax: {cost_of_debt*(1-0.25)*100:.2f}%")
    print(f"      ├─ Weight Equity: {weight_equity*100:.1f}%")
    print(f"      └─ Weight Debt: {weight_debt*100:.1f}%")

    # Terminal growth conservador para infraestructura
    terminal_growth = 0.025  # 2.5% (inflación europea + crecimiento PIB)

    print(f"   ✓ Terminal Growth: {terminal_growth*100:.2f}%")
    print(f"      └─ Conservador: inflación (2%) + crecimiento PIB (0.5%)")

    # Crear modelo
    model = EnhancedDCFModel(
        wacc=wacc,
        terminal_growth=terminal_growth
    )

    # Tasas de crecimiento personalizadas
    custom_growth_rates = [0.08, 0.10, 0.12, 0.15, 0.18]

    print(f"\n   ✓ Tasas de crecimiento personalizadas:")
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"      Año {i}: {rate*100:.1f}%")
    print(f"   ✓ Razonamiento: Rampa de conversión EBITDA → FCF")
    print(f"      - Años 1-2: Expansión moderada (8-10%)")
    print(f"      - Años 3-4: Aceleración (12-15%)")
    print(f"      - Año 5: Peak conversion (18%)")

    # Paso 4: Ejecutar valoración
    print("\n[4/4] Ejecutando valoración DCF...")

    result = model.full_dcf_valuation(
        base_fcf=base_fcf_normalized,
        historical_fcf=[],  # No usar histórico (negativo)
        cash=data['cash'],
        debt=data['debt'],
        diluted_shares=data['shares'],
        years=5,
        custom_growth_rates=custom_growth_rates,
        normalize_base=False  # Ya normalizado manualmente
    )

    # Imprimir resultados
    print_valuation_summary(result, data, custom_growth_rates,
                          (cost_of_equity, cost_of_debt, weight_equity, weight_debt))

    # Verificación de rigor financiero
    checks_passed, checks_total, warnings = verify_financial_rigor(result, data)

    print("\n" + "="*80)
    print("FIN DEL ANÁLISIS - CELLNEX TELECOM")
    print("="*80 + "\n")

    # Retornar resultado para posibles análisis adicionales
    return result, data


if __name__ == "__main__":
    main()
