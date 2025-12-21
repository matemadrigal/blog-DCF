"""
Valoración DCF de Cellnex (CLNX.MC) con tasas de crecimiento personalizadas.

Tasas de crecimiento especificadas:
- Año 1: 8%
- Año 2: 10%
- Año 3: 12%
- Año 4: 15%
- Año 5: 18%

Este script ajusta los parámetros del modelo para empresas de infraestructura
en fase de expansión, donde el FCF histórico puede ser negativo pero el
potencial de generación de caja futura es fuerte.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import yfinance as yf
import numpy as np
from src.dcf.enhanced_model import EnhancedDCFModel, ScenarioAnalyzer
from src.dcf.wacc_calculator import calculate_wacc_simple
from datetime import datetime


def get_cellnex_data():
    """
    Obtiene datos fundamentales de Cellnex desde Yahoo Finance.

    Returns:
        dict: Diccionario con datos fundamentales
    """
    ticker = yf.Ticker("CLNX.MC")
    info = ticker.info

    # Obtener estados financieros
    cash_flow = ticker.cashflow
    balance_sheet = ticker.balance_sheet
    income_stmt = ticker.income_stmt

    print("\n" + "="*80)
    print("DATOS FUNDAMENTALES DE CELLNEX (CLNX.MC)")
    print("="*80)

    # Información básica
    print(f"\n📊 INFORMACIÓN GENERAL:")
    print(f"   Nombre: {info.get('longName', 'N/A')}")
    print(f"   Sector: {info.get('sector', 'N/A')}")
    print(f"   Industria: {info.get('industry', 'N/A')}")
    print(f"   Precio actual: €{info.get('currentPrice', 0):.2f}")
    print(f"   Market Cap: €{info.get('marketCap', 0)/1e9:.2f}B")

    # Obtener FCF histórico
    fcf_history = []
    if not cash_flow.empty:
        print(f"\n💰 FREE CASH FLOW HISTÓRICO:")
        for col in cash_flow.columns[:5]:  # Últimos 5 años
            try:
                fcf = 0
                # Buscar Free Cash Flow
                for idx in cash_flow.index:
                    if 'Free Cash Flow' in str(idx):
                        fcf = cash_flow.loc[idx, col]
                        if pd.notna(fcf):
                            fcf_history.append(float(fcf))
                            print(f"   {col.year}: €{fcf/1e9:.2f}B")
                            break
            except Exception as e:
                print(f"   Error procesando {col}: {e}")

    # Si no hay FCF, calcular desde Operating Cash Flow - CapEx
    if len(fcf_history) == 0:
        print(f"\n⚠️  FCF no disponible directamente. Calculando desde OCF - CapEx...")
        for col in cash_flow.columns[:5]:
            try:
                ocf = 0
                capex = 0

                for idx in cash_flow.index:
                    idx_str = str(idx)
                    if 'Operating Cash Flow' in idx_str or 'Total Cash From Operating Activities' in idx_str:
                        ocf = cash_flow.loc[idx, col]
                    elif 'Capital Expenditure' in idx_str or 'Capital Expenditures' in idx_str:
                        capex = cash_flow.loc[idx, col]

                if pd.notna(ocf) and pd.notna(capex):
                    fcf = float(ocf) + float(capex)  # CapEx is negative
                    fcf_history.append(fcf)
                    print(f"   {col.year}: OCF €{ocf/1e9:.2f}B + CapEx €{capex/1e9:.2f}B = FCF €{fcf/1e9:.2f}B")
            except Exception as e:
                print(f"   Error calculando FCF para {col}: {e}")

    # Balance sheet
    cash = 0
    debt = 0

    if not balance_sheet.empty:
        col = balance_sheet.columns[0]  # Más reciente

        print(f"\n🏦 BALANCE SHEET (más reciente):")
        for idx in balance_sheet.index:
            idx_str = str(idx).lower()
            if 'cash' in idx_str and 'equivalents' in idx_str:
                cash = float(balance_sheet.loc[idx, col]) if pd.notna(balance_sheet.loc[idx, col]) else 0
                print(f"   Cash & Equivalents: €{cash/1e9:.2f}B")
            elif 'total debt' in idx_str or ('long term debt' in idx_str and debt == 0):
                debt_val = balance_sheet.loc[idx, col]
                if pd.notna(debt_val):
                    debt = float(debt_val)
                    print(f"   Total Debt: €{debt/1e9:.2f}B")

    # Shares outstanding
    shares = info.get('sharesOutstanding', 0)
    if shares == 0:
        shares = info.get('impliedSharesOutstanding', 0)

    print(f"\n📈 ACCIONES:")
    print(f"   Shares Outstanding: {shares/1e9:.3f}B")

    # EBITDA (para empresas de infraestructura)
    ebitda = info.get('ebitda', 0)
    print(f"\n💡 EBITDA: €{ebitda/1e9:.2f}B")

    # Beta y cálculo de WACC
    beta = info.get('beta', 0.7)  # Tower companies típicamente tienen beta bajo
    print(f"\n📊 RIESGO:")
    print(f"   Beta: {beta:.3f}")

    return {
        'ticker': 'CLNX.MC',
        'name': info.get('longName', 'Cellnex'),
        'current_price': info.get('currentPrice', 0),
        'fcf_history': fcf_history,
        'cash': cash,
        'debt': debt,
        'shares': shares,
        'ebitda': ebitda,
        'beta': beta,
        'market_cap': info.get('marketCap', 0),
    }


def calculate_normalized_fcf_forward_looking(ebitda, maintenance_capex_rate=0.10, tax_rate=0.25):
    """
    Calcula FCF normalizado usando método forward-looking para infraestructura.

    Para empresas de infraestructura en expansión:
    - Base = EBITDA (no FCF histórico negativo)
    - Capex de mantenimiento solamente (no growth capex)
    - Impuestos normalizados
    - No cambios en working capital (contratos largos)

    Args:
        ebitda: EBITDA más reciente
        maintenance_capex_rate: Capex de mantenimiento como % de EBITDA (default 10%)
        tax_rate: Tasa impositiva normalizada (default 25%)

    Returns:
        float: FCF normalizado base para proyecciones
    """
    # FCF = EBITDA - D&A - Taxes - Maintenance CapEx + D&A - ΔWC
    # Simplificado: FCF ≈ EBITDA × (1 - tax_rate) - Maintenance CapEx

    # Para infraestructura, D&A es alto pero es non-cash
    # Asumimos que D&A ≈ Maintenance CapEx en estado estacionario

    maintenance_capex = ebitda * maintenance_capex_rate
    nopat = ebitda * (1 - tax_rate)  # Aproximación conservadora

    fcf_normalized = nopat - maintenance_capex

    return fcf_normalized


def adjust_wacc_for_infrastructure(base_beta=0.7, debt_to_equity=2.0, tax_rate=0.25):
    """
    Calcula WACC ajustado para empresa de infraestructura.

    Tower companies típicamente tienen:
    - Beta bajo (0.5-0.8): ingresos contractuales de largo plazo
    - Alta deuda (apalancamiento 60-70%): flujos predecibles permiten más deuda
    - Costo de deuda bajo (2-3%): deuda investment-grade

    Args:
        base_beta: Beta de mercado (default 0.7)
        debt_to_equity: Ratio deuda/equity (default 2.0)
        tax_rate: Tasa impositiva (default 25%)

    Returns:
        float: WACC ajustado
    """
    # Risk-free rate (bonos europeos a 10 años)
    rf = 0.025  # 2.5%

    # Market risk premium (Europa)
    mrp = 0.06  # 6%

    # Cost of equity (CAPM)
    cost_of_equity = rf + base_beta * mrp

    # Cost of debt (infraestructura investment grade)
    cost_of_debt = 0.03  # 3%

    # Weights
    weight_debt = debt_to_equity / (1 + debt_to_equity)
    weight_equity = 1 / (1 + debt_to_equity)

    # WACC
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt * (1 - tax_rate))

    return wacc


def print_valuation_summary(result, data, custom_growth_rates):
    """Imprime resumen detallado de la valoración."""

    print("\n" + "="*80)
    print("RESUMEN DE VALORACIÓN DCF - CELLNEX")
    print("="*80)

    print(f"\n📋 INPUTS UTILIZADOS:")
    print(f"   {'─'*76}")
    print(f"   Ticker: {data['ticker']}")
    print(f"   Nombre: {data['name']}")
    print(f"   Precio actual: €{data['current_price']:.2f}")
    print(f"\n   💰 FCF Base (normalizado): €{result['base_fcf']/1e9:.3f}B")
    print(f"   📊 Método: Forward-looking (EBITDA-based)")
    print(f"   ⚙️  EBITDA: €{data['ebitda']/1e9:.2f}B")
    print(f"   🔧 Maintenance CapEx: 10% EBITDA")
    print(f"   📈 Tax Rate: 25%")

    print(f"\n   🏦 Balance Sheet:")
    print(f"   {'─'*76}")
    print(f"   Cash & Equivalents: €{data['cash']/1e9:.2f}B")
    print(f"   Total Debt: €{data['debt']/1e9:.2f}B")
    print(f"   Net Debt: €{(data['debt']-data['cash'])/1e9:.2f}B")
    print(f"   Shares Outstanding: {data['shares']/1e9:.3f}B")

    print(f"\n   📊 Parámetros DCF:")
    print(f"   {'─'*76}")
    print(f"   WACC: {result['wacc']*100:.2f}%")
    print(f"   Terminal Growth: {result['terminal_growth']*100:.2f}%")
    print(f"   Beta: {data['beta']:.3f}")

    print(f"\n   📈 Tasas de Crecimiento (Personalizadas):")
    print(f"   {'─'*76}")
    for i, rate in enumerate(custom_growth_rates, 1):
        print(f"   Año {i}: {rate*100:.1f}%")

    print(f"\n📊 PROYECCIONES FCF (5 años):")
    print(f"   {'─'*76}")
    for i, (fcf, pv) in enumerate(zip(result['projected_fcf'], result['pv_fcf']), 1):
        print(f"   Año {i}: €{fcf/1e9:.3f}B  (PV: €{pv/1e9:.3f}B)")

    print(f"\n🎯 VALORACIÓN:")
    print(f"   {'─'*76}")
    print(f"   PV de FCF (5 años): €{sum(result['pv_fcf'])/1e9:.2f}B")
    print(f"   Terminal Value: €{result['terminal_value']/1e9:.2f}B")
    print(f"   PV Terminal Value: €{result['pv_terminal_value']/1e9:.2f}B")
    print(f"   {'─'*76}")
    print(f"   Enterprise Value: €{result['enterprise_value']/1e9:.2f}B")
    print(f"   + Cash: €{data['cash']/1e9:.2f}B")
    print(f"   - Debt: €{data['debt']/1e9:.2f}B")
    print(f"   {'─'*76}")
    print(f"   Equity Value: €{result['equity_value']/1e9:.2f}B")
    print(f"   ÷ Shares: {data['shares']/1e9:.3f}B")
    print(f"   {'─'*76}")
    print(f"   💎 VALOR INTRÍNSECO: €{result['fair_value_per_share']:.2f}")
    print(f"   📈 Precio Actual: €{data['current_price']:.2f}")

    # Upside/Downside
    upside = ((result['fair_value_per_share'] - data['current_price']) / data['current_price']) * 100

    print(f"\n🎲 ANÁLISIS:")
    print(f"   {'─'*76}")
    if upside > 0:
        print(f"   ✅ UPSIDE: +{upside:.1f}%")
        if upside > 50:
            print(f"   🚀 Recomendación: STRONG BUY")
        elif upside > 25:
            print(f"   📈 Recomendación: BUY")
        elif upside > 10:
            print(f"   👍 Recomendación: HOLD (sesgo alcista)")
        else:
            print(f"   ⚖️  Recomendación: HOLD")
    else:
        print(f"   ⚠️  DOWNSIDE: {upside:.1f}%")
        if upside < -25:
            print(f"   🔻 Recomendación: STRONG SELL")
        elif upside < -10:
            print(f"   📉 Recomendación: SELL")
        else:
            print(f"   ⚖️  Recomendación: HOLD (sesgo bajista)")

    print(f"\n💡 NOTAS METODOLÓGICAS:")
    print(f"   {'─'*76}")
    print(f"   ✓ Empresa de infraestructura en fase de expansión")
    print(f"   ✓ FCF histórico negativo → Usado EBITDA forward-looking")
    print(f"   ✓ Solo capex de mantenimiento (excluye growth capex)")
    print(f"   ✓ WACC ajustado para beta bajo de tower companies")
    print(f"   ✓ Tasas de crecimiento personalizadas reflejan rampa de generación de caja")
    print(f"   ✓ Terminal growth conservador (2.5%) apropiado para infraestructura madura")

    print("\n" + "="*80)


def main():
    """Función principal de valoración."""

    print("\n" + "="*80)
    print("VALORACIÓN DCF DE CELLNEX (CLNX.MC)")
    print("Empresa de Infraestructura de Torres de Telecomunicaciones")
    print("="*80)

    # Paso 1: Obtener datos
    print("\n[1/4] Obteniendo datos fundamentales...")
    data = get_cellnex_data()

    if data['shares'] == 0:
        print("\n❌ Error: No se pudieron obtener shares outstanding")
        return

    # Paso 2: Calcular FCF normalizado (forward-looking)
    print("\n[2/4] Calculando FCF normalizado (método forward-looking)...")

    if data['ebitda'] == 0:
        print("\n⚠️  EBITDA no disponible. Usando aproximación conservadora...")
        # Aproximar EBITDA desde market cap (EV/EBITDA typical = 15x para torres)
        ev = data['market_cap'] + data['debt'] - data['cash']
        data['ebitda'] = ev / 15
        print(f"   EBITDA estimado: €{data['ebitda']/1e9:.2f}B")

    base_fcf_normalized = calculate_normalized_fcf_forward_looking(
        ebitda=data['ebitda'],
        maintenance_capex_rate=0.10,  # 10% mantenimiento
        tax_rate=0.25  # 25% tasa efectiva
    )

    print(f"   ✓ FCF Base Normalizado: €{base_fcf_normalized/1e9:.3f}B")
    print(f"   ✓ Método: EBITDA × (1 - tax) - Maintenance CapEx")
    print(f"   ✓ Excluye: Growth CapEx, M&A, expansion activities")

    # Paso 3: Configurar modelo DCF
    print("\n[3/4] Configurando modelo DCF...")

    # WACC ajustado para infraestructura
    debt_to_equity_ratio = data['debt'] / (data['market_cap']) if data['market_cap'] > 0 else 2.0
    wacc = adjust_wacc_for_infrastructure(
        base_beta=data['beta'],
        debt_to_equity=debt_to_equity_ratio,
        tax_rate=0.25
    )

    print(f"   ✓ WACC calculado: {wacc*100:.2f}%")
    print(f"   ✓ Beta: {data['beta']:.3f} (tower companies tienen beta bajo)")
    print(f"   ✓ Debt/Equity: {debt_to_equity_ratio:.2f}x")

    # Terminal growth conservador para infraestructura
    terminal_growth = 0.025  # 2.5% (ligeramente por encima de inflación)

    print(f"   ✓ Terminal Growth: {terminal_growth*100:.2f}%")

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
    print_valuation_summary(result, data, custom_growth_rates)

    # Verificación de rigor financiero
    print("\n🔍 VERIFICACIÓN DE RIGOR FINANCIERO:")
    print(f"   {'─'*76}")

    checks_passed = 0
    checks_total = 0

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
        print(f"   ❌ Equity Value debe ser positivo")

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
        print(f"   ✅ FCF proyectado es creciente (coherente con tasas de crecimiento)")
        checks_passed += 1
    else:
        print(f"   ⚠️  FCF proyectado no es estrictamente creciente")

    # Check 6: Terminal Value razonable
    checks_total += 1
    tv_to_ev_ratio = result['terminal_value'] / result['enterprise_value']
    if 0.6 < tv_to_ev_ratio < 0.85:
        print(f"   ✅ Terminal Value es {tv_to_ev_ratio*100:.1f}% de EV (rango razonable: 60-85%)")
        checks_passed += 1
    else:
        print(f"   ⚠️  Terminal Value es {tv_to_ev_ratio*100:.1f}% de EV (fuera de rango típico)")

    print(f"\n   {'─'*76}")
    print(f"   📊 Checks Passed: {checks_passed}/{checks_total}")

    if checks_passed == checks_total:
        print(f"   ✅ TODOS LOS CHECKS PASADOS - Valoración rigurosa")
    elif checks_passed >= checks_total * 0.8:
        print(f"   ⚠️  Mayoría de checks pasados - Revisar advertencias")
    else:
        print(f"   ❌ Múltiples checks fallidos - Revisar inputs")

    print("\n" + "="*80)
    print("FIN DEL ANÁLISIS")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Importar pandas aquí para evitar error si no está instalado
    import pandas as pd
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    main()
