# 💰 Cómo se Calcula el Fair Value (DCF)

## Resumen Ejecutivo

El **Fair Value** (Valor Justo) se calcula usando el método **DCF (Discounted Cash Flow)**, que descuenta todos los flujos de caja futuros proyectados a valor presente.

**Fórmula simplificada**:
```
Fair Value = PV(FCF₁) + PV(FCF₂) + ... + PV(FCF_N) + PV(Terminal Value)
```

---

## 📐 Fórmula Completa

### Componentes del Cálculo

El Fair Value tiene **dos partes principales**:

1. **Valor Presente de FCF Proyectados** (años 1 a N)
2. **Valor Terminal** (perpetuidad después del año N)

### Fórmula Matemática

```
                N      FCF_i              TV
Fair Value = Σ     ──────────  +  ────────────
               i=1   (1 + r)ⁱ       (1 + r)ᴺ

Donde:
  Terminal Value (TV) = FCF_N × (1 + g)
                        ──────────────
                           (r - g)

  FCF_i = Free Cash Flow del año i
  r     = Tasa de descuento (WACC o costo de capital)
  g     = Tasa de crecimiento perpetuo terminal
  N     = Número de años de proyección
```

---

## 🔢 Ejemplo Paso a Paso (Apple)

### Datos de Entrada

```
Empresa: AAPL (Apple Inc.)
FCF Base (Año 0): $108.81B
Años de proyección: 5
Tasa de descuento (r): 10% (0.10)
Crecimiento terminal (g): 2% (0.02)
```

### Paso 1: Proyectar FCF Futuros

Usando tasas de crecimiento (ej: 9.26% anual basado en regresión lineal):

```
Año 1: $108.81B × (1 + 0.0926) = $118.89B
Año 2: $118.89B × (1 + 0.0926) = $129.90B
Año 3: $129.90B × (1 + 0.0926) = $141.93B
Año 4: $141.93B × (1 + 0.0926) = $155.07B
Año 5: $155.07B × (1 + 0.0926) = $169.43B
```

### Paso 2: Descontar Cada FCF a Valor Presente

```
PV(FCF₁) = $118.89B / (1.10)¹ = $108.08B
PV(FCF₂) = $129.90B / (1.10)² = $107.36B
PV(FCF₃) = $141.93B / (1.10)³ = $106.64B
PV(FCF₄) = $155.07B / (1.10)⁴ = $105.93B
PV(FCF₅) = $169.43B / (1.10)⁵ = $105.23B

Suma PV de FCF proyectados = $533.24B
```

### Paso 3: Calcular Terminal Value

El Terminal Value representa el valor de todos los FCF después del año 5, asumiendo crecimiento perpetuo al 2%:

```
Terminal Value = FCF₅ × (1 + g)
                 ──────────────
                    (r - g)

               = $169.43B × (1 + 0.02)
                 ─────────────────────
                      (0.10 - 0.02)

               = $169.43B × 1.02
                 ─────────────────
                       0.08

               = $172.82B
                 ─────────
                   0.08

               = $2,160.25B
```

### Paso 4: Descontar Terminal Value a Valor Presente

```
PV(Terminal Value) = $2,160.25B / (1.10)⁵
                   = $2,160.25B / 1.61051
                   = $1,341.26B
```

### Paso 5: Sumar Todo

```
Enterprise Value = Suma PV FCF + PV(Terminal Value)
                 = $533.24B + $1,341.26B
                 = $1,874.50B
```

### Paso 6: Calcular Fair Value por Acción

```
Fair Value por Acción = Enterprise Value / Shares Outstanding
                      = $1,874.50B / 15.7B shares
                      = $119.39 por acción
```

---

## 🖥️ Implementación en el Código

### Ubicación: `src/dcf/model.py`

```python
def dcf_value(
    cash_flows: Iterable[float],
    discount_rate: float,
    perpetuity_growth: float = 0.02
) -> float:
    """
    Calcula el valor presente DCF.

    Args:
        cash_flows: FCF proyectados [año1, año2, ..., añoN]
        discount_rate: Tasa de descuento (r)
        perpetuity_growth: Crecimiento terminal (g)

    Returns:
        Enterprise Value (valor total de la empresa)
    """
    cf_list = list(cash_flows)

    # Paso 1: Valor presente de FCF proyectados
    pv = 0.0
    for i, cf in enumerate(cf_list, start=1):
        pv += cf / ((1 + discount_rate) ** i)

    # Paso 2: Terminal Value
    last_cf = cf_list[-1]
    terminal_value = (
        last_cf * (1 + perpetuity_growth) /
        (discount_rate - perpetuity_growth)
    )

    # Paso 3: Valor presente del Terminal Value
    pv += terminal_value / ((1 + discount_rate) ** len(cf_list))

    return pv
```

---

## 📊 Desglose Visual del DCF

### Contribución de Cada Año al Fair Value

Para Apple con el ejemplo anterior:

```
┌─────────┬──────────────┬──────────────┬───────────┐
│ Año     │ FCF Proy.    │ Valor Pres.  │ % Total   │
├─────────┼──────────────┼──────────────┼───────────┤
│ 1       │ $118.89B     │ $108.08B     │ 5.8%      │
│ 2       │ $129.90B     │ $107.36B     │ 5.7%      │
│ 3       │ $141.93B     │ $106.64B     │ 5.7%      │
│ 4       │ $155.07B     │ $105.93B     │ 5.7%      │
│ 5       │ $169.43B     │ $105.23B     │ 5.6%      │
├─────────┼──────────────┼──────────────┼───────────┤
│ Total   │ $715.22B     │ $533.24B     │ 28.4%     │
├─────────┼──────────────┼──────────────┼───────────┤
│ Terminal│ $2,160.25B   │ $1,341.26B   │ 71.6%     │
├─────────┼──────────────┼──────────────┼───────────┤
│ TOTAL   │              │ $1,874.50B   │ 100.0%    │
└─────────┴──────────────┴──────────────┴───────────┘

⚠️ Nota: El Terminal Value representa ~72% del valor total.
Esto es típico en DCF - la mayoría del valor está en la perpetuidad.
```

### Gráfico del Valor Presente por Año

```
Valor Presente por Año:

Año 1  ████████████████████ $108.08B
Año 2  ███████████████████▌ $107.36B
Año 3  ███████████████████  $106.64B
Año 4  ██████████████████▌  $105.93B
Año 5  ██████████████████   $105.23B
─────────────────────────────────────────────────────
Term.  ████████████████████████████████████████████████████████████████████ $1,341.26B
```

---

## 🎛️ Parámetros Clave

### 1. Tasa de Descuento (r)

**¿Qué es?**
La tasa de retorno esperada o costo de capital (WACC).

**Valor típico**: 8-12%

**Impacto**:
- **↑ r**: Fair Value ↓ (más conservador)
- **↓ r**: Fair Value ↑ (más optimista)

**Ejemplo**:
```
Con r = 8%:  Fair Value = $2,200B
Con r = 10%: Fair Value = $1,875B  ← base
Con r = 12%: Fair Value = $1,600B
```

### 2. Crecimiento Terminal (g)

**¿Qué es?**
Tasa de crecimiento perpetuo después de los años proyectados.

**Valor típico**: 2-3% (aproximado al crecimiento del PIB)

**Restricción**: **g < r** (siempre debe ser menor que la tasa de descuento)

**Impacto**:
- **↑ g**: Fair Value ↑ (terminal value más alto)
- **↓ g**: Fair Value ↓ (terminal value más bajo)

**Ejemplo**:
```
Con g = 1%: Fair Value = $1,650B
Con g = 2%: Fair Value = $1,875B  ← base
Con g = 3%: Fair Value = $2,150B
```

### 3. FCF Proyectados

**¿Qué son?**
Los Free Cash Flows futuros esperados.

**Cómo se proyectan** (en esta app):
- **Manual**: Usuario ingresa % de crecimiento
- **Autocompletar**: Regresión lineal sobre datos históricos
- **Multi-fuente**: Igual que Autocompletar pero con múltiples fuentes

**Impacto**:
- **FCF más altos**: Fair Value ↑
- **FCF más bajos**: Fair Value ↓

---

## 🔍 Fair Value vs Precio de Mercado

### Interpretación

Una vez calculado el Fair Value por acción, se compara con el precio de mercado:

```
Fair Value por Acción: $119.39
Precio de Mercado:     $225.00 (ejemplo)
────────────────────────────────────
Upside/Downside:       -46.9%
```

**Interpretación**:
- **Fair Value > Precio**: Acción **infravalorada** (oportunidad de compra)
- **Fair Value < Precio**: Acción **sobrevalorada** (posible venta)
- **Fair Value ≈ Precio**: Acción **justamente valorada**

---

## ⚠️ Limitaciones del DCF

### 1. Sensibilidad a Parámetros

El DCF es **muy sensible** a pequeños cambios en:
- Tasa de descuento (r)
- Crecimiento terminal (g)
- Proyecciones de FCF

**Ejemplo**: Cambiar r de 10% a 11% puede cambiar el Fair Value en 15-20%.

### 2. Terminal Value Domina

Como vimos, el Terminal Value representa **~70-80%** del Fair Value total.
Esto significa que el modelo depende fuertemente de supuestos sobre el **futuro lejano**.

### 3. Supuestos de Crecimiento

Las proyecciones de FCF asumen:
- La empresa continuará operando indefinidamente
- No habrá disrupciones mayores
- El crecimiento seguirá patrones históricos

**Realidad**: Estos supuestos pueden no cumplirse.

### 4. No Considera Factores Cualitativos

El DCF solo usa números. No considera:
- Calidad del management
- Ventaja competitiva (moat)
- Innovación y R&D
- Riesgos geopolíticos
- Cambios regulatorios

---

## 🎯 Recomendaciones de Uso

### 1. Análisis de Sensibilidad

Siempre prueba el DCF con diferentes escenarios:

**Escenario Conservador**:
- r = 12%
- g = 1%
- FCF con crecimiento bajo

**Escenario Base**:
- r = 10%
- g = 2%
- FCF con crecimiento medio

**Escenario Optimista**:
- r = 8%
- g = 3%
- FCF con crecimiento alto

### 2. Margen de Seguridad

No compres exactamente al Fair Value. Usa un **margen de seguridad**:

```
Fair Value: $119
Margen de seguridad: 20%
Precio objetivo de compra: $95 o menos
```

### 3. Combinar con Otros Métodos

El DCF es una herramienta, no la única verdad. Combina con:
- **Análisis de múltiplos** (P/E, EV/EBITDA)
- **Análisis cualitativo** (ventaja competitiva)
- **Análisis técnico** (momentum, soporte/resistencia)

---

## 📚 Fórmulas de Referencia

### Gordon Growth Model (Terminal Value)

```
TV = FCF_N × (1 + g)
     ──────────────
        (r - g)
```

### Valor Presente (Descuento)

```
PV = FV
     ────────
     (1 + r)ⁿ

Donde:
  FV = Valor futuro
  r  = Tasa de descuento
  n  = Número de períodos
```

### WACC (Weighted Average Cost of Capital)

```
WACC = (E/V × Re) + (D/V × Rd × (1 - Tc))

Donde:
  E  = Equity (patrimonio)
  D  = Debt (deuda)
  V  = E + D (valor total)
  Re = Costo del equity
  Rd = Costo de la deuda
  Tc = Tasa impositiva
```

**Nota**: En esta app usamos r (tasa de descuento) directamente en lugar de calcular WACC.

---

## 🧮 Ejemplo Interactivo

### Caso: Comparar dos empresas

**Empresa A (High Growth Tech)**:
```
FCF Base: $10B
Crecimiento: 20% anual
r: 12%, g: 3%
→ Fair Value: $180B
→ Fair Value/Acción: $45
```

**Empresa B (Mature Dividend)**:
```
FCF Base: $50B
Crecimiento: 5% anual
r: 8%, g: 2%
→ Fair Value: $900B
→ Fair Value/Acción: $90
```

**Análisis**:
- Empresa A tiene **mayor riesgo** (r alto) pero **mayor crecimiento**
- Empresa B es **más estable** (r bajo) pero **menor crecimiento**
- El Fair Value refleja estos trade-offs

---

## 🔗 Código Relevante

### Archivo Principal
- **Cálculo DCF**: [`src/dcf/model.py`](src/dcf/model.py) línea 4-39
- **Aplicación en UI**: [`pages/1_📈_Análisis_Individual.py`](pages/1_📈_Análisis_Individual.py) línea 464
- **Proyección FCF**: [`src/dcf/projections.py`](src/dcf/projections.py) línea 68-80

---

## 📖 Resumen

**Fair Value** se calcula en **3 pasos**:

1. **Proyectar FCF futuros** usando tasas de crecimiento
2. **Descontar a valor presente** usando tasa r
3. **Añadir Terminal Value** (perpetuidad con crecimiento g)

**Resultado**: Enterprise Value total → Dividir por shares → Fair Value/Acción

**Uso**: Comparar con precio de mercado para identificar oportunidades de compra/venta.
