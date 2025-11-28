# DCF Platform - Flask Version

## 🎯 Migración Completa: Streamlit → Flask

Este proyecto ha sido completamente refactorizado eliminando **Streamlit** y migrando a **Flask** con menú funcional, manteniendo toda la funcionalidad del modelo financiero DCF.

## ✨ Características Principales

### 🏦 Branding Santander
- Logo del Banco Santander en la página principal
- Mensaje de bienvenida: "Bienvenidos, amigos del Banco Santander"
- Paleta de colores profesional: Cream (#FFFADC) y Lime Greens

### 📊 Modelo Financiero Verificado
El modelo DCF ha sido auditado y es matemáticamente consistente:
- **DCF Core**: Gordon Growth Model con mid-year convention
- **WACC**: Cálculo dinámico con CAPM y datos de Damodaran
- **Validaciones**: Spread (r-g) > 2% para evitar valuaciones explosivas
- **Tasas de crecimiento**: Escalonadas basadas en volatilidad histórica

### 🎨 Mejoras Estéticas
- **Diseño moderno**: CSS mejorado con variables, gradientes y animaciones
- **Fuentes personalizadas**: TT Gertika (títulos) y Roboto (texto)
- **Responsive**: Menú hamburguesa para móviles
- **Iconos**: Font Awesome 6.4.0
- **Gráficos**: Plotly interactivos

### 🧭 Menú de Navegación Funcional
- **Home**: Página principal con logo de Santander
- **Análisis**: Valoración DCF individual de empresas
- **Dashboard**: Vista consolidada de empresas analizadas
- **Comparador**: Comparación lado a lado de múltiples empresas
- **Histórico**: Evolución temporal de Market Price vs Fair Value
- **Alertas**: Sistema de notificaciones de precio

## 🚀 Instalación y Ejecución

### 1. Instalar Dependencias

```bash
pip install -r requirements-flask.txt
```

### 2. Ejecutar la Aplicación

```bash
python flask_app.py
```

La aplicación estará disponible en: **http://localhost:8501**

### 3. Producción (con Gunicorn)

```bash
gunicorn -w 4 -b 0.0.0.0:8501 flask_app:app
```

## 📁 Estructura de Archivos

```
blog-DCF/
├── flask_app.py                    # Aplicación Flask principal
├── templates/                      # Templates Jinja2
│   ├── base.html                   # Template base con menú
│   ├── home.html                   # Página principal (Santander)
│   ├── analisis.html               # Análisis DCF
│   ├── dashboard.html              # Dashboard ejecutivo
│   ├── comparador.html             # Comparador de empresas
│   ├── historico.html              # Gráfico histórico
│   ├── alertas.html                # Sistema de alertas
│   ├── 404.html                    # Página de error 404
│   └── 500.html                    # Página de error 500
├── assets/                         # Archivos estáticos
│   ├── style.css                   # CSS mejorado
│   └── santander-logo.svg          # Logo de Santander
├── pages/                          # Lógica de negocio
│   ├── analysis_logic.py           # Lógica de análisis DCF
│   ├── comparison_logic.py         # Lógica de comparación
│   └── historical_logic.py         # Lógica de históricos
├── src/                            # Módulos core (sin cambios)
│   ├── dcf/                        # Motor DCF
│   ├── data_providers/             # Agregador de datos
│   ├── reports/                    # Generación de reportes
│   └── ...
├── requirements-flask.txt          # Dependencias Flask
└── README_FLASK.md                 # Este archivo
```

## 🎯 Diferencias vs Streamlit

| Aspecto | Streamlit (Anterior) | Flask (Actual) |
|---------|---------------------|----------------|
| **Framework** | Streamlit | Flask + Jinja2 |
| **Menú** | Sidebar con emojis | Navbar superior funcional |
| **Navegación** | JavaScript + hacks | Rutas Flask nativas |
| **Templates** | st.markdown() | Jinja2 templates |
| **Estado** | st.session_state | Flask session/cache |
| **CSS** | Inyectado con st.markdown() | Archivo CSS dedicado |
| **Flexibilidad** | Limitada por Streamlit | Total control |
| **Performance** | Reruns completos | Renderizado selectivo |

## 📊 Rutas de la Aplicación

| Ruta | Método | Descripción |
|------|--------|-------------|
| `/` | GET | Página principal (Home) |
| `/analisis` | GET, POST | Análisis DCF individual |
| `/dashboard` | GET | Dashboard ejecutivo |
| `/comparador` | GET, POST | Comparador de empresas |
| `/historico` | GET | Gráfico histórico |
| `/alertas` | GET, POST | Sistema de alertas |
| `/api/company/<ticker>` | GET | API: datos de empresa |
| `/api/dcf-calculate` | POST | API: cálculo DCF |

## 🧮 Fórmulas Matemáticas

### DCF Core
```
PV = Σ(FCF_t / (1 + r)^(t - 0.5)) + TV / (1 + r)^(n - 0.5)
TV = FCF_n × (1 + g) / (r - g)
```

### WACC
```
WACC = (E/V) × R_e + (D/V) × R_d × (1 - T_c)
```

### CAPM (Cost of Equity)
```
R_e = R_f + β × (R_m - R_f)
```

### Equity Value
```
Equity Value = Enterprise Value + Cash - Debt
```

## 🎨 Paleta de Colores

```css
--cream: #FFFADC
--lime-light: #B8E986
--lime-medium: #9ED85C
--lime-dark: #7AB83A
--black: #000000
--santander-red: #EC0000
```

## 📝 Notas de Migración

### Eliminado
- ❌ Streamlit (completo)
- ❌ st.session_state
- ❌ st.sidebar
- ❌ st.columns
- ❌ st.tabs
- ❌ @st.cache_resource

### Añadido
- ✅ Flask routing
- ✅ Jinja2 templates
- ✅ CSS profesional
- ✅ Menú navbar funcional
- ✅ Logo de Santander
- ✅ Mensaje de bienvenida

### Mantenido (sin cambios)
- ✅ Modelo DCF core
- ✅ WACC calculator
- ✅ Data aggregator
- ✅ Plotly charts
- ✅ Report generators
- ✅ Cache SQLite
- ✅ Alert manager

## 🚨 Importante

- El puerto por defecto es **8501** (mismo que Streamlit) para facilitar la transición
- Los gráficos Plotly se renderizan con `include_plotlyjs=False` para reducir tamaño
- El logo de Santander está en formato SVG para máxima calidad
- Las fuentes TT Gertika y Roboto deben estar en sus carpetas respectivas

## 🔮 Próximos Pasos

1. **Testing**: Probar todas las rutas y funcionalidades
2. **Optimización**: Cachear resultados DCF con Flask-Caching
3. **Autenticación**: Añadir login para usuarios del Banco Santander
4. **Base de datos**: Migrar cache SQLite a PostgreSQL
5. **Deploy**: Configurar Docker y deploy en producción

## 📧 Contacto

Para dudas o sugerencias sobre esta migración, contacta al equipo de desarrollo.

---

**© 2024 DCF Platform - Banco Santander**

*Esta plataforma es una herramienta de análisis financiero. Las valoraciones son estimaciones y no constituyen asesoramiento de inversión.*
