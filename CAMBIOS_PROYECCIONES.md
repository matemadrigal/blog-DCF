# Cambios en Sistema de Proyecciones FCF

## Resumen
Se ha modificado el sistema de proyecciones de Free Cash Flow para usar **porcentajes de crecimiento** en lugar de valores absolutos.

## Cambios Implementados

### 1. Nuevo Módulo: `src/dcf/projections.py`
Contiene funciones para:
- **`calculate_historical_growth_rates()`**: Calcula tasas de crecimiento año sobre año
- **`predict_growth_rate_linear_regression()`**: Predice % de crecimiento futuro usando regresión lineal
- **`apply_growth_rates_to_base()`**: Aplica % de crecimiento al año base para generar proyecciones
- **`get_average_historical_growth()`**: Calcula promedio histórico de crecimiento

### 2. Interfaz de Usuario Actualizada

#### Antes:
- Usuario ingresaba valores absolutos de FCF (ej: $100,000,000)

#### Ahora:
- Usuario ingresa **% de crecimiento** para cada año (ej: +5.00%)
- Cada año crece respecto al año anterior
- Se muestra el FCF base claramente

### 3. Modo Manual
- Usuario debe ingresar el **FCF Año Base** (año más reciente)
- Luego ingresa % de crecimiento para cada año proyectado
- Ejemplo:
  - Año Base: $100M
  - Año 1: +3% → $103M
  - Año 2: +2% → $105.06M
  - Año 3: +4% → $109.26M

### 4. Modo Autocompletar
- Obtiene datos históricos (últimos 5 años) desde Yahoo Finance
- Calcula FCF histórico (Operating Cash Flow - CAPEX)
- Usa **regresión lineal** sobre las tasas de crecimiento históricas
- Predice % de crecimiento para los próximos años
- Aplica restricciones conservadoras:
  - Mínimo: -20% (protección contra caídas extremas)
  - Máximo: +30% (evita proyecciones demasiado optimistas)
  - Si la tendencia es negativa, se atenúa gradualmente

### 5. Modo Multi-fuente
- Funciona igual que Autocompletar pero usando múltiples fuentes
- Obtiene datos de la mejor fuente disponible
- Calcula % de crecimiento usando regresión lineal

### 6. Mejoras en la Visualización
- Nueva columna "Crecimiento" en tabla de desglose DCF
- Muestra % aplicado a cada año
- Formato: `+5.00%` o `-2.50%`

## Ventajas del Nuevo Sistema

1. **Más Intuitivo**: Es más fácil pensar "crecerá 5%" que calcular valores absolutos
2. **Basado en Histórico**: Usa datos reales para proyectar el futuro
3. **Más Conservador**: Aplica límites para evitar proyecciones irreales
4. **Tendencias**: La regresión lineal captura si la empresa acelera o desacelera
5. **Flexibilidad**: El usuario puede ajustar manualmente los %

## Ejemplo de Uso

### Escenario 1: Empresa en Crecimiento Constante
```
Histórico (últimos 5 años):
- Año -5: $10,000M
- Año -4: $11,000M (+10%)
- Año -3: $12,100M (+10%)
- Año -2: $13,310M (+10%)
- Año -1: $14,641M (+10%)

Proyección (regresión lineal):
- Año 1: +10.00% → $16,105M
- Año 2: +10.00% → $17,716M
- Año 3: +10.00% → $19,487M
```

### Escenario 2: Empresa en Declive
```
Histórico (últimos 5 años):
- Año -5: $15,000M
- Año -4: $14,000M (-6.7%)
- Año -3: $13,000M (-7.1%)
- Año -2: $12,000M (-7.7%)
- Año -1: $11,000M (-8.3%)

Proyección (regresión lineal con atenuación):
- Año 1: -8.85% → $10,027M
- Año 2: -4.70% → $9,556M (se atenúa)
- Año 3: -3.32% → $9,238M (se atenúa)
```

## Dependencias Nuevas
- **NumPy**: Necesario para regresión lineal (`pip install numpy`)

## Archivos Modificados
1. `src/dcf/projections.py` (NUEVO)
2. `pages/1_📈_Análisis_Individual.py` (MODIFICADO)
3. `test_projections.py` (NUEVO - test unitario)

## Testing
Ejecutar `python3 test_projections.py` para verificar el funcionamiento.
