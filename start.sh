#!/bin/bash

# =============================================================================
# DCF Valuation Platform - Script de Inicio Único
# =============================================================================
# Uso:
#   ./start.sh           - Inicia la aplicación
#   ./start.sh install   - Instala/actualiza dependencias
#   ./start.sh stop      - Detiene todos los procesos
#   ./start.sh help      - Muestra ayuda
# =============================================================================

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directorio del proyecto
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
APP_FILE="$PROJECT_DIR/app.py"
PORT=8501

# =============================================================================
# Funciones de utilidad
# =============================================================================

print_header() {
    echo -e "${BLUE}"
    echo "=========================================="
    echo "  DCF Valuation Platform"
    echo "=========================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# =============================================================================
# Función: Verificar Python
# =============================================================================

check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 11 ]; then
            print_success "Python $PYTHON_VERSION encontrado"
            return 0
        else
            print_error "Python 3.11 o superior requerido (encontrado: $PYTHON_VERSION)"
            return 1
        fi
    else
        print_error "Python 3 no está instalado"
        return 1
    fi
}

# =============================================================================
# Función: Crear entorno virtual
# =============================================================================

create_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creando entorno virtual..."
        python3 -m venv "$VENV_DIR"
        print_success "Entorno virtual creado"
    else
        print_success "Entorno virtual ya existe"
    fi
}

# =============================================================================
# Función: Activar entorno virtual
# =============================================================================

activate_venv() {
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "Entorno virtual activado"
    else
        print_error "No se pudo encontrar el entorno virtual"
        return 1
    fi
}

# =============================================================================
# Función: Instalar dependencias
# =============================================================================

install_dependencies() {
    print_info "Instalando/actualizando dependencias..."

    # Upgrade pip
    pip install --upgrade pip setuptools wheel --quiet

    # Instalar requirements
    if [ -f "$PROJECT_DIR/requirements.txt" ]; then
        pip install -r "$PROJECT_DIR/requirements.txt" --quiet
        print_success "Dependencias instaladas correctamente"
    else
        print_error "No se encontró requirements.txt"
        return 1
    fi
}

# =============================================================================
# Función: Verificar si el puerto está en uso
# =============================================================================

check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Puerto en uso
    else
        return 1  # Puerto libre
    fi
}

# =============================================================================
# Función: Detener procesos existentes
# =============================================================================

stop_processes() {
    print_info "Buscando procesos de Streamlit..."

    # Buscar procesos en el puerto específico
    if check_port; then
        print_info "Deteniendo proceso en puerto $PORT..."
        PID=$(lsof -ti :$PORT)
        kill -9 $PID 2>/dev/null || true
        sleep 2
        print_success "Proceso detenido"
    fi

    # Buscar cualquier proceso de streamlit
    if pgrep -f "streamlit run" > /dev/null 2>&1; then
        print_info "Deteniendo otros procesos de Streamlit..."
        pkill -f "streamlit run" 2>/dev/null || true
        sleep 2
        print_success "Procesos de Streamlit detenidos"
    else
        print_info "No hay procesos de Streamlit ejecutándose"
    fi
}

# =============================================================================
# Función: Iniciar la aplicación
# =============================================================================

start_app() {
    print_header

    # Verificar Python
    check_python || exit 1

    # Crear y activar entorno virtual
    create_venv
    activate_venv || exit 1

    # Verificar si las dependencias están instaladas
    if ! pip show streamlit &> /dev/null; then
        print_info "Streamlit no está instalado. Instalando dependencias..."
        install_dependencies || exit 1
    fi

    # Detener procesos existentes
    stop_processes

    # Verificar que el archivo principal existe
    if [ ! -f "$APP_FILE" ]; then
        print_error "No se encontró app.py en $PROJECT_DIR"
        exit 1
    fi

    # Iniciar Streamlit
    print_info "Iniciando DCF Valuation Platform..."
    echo ""
    print_success "Aplicación iniciada!"
    print_info "Accede en tu navegador: ${BLUE}http://localhost:$PORT${NC}"
    echo ""
    echo -e "${YELLOW}Presiona Ctrl+C para detener la aplicación${NC}"
    echo ""

    cd "$PROJECT_DIR"
    streamlit run "$APP_FILE" --server.port=$PORT
}

# =============================================================================
# Función: Modo instalación
# =============================================================================

install_mode() {
    print_header
    print_info "Modo de instalación"
    echo ""

    check_python || exit 1
    create_venv
    activate_venv || exit 1
    install_dependencies || exit 1

    echo ""
    print_success "¡Instalación completada!"
    print_info "Ejecuta './start.sh' para iniciar la aplicación"
}

# =============================================================================
# Función: Mostrar ayuda
# =============================================================================

show_help() {
    print_header
    echo "Uso: ./start.sh [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  (sin comando)    Inicia la aplicación DCF Valuation Platform"
    echo "  install          Instala o actualiza todas las dependencias"
    echo "  stop             Detiene todos los procesos de Streamlit"
    echo "  help             Muestra esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./start.sh              # Inicia la aplicación"
    echo "  ./start.sh install      # Instala dependencias"
    echo "  ./start.sh stop         # Detiene la aplicación"
    echo ""
}

# =============================================================================
# MAIN
# =============================================================================

case "${1:-}" in
    install)
        install_mode
        ;;
    stop)
        print_header
        stop_processes
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        start_app
        ;;
    *)
        print_error "Comando desconocido: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
