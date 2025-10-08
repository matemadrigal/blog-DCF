# ✅ Unificación del Cálculo de FCF Base

## Problema Resuelto

**Antes**: Los tres modos (Manual, Autocompletar, Multi-fuente) daban valores diferentes para el FCF base:
- **Autocompletar**: $108.81B ✅ (correcto)
- **Multi-fuente**: $92.95B ❌ (tomaba año incorrecto)
- **Manual**: $0.00 (usuario tenía que ingresarlo manualmente)

**Después**: Los tres modos ahora usan el **mismo cálculo unificado** y dan el **mismo valor**:
- **Autocompletar**: $108.81B ✅
- **Multi-fuente**: $108.81B ✅
- **Manual**: $108.81B (autosugerido) ✅

---

## Cambios Implementados

### 1. Fórmula Unificada

Se estableció una **fórmula única** para calcular FCF en todos los casos:

```
FCF = Operating Cash Flow - |Capital Expenditure|
```

**Ubicación**: `src/data_providers/base.py` línea 42-60

**Cambio clave**: Ya no se usa el campo `free_cash_flow` directo que podría venir de las APIs, siempre se calcula desde OCF y CAPEX.

```python
def calculate_fcf(self) -> Optional[List[float]]:
    """
    Calculate Free Cash Flow from operating cash flow and capex.

    Formula: FCF = Operating Cash Flow - |Capital Expenditure|

    NOTE: Always calculates from OCF and CAPEX, never uses free_cash_flow field
    to ensure consistency across all data sources.
    """
    if self.operating_cash_flow and self.capital_expenditure:
        if len(self.operating_cash_flow) == len(self.capital_expenditure):
            return [
                ocf - abs(capex)
                for ocf, capex in zip(
                    self.operating_cash_flow, self.capital_expenditure
                )
            ]
    # Only return None if we can't calculate
    return None
```

### 2. Función Unificada de Obtención

Se creó una función `get_base_fcf_from_yahoo()` que centraliza la obtención del FCF base:

**Ubicación**: `pages/1_📈_Análisis_Individual.py` línea 116-163

```python
@st.cache_data(ttl=3600)
def get_base_fcf_from_yahoo(ticker: str):
    """
    Get base year FCF from Yahoo Finance using unified calculation.

    Returns:
        tuple: (base_fcf, historical_fcf_list) or (0.0, [])

    Formula: FCF = Operating Cash Flow - |Capital Expenditure|
    """
    # ... obtiene datos de Yahoo Finance
    # ... calcula FCF = OCF - |CAPEX|
    # ... retorna año más reciente como base
    return base_fcf, historical_fcf
```

### 3. Corrección de Orden de Datos

**Problema**: Yahoo Finance ordena datos de **más reciente a más antiguo** (2024, 2023, 2022...)

**Solución**:
- **Año base**: Siempre tomar `fcf_data[0]` (primer elemento = más reciente)
- **Regresión lineal**: Reversar la lista antes de calcular (`list(reversed(fcf_data))`)

**Antes (Multi-fuente)**:
```python
base_fcf = fcf_data[-1]  # ❌ Tomaba el más antiguo (2021)
```

**Después (Multi-fuente)**:
```python
base_fcf = fcf_data[0]  # ✅ Toma el más reciente (2024)
autofill_growth_rates = predict_growth_rate_linear_regression(
    list(reversed(fcf_data)), years  # ✅ Reversa para regresión
)
```

### 4. Autocompletado en Modo Manual

Ahora el **modo Manual** también sugiere automáticamente el FCF base:

**Antes**:
```python
base_fcf = st.number_input("FCF Año Base", value=0.0)  # Usuario tenía que ingresarlo
```

**Después**:
```python
suggested_base_fcf, _ = get_base_fcf_from_yahoo(ticker)
base_fcf = st.number_input(
    "FCF Año Base",
    value=float(suggested_base_fcf),  # ✅ Autosugerido
    help=f"Autocompletado: ${suggested_base_fcf/1e9:.2f}B"
)
```

---

## Resultados de Verificación

### Test con Apple (AAPL)

```
======================================================================
Testing Unified FCF Calculation for AAPL
======================================================================

Cash Flow Statement Data:
----------------------------------------------------------------------
Year 2024:
  Operating Cash Flow: $118.25B
  Capital Expenditure: $-9.45B
  FCF = OCF - |CAPEX| = $108.81B  ← AÑO BASE

Year 2023:
  Operating Cash Flow: $110.54B
  Capital Expenditure: $-10.96B
  FCF = OCF - |CAPEX| = $99.58B

Year 2022:
  Operating Cash Flow: $122.15B
  Capital Expenditure: $-10.71B
  FCF = OCF - |CAPEX| = $111.44B

Year 2021:
  Operating Cash Flow: $104.04B
  Capital Expenditure: $-11.09B
  FCF = OCF - |CAPEX| = $92.95B

======================================================================
RESULT:
======================================================================
Base Year: 2024
Base FCF: $108.81B

✓ Mode: Manual (autosuggested)      → $108.81B
✓ Mode: Autocompletar               → $108.81B
✓ Mode: Multi-fuente                → $108.81B
```

### Nota Importante

El valor que mencionaste inicialmente ($99.6B) corresponde al año **2023**, no al año base actual que es **2024** ($108.81B).

---

## Beneficios de la Unificación

1. **Consistencia Total**: Los tres modos dan exactamente el mismo valor
2. **Sin Confusión**: No más discrepancias entre modos
3. **Transparencia**: Fórmula clara y documentada (OCF - |CAPEX|)
4. **Mejor UX**: Modo Manual ahora también autosuggiere
5. **Trazabilidad**: Todos los mensajes muestran el FCF base calculado

---

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `src/data_providers/base.py` | Forzar cálculo OCF - \|CAPEX\|, nunca usar `free_cash_flow` directo |
| `pages/1_📈_Análisis_Individual.py` | Nueva función `get_base_fcf_from_yahoo()`, corregir orden Multi-fuente, autosugestión en Manual |

---

## Testing

**Ejecutar test**:
```bash
python3 test_fcf_unified.py
```

Este test verifica que:
- ✅ El cálculo sea correcto (OCF - |CAPEX|)
- ✅ El año base sea el más reciente
- ✅ Los valores coincidan entre modos

---

## Ejemplo de Uso en la UI

### Modo Autocompletar
```
✅ Calculados % de crecimiento basados en 4 años históricos (FCF Base: $108.81B)
📊 Año Base FCF: $108.81B
```

### Modo Multi-fuente
```
✅ Datos obtenidos de Yahoo Finance | FCF Base: $108.81B | Completitud: 75.0% | Confianza: 75.0%
📊 Año Base FCF: $108.81B
```

### Modo Manual
```
FCF Año Base: 108810000000
💡 Autocompletado: $108.81B
📊 Año Base FCF: $108.81B
```

---

## Resumen

**Problema**: Inconsistencia entre modos → **Solución**: Cálculo unificado

**Fórmula única**: `FCF = Operating Cash Flow - |CAPEX|`

**Resultado**: **$108.81B** para Apple (año 2024) en todos los modos ✅
