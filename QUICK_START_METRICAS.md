# 🚀 Quick Start: Métricas de Valoración

## ⚡ En 2 Minutos

### ¿Qué se agregó?
3 métricas nuevas para comparar valoraciones:
- **EV/EBITDA**: Cuánto pagas por el flujo operativo
- **P/E Ratio**: Cuánto pagas por los beneficios
- **P/B Ratio**: Cuánto pagas vs valor contable

### ¿Dónde lo encuentro?
1. Abre la app: `streamlit run app.py`
2. Ve a "📈 Análisis Individual"
3. Elige un ticker (ej: AAPL)
4. Scroll hasta "📊 Métricas de Valoración Relativa"

### ¿Cómo lo interpreto?
- 🟢 = Potencialmente subvaluada
- 🟡 = Valoración razonable
- 🔴 = Potencialmente sobrevaluada
- ⚪ = No disponible (datos negativos)

---

## 📊 Ejemplo Visual: Apple (AAPL)

```
┌─────────────────────────────────────────────────────────┐
│  🎯 Métricas Clave                                      │
├─────────────────────────────────────────────────────────┤
│  EV/EBITDA      P/E Ratio      P/B Ratio      EV        │
│  26.93x         38.61x         57.33x      $3.82T       │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  📈 Interpretación                                      │
├─────────────────────────────────────────────────────────┤
│  EV/EBITDA: 🔴 Valoración muy elevada                   │
│             Rangos: <10 (baja), 10-15 (normal)          │
│                                                          │
│  P/E Ratio: 🔴 Valoración muy elevada                   │
│             Rangos: <15 (baja), 15-25 (normal)          │
│                                                          │
│  P/B Ratio: 🔴 Prima muy elevada                        │
│             Rangos: <1 (baja), 1-3 (normal)             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  ⚖️ Comparación DCF vs Métricas                         │
├─────────────────────────────────────────────────────────┤
│  Señal DCF: 🟢 Subvaluada (Fair Value > Precio)        │
│  Señales Relativas: 🔴 EV/EBITDA alto, 🔴 P/E alto     │
│                                                          │
│  Consenso: 🟡 NEUTRAL - Señales mixtas                  │
│            DCF alcista pero múltiplos elevados          │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Guía Rápida de Interpretación

### Caso 1: Todas las Señales Verdes
```
DCF:     🟢 Subvaluada
Múltiplos: 🟢 Bajos
────────────────────
Acción:  💚 COMPRA FUERTE
```

### Caso 2: Señales Mixtas
```
DCF:     🟢 Subvaluada
Múltiplos: 🔴 Altos
────────────────────
Acción:  🟡 REVISAR
         Analizar sector y supuestos DCF
```

### Caso 3: Todas las Señales Rojas
```
DCF:     🔴 Sobrevaluada
Múltiplos: 🔴 Altos
────────────────────
Acción:  🔴 EVITAR
```

---

## 💡 Cheat Sheet: Rangos Típicos

### EV/EBITDA
| Rango | Interpretación | Típico de |
|-------|----------------|-----------|
| < 8x  | 🟢 Baja | Empresas maduras, cíclicas |
| 8-12x | 🟡 Normal | Empresas estables |
| 12-15x | 🟠 Elevada | Empresas en crecimiento |
| > 15x | 🔴 Muy alta | Tech, alto crecimiento |

### P/E Ratio
| Rango | Interpretación | Típico de |
|-------|----------------|-----------|
| < 15x | 🟢 Bajo | Value, cíclicas |
| 15-20x | 🟡 Normal | S&P 500 promedio |
| 20-25x | 🟠 Elevado | Calidad, crecimiento moderado |
| > 25x | 🔴 Muy alto | Growth, tech |

### P/B Ratio
| Rango | Interpretación | Típico de |
|-------|----------------|-----------|
| < 1x  | 🟢 Muy bajo | Bancos, industriales (oportunidad) |
| 1-2x  | 🟡 Normal | Empresas tradicionales |
| 2-3x  | 🟠 Premium | Calidad superior |
| > 3x  | 🔴 Muy alto | Tech, intangibles |

---

## 🔥 Casos de Uso Rápidos

### Buscar Value (Subvaluadas)
1. Ve a Análisis Individual
2. Busca empresas con:
   - EV/EBITDA < 10x 🟢
   - P/E < 15x 🟢
   - DCF upside > 20% 🟢
3. Valida calidad de balance (Cash/Debt)

### Buscar Growth (Crecimiento)
1. Ve a Análisis Individual
2. Busca empresas con:
   - Revenue growth > 20%
   - P/E 20-35x (no importa si alto)
   - DCF positivo
3. Valida sostenibilidad del crecimiento

### Validar DCF
1. Calcula DCF para empresa
2. Revisa múltiplos:
   - Si DCF dice "COMPRA" y múltiplos están bajos → ✅ Alta convicción
   - Si DCF dice "COMPRA" pero múltiplos altos → ⚠️ Revisar supuestos
   - Si ambos dicen "EVITAR" → ❌ No invertir

---

## 📚 Dónde Aprender Más

### Documentación Completa
- `METRICAS_VALORACION.md` → Teoría y fórmulas detalladas
- `EJEMPLOS_METRICAS.md` → Casos reales y ejemplos prácticos
- `RESUMEN_IMPLEMENTACION_METRICAS.md` → Detalles técnicos

### Tests y Validación
```bash
python3 test_valuation_metrics.py
```

### Ejemplos de Código
```python
from src.dcf.valuation_metrics import ValuationMetricsCalculator

calc = ValuationMetricsCalculator()
metrics = calc.calculate_all_metrics("AAPL")

print(f"EV/EBITDA: {metrics.ev_ebitda:.2f}x")
print(f"P/E: {metrics.pe_ratio:.2f}x")
print(f"P/B: {metrics.pb_ratio:.2f}x")
```

---

## ⚠️ Advertencias Importantes

### NO Confíes Solo en Múltiplos
❌ "P/E 10x → Comprar"
✅ "P/E 10x + DCF alcista + balance sólido → Analizar más"

### Contexto es Clave
- Comparar con sector (no con mercado general)
- Considerar ciclo económico
- Entender el business model

### Métricas N/A
- EBITDA/EPS negativos → Múltiplos no aplicables
- Usar métricas alternativas (EV/Sales, Price/Sales)

---

## 🎓 Regla de Oro

> **"Usa múltiplos para screening rápido,**
> **usa DCF para decisión final"**

### Workflow Recomendado:
```
1. Screen inicial → Múltiplos (encuentra candidatos)
   ├─ P/E < 20x
   └─ EV/EBITDA < 15x

2. Análisis profundo → DCF (valora intrínsecamente)
   ├─ Proyecta FCF 5-10 años
   └─ Calcula fair value

3. Decisión → Combina ambos (alta convicción)
   ├─ Si convergen → Invertir
   └─ Si divergen → Investigar más
```

---

## ✅ Checklist Antes de Invertir

Antes de tomar decisión basada en métricas:

- [ ] He calculado el DCF fair value
- [ ] He revisado los múltiplos (EV/EBITDA, P/E, P/B)
- [ ] He comparado con empresas del mismo sector
- [ ] Entiendo por qué están altos/bajos
- [ ] He leído los últimos earnings calls
- [ ] Conozco los riesgos principales
- [ ] He validado calidad de balance (Cash/Debt)
- [ ] Sé cuál es mi tesis de inversión
- [ ] Sé cuándo vender (precio objetivo)

---

## 🚀 ¡Empieza Ahora!

```bash
# 1. Ejecuta la app
streamlit run app.py

# 2. Analiza tu primera empresa
Ve a "Análisis Individual" → Elige AAPL

# 3. Compara DCF vs Métricas
Scroll hasta "Métricas de Valoración Relativa"

# 4. Lee la interpretación automática
Revisa los semáforos 🟢🟡🔴

# 5. Toma tu decisión
COMPRA / NEUTRAL / EVITAR
```

---

**¿Preguntas?**
- Lee `METRICAS_VALORACION.md` para detalles técnicos
- Lee `EJEMPLOS_METRICAS.md` para casos prácticos
- Ejecuta `test_valuation_metrics.py` para ver ejemplos de código

**Happy Investing! 📈**

---

*Versión: 1.0 | Fecha: 2025-10-10*
