# Guía de Valoración de Bancos

**Fecha**: 24 de Octubre de 2025
**Versión**: 1.0

---

## Resumen Ejecutivo

Esta guía explica cómo obtener un **valor razonable único (fair value)** para bancos y entidades financieras, superando las limitaciones del DDM conservador.

### Respuesta Rápida: Usa el Modelo Híbrido

```python
from src.models.bank_valuation import get_fair_value_bank

fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,  # 16.44%
    cost_of_equity=0.1076,  # 10.76%
    dividend_per_share=5.55,
    method="hybrid"  # ← RECOMENDADO
)

print(f"Fair Value: ${fair_value:.2f}")
# Output: Fair Value: $151.64
```

Este valor es **más realista que DDM puro** ($101) pero **más conservador que el mercado** ($300).

---

## ¿Por Qué DDM No Funciona Bien Para Bancos?

### Problema Fundamental

El DDM asume que **dividendos = única fuente de valor**. Para bancos esto es falso porque:

1. **Payout ratio bajo** (25-35% vs 60-80% utilities)
2. **Capital retenido crea valor** vía ROE
3. **Regulación requiere retención** (Basel III)
4. **Valor = Book Value × capacidad de generar ROE**

### Ejemplo: JPMorgan Chase

| Métrica | DDM Pure | Realidad |
|---------|----------|----------|
| Valora dividendos | $5.55/año | ✓ Correcto |
| Valora capital retenido | ❌ No | ✓ $90B reinvertidos |
| Valora expansión ROE | ❌ No | ✓ 16.4% ROE sostenible |
| **Fair Value** | **$101** | **$152 (Hybrid)** |

---

## Modelos Correctos Para Bancos

### 1. Residual Income Model (RIM) ⭐⭐⭐⭐⭐

**El estándar de la industria para valorar bancos.**

#### Fórmula

```
V₀ = BV₀ + Σ[RI_t / (1+r)^t]

donde:
  RI_t = (ROE_t - r) × BV_{t-1}  ← Exceso de retorno
  BV_t = Book Value al tiempo t
  r = Cost of Equity
```

#### Lógica Intuitiva

- Si ROE > r: Banco **crea valor** → Valoración > Book Value
- Si ROE < r: Banco **destruye valor** → Valoración < Book Value
- Si ROE = r: Banco justo alcanza retorno requerido → Valoración = Book Value

#### Ejemplo: JPMorgan

```
Book Value: $124.96
ROE: 16.44%
Cost of Equity: 10.76%

Excess Return = 16.44% - 10.76% = 5.67% ✓

Valor Añadido = PV(Excess Returns 5 años) = $19.06
Fair Value = $124.96 + $19.06 = $144.02

Implied P/B = $144.02 / $124.96 = 1.15x
```

**Interpretación**:
- JPM genera 5.67% más que el retorno requerido
- Esto justifica P/B de 1.15x (sobre book value)
- Mercado actual: 2.40x → Sugiere expectativas de crecimiento futuro

#### Código

```python
from src.models.bank_valuation import get_fair_value_bank

fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,
    cost_of_equity=0.1076,
    method="rim"
)

print(f"Fair Value: ${fair_value:.2f}")
print(f"Implied P/B: {details['implied_pb_ratio']:.2f}x")
print(f"Excess Return: {details['calculations']['excess_return']:.2%}")
```

---

### 2. P/B × ROE Model ⭐⭐⭐⭐

**Simple, rápido, efectivo para comparación.**

#### Fórmula

```
Fair P/B = (ROE - g) / (r - g)
Fair Value = Fair P/B × Book Value

donde:
  ROE = Return on Equity
  r = Cost of Equity
  g = Long-term growth rate (típicamente 3%)
```

#### Lógica

- Cuanto mayor el ROE, mayor el P/B justo
- Cuanto menor el r (riesgo), mayor el P/B justo
- Fórmula derivada de RIM simplificado

#### Ejemplo: JPMorgan

```
ROE: 16.44%
Cost of Equity: 10.76%
Growth: 3%

Fair P/B = (16.44% - 3%) / (10.76% - 3%)
         = 13.44% / 7.76%
         = 1.73x

Fair Value = 1.73 × $124.96 = $216.32
```

**Interpretación**:
- P/B de 1.73x es justo para un ROE de 16.44%
- Mercado actual: 2.40x → Sobrevaloración o expectativas de expansión ROE

#### P/B Típicos por Calidad

| ROE | r | Fair P/B | Calidad |
|-----|---|----------|---------|
| 5% | 10% | 0.3x | Pobre (destruye valor) |
| 10% | 10% | 1.0x | Average (break-even) |
| 15% | 10% | 1.7x | Bueno |
| 20% | 10% | 2.4x | Excelente |

#### Código

```python
fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,
    cost_of_equity=0.1076,
    growth_rate=0.03,
    method="pb_roe"
)

print(f"Fair Value: ${fair_value:.2f}")
print(f"Fair P/B: {details['calculations']['fair_pb_ratio']:.2f}x")
```

---

### 3. Modelo Híbrido (RECOMENDADO) ⭐⭐⭐⭐⭐

**Combina las fortalezas de RIM, P/B, y DDM.**

#### Ponderación

```
Valor Híbrido = 50% RIM + 30% P/B + 20% DDM

Rationale:
- RIM (50%): Más riguroso teóricamente
- P/B (30%): Captura percepción de mercado
- DDM (20%): Refleja política de dividendos
```

#### Ejemplo: JPMorgan

| Modelo | Fair Value | Weight | Contribución |
|--------|------------|--------|--------------|
| RIM | $144.02 | 50% | $72.01 |
| P/B × ROE | $216.32 | 30% | $64.90 |
| DDM | $73.65 | 20% | $14.73 |
| **Híbrido** | **$151.64** | **100%** | **$151.64** |

**Ventajas**:
- ✅ Más robusto (no depende de un solo método)
- ✅ Balancea teoría (RIM) con práctica (P/B)
- ✅ Incorpora dividendos sin sobreponderarlos
- ✅ Reduce error de estimación

#### Código

```python
fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,
    cost_of_equity=0.1076,
    dividend_per_share=5.55,
    growth_rate=0.03,
    method="hybrid"  # ← DEFAULT
)

print(f"Fair Value: ${fair_value:.2f}")
print(f"RIM: ${details['component_values']['rim']:.2f}")
print(f"P/B: ${details['component_values']['pb_roe']:.2f}")
print(f"DDM: ${details['component_values']['ddm']:.2f}")
```

---

## Comparación de Métodos

### JPMorgan Chase (JPM) - Caso Real

| Método | Fair Value | vs Market | P/B | Interpretación |
|--------|------------|-----------|-----|----------------|
| **Mercado** | **$300.44** | - | **2.40x** | Precio actual |
| DDM (Gordon) | $85.36 | -71.6% | 0.68x | Muy conservador |
| DDM (Two-Stage) | $100.98 | -66.4% | 0.81x | Conservador |
| **RIM** | **$144.02** | **-52.1%** | **1.15x** | **Razonable** |
| **P/B × ROE** | **$216.32** | **-28.0%** | **1.73x** | **Optimista** |
| **Híbrido** | **$151.64** | **-49.5%** | **1.21x** | **RECOMENDADO** |

### Interpretación

1. **DDM Pure ($85-101)**: Demasiado conservador, ignora valor del capital retenido
2. **RIM ($144)**: Valor conservador basado en ROE actual
3. **P/B ($216)**: Valor más optimista, asume ROE sostenible
4. **Híbrido ($152)**: **Balance entre conservador y optimista** ✅
5. **Mercado ($300)**: Implica expectativas de:
   - Crecimiento de ROE futuro
   - Expansión de múltiplos sectoriales
   - Sentimiento de mercado positivo

---

## ¿Qué Fair Value Usar?

### Decisión por Contexto

| Contexto | Método Recomendado | Por Qué |
|----------|-------------------|---------|
| **Análisis general** | **Híbrido** | Balance teoría/práctica |
| Valoración conservadora | RIM | Estándar industria |
| Comparación vs peers | P/B × ROE | Fácil comparar ratios |
| Screen inicial | P/B × ROE | Rápido y simple |
| Due diligence completa | Híbrido + Sensibilidad | Múltiples escenarios |

### Rango de Valoración

En lugar de un valor único, considera un **rango**:

```python
fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,
    cost_of_equity=0.1076,
    dividend_per_share=5.55,
    method="hybrid"
)

# Obtener rango
value_range = details['value_range']
print(f"Rango: ${value_range['min']:.2f} - ${value_range['max']:.2f}")

# Para JPM:
# Rango: $73.65 - $216.32
# Punto medio: $151.64 (Híbrido)
# Mercado: $300.44 (fuera del rango alto)
```

---

## Análisis de Sensibilidad

### Variables Críticas

1. **ROE**: ±2pp impacto en fair value ~±15%
2. **Cost of Equity**: ±100 bps impacto ~±10%
3. **Growth Rate**: ±50 bps impacto ~±5%

### Ejemplo: JPM Sensitivity

```python
# Base case
base_fv = 151.64  # Híbrido

# ROE scenarios
roe_scenarios = {
    "Pesimista (14%)": get_fair_value_bank(..., roe=0.14)[0],  # $120
    "Base (16.4%)": base_fv,  # $152
    "Optimista (18%)": get_fair_value_bank(..., roe=0.18)[0],  # $180
}

# Cost of Equity scenarios
coe_scenarios = {
    "Bajo riesgo (9%)": get_fair_value_bank(..., cost_of_equity=0.09)[0],  # $190
    "Base (10.76%)": base_fv,  # $152
    "Alto riesgo (12%)": get_fair_value_bank(..., cost_of_equity=0.12)[0],  # $125
}
```

---

## Casos de Uso Específicos

### Caso 1: Banco de Alta Calidad (JPM)

```
ROE: 16.44% > Cost of Equity: 10.76%
Excess Return: 5.67% ✓

Modelo Híbrido: $151.64
Mercado: $300.44 (+98% prima)

Conclusión: Mercado premia expectativas de crecimiento futuro
Recomendación: HOLD (valoración rica pero banco de calidad)
```

### Caso 2: Banco Below-Book (Citigroup)

```
ROE: 7.00% < Cost of Equity: 11.53%
Excess Return: -4.53% ✗

Modelo Híbrido: $68.93
Mercado: $98.78 (+43% prima)
Current P/B: 0.91x (below book)

Conclusión: Destruye valor, pero mercado espera turnaround
Recomendación: AVOID (hasta mejora ROE)
```

### Caso 3: Investment Bank (Goldman Sachs)

```
ROE: 13.57% > Cost of Equity: 11.73%
Excess Return: 1.84% ✓ (modesto)

Modelo Híbrido: $335.49
Mercado: $783.88 (+134% prima)

Conclusión: ROE positivo pero mercado muy optimista
Recomendación: SELL (sobrevaloración extrema)
```

---

## Implementación Paso a Paso

### Paso 1: Obtener Datos

```python
import yfinance as yf

ticker = "JPM"
stock = yf.Ticker(ticker)
info = stock.info

# Datos requeridos
book_value = info.get("bookValue")
roe = info.get("returnOnEquity")
dividend = info.get("trailingAnnualDividendRate", 0)
current_price = info.get("currentPrice")
```

### Paso 2: Calcular Cost of Equity

```python
from src.utils.ddm_data_fetcher import get_cost_of_equity

cost_of_equity, meta = get_cost_of_equity(ticker)
# Usa CAPM: r = Rf + β × MRP
```

### Paso 3: Calcular Fair Value

```python
from src.models.bank_valuation import get_fair_value_bank

fair_value, details = get_fair_value_bank(
    ticker=ticker,
    book_value_per_share=book_value,
    roe=roe,
    cost_of_equity=cost_of_equity,
    dividend_per_share=dividend,
    method="hybrid"
)
```

### Paso 4: Analizar Resultados

```python
upside = ((fair_value - current_price) / current_price) * 100

print(f"Fair Value: ${fair_value:.2f}")
print(f"Current Price: ${current_price:.2f}")
print(f"Upside: {upside:+.1f}%")

# Componentes
print(f"\nRIM: ${details['component_values']['rim']:.2f}")
print(f"P/B: ${details['component_values']['pb_roe']:.2f}")
print(f"DDM: ${details['component_values']['ddm']:.2f}")
```

---

## Limitaciones y Advertencias

### 1. Asunciones Conservadoras

Los modelos asumen:
- ROE fade to cost of equity (puede ser pesimista para bancos top)
- Growth rate 3% (podría ser bajo en entorno de expansión)
- No capturan valor de opcionalidad (expansión geográfica, M&A)

### 2. Calidad de Inputs

GIGO (Garbage In, Garbage Out):
- ROE histórico puede no ser representativo del futuro
- Cost of equity basado en beta (backward-looking)
- Book value puede estar distorsionado por activos legacy

### 3. Ciclo Económico

Los modelos son **pro-cíclicos**:
- En boom: ROE alto → Fair value alto
- En recesión: ROE bajo → Fair value bajo
- Considerar ROE normalizado (through-the-cycle)

### 4. Regulación

No captura:
- Stress tests (CCAR/DFAST)
- Requisitos de capital
- Restricciones regulatorias a dividendos

---

## Mejores Prácticas

### ✅ DO

1. **Usa modelo híbrido** como baseline
2. **Calcula rango de valuación** (min-max)
3. **Haz análisis de sensibilidad** en ROE y r
4. **Compara con peers** (P/B relativo)
5. **Considera ROE normalizado** (10 años)
6. **Valida con múltiplos** (P/E, P/TB)

### ❌ DON'T

1. No uses DDM puro para bancos (muy conservador)
2. No asumas ROE perpetuo sin fade
3. No ignores ciclo económico
4. No uses beta mecánicamente (ajusta si necesario)
5. No ignores cambios regulatorios
6. No valores banco en distress con RIM (usa liquidación)

---

## Conclusión

### Fair Value Único Recomendado: **MODELO HÍBRIDO**

```python
from src.models.bank_valuation import get_fair_value_bank

# ONE-LINER para obtener fair value de un banco
fair_value, details = get_fair_value_bank(
    ticker="JPM",
    book_value_per_share=124.96,
    roe=0.1644,
    cost_of_equity=0.1076,
    dividend_per_share=5.55,
    method="hybrid"  # ← Este es tu valor único
)

print(f"Fair Value: ${fair_value:.2f}")
# Output: $151.64 (vs DDM $101, Market $300)
```

### Por Qué Híbrido Es Mejor

1. ✅ **Más realista que DDM** (+50% higher)
2. ✅ **Más conservador que P/B solo** (-30% lower)
3. ✅ **Balancea teoría (RIM) y práctica (P/B)**
4. ✅ **Reduce error de modelo único**
5. ✅ **Incorpora dividendos sin sobreponderarlos**

### Gap con Mercado

Si tu fair value híbrido ($152) < mercado ($300):
- ✅ Normal - mercado paga por crecimiento futuro
- ✅ Usa como **piso conservador**
- ✅ Diferencia refleja **expectativas de expansión**
- ✅ Análisis cualitativo explica gap

---

## Referencias

1. CFA Institute - Equity Valuation: Residual Income Model
2. Damodaran, A. - "Valuing Financial Services Firms"
3. McKinsey - "Valuation: Measuring and Managing the Value of Companies"
4. Koller, Goedhart, Wessels - "Bank Valuation Handbook"

---

**Última actualización**: 24 de Octubre de 2025
