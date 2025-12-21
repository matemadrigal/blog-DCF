#!/bin/bash
# Script bash simple para publicar PDFs en GitHub Pages
# Uso: ./scripts/publish_pdf.sh <pdf_file>

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para mostrar mensajes
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Función para mostrar ayuda
show_help() {
    cat << EOF

╔════════════════════════════════════════════════════════════════════════════╗
║             PUBLICAR REPORTE DCF EN GITHUB PAGES (Versión Simple)         ║
╚════════════════════════════════════════════════════════════════════════════╝

Uso:
    ./scripts/publish_pdf.sh <pdf_file>

Ejemplo:
    ./scripts/publish_pdf.sh outputs/DCF_Report_AAPL.pdf

Este script:
    1. Copia el PDF a docs/reports/
    2. Hace git add automáticamente
    3. Listo para commit y push

Para actualizar index.html con los metadatos del reporte, usa:
    python scripts/publish_pdf.py (versión completa)

════════════════════════════════════════════════════════════════════════════
EOF
    exit 0
}

# Validar argumentos
if [ $# -eq 0 ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
fi

PDF_FILE="$1"

# Validar que el archivo existe
if [ ! -f "$PDF_FILE" ]; then
    error "El archivo '$PDF_FILE' no existe"
    exit 1
fi

# Validar que es un PDF
if [[ ! "$PDF_FILE" =~ \.pdf$ ]]; then
    error "El archivo debe ser un PDF"
    exit 1
fi

# Crear directorio de reportes si no existe
mkdir -p docs/reports

# Obtener nombre del archivo
PDF_NAME=$(basename "$PDF_FILE")

# Copiar PDF
info "Copiando PDF a docs/reports/..."
cp "$PDF_FILE" docs/reports/

success "PDF copiado: docs/reports/$PDF_NAME"

# Agregar a git
info "Agregando a git..."
git add "docs/reports/$PDF_NAME"

success "Archivo agregado a git"

# Obtener tamaño del archivo
FILE_SIZE=$(du -h "$PDF_FILE" | cut -f1)

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
success "PDF PUBLICADO"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📄 Archivo: $PDF_NAME"
echo "📁 Ubicación: docs/reports/$PDF_NAME"
echo "💾 Tamaño: $FILE_SIZE"
echo ""
echo "🔗 Una vez en GitHub Pages estará disponible en:"
echo "   https://matemadrigal.github.io/blog-DCF/reports/$PDF_NAME"
echo ""
info "Próximos pasos:"
echo "   1. Editar docs/index.html manualmente para agregar metadatos"
echo "      O usar: python scripts/publish_pdf.py (para automatizar)"
echo "   2. git add docs/index.html"
echo "   3. git commit -m 'Add DCF report $PDF_NAME'"
echo "   4. git push"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
