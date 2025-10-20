# Control de Errores Exhaustivo - DCF Valuation Platform

## 🛡️ Sistema de Control de Errores Implementado

Este documento detalla el sistema exhaustivo de manejo de errores implementado en la plataforma DCF.

---

## 1. Obtención Robusta de Datos

### **Shares Outstanding** (`get_shares_outstanding`)

**Prioridad de fallbacks:**
1. **Input manual del usuario** (si > 0)
2. Yahoo Finance `info.sharesOutstanding`
3. Yahoo Finance `info.impliedSharesOutstanding`
4. Calculado: `market_cap / current_price`
5. Balance sheet: "common stock shares outstanding"

**Validación:**
- Shares <= 0 → Error: "Shares outstanding must be greater than zero"
- Shares < 1,000 → Warning: "Did you enter in millions/billions?"

**Ejemplo de uso:**
```python
shares, source = get_shares_outstanding("AAPL", user_input=0)
# shares = 14,840,390,000
# source = "Yahoo Finance (sharesOutstanding)"
```

---

### **Balance Sheet Data** (`get_balance_sheet_data`)

**Cash - Prioridad de fallbacks:**
1. Input manual del usuario
2. Balance sheet: "cash and cash equivalents"
3. Yahoo Finance `info.totalCash`
4. Yahoo Finance `info.cash`
5. Default: 0.0

**Debt - Prioridad de fallbacks:**
1. Input manual del usuario
2. Balance sheet: "total debt"
3. Balance sheet: "long term debt"
4. Yahoo Finance `info.totalDebt`
5. Yahoo Finance `info.longTermDebt`
6. Default: 0.0

**Validación:**
- Cash < 0 → Warning: "Cash is negative - please verify"
- Debt < 0 → Warning: "Debt is negative - please verify"

**Return:**
```python
cash, debt, sources = get_balance_sheet_data("AAPL")
# sources = {
#     "cash": "Balance Sheet",
#     "debt": "Balance Sheet (total debt)"
# }
```

---

### **Free Cash Flow** (`get_fcf_data`)

**Cálculo:** `FCF = Operating Cash Flow - |Capital Expenditure|`

**Fallbacks:**
1. Operating CF y CAPEX desde cash flow statement
2. Si no hay CAPEX: usa Operating CF directamente (conservador)
3. Si no hay datos: FCF = 0, metadata.success = False

**Validación:**
- FCF = 0 → Error: "Base FCF is zero - cannot calculate valuation"
- FCF < 0 → Warning: "Base FCF is negative - company is burning cash"

**Return con metadata:**
```python
base_fcf, historical_fcf, metadata = get_fcf_data("AAPL", max_years=5)
# metadata = {
#     "success": True,
#     "years_found": 4,
#     "data_source": "Yahoo Finance Cash Flow",
#     "errors": []
# }
```

---

### **Current Price** (`get_current_price`)

**Prioridad de fallbacks:**
1. Yahoo Finance `info.currentPrice`
2. Yahoo Finance `info.regularMarketPrice`
3. Yahoo Finance `info.previousClose`
4. Historical data (último cierre)

**Return:**
```python
price, source = get_current_price("AAPL")
# price = 258.06
# source = "Yahoo Finance (currentPrice)"
```

---

## 2. Conversión Segura de Tipos

### **`safe_get_float(value, default=0.0)`**

Maneja todos estos casos:
- `None` → default
- `NaN` → default
- `inf` / `-inf` → default
- Pandas Series → extrae valor con `.item()`
- Strings numéricos → convierte a float
- Errores de conversión → default

**Ejemplos:**
```python
safe_get_float(None)              # → 0.0
safe_get_float(float('nan'))      # → 0.0
safe_get_float(float('inf'))      # → 0.0
safe_get_float("1.5e9")           # → 1500000000.0
safe_get_float("invalid", 100)    # → 100.0
```

### **`safe_get_int(value, default=0)`**

Similar a `safe_get_float` pero convierte a int:
- Maneja notación científica: `"1.5e9"` → `1500000000`
- Sanity check: valores > 1e15 → default
- Mismo manejo de None, NaN, inf

---

## 3. Validación Exhaustiva de Inputs DCF

### **`validate_dcf_inputs(base_fcf, wacc, terminal_growth, shares, cash, debt)`**

**Valida todos los parámetros críticos antes del cálculo DCF:**

| Input | Validación | Error si falla |
|-------|-----------|---------------|
| **base_fcf** | > 0 | "Base FCF is zero - cannot calculate valuation" |
| | | "Base FCF is negative ($X.XXB) - company is burning cash" |
| **wacc** | > 0 | "WACC must be positive (current: X.XX%)" |
| | < 0.5 | "WACC seems unreasonably high (X.XX%) - please verify" |
| **terminal_growth** | < wacc | "Terminal growth (X.XX%) must be less than WACC (Y.YY%)" |
| | > -0.05 | "Terminal growth (X.XX%) is very negative - is this correct?" |
| | < 0.10 | "Terminal growth (X.XX%) is very high - perpetual growth >10% is unrealistic" |
| **shares** | > 0 | "Shares outstanding must be greater than zero" |
| | > 1000 | "Shares outstanding (XXX) seems too low - did you enter in millions/billions?" |
| **cash** | >= 0 | Warning: "Cash is negative ($X.XXB) - please verify" |
| **debt** | >= 0 | Warning: "Debt is negative ($X.XXB) - please verify" |

**Return:**
```python
is_valid, errors = validate_dcf_inputs(
    base_fcf=10e9,
    wacc=0.08,
    terminal_growth=0.025,
    shares=1e9,
    cash=5e9,
    debt=2e9
)
# is_valid = True
# errors = []
```

---

## 4. UI - Persistencia de Inputs del Usuario

### **Problema resuelto: Shares outstanding no se actualizaba manualmente**

**Solución:** Session state en Streamlit

```python
# Inicializar session state
if "shares_input" not in st.session_state:
    st.session_state.shares_input = 0

# Widget con valor persistente
shares_input = st.sidebar.number_input(
    "Shares outstanding",
    min_value=0,
    value=st.session_state.shares_input,  # ← Valor persistente
    key="shares_input_widget",
)

# Actualizar session state cuando el usuario cambia el valor
if shares_input != st.session_state.shares_input:
    st.session_state.shares_input = shares_input
```

**Ahora:**
- ✅ El usuario puede ingresar shares manualmente
- ✅ El valor se persiste aunque se recargue la página
- ✅ El valor manual tiene prioridad sobre el autocompletado

---

## 5. Expander de Fuentes de Datos

**UI muestra de dónde vino cada dato:**

```
📊 Ver fuentes de datos
  Shares Outstanding:
    ✓ Yahoo Finance (sharesOutstanding)
    Valor: 14,840,390,000

  Balance Sheet:
    ✓ Cash: Balance Sheet
    Valor: $65.17B
    ✓ Debt: Balance Sheet (total debt)
    Valor: $106.63B
```

---

## 6. Mensajes de Error Accionables

### **Antes:**
```
❌ Error en el cálculo: float division by zero
```

### **Ahora:**
```
❌ Errores de validación detectados:
⚠️ Base FCF is zero - cannot calculate valuation
⚠️ Shares outstanding must be greater than zero

💡 Sugerencias:
• Si el FCF es 0, prueba con modo 'Autocompletar' o 'Multi-fuente'
• Si shares = 0, ingresa el número de acciones manualmente en el sidebar
• Si WACC ≤ g, reduce el terminal growth o aumenta WACC
• Verifica que los datos del ticker sean correctos
```

---

## 7. Casos Extremos Manejados

### **Tickers Inválidos**
```python
shares, source = get_shares_outstanding("INVALID123")
# shares = 0
# source = "Not found"
```

### **Empresas sin Deuda**
```python
cash, debt, sources = get_balance_sheet_data("GOOG")
# debt = 0.0 (válido, no es error)
# sources["debt"] = "Not found (defaulted to 0)"
```

### **FCF Negativo** (empresas quemando cash)
```python
is_valid, errors = validate_dcf_inputs(base_fcf=-5e9, ...)
# is_valid = False
# errors = ["Base FCF is negative ($-5.00B) - company is burning cash"]
```

### **WACC <= Terminal Growth**
```python
is_valid, errors = validate_dcf_inputs(wacc=0.08, terminal_growth=0.09, ...)
# is_valid = False
# errors = ["Terminal growth (9.00%) must be less than WACC (8.00%)"]
```

### **Terminal Growth Irrealista**
```python
is_valid, errors = validate_dcf_inputs(terminal_growth=0.15, ...)
# is_valid = False
# errors = ["Terminal growth (15.00%) is very high - perpetual growth >10% is unrealistic"]
```

---

## 8. Testing

### **Test Suite: `test_error_handling.py`**

**Prueba:**
- ✅ 4 tickers diferentes (AAPL, TSLA, BRK-B, INVALID123)
- ✅ 7 casos de validación (normal, zero FCF, negative FCF, g>=WACC, etc.)
- ✅ Múltiples fallbacks para cada tipo de dato
- ✅ Manual override vs autocompletar

**Ejecutar:**
```bash
python test_error_handling.py
```

---

## 9. Resumen de Mejoras

### **Antes:**
- ❌ Shares outstanding no se actualizaba manualmente
- ❌ Crashes con datos faltantes (NaN, None, inf)
- ❌ Mensajes de error genéricos
- ❌ No se sabía de dónde venía cada dato
- ❌ Sin validación previa al cálculo DCF

### **Ahora:**
- ✅ Input manual persistente con session state
- ✅ 3-5 fallbacks para cada tipo de dato
- ✅ Conversión segura de tipos (safe_get_float/int)
- ✅ Validación exhaustiva con mensajes accionables
- ✅ Expander mostrando fuente de cada dato
- ✅ Manejo de 7+ casos extremos
- ✅ Test suite comprehensivo

---

## 10. Garantías del Sistema

**Nunca crashea por:**
- ✅ Ticker inválido
- ✅ Datos faltantes (None, NaN)
- ✅ Valores infinitos (inf, -inf)
- ✅ Shares = 0
- ✅ FCF = 0 o negativo
- ✅ Balance sheet vacío
- ✅ WACC <= terminal growth
- ✅ Conversión de tipos fallida

**Siempre proporciona:**
- ✅ Mensaje de error claro
- ✅ Sugerencias accionables
- ✅ Fuente de cada dato
- ✅ Opción de input manual
- ✅ Valores default seguros

---

## Arquitectura de Robustez

```
┌─────────────────────────────────────────────────┐
│           User Input (UI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Ticker   │  │ Shares   │  │ FCF      │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼─────────────┼────────────┘
        │             │             │
        ▼             ▼             ▼
┌─────────────────────────────────────────────────┐
│     Data Fetching Layer (data_fetcher.py)       │
│  ┌──────────────────────────────────────────┐  │
│  │  Fallback 1: Yahoo Finance info          │  │
│  │  Fallback 2: Balance Sheet               │  │
│  │  Fallback 3: Calculated                  │  │
│  │  Fallback 4: Manual Input                │  │
│  │  Fallback 5: Safe Default (0)            │  │
│  └──────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│     Safe Type Conversion                        │
│  • safe_get_float(value, default)               │
│  • safe_get_int(value, default)                 │
│  • Handles: None, NaN, inf, pandas, strings     │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│     Validation Layer (validate_dcf_inputs)      │
│  • Check FCF > 0                                │
│  • Check WACC > terminal_growth                 │
│  • Check shares > 0                             │
│  • Check reasonable ranges                      │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│     DCF Calculation                             │
│  • EnhancedDCFModel.full_dcf_valuation()        │
│  • WACC calculation                             │
│  • Terminal growth calculation                  │
└─────────────────────────────────────────────────┘
```

---

**Última actualización:** 2025-10-09
**Versión:** 2.0 (Control de Errores Exhaustivo)
