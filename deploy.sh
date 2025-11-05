#!/bin/bash

# Script de deployment para blog-DCF
# Uso: ./deploy.sh [platform]
# Plataformas: streamlit, render, railway, local

set -e

PLATFORM=${1:-"streamlit"}

echo "=========================================="
echo "🚀 DCF Valuation Platform - Deployment"
echo "=========================================="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función de ayuda
show_help() {
    echo "Uso: ./deploy.sh [platform]"
    echo ""
    echo "Plataformas disponibles:"
    echo "  streamlit  - Deploy a Streamlit Community Cloud (default)"
    echo "  render     - Deploy a Render"
    echo "  railway    - Deploy a Railway"
    echo "  local      - Correr localmente"
    echo "  check      - Verificar que todo está listo para deploy"
    echo ""
    echo "Ejemplos:"
    echo "  ./deploy.sh              # Deploy a Streamlit (default)"
    echo "  ./deploy.sh render       # Deploy a Render"
    echo "  ./deploy.sh check        # Solo verificar"
    echo "  ./deploy.sh local        # Correr local"
}

# Verificar pre-requisitos
check_requirements() {
    echo "📋 Verificando requisitos..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 no encontrado${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Python 3 instalado"

    # Check Git
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git no encontrado${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Git instalado"

    # Check requirements.txt
    if [ ! -f "requirements.txt" ]; then
        echo -e "${RED}❌ requirements.txt no encontrado${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} requirements.txt existe"

    # Check app.py
    if [ ! -f "app.py" ]; then
        echo -e "${RED}❌ app.py no encontrado${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} app.py existe"

    # Check .gitignore
    if [ ! -f ".gitignore" ]; then
        echo -e "${YELLOW}⚠${NC}  .gitignore no encontrado (recomendado)"
    else
        echo -e "${GREEN}✓${NC} .gitignore existe"
    fi

    # Check Streamlit config
    if [ ! -f ".streamlit/config.toml" ]; then
        echo -e "${YELLOW}⚠${NC}  .streamlit/config.toml no encontrado (recomendado)"
    else
        echo -e "${GREEN}✓${NC} .streamlit/config.toml existe"
    fi

    echo ""
}

# Deploy a Streamlit Cloud
deploy_streamlit() {
    echo "🎯 Preparando para Streamlit Community Cloud..."
    echo ""

    check_requirements

    echo "📝 Pasos para deploy en Streamlit Cloud:"
    echo ""
    echo "1. Asegúrate de que tu código está en GitHub"
    echo "   git add ."
    echo "   git commit -m 'Ready for Streamlit Cloud'"
    echo "   git push origin main"
    echo ""
    echo "2. Visita: https://share.streamlit.io"
    echo ""
    echo "3. Click 'New app'"
    echo ""
    echo "4. Configura:"
    echo "   Repository: $(git config --get remote.origin.url | sed 's/.*github.com[:/]\(.*\)\.git/\1/')"
    echo "   Branch: main"
    echo "   Main file: app.py"
    echo ""
    echo "5. Click 'Deploy'"
    echo ""
    echo -e "${GREEN}✅ Tu app estará disponible en:${NC}"
    echo "   https://tu-usuario-blog-dcf.streamlit.app"
    echo ""
}

# Deploy a Render
deploy_render() {
    echo "🎯 Preparando para Render..."
    echo ""

    check_requirements

    echo "📝 Pasos para deploy en Render:"
    echo ""
    echo "1. Commit y push tu código:"
    echo "   git add ."
    echo "   git commit -m 'Ready for Render'"
    echo "   git push origin main"
    echo ""
    echo "2. Visita: https://render.com"
    echo ""
    echo "3. Click 'New +' → 'Web Service'"
    echo ""
    echo "4. Conecta tu repositorio GitHub"
    echo ""
    echo "5. Configura:"
    echo "   Build Command: pip install -r requirements.txt"
    echo "   Start Command: streamlit run app.py --server.port=\$PORT --server.address=0.0.0.0 --server.headless=true"
    echo ""
    echo "6. Click 'Create Web Service'"
    echo ""
    echo -e "${GREEN}✅ Tu app estará disponible en:${NC}"
    echo "   https://dcf-valuation.onrender.com"
    echo ""
}

# Deploy a Railway
deploy_railway() {
    echo "🎯 Preparando para Railway..."
    echo ""

    check_requirements

    echo "📝 Pasos para deploy en Railway:"
    echo ""
    echo "1. Commit y push tu código:"
    echo "   git add ."
    echo "   git commit -m 'Ready for Railway'"
    echo "   git push origin main"
    echo ""
    echo "2. Visita: https://railway.app"
    echo ""
    echo "3. Click 'New Project' → 'Deploy from GitHub repo'"
    echo ""
    echo "4. Selecciona tu repositorio"
    echo ""
    echo "5. Railway detectará Streamlit automáticamente"
    echo ""
    echo "6. Espera 3-5 minutos"
    echo ""
    echo -e "${GREEN}✅ Tu app estará disponible en:${NC}"
    echo "   https://blog-dcf-production.up.railway.app"
    echo ""
}

# Correr localmente
run_local() {
    echo "🏠 Corriendo localmente..."
    echo ""

    check_requirements

    # Activar virtual environment si existe
    if [ -d ".venv" ]; then
        echo "📦 Activando virtual environment..."
        source .venv/bin/activate
    fi

    # Instalar dependencias
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt > /dev/null 2>&1

    echo ""
    echo -e "${GREEN}✅ Iniciando Streamlit...${NC}"
    echo ""
    echo "App disponible en: http://localhost:8501"
    echo ""
    echo "Presiona Ctrl+C para detener"
    echo ""

    streamlit run app.py
}

# Main
case $PLATFORM in
    streamlit)
        deploy_streamlit
        ;;
    render)
        deploy_render
        ;;
    railway)
        deploy_railway
        ;;
    local)
        run_local
        ;;
    check)
        check_requirements
        echo -e "${GREEN}✅ Todo listo para deployment!${NC}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Plataforma desconocida: $PLATFORM${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
