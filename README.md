# DCF Valuation Platform 📊


Plataforma profesional de valoración de empresas mediante **Discounted Cash Flow (DCF)** que permite:

1. **Calcular Fair Value** de acciones mediante modelo DCF
2. **Comparar con precio de mercado** en tiempo real
3. **Visualizar evolución histórica** Fair Value vs Precio
4. **Generar informes PDF** profesionales

## 🆕 Nuevas Funcionalidades (Oct 2025)

- 🎯 **Análisis de Escenarios**: Pesimista/Base/Optimista con recomendación ajustada por riesgo
- 🔔 **Sistema de Alertas**: Notificaciones automáticas cuando se cumplen condiciones
- 📥 **Exportación a Excel**: Reportes profesionales multi-hoja con fórmulas
- 📊 **Dashboard Ejecutivo**: KPIs, gráficos interactivos, Top 5 oportunidades
- 🎨 **Gráficos Mejorados**: Waterfall DCF, Heatmap animado, exportación PNG/SVG/HTML
- ⚡ **WACC Dinámico**: Beta ajustado (Blume), Hamada, risk-free rate actualizado, country risk premium
- 📄 **Executive PDF**: Cover page de 1-min, gráficos vectoriales, branding, comparación S&P 500

Ver: [FEATURES_IMPLEMENTED](docs/FEATURES_IMPLEMENTED.md) | [ANALISIS_ESCENARIOS](IMPLEMENTACION_ANALISIS_ESCENARIOS.md) | [GRAFICOS_MEJORADOS](docs/GRAFICOS_INTERACTIVOS_MEJORADOS.md) | [WACC_DINAMICO](docs/WACC_DINAMICO_IMPLEMENTADO.md) | [EXECUTIVE_PDF](EXECUTIVE_PDF_RESUMEN.txt)

## Documentación Rápida

- 📘 [README_CEO.md](README_CEO.md) - Guía ejecutiva para no técnicos
- 🚀 [QUICK_START.md](QUICK_START.md) - Inicio en 3 pasos
- 📁 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) - Estructura del proyecto
- 📚 [docs/MULTI_SOURCE_DATA.md](docs/MULTI_SOURCE_DATA.md) - Guía de fuentes de datos
- 🔧 [docs/technical/](docs/technical/) - Documentación técnica detallada

## 🚀 Características

### 📈 Análisis Individual
- Cálculo DCF con inputs manuales o **búsqueda inteligente multi-fuente**
- **3 modos de datos**: Manual, Autocompletar (Yahoo), Multi-fuente (varios APIs)
- **Estrategias de búsqueda**: Mejor calidad, Primera disponible, Combinar fuentes
- **🎯 Análisis de Escenarios**: Pesimista/Base/Optimista con recomendación ajustada por riesgo
- **Valor ponderado por probabilidad** (25%/50%/25%)
- **Recomendaciones inteligentes**: STRONG BUY/BUY/HOLD/SELL/STRONG SELL con confianza
- Métricas clave: Enterprise Value, Fair Value por acción, Upside/Downside, Risk/Reward Ratio
- Desglose detallado de flujos de caja proyectados
- Gráficos interactivos con Plotly (incluyendo rango de valoración)
- Comparación histórica Fair Value vs Precio de Mercado

### 📊 Dashboard
- Vista consolidada de todas las empresas analizadas
- Métricas agregadas y recomendaciones (Comprar/Mantener/Vender)
- Tabla resumen con señales de trading

### ⚖️ Comparador
- Comparación lado a lado de múltiples empresas
- Gráficos comparativos de valoración y upside

### 📅 Histórico
- Evolución temporal del Fair Value vs Precio
- Análisis de tendencias y estadísticas históricas
- Gráficos de upside/downside en el tiempo

### 📄 Informes PDF
- Generación automática de informes profesionales
- Resumen ejecutivo con recomendación
- Desglose completo del modelo DCF
- Disclaimer legal incluido

### 💾 Caché Persistente
- Base de datos SQLite para guardar cálculos históricos
- Optimización de consultas con índices
- Persistencia de precios y valoraciones

## 🛠️ Requisitos

- Python 3.11 o 3.12
- Git

## 📦 Instalación

### 1. Clonar y navegar al proyecto

```bash
cd /home/mateo/blog-DCF
```

### 2. Crear y activar entorno virtual

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
```

### 3. Instalar dependencias

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### 4. Configurar APIs (Opcional pero recomendado)

Para usar el modo **Multi-fuente** con mejor calidad de datos:

```bash
# Opción A: Variables de entorno
cp .env.example .env
# Edita .env y agrega tus API keys

# Opción B: Streamlit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edita secrets.toml y agrega tus API keys
```

**Obtener API keys gratuitas:**
- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key (25 req/día)
- **Financial Modeling Prep**: https://site.financialmodelingprep.com/developer/docs (250 req/día)

📚 Ver guía completa: [docs/MULTI_SOURCE_DATA.md](docs/MULTI_SOURCE_DATA.md)

## 🚀 Ejecución

### Método Recomendado: Script único

```bash
# Solo la primera vez
chmod +x start.sh
./start.sh install

# Cada vez que quieras usar la aplicación
./start.sh
```

### Método Alternativo: Comando directo

```bash
source .venv/bin/activate
streamlit run app.py
```

La aplicación se abrirá en `http://localhost:8501`

### Otros comandos útiles

```bash
./start.sh stop     # Detener la aplicación
./start.sh help     # Ver ayuda
```

## 📖 Uso

### 1️⃣ Análisis Individual

1. Ingresa un ticker (ej: AAPL, GOOGL, MSFT)
2. Configura parámetros DCF:
   - **Modo**: Manual, Autocompletar (Yahoo Finance), o **Multi-fuente** (búsqueda inteligente)
   - **Estrategia** (si usas Multi-fuente): Mejor calidad, Primera disponible, o Combinar fuentes
   - **Tasa de descuento (r)**: Típicamente 8-15%
   - **Crecimiento terminal (g)**: Típicamente 2-3%
   - **Shares outstanding**: Dejar en 0 para autocompletar
3. Revisa los resultados:
   - Fair Value calculado
   - **Métricas de calidad** (fuente, completitud, confianza)
   - Comparación con precio de mercado
   - Upside/Downside potencial
4. Exporta:
   - 💾 Guarda en base de datos para histórico
   - 📥 Descarga informe PDF profesional

### 2️⃣ Dashboard

- Visualiza resumen de todas las empresas analizadas
- Identifica oportunidades (🟢 Comprar, 🟡 Mantener, 🔴 Vender)

### 3️⃣ Comparador

- Selecciona hasta 5 empresas
- Compara Fair Value vs Precio de mercado
- Analiza upside relativo entre empresas

### 4️⃣ Histórico

- Selecciona una empresa
- Visualiza evolución temporal del Fair Value
- Analiza tendencias y estadísticas

## 🗂️ Estructura del Proyecto

```
blog-DCF/
├── app.py                          # Página principal (landing)
├── pages/                          # Páginas multipágina Streamlit
│   ├── 1_📈_Análisis_Individual.py
│   ├── 2_📊_Dashboard.py
│   ├── 3_⚖️_Comparador.py
│   └── 4_📅_Histórico.py
├── src/
│   ├── dcf/
│   │   ├── model.py               # Modelo DCF core
│   │   └── fundamentals.py        # Normalización de datos
│   ├── data_providers/            # 🆕 Sistema multi-fuente
│   │   ├── base.py                # Clases base y FinancialData
│   │   ├── yahoo_provider.py      # Yahoo Finance provider
│   │   ├── alpha_vantage_provider.py  # Alpha Vantage provider
│   │   ├── fmp_provider.py        # Financial Modeling Prep provider
│   │   └── aggregator.py          # Búsqueda inteligente multi-fuente
│   ├── cache/
│   │   └── db.py                  # Sistema de caché SQLite
│   └── reports/
│       └── pdf_generator.py       # Generador de informes PDF
├── data/
│   └── dcf_cache.db               # Base de datos SQLite (creada automáticamente)
├── tests/                         # Tests unitarios
├── requirements.txt               # Dependencias Python
└── README.md                      # Este archivo
```

## 📊 Tecnologías Utilizadas

- **Streamlit**: Framework web interactivo
- **yfinance**: Datos financieros de Yahoo Finance
- **Alpha Vantage API**: Datos fundamentales de alta calidad
- **Financial Modeling Prep API**: Estados financieros detallados
- **Plotly**: Gráficos interactivos profesionales
- **SQLite**: Base de datos persistente local
- **ReportLab**: Generación de informes PDF
- **Pandas/NumPy**: Procesamiento de datos
- **Requests**: Cliente HTTP para APIs REST

## 🎯 Metodología DCF

El modelo utiliza **Discounted Cash Flow (DCF)** para estimar el valor intrínseco:

1. **Proyección de Free Cash Flows** (FCF) futuros
2. **Descuento a valor presente** usando tasa de descuento `r`
3. **Valor terminal** usando Gordon Growth Model: `TV = FCF_N × (1+g) / (r-g)`
4. **Fair Value = Σ(FCF descontados) + Valor Terminal descontado**

### Fórmulas clave:

```
PV(FCF_i) = FCF_i / (1 + r)^i

Terminal Value = FCF_N × (1 + g) / (r - g)

Enterprise Value = Σ PV(FCF_i) + PV(Terminal Value)

Fair Value por acción = Enterprise Value / Shares Outstanding
```

## ⚠️ Disclaimer

**Este software es solo para fines educativos e informativos.** No constituye asesoramiento financiero ni recomendación de inversión. Las valoraciones son estimaciones basadas en supuestos que pueden no materializarse. Consulte con un asesor financiero profesional antes de tomar decisiones de inversión.

## 🐛 Troubleshooting

### Error: "No module named 'reportlab'"

```bash
pip install reportlab
```

### Error: "No se encontraron datos para ticker"

- Verifica que el ticker sea válido en Yahoo Finance
- Algunos tickers internacionales requieren sufijo (ej: `SAP.DE`)

### La base de datos no se crea

- Verifica permisos de escritura en la carpeta `data/`
- La carpeta se crea automáticamente al primer uso

## 🔮 Próximas Mejoras

- [x] ✅ Múltiples fuentes de datos (Alpha Vantage, Financial Modeling Prep)
- [x] ✅ Búsqueda inteligente con estrategias (mejor calidad, merge, fallback)
- [ ] Cálculo automático de WACC
- [ ] Proyecciones inteligentes basadas en histórico
- [ ] Análisis de sensibilidad (heat maps r vs g)
- [ ] Escenarios múltiples (pesimista/base/optimista)
- [ ] Comparación con múltiplos (P/E, EV/EBITDA)
- [ ] Notificaciones de oportunidades
- [ ] Export a Excel

## 📄 Licencia

Este proyecto es de código abierto para uso educativo.

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea un branch para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

**Hecho con ❤️ usando Streamlit, Plotly y Python**
