# Sistema Multi-Fuente de Datos Financieros

Este documento explica cómo funciona el sistema de búsqueda inteligente de datos financieros y cómo configurarlo.

## 🎯 Características

- **Búsqueda multi-fuente**: Obtiene datos de múltiples APIs automáticamente
- **Selección inteligente**: Compara calidad y completitud de datos
- **Fallback automático**: Si una fuente falla, prueba con otras
- **Combinación de datos**: Puede mezclar datos de diferentes fuentes para máxima completitud

## 📊 Fuentes de Datos Disponibles

### 1. **Yahoo Finance** (Gratuito, sin API key)
- **Prioridad**: Alta (1)
- **Datos**: Precios, cash flow, income statement, balance sheet
- **Limitaciones**: Puede tener datos incompletos para algunas empresas
- **Configuración**: No requiere configuración

### 2. **Alpha Vantage** (Gratuito con límites)
- **Prioridad**: Media-Alta (2)
- **Datos**: Estados financieros completos, precios históricos
- **Límite**: 25 requests/día (tier gratuito)
- **Calidad**: Excelente (98% confianza)
- **Configuración**: Requiere API key gratuita

### 3. **Financial Modeling Prep** (Gratuito con límites)
- **Prioridad**: Media (3)
- **Datos**: Estados financieros, ratios, precios
- **Límite**: 250 requests/día (tier gratuito)
- **Calidad**: Muy buena (97% confianza)
- **Configuración**: Requiere API key gratuita

## 🔧 Configuración

### Opción 1: Variables de Entorno (.env)

1. Copia el archivo de ejemplo:
   ```bash
   cp .env.example .env
   ```

2. Edita `.env` y agrega tus API keys:
   ```bash
   ALPHA_VANTAGE_API_KEY=tu_clave_aqui
   FMP_API_KEY=tu_clave_aqui
   ```

### Opción 2: Streamlit Secrets

1. Crea el directorio si no existe:
   ```bash
   mkdir -p .streamlit
   ```

2. Copia el archivo de ejemplo:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```

3. Edita `.streamlit/secrets.toml` y agrega tus API keys:
   ```toml
   alpha_vantage = "tu_clave_aqui"
   fmp = "tu_clave_aqui"
   ```

## 🔑 Cómo Obtener API Keys

### Alpha Vantage

1. Visita: https://www.alphavantage.co/support/#api-key
2. Completa el formulario simple
3. Recibirás tu API key inmediatamente por email
4. **Gratis**: 25 requests por día

### Financial Modeling Prep

1. Visita: https://site.financialmodelingprep.com/developer/docs
2. Crea una cuenta gratuita
3. Ve a tu dashboard para obtener la API key
4. **Gratis**: 250 requests por día

## 🚀 Uso en la Aplicación

### Modo Multi-fuente

En el Análisis Individual, selecciona **"Multi-fuente"** en el radio button "Modo FCF".

### Estrategias Disponibles

1. **Mejor Calidad** (`best_quality`)
   - Consulta TODAS las fuentes disponibles en paralelo
   - Compara calidad y completitud de datos
   - Selecciona automáticamente la mejor
   - ⏱️ Más lento pero mejor calidad

2. **Primera Disponible** (`first_available`)
   - Prueba fuentes en orden de prioridad
   - Usa la primera que responda correctamente
   - ⚡ Más rápido
   - Recomendado si solo tienes Yahoo Finance

3. **Combinar Fuentes** (`merge`)
   - Obtiene datos de múltiples fuentes
   - Combina lo mejor de cada una
   - Máxima completitud de datos
   - 🎯 Mejor para análisis detallado

## 📈 Métricas de Calidad

El sistema muestra automáticamente:

- **Fuente**: De dónde vienen los datos
- **Completitud**: % de campos con datos (0-100%)
- **Confianza**: Score de confiabilidad de la fuente (0-100%)

Ejemplo:
```
📊 Fuente: Alpha Vantage + Yahoo Finance | Completitud: 88.9% | Confianza: 96.5%
```

## 🏗️ Arquitectura

```
┌─────────────────────────────────────┐
│       DataAggregator                │
│  (Búsqueda inteligente)             │
└─────────────────┬───────────────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
┌─────▼─────┐ ┌──▼───────┐ ┌─▼──────────┐
│  Yahoo    │ │  Alpha   │ │    FMP     │
│  Finance  │ │  Vantage │ │            │
└───────────┘ └──────────┘ └────────────┘
```

### Clases Principales

- **`DataProvider`**: Clase base abstracta para todos los proveedores
- **`FinancialData`**: Estructura de datos estandarizada
- **`YahooFinanceProvider`**: Implementación para Yahoo Finance
- **`AlphaVantageProvider`**: Implementación para Alpha Vantage
- **`FinancialModelingPrepProvider`**: Implementación para FMP
- **`DataAggregator`**: Orquestador inteligente multi-fuente

## 🔍 Ejemplo de Uso Programático

```python
from src.data_providers import DataAggregator

# Crear agregador con API keys
config = {
    'alpha_vantage': 'tu_clave',
    'fmp': 'tu_clave'
}
aggregator = DataAggregator(config)

# Obtener datos con estrategia "mejor calidad"
data = aggregator.get_financial_data(
    ticker='AAPL',
    years=5,
    strategy='best_quality'
)

# Usar los datos
if data:
    print(f"Fuente: {data.data_source}")
    print(f"Precio actual: ${data.current_price}")
    print(f"FCF: {data.calculate_fcf()}")
```

## 🐛 Troubleshooting

### "No data found"
- Verifica que el ticker sea correcto
- Prueba con diferentes estrategias
- Revisa que tus API keys sean válidas

### "Rate limit exceeded"
- Alpha Vantage: Máximo 25 requests/día (gratis)
- FMP: Máximo 250 requests/día (gratis)
- Solución: Espera hasta el día siguiente o usa Yahoo Finance

### API keys no funcionan
- Verifica que estén en `.env` o `secrets.toml`
- No compartas tus API keys en git
- Verifica que no tengan espacios o comillas extras

## 📝 Notas Importantes

1. **Yahoo Finance** siempre está disponible y no requiere configuración
2. Las API keys son **opcionales** - la app funciona sin ellas
3. Con más fuentes configuradas, mejor calidad de datos
4. Los archivos `.env` y `secrets.toml` están en `.gitignore` por seguridad
5. El sistema usa cache para evitar llamadas duplicadas

## 🔐 Seguridad

⚠️ **NUNCA** subas tus API keys a git:
- `.env` y `.streamlit/secrets.toml` están en `.gitignore`
- Usa siempre los archivos `.example` como plantilla
- No hardcodees API keys en el código

## 📚 Referencias

- [Alpha Vantage Docs](https://www.alphavantage.co/documentation/)
- [FMP API Docs](https://site.financialmodelingprep.com/developer/docs)
- [yfinance Docs](https://pypi.org/project/yfinance/)
