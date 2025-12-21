#!/usr/bin/env python3
"""
Script para publicar nuevos reportes DCF en GitHub Pages.

Uso:
    python scripts/publish_pdf.py path/to/report.pdf TICKER "Company Name" "Sector" "Date"

Ejemplo:
    python scripts/publish_pdf.py outputs/DCF_Report_AAPL.pdf AAPL "Apple Inc." "Technology / Consumer Electronics" "Q4 2024"
"""

import sys
import os
import shutil
import re
from pathlib import Path


def get_file_size_human(file_path):
    """Obtener tamaño de archivo en formato legible."""
    size_bytes = os.path.getsize(file_path)

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def update_index_html(report_info):
    """Actualizar index.html con el nuevo reporte."""

    index_path = Path("docs/index.html")

    if not index_path.exists():
        print(f"❌ Error: {index_path} no existe")
        return False

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Buscar el array de reports
    reports_pattern = r'const reports = \[(.*?)\];'
    match = re.search(reports_pattern, content, re.DOTALL)

    if not match:
        print("❌ Error: No se pudo encontrar el array de reports en index.html")
        return False

    # Crear nueva entrada
    new_entry = f"""            {{
                ticker: '{report_info['ticker']}',
                company: '{report_info['company']}',
                filename: '{report_info['filename']}',
                sector: '{report_info['sector']}',
                date: '{report_info['date']}',
                size: '{report_info['size']}'
            }}"""

    # Obtener el contenido actual del array
    current_reports = match.group(1).strip()

    # Agregar coma al final si hay reportes existentes
    if current_reports:
        new_reports = current_reports + ",\n" + new_entry
    else:
        new_reports = new_entry

    # Reemplazar el array completo
    new_content = content.replace(
        f"const reports = [{current_reports}];",
        f"const reports = [\n{new_reports}\n        ];"
    )

    # Guardar
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ index.html actualizado con el nuevo reporte")
    return True


def publish_pdf(pdf_path, ticker, company, sector, date):
    """Publicar un PDF en GitHub Pages."""

    pdf_path = Path(pdf_path)

    # Validar que el PDF existe
    if not pdf_path.exists():
        print(f"❌ Error: El archivo {pdf_path} no existe")
        return False

    if not pdf_path.suffix.lower() == '.pdf':
        print(f"❌ Error: El archivo debe ser un PDF")
        return False

    # Crear carpeta de destino si no existe
    reports_dir = Path("docs/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Copiar PDF
    dest_path = reports_dir / pdf_path.name
    shutil.copy2(pdf_path, dest_path)
    print(f"✅ PDF copiado a {dest_path}")

    # Obtener información del reporte
    report_info = {
        'ticker': ticker,
        'company': company,
        'filename': pdf_path.name,
        'sector': sector,
        'date': date,
        'size': get_file_size_human(pdf_path)
    }

    # Actualizar index.html
    if update_index_html(report_info):
        print("\n" + "="*60)
        print("✅ REPORTE PUBLICADO EXITOSAMENTE")
        print("="*60)
        print(f"\n📊 Reporte: {company} ({ticker})")
        print(f"📄 Archivo: {pdf_path.name}")
        print(f"📁 Ubicación: docs/reports/{pdf_path.name}")
        print(f"💾 Tamaño: {report_info['size']}")
        print(f"\n🔗 Una vez en GitHub Pages estará disponible en:")
        print(f"   https://matemadrigal.github.io/blog-DCF/reports/{pdf_path.name}")
        print(f"\n📋 Próximos pasos:")
        print(f"   1. git add docs/reports/{pdf_path.name} docs/index.html")
        print(f"   2. git commit -m 'Add DCF report for {ticker}'")
        print(f"   3. git push")
        print("="*60 + "\n")
        return True

    return False


def show_usage():
    """Mostrar instrucciones de uso."""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                     PUBLICAR REPORTE DCF EN GITHUB PAGES                   ║
╚════════════════════════════════════════════════════════════════════════════╝

Uso:
    python scripts/publish_pdf.py <pdf_path> <ticker> <company> <sector> <date>

Argumentos:
    pdf_path    Ruta al archivo PDF del reporte
    ticker      Símbolo bursátil (ej: AAPL, MSFT, TSLA)
    company     Nombre completo de la empresa
    sector      Sector / Industria
    date        Fecha del análisis (ej: Q4 2024, December 2024)

Ejemplos:

    # Publicar reporte de Apple
    python scripts/publish_pdf.py \\
        outputs/DCF_Report_AAPL.pdf \\
        AAPL \\
        "Apple Inc." \\
        "Technology / Consumer Electronics" \\
        "Q4 2024"

    # Publicar reporte de Microsoft
    python scripts/publish_pdf.py \\
        outputs/DCF_Report_MSFT.pdf \\
        MSFT \\
        "Microsoft Corporation" \\
        "Technology / Software" \\
        "December 2024"

    # Publicar reporte de Tesla
    python scripts/publish_pdf.py \\
        DCF_Report_TSLA_2024.pdf \\
        TSLA \\
        "Tesla, Inc." \\
        "Automotive / Electric Vehicles" \\
        "Q3 2024"

Notas:
    • El PDF será copiado a docs/reports/
    • El archivo index.html será actualizado automáticamente
    • Recuerda hacer commit y push después de ejecutar este script
    • Los nombres de archivo con espacios funcionan correctamente

════════════════════════════════════════════════════════════════════════════
""")


def main():
    """Función principal."""

    # Validar argumentos
    if len(sys.argv) == 1 or sys.argv[1] in ['-h', '--help', 'help']:
        show_usage()
        return

    if len(sys.argv) != 6:
        print("❌ Error: Número incorrecto de argumentos\n")
        show_usage()
        sys.exit(1)

    # Extraer argumentos
    pdf_path = sys.argv[1]
    ticker = sys.argv[2]
    company = sys.argv[3]
    sector = sys.argv[4]
    date = sys.argv[5]

    # Validar ticker (solo letras y números, máximo 5 caracteres)
    if not re.match(r'^[A-Z0-9]{1,5}$', ticker):
        print(f"⚠️  Advertencia: El ticker '{ticker}' debería ser mayúsculas (ej: AAPL)")
        ticker = ticker.upper()

    # Publicar
    success = publish_pdf(pdf_path, ticker, company, sector, date)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
