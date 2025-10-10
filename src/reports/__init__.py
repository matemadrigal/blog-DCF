"""Reports module for PDF and HTML generation."""

# Try to import enhanced PDF generator first (with charts and modern design)
try:
    from src.reports.enhanced_pdf_generator import (
        EnhancedPDFReportGenerator,
        generate_enhanced_dcf_report,
    )

    # Use enhanced generator as default
    generate_dcf_report = generate_enhanced_dcf_report
    PDFReportGenerator = EnhancedPDFReportGenerator
    ENHANCED_PDF_AVAILABLE = True
except ImportError:
    # Fallback to basic PDF generator
    try:
        from src.reports.pdf_generator import PDFReportGenerator, generate_dcf_report

        ENHANCED_PDF_AVAILABLE = False
    except ImportError:
        PDFReportGenerator = None
        generate_dcf_report = None
        ENHANCED_PDF_AVAILABLE = False

# HTML generator (no dependencies)
try:
    from src.reports.html_report_generator import HTMLReportGenerator

    HTML_AVAILABLE = True
except ImportError:
    HTMLReportGenerator = None
    HTML_AVAILABLE = False

__all__ = [
    "PDFReportGenerator",
    "generate_dcf_report",
    "HTMLReportGenerator",
    "ENHANCED_PDF_AVAILABLE",
    "HTML_AVAILABLE",
]
