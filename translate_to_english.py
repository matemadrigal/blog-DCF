#!/usr/bin/env python3
"""
Script to translate all Spanish text to English in the DCF platform.
"""

import re
import os
from pathlib import Path

# Translation dictionary
TRANSLATIONS = {
    # Dashboard
    "Dashboard Ejecutivo": "Executive Dashboard",
    "Vista consolidada de tu portafolio de valoraciones DCF con análisis avanzado": "Consolidated view of your DCF valuation portfolio with advanced analysis",
    "Alertas Disparadas": "Triggered Alerts",
    "Tienes notificaciones pendientes. Ve a la página de": "You have pending notifications. Go to the",
    "para revisarlas": "page to review them",
    "No hay análisis guardados aún": "No saved analyses yet",
    "Ve a": "Go to",
    "para calcular tu primer DCF y comenzar a construir tu portafolio": "to calculate your first DCF and start building your portfolio",
    "Resumen Ejecutivo": "Executive Summary",
    "ROI Potencial": "Potential ROI",
    "Mejor Oportunidad": "Best Opportunity",
    "Empresas Analizadas": "Companies Analyzed",
    "Upside Promedio": "Average Upside",
    "Salud Portafolio": "Portfolio Health",
    "Comprar": "Buy",
    "Visualizaciones Ejecutivas": "Executive Visualizations",
    "Distribución de Oportunidades": "Opportunity Distribution",
    "Upside por Empresa": "Upside by Company",
    "Top 5 Mejores Oportunidades": "Top 5 Best Opportunities",
    "Precio Actual": "Current Price",
    "Tabla Detallada de Valoraciones": "Detailed Valuation Table",
    "Empresa": "Company",
    "Precio Mercado": "Market Price",
    "Recomendación": "Recommendation",
    "Última Actualización": "Last Update",
    "Tasa r": "Rate r",
    "Crecimiento g": "Growth g",
    "Insights y Recomendaciones": "Insights and Recommendations",
    "Oportunidades Destacadas": "Featured Opportunities",
    "Oportunidades de Compra": "Buy Opportunities",
    "empresas": "companies",
    "muestran oportunidades de compra con upside >20%": "show buy opportunities with upside >20%",
    "Mejor oportunidad:": "Best opportunity:",
    "de upside": "upside",
    "ROI potencial total:": "Total potential ROI:",
    "No hay oportunidades de compra claras en este momento (upside >20%)": "No clear buy opportunities at this time (upside >20%)",
    "Empresas Sobrevaluadas": "Overvalued Companies",
    "podrían estar sobrevaluadas (downside >20%)": "may be overvalued (downside >20%)",
    "Considera revisar:": "Consider reviewing:",
    "Análisis del Portafolio": "Portfolio Analysis",
    "Composición del Portafolio": "Portfolio Composition",
    "Mantener": "Hold",
    "Vender": "Sell",
    "Calidad general": "Overall quality",
    "Portafolio saludable con buenas oportunidades de inversión": "Healthy portfolio with good investment opportunities",
    "Portafolio balanceado. Considera diversificar más": "Balanced portfolio. Consider diversifying more",
    "Portafolio con pocas oportunidades. Busca nuevas empresas para analizar": "Portfolio with few opportunities. Look for new companies to analyze",
    "Exportar Portafolio a Excel": "Export Portfolio to Excel",
    "Exporta todo tu portafolio a Excel": "Export your entire portfolio to Excel",
    "con formato profesional:": "with professional formatting:",
    "Resumen completo de todas las empresas": "Complete summary of all companies",
    "Métricas clave y recomendaciones": "Key metrics and recommendations",
    "ROI potencial calculado": "Calculated potential ROI",
    "Colores y formato profesional": "Professional colors and formatting",
    "Empresas a Exportar": "Companies to Export",
    "Exportar Dashboard a Excel": "Export Dashboard to Excel",
    "Generando archivo Excel del dashboard...": "Generating Excel file from dashboard...",
    "Descargar Portfolio Excel": "Download Portfolio Excel",
    "Portafolio exportado:": "Portfolio exported:",
    "empresas en Excel!": "companies in Excel!",
    "Error al exportar:": "Error exporting:",
    "Asegúrate de que openpyxl esté instalado:": "Make sure openpyxl is installed:",
    "Leyenda y Notas": "Legend and Notes",
    "COMPRAR": "BUY",
    "MANTENER": "HOLD",
    "VENDER": "SELL",
    "por encima del precio de mercado": "above market price",
    "entre -20% y +20% del precio de mercado": "between -20% and +20% of market price",
    "por debajo del precio de mercado": "below market price",
    "Ganancia potencial asumiendo inversión de $100,000 por empresa": "Potential gain assuming $100,000 investment per company",
    "Score de 0-100 basado en calidad de oportunidades": "Score of 0-100 based on opportunity quality",
    "Promedio del upside/downside de todas las empresas": "Average of upside/downside of all companies",
    "Los cálculos están basados en los parámetros DCF ingresados (r y g)": "Calculations are based on entered DCF parameters (r and g)",
    "Los precios de mercado pueden haber cambiado desde el último cálculo": "Market prices may have changed since last calculation",
    "Esta herramienta es solo para fines educativos e informativos": "This tool is for educational and informational purposes only",
    
    # Individual Analysis
    "Análisis Individual": "Individual Analysis",
    "Calcula el Fair Value de una acción mediante DCF y compáralo con el precio de mercado": "Calculate the Fair Value of a stock using DCF and compare it with market price",
    
    # Comparator
    "Comparador de Empresas": "Company Comparator",
    "Compara múltiples empresas lado a lado para identificar las mejores oportunidades": "Compare multiple companies side by side to identify the best opportunities",
    "Selecciona empresas para comparar (máximo 5)": "Select companies to compare (max 5)",
    "Selecciona al menos una empresa": "Select at least one company",
    "Comparación de Métricas": "Metric Comparison",
    "Tamaño de Empresa (Enterprise Value)": "Company Size (Enterprise Value)",
    "No hay datos para las empresas seleccionadas": "No data for selected companies",
    
    # Historical
    "Evolución Histórica": "Historical Evolution",
    "Analiza la evolución temporal del Fair Value vs Precio de Mercado": "Analyze the temporal evolution of Fair Value vs Market Price",
    "Selecciona una empresa": "Select a company",
    "Solo hay": "Only",
    "cálculo(s) para": "calculation(s) for",
    "Necesitas al menos 2 para ver la evolución histórica": "You need at least 2 to see historical evolution",
    "Realiza cálculos periódicos para construir un historial": "Perform periodic calculations to build a history",
    "Fair Value vs Precio de Mercado": "Fair Value vs Market Price",
    "Evolución del Upside/Downside": "Upside/Downside Evolution",
    "Estadísticas Históricas": "Historical Statistics",
    "Fair Value Promedio": "Average Fair Value",
    "Precio Promedio": "Average Price",
    "Upside Promedio": "Average Upside",
    "Cálculos Realizados": "Calculations Performed",
    "Tabla Histórica": "Historical Table",
    "Fecha": "Date",
    
    # General
    "Análisis Individual": "Individual Analysis",
    "No hay análisis guardados": "No saved analyses",
    "primero para crear análisis de empresas": "first to create company analyses",
    "Datos Insuficientes": "Insufficient Data",
    "Tip:": "Tip:",
}

def translate_file(file_path: Path):
    """Translate a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply translations
        for spanish, english in TRANSLATIONS.items():
            content = content.replace(spanish, english)
        
        # Only write if content changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Translated: {file_path}")
            return True
        else:
            print(f"⏭️  No changes: {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error translating {file_path}: {e}")
        return False

def main():
    """Main translation function."""
    base_dir = Path(__file__).parent
    
    # Files to translate
    files_to_translate = [
        base_dir / "app.py",
        base_dir / "pages" / "1_📈_Análisis_Individual.py",
        base_dir / "pages" / "2_📊_Dashboard.py",
        base_dir / "pages" / "3_⚖️_Comparador.py",
        base_dir / "pages" / "4_📅_Histórico.py",
        base_dir / "src" / "utils" / "error_handler.py",
        base_dir / "src" / "utils" / "dependency_checker.py",
    ]
    
    translated_count = 0
    for file_path in files_to_translate:
        if file_path.exists():
            if translate_file(file_path):
                translated_count += 1
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print(f"\n✨ Translation complete! {translated_count} files updated.")

if __name__ == "__main__":
    main()

