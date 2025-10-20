"""
Example script to generate professional HTML report.

Run this to see the advanced HTML generator in action.
"""

from src.reports.advanced_html_generator import generate_professional_report
from src.reports.report_calculations import DCFReportData

# Example: Apple Inc. DCF Valuation
apple_dcf = DCFReportData(
    # Company identification
    ticker="AAPL",
    company_name="Apple Inc.",
    sector="Technology",
    # Valuation results
    fair_value_total=3_750_000_000_000,  # $3.75 Trillion
    shares_outstanding=15_000_000_000,  # 15 Billion shares
    market_price=250.0,  # $250 per share
    # DCF parameters
    wacc=0.088,  # 8.8%
    terminal_growth=0.031,  # 3.1%
    base_fcf=108_810_000_000,  # $108.81 Billion
    # Detailed projections
    projection_years=5,
    fcf_projections=[
        115_000_000_000,  # Year 1: +5.7%
        121_500_000_000,  # Year 2: +5.7%
        128_300_000_000,  # Year 3: +5.6%
        135_400_000_000,  # Year 4: +5.5%
        142_700_000_000,  # Year 5: +5.4%
    ],
    terminal_value=2_500_000_000_000,  # $2.5T
    # Balance sheet
    total_debt=120_000_000_000,  # $120B
    cash=60_000_000_000,  # $60B
    # Additional metrics (optional)
    revenue=383_000_000_000,  # $383B
    ebitda=125_000_000_000,  # $125B
    net_income=97_000_000_000,  # $97B
)


def main():
    """Generate example report."""
    print("=" * 80)
    print("🚀 GENERANDO REPORTE HTML PROFESIONAL")
    print("=" * 80)
    print()
    print(f"📊 Empresa: {apple_dcf.company_name} ({apple_dcf.ticker})")
    print(f"💰 Fair Value: ${apple_dcf.fair_value_per_share:.2f} per share")
    print(f"📈 Market Price: ${apple_dcf.market_price:.2f}")
    print(
        f"📊 Upside: {((apple_dcf.fair_value_per_share - apple_dcf.market_price) / apple_dcf.market_price * 100):+.1f}%"
    )
    print()

    # Generate report
    print("⏳ Generando reporte HTML con gráficos Plotly...")

    output_path = "output/AAPL_Professional_Report.html"

    html_content = generate_professional_report(
        dcf_data=apple_dcf, output_path=output_path
    )

    print()
    print("=" * 80)
    print("✅ REPORTE GENERADO EXITOSAMENTE")
    print("=" * 80)
    print()
    print(f"📁 Archivo: {output_path}")
    print(f"📏 Tamaño: {len(html_content):,} caracteres")
    print()
    print("🎯 PRÓXIMOS PASOS:")
    print()
    print("1. Abrir el archivo HTML en tu navegador:")
    print(f"   → open {output_path}  (macOS)")
    print(f"   → xdg-open {output_path}  (Linux)")
    print(f"   → start {output_path}  (Windows)")
    print()
    print("2. Descargar gráficos individuales:")
    print("   → Hover sobre cada gráfico")
    print("   → Click en icono de cámara")
    print("   → Descargar como PNG (1000x600)")
    print()
    print("3. Exportar reporte completo a PDF:")
    print("   → Ctrl+P (Cmd+P en Mac)")
    print("   → Destino: Guardar como PDF")
    print("   → Márgenes: Ninguno")
    print("   → ✓ Gráficos de fondo")
    print()
    print("=" * 80)
    print()

    # Display validation warnings
    from src.reports.report_calculations import ReportCalculations

    warnings = ReportCalculations.validate_dcf_sanity(apple_dcf)
    if warnings:
        print("⚠️  MODEL VALIDATION WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
        print()
    else:
        print("✅ Model validation: All checks passed!")
        print()


if __name__ == "__main__":
    main()
