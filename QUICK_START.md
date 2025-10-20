# Inicio Rápido - DCF Valuation Platform

## ¡En solo 3 pasos!

### Paso 1: Dar permisos al script
```bash
chmod +x start.sh
```

### Paso 2: Instalar (solo la primera vez)
```bash
./start.sh install
```

### Paso 3: ¡Ejecutar!
```bash
./start.sh
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

---

## ¿Qué puedo hacer?

### 📈 Análisis Individual
Valora una empresa específica (ej: AAPL, GOOGL, MSFT)

### 📊 Dashboard
Ve todas tus valoraciones en un solo lugar

### ⚖️ Comparador
Compara hasta 5 empresas lado a lado

### 📅 Histórico
Ve la evolución del precio vs valor justo

---

## Ejemplo Práctico

1. **Selecciona "Análisis Individual"** en el menú lateral
2. **Ingresa un ticker**: `AAPL`
3. **Presiona "Calcular"**
4. **Resultado**: Verás si Apple está sobrevaluada o infravalorada
5. **Descarga el informe PDF** con un solo clic

---

## Comandos Útiles

```bash
./start.sh          # Iniciar la aplicación
./start.sh install  # Instalar dependencias
./start.sh stop     # Detener la aplicación
./start.sh help     # Ver ayuda
```

---

## ¿Necesitas ayuda?

- **Guía Ejecutiva**: [README_CEO.md](README_CEO.md)
- **Documentación Completa**: [README.md](README.md)
- **Estructura del Proyecto**: [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

---

## Solución de Problemas Comunes

### "Python no encontrado"
```bash
# Instala Python 3.11+
sudo apt install python3.11  # Ubuntu/Debian
brew install python@3.11     # macOS
```

### "Puerto en uso"
```bash
./start.sh stop  # Detiene todos los procesos
./start.sh       # Reinicia la aplicación
```

### "No se encuentran datos"
- Verifica tu conexión a internet
- Asegúrate de usar tickers válidos (ej: AAPL, MSFT, GOOGL)
- Algunos tickers internacionales requieren sufijo (ej: SAP.DE)

---

**¡Listo para usar! 🚀**
