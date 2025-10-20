# 📊 Cómo se Calcula el FCF del Año Base

## Resumen
El **FCF (Free Cash Flow) del Año Base** es el punto de partida para todas las proyecciones. Representa el FCF más reciente (año 0) sobre el cual se aplican los porcentajes de crecimiento.

---

## 🔍 Fórmula del FCF

```
FCF = Operating Cash Flow - |Capital Expenditure|
```

**Componentes:**
- **Operating Cash Flow (OCF)**: Efectivo generado por las operaciones del negocio
- **Capital Expenditure (CAPEX)**: Inversión en activos fijos (plantas, equipos, tecnología)
- Se usa `abs(CAPEX)` porque CAPEX suele venir como valor negativo

---

## 📌 Por Modo de Operación

### 1. Modo MANUAL
**El usuario ingresa manualmente el FCF base.**

```python
# En la UI
base_fcf = st.number_input("FCF Año Base", value=0.0)
```

**Ventajas:**
- Total control del usuario
- Útil para ajustes personalizados
- Permite usar datos de otras fuentes

**Desventajas:**
- Requiere que el usuario conozca el FCF actual
- Más trabajo manual

---

### 2. Modo AUTOCOMPLETAR (Yahoo Finance)

**Obtiene datos históricos y calcula FCF automáticamente.**

#### Paso a Paso:

```python
# 1. Obtener estado de cash flow desde Yahoo Finance
t = yf.Ticker(ticker)
cashflow = t.cashflow

# 2. Extraer últimos 5 años de datos
cols = list(cashflow.columns)[:5]  # Columnas = años

# 3. Para cada año, buscar:
for c in cols:
    # Buscar "Operating Cash Flow" en las filas
    if "operating cash flow" in name:
        op = cashflow.loc[idx, c]

    # Buscar "Capital Expenditure" en las filas
    if "capital expenditure" in name or "purchase of ppe" in name:
        capex = cashflow.loc[idx, c]

    # Calcular FCF para ese año
    if op is not None and capex is not None:
        fcf = op - abs(capex)
        historical_fcf.append(fcf)

# 4. El primer elemento es el año MÁS RECIENTE
base_fcf = historical_fcf[0]  # ← AÑO BASE
```

#### Ejemplo Real (Apple - AAPL):

```
Yahoo Finance Cash Flow Statement (últimos 5 años):
┌──────────────────────┬─────────┬─────────┬─────────┬─────────┬─────────┐
│                      │ 2023    │ 2022    │ 2021    │ 2020    │ 2019    │
├──────────────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ Operating Cash Flow  │ $110.5B │ $122.1B │ $104.0B │ $80.7B  │ $69.4B  │
│ Capital Expenditure  │ -$10.9B │ -$10.7B │ -$11.1B │ -$7.3B  │ -$10.5B │
├──────────────────────┼─────────┼─────────┼─────────┼─────────┼─────────┤
│ **FCF Calculado**    │ $99.6B  │ $111.4B │ $92.9B  │ $73.4B  │ $58.9B  │
└──────────────────────┴─────────┴─────────┴─────────┴─────────┴─────────┘

historical_fcf = [99.6B, 111.4B, 92.9B, 73.4B, 58.9B]
base_fcf = historical_fcf[0] = $99.6B  ← AÑO BASE (2023)
```

**Ventajas:**
- Automático, sin trabajo manual
- Usa datos oficiales de Yahoo Finance
- Incluye 5 años para regresión lineal

**Desventajas:**
- Depende de la calidad de datos de Yahoo Finance
- Algunos tickers pueden tener datos incompletos

---

### 3. Modo MULTI-FUENTE

**Similar a Autocompletar, pero usa múltiples fuentes de datos.**

```python
# 1. El aggregator busca en múltiples fuentes:
#    - Financial Modeling Prep (FMP)
#    - Alpha Vantage
#    - Yahoo Finance

financial_data = aggregator.get_financial_data(ticker, years, strategy)

# 2. financial_data contiene:
#    - operating_cash_flow: [año1, año2, año3, año4, año5]
#    - capital_expenditure: [año1, año2, año3, año4, año5]

# 3. Calcular FCF usando base.py:
def calculate_fcf(self) -> Optional[List[float]]:
    if self.operating_cash_flow and self.capital_expenditure:
        return [
            ocf - abs(capex)
            for ocf, capex in zip(
                self.operating_cash_flow,
                self.capital_expenditure
            )
        ]

# 4. El último elemento es el MÁS RECIENTE
fcf_data = financial_data.calculate_fcf()
base_fcf = fcf_data[-1]  # ← AÑO BASE
```

#### Estrategias de Multi-fuente:

| Estrategia | Descripción |
|------------|-------------|
| **best_quality** | Compara todas las fuentes, elige la que tiene mayor `data_completeness` |
| **first_available** | Usa la primera fuente que funcione (más rápido) |
| **merge** | Combina datos de múltiples fuentes (experimental) |

**Ventajas:**
- Mayor confiabilidad (múltiples fuentes)
- Mejor cobertura de datos
- Métricas de calidad (`data_completeness`, `confidence_score`)

**Desventajas:**
- Más lento (consulta varias APIs)
- Requiere API keys para todas las fuentes

---

## 🧮 Ejemplo Completo: De Año Base a Proyecciones

### Datos de Entrada:
```
base_fcf = $100,000,000 (año base)
growth_rates = [+5%, +4%, +3%, +3%, +2%]
```

### Cálculo de Proyecciones:

```python
# Función apply_growth_rates_to_base()
projections = []
current_fcf = base_fcf  # $100M

# Año 1: +5%
current_fcf = 100M * (1 + 0.05) = $105M
projections.append(105M)

# Año 2: +4% sobre Año 1
current_fcf = 105M * (1 + 0.04) = $109.2M
projections.append(109.2M)

# Año 3: +3% sobre Año 2
current_fcf = 109.2M * (1 + 0.03) = $112.476M
projections.append(112.476M)

# Año 4: +3% sobre Año 3
current_fcf = 112.476M * (1 + 0.03) = $115.850M
projections.append(115.850M)

# Año 5: +2% sobre Año 4
current_fcf = 115.850M * (1 + 0.02) = $118.167M
projections.append(118.167M)
```

### Resultado:
```
Año Base: $100.0M
Año 1:    $105.0M  (+5%)
Año 2:    $109.2M  (+4%)
Año 3:    $112.5M  (+3%)
Año 4:    $115.9M  (+3%)
Año 5:    $118.2M  (+2%)
```

---

## 🎯 Puntos Clave

1. **FCF = OCF - |CAPEX|** es la fórmula universal
2. **Año Base = año más reciente** con datos disponibles
3. **Los % se aplican secuencialmente** (año 2 crece sobre año 1, no sobre base)
4. **Autocompletar y Multi-fuente** hacen el mismo cálculo, solo difieren en la fuente de datos
5. **Manual** requiere que el usuario conozca el FCF base

---

## 🔍 Dónde Está el Código

| Funcionalidad | Archivo | Línea |
|---------------|---------|-------|
| Cálculo FCF (Autocompletar) | `pages/1_📈_Análisis_Individual.py` | 214-216 |
| Cálculo FCF (Multi-fuente) | `src/data_providers/base.py` | 42-52 |
| Aplicar % de crecimiento | `src/dcf/projections.py` | 68-80 |
| Input manual FCF base | `pages/1_📈_Análisis_Individual.py` | 271-278 |

---

## ❓ Preguntas Frecuentes

**Q: ¿Por qué `historical_fcf[0]` para Autocompletar pero `fcf_data[-1]` para Multi-fuente?**

A: Diferente orden de datos:
- **Yahoo Finance**: Ordena años de más reciente a más antiguo → `[2023, 2022, 2021...]`
- **Multi-fuente**: Ordena años de más antiguo a más reciente → `[2019, 2020, 2021...]`

**Q: ¿Qué pasa si CAPEX es positivo?**

A: Se usa `abs(capex)` para manejar ambos casos. Siempre resta el valor absoluto.

**Q: ¿Y si falta Operating Cash Flow o CAPEX?**

A: El programa muestra warning:
```
⚠️ No se encontraron datos de Operating Cash Flow y CAPEX
```

**Q: ¿Puedo modificar el año base después?**

A: No directamente, pero puedes:
1. Cambiar a modo Manual
2. Ingresar el nuevo valor base
3. Ajustar los % manualmente
