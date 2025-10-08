# DCF Valuation Platform 📊

Plataforma profesional de valoración de empresas mediante **Discounted Cash Flow (DCF)** que permite:

1. **Calcular Fair Value** de acciones mediante modelo DCF
2. **Comparar con precio de mercado** en tiempo real
3. **Visualizar evolución histórica** Fair Value vs Precio
4. **Generar informes PDF** profesionales

## 🚀 Características

### 📈 Análisis Individual
- Cálculo DCF con inputs manuales o autocompletado desde Yahoo Finance
- Métricas clave: Enterprise Value, Fair Value por acción, Upside/Downside
- Desglose detallado de flujos de caja proyectados
- Gráficos interactivos con Plotly
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

## 🚀 Ejecución

### Método 1: Comando directo

```bash
source .venv/bin/activate
streamlit run app.py
```

### Método 2: Task de VS Code

1. `Ctrl+Shift+P` → "Tasks: Run Task"
2. Seleccionar "Streamlit: Run app.py"

La aplicación se abrirá en `http://localhost:8501`

## 📖 Uso

### 1️⃣ Análisis Individual

1. Ingresa un ticker (ej: AAPL, GOOGL, MSFT)
2. Configura parámetros DCF:
   - **Modo**: Manual o Autocompletar (desde Yahoo Finance)
   - **Tasa de descuento (r)**: Típicamente 8-15%
   - **Crecimiento terminal (g)**: Típicamente 2-3%
   - **Shares outstanding**: Dejar en 0 para autocompletar
3. Revisa los resultados:
   - Fair Value calculado
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
- **Plotly**: Gráficos interactivos profesionales
- **SQLite**: Base de datos persistente local
- **ReportLab**: Generación de informes PDF
- **Pandas/NumPy**: Procesamiento de datos

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

- [ ] Múltiples fuentes de datos (Alpha Vantage, Financial Modeling Prep)
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
