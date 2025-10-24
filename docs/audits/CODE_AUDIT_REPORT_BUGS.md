# Auditoría Exhaustiva de Código - Reporte de Bugs y Errores

**Fecha:** 24 de Octubre, 2025
**Auditor:** Auditoría Profesional de Código
**Alcance:** Revisión completa de bugs, edge cases, errores lógicos y calidad de código

---

## 🔴 BUGS CRÍTICOS ENCONTRADOS

### 1. **src/dcf/projections.py** - Línea 47: Bug en manejo de zeros
**Severidad:** 🔴 CRÍTICA
**Archivo:** `src/dcf/projections.py:47`
**Línea problemática:**
```python
if fcf_prev == 0:
    if fcf_curr > 0:
        growth_rates.append(5.0)
    elif fcf_curr < 0:
        growth_rates.append(-1.0)
    # else: both zero, skip (no meaningful growth)
    continue  # ❌ BUG: continue cuando ambos son zero NO agrega nada
```

**Problema:**
Cuando `fcf_prev == 0` y `fcf_curr == 0`, el código hace `continue` sin agregar nada a `growth_rates`. Esto causa:
- **Desincronización de índices**: `growth_rates` tiene menos elementos que `fcf_history - 1`
- **Error en funciones downstream**: Cualquier código que asuma `len(growth_rates) == len(fcf_history) - 1` fallará

**Ejemplo del bug:**
```python
fcf_history = [100, 0, 0, 150]
growth_rates = calculate_historical_growth_rates(fcf_history)
# Expected: 3 growth rates [-1.0, 0.0, infinity]
# Actual: 2 growth rates [-1.0, 5.0]  # MISSING one!
# Index mismatch!
```

**Fix requerido:**
```python
if fcf_prev == 0:
    if fcf_curr > 0:
        growth_rates.append(5.0)
    elif fcf_curr < 0:
        growth_rates.append(-1.0)
    else:  # both zero
        growth_rates.append(0.0)  # ✅ FIXED: add 0% growth
    continue  # Safe now
```

---

### 2. **src/dcf/model.py** - Línea 74-75: Terminal Value con FCF negativo
**Severidad:** 🔴 CRÍTICA
**Archivo:** `src/dcf/model.py:74-75`
**Línea problemática:**
```python
last_cf = cf_list[-1]
terminal_value = last_cf * (1 + perpetuity_growth) / spread
# ❌ BUG: Si last_cf es negativo, TV será negativo
```

**Problema:**
Si el último FCF proyectado es negativo (empresa en distress), el cálculo del Terminal Value producirá un valor negativo, lo cual:
- **No tiene sentido financiero**: Una empresa con FCF negativo perpetuo no puede valer algo
- **Debería valer 0 o ser flag de error**: El modelo DCF no es apropiado
- **Puede dar valuaciones absurdas**: EV negativo cuando suma PV de FCF positivos + TV negativo

**Ejemplo del bug:**
```python
cf_list = [100, 80, 60, 40, -20]  # Distressed company
last_cf = -20
terminal_value = -20 * 1.025 / 0.08 = -256.25  # ❌ Nonsense
```

**Fix requerido:**
```python
last_cf = cf_list[-1]

# [AuditFix] Handle negative terminal FCF
if last_cf <= 0:
    warnings.warn(
        f"⚠️  Terminal FCF is non-positive ({last_cf:,.0f}). "
        f"Setting Terminal Value to 0. DCF may not be appropriate for this company.",
        UserWarning
    )
    terminal_value = 0.0
else:
    terminal_value = last_cf * (1 + perpetuity_growth) / spread
```

---

### 3. **src/dcf/projections.py** - Línea 242-250: Reinvestment rate sin validación
**Severidad:** 🟡 MEDIA
**Archivo:** `src/dcf/projections.py:242-250`
**Línea problemática:**
```python
def calculate_implied_reinvestment_rate(
    fcf_growth_rate: float,
    roic: float = 0.15,
) -> float:
    if roic <= 0:
        return 0.0  # ❌ BUG: Should raise error, not silently return 0

    reinvestment_rate = fcf_growth_rate / roic
```

**Problema:**
- **ROIC negativo o cero NO debería ser silenciosamente manejado**
- Si ROIC ≤ 0, la empresa está destruyendo valor
- Retornar 0.0 esconde el problema y permite continuar con datos inválidos

**Fix requerido:**
```python
if roic <= 0:
    raise ValueError(
        f"ROIC must be positive. Got: {roic:.2%}. "
        f"Negative/zero ROIC means the company destroys value."
    )
```

---

### 4. **src/dcf/valuation_bridge.py** - Línea 80-95: Division by zero en diluted shares
**Severidad:** 🔴 CRÍTICA
**Archivo:** `src/dcf/valuation_bridge.py:80-95` (aproximado)

**Código problemático:**
```python
def get_fully_diluted_shares(...):
    # ...
    basic_shares = info.get("sharesOutstanding", 0)
    metadata["basic_shares"] = basic_shares

    if basic_shares <= 0:
        metadata["warnings"].append("No shares outstanding data available")
        return 0, metadata  # ❌ BUG: returns 0 shares!

    # Later in calculate_price_per_share:
    intrinsic_price = equity_value / diluted_shares  # ❌ Division by ZERO!
```

**Problema:**
La función `get_fully_diluted_shares()` retorna `0` cuando no hay datos, pero luego `calculate_price_per_share()` divide por este valor sin validación adicional.

**Solución verificada:**
Revisando el código actual (línea 239 en valuation_bridge.py):
```python
if diluted_shares <= 0:
    analysis["warnings"].append("No shares data - cannot calculate price per share")
    return 0.0, analysis  # ✅ GOOD: Returns early, no division
```

**Estado:** ✅ YA MANEJADO CORRECTAMENTE (línea 239-241)

---

### 5. **src/dcf/ifrs16_adjustments.py** - Línea 98: Perpetuity assumption sin validación
**Severidad:** 🟡 MEDIA
**Archivo:** `src/dcf/ifrs16_adjustments.py:98`

**Línea problemática:**
```python
# Simple capitalization: PV = Annual Payment / r
# Assumes constant lease payments in perpetuity
estimated_liability = annual_lease_expense / discount_rate  # ❌ Simplification extrema
```

**Problema:**
- **Leases NO son perpetuos**: Típicamente 3-10 años
- **Formula correcta**: PV de anuidad finita = PMT × [1 - (1+r)^-n] / r
- **Sobreestima el liability**: Perpetuity formula da valores muy altos

**Fix requerido:**
```python
# Better: Assume finite lease term (conservative 7 years average)
average_lease_term = 7
discount_rate = 0.05

# Annuity formula: PV = PMT × [1 - (1+r)^-n] / r
pv_factor = (1 - (1 + discount_rate) ** -average_lease_term) / discount_rate
estimated_liability = annual_lease_expense * pv_factor

metadata["lease_term_assumed"] = average_lease_term
metadata["formula"] = "Finite annuity (not perpetuity)"
```

---

### 6. **src/dcf/wacc_calculator.py** - Línea 596: ERP division by zero
**Severidad:** 🟡 MEDIA
**Archivo:** `src/dcf/wacc_calculator.py:599`

**Línea problemática:**
```python
# [AuditFix] Apply country risk premium method
if apply_country_risk_to_beta and country_risk_premium > 0 and equity_risk_premium > 0:
    # METHOD 1: Adjust beta (Damodaran method)
    # β_adjusted = β + λ × (CRP / ERP)
    lambda_exposure = 1.0
    beta_crp_adjustment = lambda_exposure * (country_risk_premium / equity_risk_premium)
    # ❌ Si ERP es cercano a 0 (pero > 0), beta_crp_adjustment explota
```

**Problema:**
La condición `equity_risk_premium > 0` previene división por cero exacto, pero no protege contra:
- **ERP muy pequeño** (0.001): Beta adjustment = 10 × CRP/0.001 = 10,000 × CRP (absurdo)
- **Valuaciones en mercados de baja volatilidad**: ERP puede ser < 2%

**Fix requerido:**
```python
MIN_ERP = 0.02  # Minimum 2% ERP for stability

if apply_country_risk_to_beta and country_risk_premium > 0 and equity_risk_premium > MIN_ERP:
    # Safe to divide
    beta_crp_adjustment = lambda_exposure * (country_risk_premium / equity_risk_premium)
else:
    # ERP too low or negative, fall back to separate addition
    beta_crp_adjustment = 0.0
    cost_of_equity = self.risk_free_rate + (beta_final * equity_risk_premium) + country_risk_premium
```

---

## 🟡 BUGS MEDIOS / EDGE CASES

### 7. **src/dcf/projections.py** - Línea 102: Median de array vacío
**Severidad:** 🟡 MEDIA
**Archivo:** `src/dcf/projections.py:102`

**Protección actual:**
```python
if len(growth_rates) == 0:
    return [0.025] * years_to_predict  # ✅ GOOD: Early return
median_growth = float(np.median(growth_rates))  # Safe now
```

**Estado:** ✅ BIEN MANEJADO (línea 97-99)

---

### 8. **src/dcf/valuation_bridge.py** - Enterprise Value negativo
**Severidad:** 🟡 MEDIA

**Código vulnerable:**
```python
def calculate_equity_value_from_ev(
    enterprise_value: float,  # ❌ No validation if EV < 0
    ...
):
```

**Problema:**
Si el DCF produce un EV negativo (posible con FCF negativos), toda la cascade falla:
- Equity Value puede ser incorrecto
- No hay warning al usuario

**Fix requerido:**
```python
def calculate_equity_value_from_ev(
    enterprise_value: float,
    ...
):
    # Validate EV
    if enterprise_value < 0:
        bridge["warnings"].append(
            f"⚠️  Negative Enterprise Value (${enterprise_value/1e9:.2f}B). "
            f"Company may be distressed or model inputs are incorrect."
        )
```

---

### 9. **src/dcf/model.py** - Línea 54: Lista vacía de cash flows
**Severidad:** 🟢 BAJA

**Código actual:**
```python
cf_list = list(cash_flows)
if len(cf_list) == 0:
    return 0.0  # ✅ GOOD: Handles empty list
```

**Estado:** ✅ BIEN MANEJADO (línea 54-56)

---

## 🔵 PROBLEMAS DE CALIDAD DE CÓDIGO

### 10. **Type hints inconsistentes**
**Severidad:** 🔵 INFO
**Archivos:** Varios

**Problema:**
- Algunas funciones tienen type hints completos
- Otras solo parciales
- Dict sin TypedDict (pérdida de type safety)

**Ejemplo:**
```python
# ❌ Inconsistent
def calculate_equity_value_from_ev(...) -> Tuple[float, Dict[str, any]]:
    # 'any' should be 'Any' from typing

# ✅ Better
def calculate_equity_value_from_ev(...) -> Tuple[float, Dict[str, Any]]:
```

---

### 11. **Hardcoded magic numbers**
**Severidad:** 🔵 INFO
**Archivos:** `projections.py`, `ifrs16_adjustments.py`

**Ejemplos:**
```python
# src/dcf/projections.py:110
GDP_FLOOR = 0.025  # ✅ GOOD: Named constant

# src/dcf/projections.py:136
base_rate = min(0.40, base_rate)  # ❌ BAD: Magic number

# Better:
MAX_SUSTAINABLE_GROWTH = 0.40  # 40% - unrealistic beyond this
base_rate = min(MAX_SUSTAINABLE_GROWTH, base_rate)
```

---

### 12. **Falta manejo de excepciones de red**
**Severidad:** 🟡 MEDIA
**Archivos:** `valuation_bridge.py`, `ifrs16_adjustments.py`

**Problema:**
```python
try:
    stock = yf.Ticker(ticker)
    info = stock.info  # ❌ Can raise HTTPError, TimeoutError, etc.
except Exception as e:  # Too broad
    metadata["warnings"].append(f"Error: {str(e)}")
    return 0.0, metadata
```

**Mejora recomendada:**
```python
import requests

try:
    stock = yf.Ticker(ticker)
    info = stock.info
except requests.exceptions.HTTPError as e:
    metadata["warnings"].append(f"Network error fetching {ticker}: {e}")
    return 0.0, metadata
except requests.exceptions.Timeout:
    metadata["warnings"].append(f"Timeout fetching {ticker}")
    return 0.0, metadata
except Exception as e:
    metadata["warnings"].append(f"Unexpected error: {e}")
    return 0.0, metadata
```

---

## 📊 RESUMEN DE BUGS

| Severidad | Cantidad | Estado |
|-----------|----------|--------|
| 🔴 Críticos | 3 | ❌ Requieren fix inmediato |
| 🟡 Medios | 4 | ⚠️ Requieren fix pronto |
| 🟢 Bajos | 1 | ✅ Bien manejados |
| 🔵 Info/Calidad | 3 | 💡 Mejoras recomendadas |

---

## ✅ FIXES PRIORITARIOS REQUERIDOS

### **Prioridad 1 (CRÍTICA - Fix inmediato)**
1. ✅ **Bug #1**: `projections.py:47` - Fix continue cuando fcf ambos son 0
2. ✅ **Bug #2**: `model.py:74` - Validar FCF negativo en terminal value
3. ✅ **Bug #3**: `projections.py:242` - ROIC ≤ 0 debe raise error

### **Prioridad 2 (ALTA - Fix esta semana)**
4. ✅ **Bug #5**: `ifrs16_adjustments.py:98` - Usar anuidad finita, no perpetuity
5. ✅ **Bug #6**: `wacc_calculator.py:599` - Validar ERP mínimo antes de dividir
6. ✅ **Bug #8**: `valuation_bridge.py` - Validar EV negativo

### **Prioridad 3 (MEDIA - Mejoras de calidad)**
7. **Mejora #10**: Consistencia en type hints
8. **Mejora #11**: Eliminar magic numbers
9. **Mejora #12**: Mejorar manejo de excepciones de red

---

## 🧪 TEST CASES RECOMENDADOS

### Test Suite para Bugs Críticos

```python
# tests/test_bug_fixes.py

import pytest
from src.dcf.model import dcf_value
from src.dcf.projections import calculate_historical_growth_rates
from src.dcf.projections import calculate_implied_reinvestment_rate

class TestCriticalBugFixes:
    """Test suite for critical bug fixes"""

    def test_bug1_zero_fcf_both(self):
        """Bug #1: Both FCF values are zero"""
        fcf_history = [100, 0, 0, 150]
        growth_rates = calculate_historical_growth_rates(fcf_history)

        # Should have 3 growth rates (not 2)
        assert len(growth_rates) == 3, f"Expected 3 rates, got {len(growth_rates)}"

        # Middle rate should be 0% (0 to 0 = no growth)
        assert growth_rates[1] == 0.0, f"Expected 0.0, got {growth_rates[1]}"

    def test_bug2_negative_terminal_fcf(self):
        """Bug #2: Negative terminal FCF"""
        negative_fcfs = [100, 80, 60, 40, -20]

        with pytest.warns(UserWarning, match="Terminal FCF is non-positive"):
            ev = dcf_value(
                cash_flows=negative_fcfs,
                discount_rate=0.10,
                perpetuity_growth=0.025
            )

        # Terminal value should be 0, not negative
        # Only sum of discounted explicit FCFs
        assert ev >= 0, "EV should not be negative when TV=0"

    def test_bug3_negative_roic(self):
        """Bug #3: ROIC <= 0 should raise error"""
        with pytest.raises(ValueError, match="ROIC must be positive"):
            calculate_implied_reinvestment_rate(
                fcf_growth_rate=0.10,
                roic=-0.05  # Negative ROIC
            )

        with pytest.raises(ValueError, match="ROIC must be positive"):
            calculate_implied_reinvestment_rate(
                fcf_growth_rate=0.10,
                roic=0.0  # Zero ROIC
            )

    def test_bug5_lease_perpetuity(self):
        """Bug #5: Lease should use finite annuity, not perpetuity"""
        from src.dcf.ifrs16_adjustments import adjust_debt_for_leases

        # TODO: Update function to use finite annuity
        # Then test that PV < perpetuity PV
        pass

    def test_bug6_low_erp(self):
        """Bug #6: Very low ERP should not explode beta adjustment"""
        from src.dcf.wacc_calculator import WACCCalculator

        calc = WACCCalculator()

        # TODO: Test with very low market_return (e.g., risk_free + 0.5%)
        # Should not produce absurd beta adjustments
        pass

    def test_bug8_negative_ev(self):
        """Bug #8: Negative EV should produce warning"""
        from src.dcf.valuation_bridge import calculate_equity_value_from_ev

        negative_ev = -100e9  # -$100B

        equity_value, bridge = calculate_equity_value_from_ev(
            enterprise_value=negative_ev,
            ticker="TEST",
        )

        # Should have warning about negative EV
        assert len(bridge["warnings"]) > 0
        assert any("Negative Enterprise Value" in w for w in bridge["warnings"])
```

---

## 📝 NOTAS DE AUDITORÍA

### Código bien escrito (positivos):
✅ Buena documentación con docstrings
✅ [AuditFix] tags para trazabilidad
✅ Warnings apropiados para edge cases (mayoría)
✅ Validaciones en puntos críticos (mayoría)
✅ Type hints (aunque inconsistentes)

### Áreas de mejora:
❌ Bugs críticos en edge cases (0 values, negative FCF)
❌ Validaciones incompletas en inputs
❌ Magic numbers sin constantes
❌ Exception handling muy amplio
❌ Falta test suite comprehensivo

---

## 🎯 CONCLUSIÓN

**Estado general del código:** 🟡 ACEPTABLE CON RESERVAS

**Fortalezas:**
- Lógica financiera sólida (fórmulas correctas)
- Buena estructura y modularidad
- Documentación clara

**Debilidades críticas:**
- 3 bugs críticos que pueden causar crashes o resultados incorrectos
- Manejo incompleto de edge cases (valores 0, negativos)
- Falta test suite para validar correcciones

**Recomendación:**
✅ **APLICAR FIXES INMEDIATAMENTE** antes de usar en producción
✅ **CREAR TEST SUITE** para prevenir regresiones
✅ **CODE REVIEW** de los fixes aplicados

---

*Fin del Reporte de Auditoría de Bugs*
