# Estructura del Proyecto DCF Valuation Platform

```
blog-DCF/
│
├── 📄 README.md                    # Documentación técnica completa
├── 📄 README_CEO.md                # Guía ejecutiva para CEO (¡EMPIEZA AQUÍ!)
├── 📄 PROJECT_STRUCTURE.md         # Este archivo
├── 🚀 start.sh                     # Script de inicio único
│
├── 📱 app.py                       # Aplicación principal de Streamlit
├── 📄 requirements.txt             # Dependencias de Python
│
├── 📁 pages/                       # Páginas multi-página de Streamlit
│   ├── 1_📈_Análisis_Individual.py
│   ├── 2_📊_Dashboard.py
│   ├── 3_⚖️_Comparador.py
│   └── 4_📅_Histórico.py
│
├── 📁 src/                         # Código fuente principal
│   ├── cache/                      # Sistema de caché y persistencia
│   ├── companies/                  # Gestión de catálogo de empresas
│   ├── core/                       # Funcionalidades core
│   ├── data_providers/             # Proveedores de datos financieros
│   ├── dcf/                        # Motor de cálculo DCF
│   ├── models/                     # Modelos de datos
│   ├── reports/                    # Generador de informes PDF
│   └── utils/                      # Utilidades compartidas
│
├── 📁 docs/                        # Documentación del proyecto
│   ├── MULTI_SOURCE_DATA.md       # Guía de múltiples fuentes de datos
│   └── technical/                  # Documentación técnica detallada
│       ├── ANALISIS_*.md
│       ├── ARQUITECTURA_*.md
│       ├── IMPLEMENTACION_*.md
│       └── ... (30+ documentos técnicos)
│
├── 📁 scripts/                     # Scripts auxiliares y análisis
│   ├── analysis/                   # Scripts de análisis
│   │   ├── analyze_*.py
│   │   ├── debug_*.py
│   │   ├── test_*.py
│   │   ├── validate_*.py
│   │   └── ... (20+ scripts)
│   ├── run.sh                      # Script legacy de ejecución
│   └── ... (otros scripts)
│
├── 📁 outputs/                     # Resultados generados
│   ├── pdfs/                       # Informes PDF exportados
│   │   └── .gitkeep
│   └── reports/                    # Reportes CSV y análisis
│       └── .gitkeep
│
├── 📁 data/                        # Base de datos y caché
│   ├── dcf_cache.db               # Base de datos SQLite (creado al ejecutar)
│   └── .gitkeep
│
├── 📁 tests/                       # Tests automatizados
│   ├── conftest.py
│   ├── test_dcf.py
│   ├── test_fundamentals.py
│   ├── test_report_calculations.py
│   └── test_sensitivity_analysis.py
│
└── 📁 .venv/                       # Entorno virtual de Python (ignorado en Git)
```

## Archivos de Configuración

- `.env` - Variables de entorno (API keys)
- `.env.example` - Plantilla para variables de entorno
- `.gitignore` - Archivos ignorados por Git
- `.pre-commit-config.yaml` - Hooks de pre-commit

## Guía de Navegación

### Para el CEO (No técnico)
1. Lee primero: [README_CEO.md](README_CEO.md)
2. Ejecuta: `./start.sh`
3. Accede: `http://localhost:8501`

### Para Desarrolladores
1. Lee primero: [README.md](README.md)
2. Revisa: [docs/MULTI_SOURCE_DATA.md](docs/MULTI_SOURCE_DATA.md)
3. Explora: `docs/technical/` para detalles de implementación

### Para QA/Testing
1. Revisa: `tests/` - Tests automatizados
2. Ejecuta: `scripts/analysis/` - Scripts de validación
3. Analiza: `outputs/` - Resultados generados

## Flujo de Trabajo

```
Usuario → start.sh → app.py → pages/ → src/ → outputs/
                                 ↓
                              data/dcf_cache.db
```

## Comandos Rápidos

```bash
# Iniciar aplicación
./start.sh

# Instalar dependencias
./start.sh install

# Detener aplicación
./start.sh stop

# Ver ayuda
./start.sh help
```

## Notas Importantes

- **NO editar** archivos en `.venv/` (generado automáticamente)
- **NO commitear** archivos `.env` (contiene API keys)
- **NO commitear** archivos en `outputs/` (resultados generados)
- **NO commitear** archivos `.db` (bases de datos locales)
