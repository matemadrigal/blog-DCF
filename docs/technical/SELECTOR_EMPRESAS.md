# 🔍 Selector de Empresas con Filtros

## Resumen

Se ha implementado un sistema avanzado de selección de empresas que permite elegir compañías del S&P 500 usando múltiples filtros:

- ✅ **Búsqueda por texto** (ticker, nombre, sector)
- ✅ **Filtro alfabético** (A-Z)
- ✅ **Filtro por sector** (Technology, Healthcare, Financial Services, etc.)
- ✅ **Ordenamiento por FCF** (más alto/más bajo)
- ✅ **Sistema de caché** para FCF (evita recalcular constantemente)

---

## 🎯 Características

### 1. Dos Modos de Selección

**Modo 1: Búsqueda Manual**
- Input de texto tradicional
- Rápido para usuarios que conocen el ticker
- Ejemplo: `AAPL`, `MSFT`, `GOOGL`

**Modo 2: Lista con Filtros**
- Lista desplegable con todas las empresas
- Múltiples filtros combinables
- Muestra FCF del año base junto al nombre

---

## 📋 Filtros Disponibles

### 1. Búsqueda por Texto 🔍
Busca en:
- **Ticker**: `AAPL`
- **Nombre**: `Apple`, `Microsoft`
- **Sector**: `Technology`, `Healthcare`

**Ejemplo**: Buscar "tech" encontrará todas las empresas de tecnología.

### 2. Filtro por Sector
Sectores disponibles:
- Technology
- Financial Services
- Healthcare
- Consumer Goods
- Consumer/Retail
- Communication Services
- Industrial
- Energy
- Automotive/Technology
- Y más...

**Ejemplo**: Seleccionar "Healthcare" mostrará solo empresas farmacéuticas y de salud.

### 3. Filtro Alfabético (A-Z)
Filtra empresas por la primera letra del ticker.

**Ejemplo**: Seleccionar "M" mostrará: `MSFT`, `META`, `MA`, `MCD`, `MRK`, etc.

### 4. Ordenamiento por FCF
Tres opciones:
- **Sin ordenar**: Orden alfabético por ticker
- **FCF más alto**: Empresas con mayor Free Cash Flow primero
- **FCF más bajo**: Empresas con menor Free Cash Flow primero

**Nota**: Requiere hacer clic en "🔄 Actualizar FCF" primero.

---

## 🚀 Cómo Usar

### Paso 1: Seleccionar Modo

En la barra lateral, elige entre:
- **Búsqueda manual**: Ingresas el ticker directamente
- **Lista con filtros**: Usas los filtros para encontrar la empresa

### Paso 2: Aplicar Filtros (Modo Lista)

1. **Búsqueda rápida**: Escribe en el campo "🔍 Buscar"
2. **Filtrar por sector**: Elige un sector del dropdown
3. **Filtrar por letra**: Selecciona una letra inicial
4. **Ordenar por FCF**:
   - Elige "FCF más alto" o "FCF más bajo"
   - Haz clic en "🔄 Actualizar FCF de empresas filtradas"
   - Espera a que se escaneen las empresas
   - La lista se ordenará automáticamente

### Paso 3: Seleccionar Empresa

Elige la empresa del dropdown "Selecciona empresa".

**Formato de visualización**:
```
AAPL - Apple Inc. (FCF: $108.8B)
MSFT - Microsoft Corporation (FCF: $71.6B)
GOOGL - Alphabet Inc. (Google) (FCF: $72.8B)
```

---

## 💾 Sistema de Caché

### ¿Qué es?

El FCF scanner almacena los resultados de FCF en un archivo `.fcf_cache.json` para evitar:
- Recalcular el mismo FCF múltiples veces
- Hacer peticiones innecesarias a Yahoo Finance
- Ralentizar la aplicación

### ¿Cuánto dura el caché?

- **Duración**: 24 horas
- **Ubicación**: Archivo `.fcf_cache.json` en la raíz del proyecto
- **Formato**:
```json
{
  "AAPL": {
    "base_fcf": 108810000000,
    "error": null,
    "timestamp": "2025-10-08T12:34:56"
  },
  "MSFT": {
    "base_fcf": 71610000000,
    "error": null,
    "timestamp": "2025-10-08T12:35:01"
  }
}
```

### ¿Cuándo se actualiza?

El caché se actualiza cuando:
1. Haces clic en "🔄 Actualizar FCF"
2. Han pasado más de 24 horas desde la última consulta
3. El ticker no está en caché

---

## 📊 Empresas Disponibles

La base de datos incluye **60 empresas** del S&P 500:

### Por Sector (Top 5):

**Technology (14 empresas)**
- AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, AVGO, ORCL, ADBE, CRM, CSCO, AMD, INTC, IBM

**Financial Services (10 empresas)**
- BRK.B, JPM, V, MA, BAC, WFC, GS, MS, BLK, C

**Healthcare (10 empresas)**
- LLY, UNH, JNJ, ABBV, MRK, PFE, TMO, ABT, DHR, CVS

**Consumer (10 empresas)**
- WMT, HD, PG, KO, PEP, COST, MCD, NKE, SBUX, TGT

**Communication Services (5 empresas)**
- NFLX, DIS, CMCSA, T, VZ

---

## 🔧 Arquitectura Técnica

### Archivos Creados

| Archivo | Descripción |
|---------|-------------|
| `src/companies/__init__.py` | Módulo principal de empresas |
| `src/companies/company_list.py` | Lista de empresas S&P 500 con metadata |
| `src/companies/fcf_scanner.py` | Scanner de FCF con caché |
| `test_company_selector.py` | Test suite completo |

### Funciones Principales

**company_list.py**:
```python
get_sp500_companies()      # Obtener todas las empresas
get_company_info(ticker)   # Info de una empresa
search_companies(query)    # Buscar por texto
get_all_sectors()          # Lista de sectores
get_companies_by_sector()  # Filtrar por sector
```

**fcf_scanner.py**:
```python
get_base_fcf(ticker)       # Obtener FCF con caché
scan_companies(tickers)    # Escanear múltiples empresas
get_cached_fcf(ticker)     # Solo leer caché (fast)
clear_cache()              # Limpiar caché
```

---

## 📈 Ejemplo de Uso Completo

### Escenario: Encontrar la empresa tecnológica con mayor FCF

**Paso 1**: Seleccionar "Lista con filtros"

**Paso 2**: Aplicar filtros
- Sector: `Technology`
- Ordenar por FCF: `FCF más alto`

**Paso 3**: Hacer clic en "🔄 Actualizar FCF de empresas filtradas"

**Resultado** (ordenado por FCF):
```
1. AAPL   - Apple Inc.                - FCF: $108.81B
2. GOOGL  - Alphabet Inc. (Google)    - FCF: $72.76B
3. MSFT   - Microsoft Corporation     - FCF: $71.61B
4. NVDA   - NVIDIA Corporation        - FCF: $60.85B
5. META   - Meta Platforms Inc.       - FCF: $XX.XXB
...
```

**Paso 4**: Seleccionar `AAPL - Apple Inc. (FCF: $108.81B)`

---

## 🎨 Interfaz de Usuario

### Vista en Sidebar

```
┌─────────────────────────────────────┐
│ Selección de Empresa                │
├─────────────────────────────────────┤
│ ◉ Búsqueda manual                   │
│ ○ Lista con filtros                 │
├─────────────────────────────────────┤
│ Filtros                             │
│                                     │
│ 🔍 Buscar: [tech_________]         │
│                                     │
│ Sector: [Technology ▼]             │
│                                     │
│ Letra inicial: [T ▼]               │
│                                     │
│ Ordenar por FCF: [FCF más alto ▼]  │
│                                     │
│ [🔄 Actualizar FCF de empresas]    │
│                                     │
│ ✅ 14 empresas escaneadas           │
│                                     │
│ 5 empresas encontradas              │
│                                     │
│ Selecciona empresa:                 │
│ [TSLA - Tesla Inc. (FCF: $3.58B) ▼]│
├─────────────────────────────────────┤
│ Parámetros DCF                      │
│ ...                                 │
└─────────────────────────────────────┘
```

---

## ⚡ Performance

### Tiempos de Respuesta

| Operación | Sin Caché | Con Caché |
|-----------|-----------|-----------|
| Obtener 1 FCF | ~2s | <0.01s |
| Escanear 10 empresas | ~20s | ~0.1s |
| Escanear 60 empresas | ~2min | ~0.5s |

### Recomendaciones

1. **Primera vez**: Escanea solo las empresas que necesites (usa filtros)
2. **Días siguientes**: El caché hará todo instantáneo
3. **Actualización**: Vuelve a escanear cada 24 horas o cuando quieras datos frescos

---

## 🧪 Testing

**Ejecutar tests**:
```bash
python3 test_company_selector.py
```

**Tests incluidos**:
- ✅ Cargar 60 empresas del S&P 500
- ✅ Obtener 13 sectores únicos
- ✅ Buscar empresas por texto
- ✅ Filtrar por letra inicial
- ✅ Filtrar por sector
- ✅ Escanear FCF de 3 empresas
- ✅ Verificar caché funciona
- ✅ Ordenar por FCF (más alto)

**Resultado esperado**:
```
======================================================================
TEST: Sorting by FCF
======================================================================

Companies sorted by FCF (highest first):
1. AAPL   - Apple Inc.                     - FCF: $108.81B
2. GOOGL  - Alphabet Inc. (Google)         - FCF: $72.76B
3. MSFT   - Microsoft Corporation          - FCF: $71.61B
4. NVDA   - NVIDIA Corporation             - FCF: $60.85B
5. TSLA   - Tesla Inc.                     - FCF: $3.58B

======================================================================
All tests completed successfully!
======================================================================
```

---

## 🚧 Limitaciones Conocidas

1. **Lista fija de empresas**: Solo 60 empresas del S&P 500
   - **Solución futura**: Integrar con API para obtener lista completa dinámica

2. **Escaneo lento sin caché**: Primera vez puede tardar 1-2 minutos
   - **Solución**: Usa filtros para reducir el número de empresas a escanear

3. **FCF puede estar desactualizado**: Depende de Yahoo Finance
   - **Solución**: Actualizar caché periódicamente

---

## 🔮 Mejoras Futuras

### Versión 2.0 (Planeado)

- [ ] Añadir todas las empresas del S&P 500 (500+)
- [ ] Filtro por capitalización de mercado
- [ ] Filtro por ratio P/E
- [ ] Escaneo en background (no bloquear UI)
- [ ] Exportar lista filtrada a CSV
- [ ] Comparar múltiples empresas lado a lado
- [ ] Gráfico de distribución de FCF por sector

---

## 📞 Soporte

**Si encuentras problemas**:

1. **Error "No se encontraron datos"**: Verifica que el ticker existe en Yahoo Finance
2. **Escaneo muy lento**: Reduce el número de empresas con filtros
3. **Caché no funciona**: Verifica permisos de escritura en `.fcf_cache.json`
4. **Empresa no aparece**: Puede que no esté en nuestra lista de 60 empresas

---

## 📚 Resumen

**Antes**: Solo podías ingresar el ticker manualmente

**Después**:
- ✅ Lista de 60 empresas del S&P 500
- ✅ 4 tipos de filtros combinables
- ✅ Ordenamiento por FCF
- ✅ Sistema de caché (24h)
- ✅ Búsqueda inteligente por texto

**Resultado**: Encuentra la empresa perfecta para analizar en segundos.
