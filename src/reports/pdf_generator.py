"""PDF report generator for DCF analysis."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import io

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.enums import TA_CENTER

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFReportGenerator:
    """Generate professional PDF reports for DCF analysis."""

    def __init__(self):
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )

        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.HexColor("#1f77b4"),
                spaceAfter=30,
                alignment=TA_CENTER,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="CustomHeading",
                parent=self.styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#2c3e50"),
                spaceAfter=12,
                spaceBefore=12,
            )
        )

        self.styles.add(
            ParagraphStyle(
                name="Disclaimer",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
                alignment=TA_CENTER,
                spaceBefore=6,
            )
        )

    def generate_report(
        self,
        ticker: str,
        company_name: str,
        dcf_data: Dict[str, Any],
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Generate a PDF report for a DCF analysis.

        Args:
            ticker: Stock ticker symbol
            company_name: Full company name
            dcf_data: Dictionary with DCF calculation data
            output_path: Optional file path to save PDF

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        # Create document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )

        # Build content
        story = []

        # Header
        story.append(Paragraph("Informe de Valoración DCF", self.styles["CustomTitle"]))

        story.append(Paragraph(f"{company_name} ({ticker})", self.styles["Heading1"]))

        story.append(
            Paragraph(
                f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                self.styles["Normal"],
            )
        )

        story.append(Spacer(1, 0.3 * inch))

        # Executive Summary
        story.append(Paragraph("Resumen Ejecutivo", self.styles["CustomHeading"]))

        fair_value = dcf_data.get("fair_value", 0)
        market_price = dcf_data.get("market_price", 0)
        shares = dcf_data.get("shares_outstanding", 0)
        fair_value_per_share = fair_value / shares if shares > 0 else 0

        summary_data = [
            ["Métrica", "Valor"],
            [
                "Enterprise Value",
                (
                    f"${fair_value/1e9:.2f}B"
                    if fair_value > 1e9
                    else f"${fair_value/1e6:.2f}M"
                ),
            ],
            [
                "Fair Value por Acción",
                f"${fair_value_per_share:.2f}" if fair_value_per_share > 0 else "N/A",
            ],
            [
                "Precio de Mercado",
                f"${market_price:.2f}" if market_price > 0 else "N/A",
            ],
        ]

        if fair_value_per_share > 0 and market_price > 0:
            upside = ((fair_value_per_share - market_price) / market_price) * 100
            summary_data.append(["Upside/Downside", f"{upside:+.1f}%"])

            if upside > 20:
                rec = "COMPRAR - Acción infravalorada"
            elif upside < -20:
                rec = "VENDER - Acción sobrevalorada"
            else:
                rec = "MANTENER - Acción valorada razonablemente"

            summary_data.append(["Recomendación", rec])

        summary_table = Table(summary_data, colWidths=[3 * inch, 2.5 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f77b4")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))

        # DCF Parameters
        story.append(
            Paragraph("Parámetros del Modelo DCF", self.styles["CustomHeading"])
        )

        params_data = [
            ["Parámetro", "Valor"],
            ["Tasa de Descuento (r)", f"{dcf_data.get('discount_rate', 0):.2%}"],
            [
                "Tasa de Crecimiento Perpetuo (g)",
                f"{dcf_data.get('growth_rate', 0):.2%}",
            ],
            ["Años de Proyección", str(len(dcf_data.get("fcf_projections", [])))],
            [
                "Shares Outstanding",
                f"{shares/1e9:.2f}B" if shares > 1e9 else f"{shares/1e6:.2f}M",
            ],
        ]

        params_table = Table(params_data, colWidths=[3 * inch, 2.5 * inch])
        params_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                ]
            )
        )

        story.append(params_table)
        story.append(Spacer(1, 0.3 * inch))

        # FCF Projections
        story.append(
            Paragraph("Proyecciones de Free Cash Flow", self.styles["CustomHeading"])
        )

        fcf_projections = dcf_data.get("fcf_projections", [])
        r = dcf_data.get("discount_rate", 0)
        g = dcf_data.get("growth_rate", 0)

        fcf_data = [["Año", "FCF Proyectado", "Valor Presente", "% del Total"]]

        discounted_fcfs = []
        for i, fcf in enumerate(fcf_projections, start=1):
            disc = fcf / ((1 + r) ** i)
            discounted_fcfs.append(disc)
            fcf_data.append(
                [
                    str(i),
                    f"${fcf/1e6:.2f}M" if abs(fcf) > 1e6 else f"${fcf/1e3:.2f}K",
                    f"${disc/1e6:.2f}M" if abs(disc) > 1e6 else f"${disc/1e3:.2f}K",
                    f"{(disc/fair_value)*100:.1f}%",
                ]
            )

        # Terminal value
        if fcf_projections:
            terminal = fcf_projections[-1] * (1 + g) / (r - g)
            disc_terminal = terminal / ((1 + r) ** len(fcf_projections))
            fcf_data.append(
                [
                    "Terminal",
                    (
                        f"${terminal/1e6:.2f}M"
                        if abs(terminal) > 1e6
                        else f"${terminal/1e3:.2f}K"
                    ),
                    (
                        f"${disc_terminal/1e6:.2f}M"
                        if abs(disc_terminal) > 1e6
                        else f"${disc_terminal/1e3:.2f}K"
                    ),
                    f"{(disc_terminal/fair_value)*100:.1f}%",
                ]
            )

        fcf_table = Table(
            fcf_data, colWidths=[1 * inch, 1.7 * inch, 1.7 * inch, 1.1 * inch]
        )
        fcf_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ff7f0e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -2),
                        [colors.white, colors.lightgrey],
                    ),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fff3cd")),
                ]
            )
        )

        story.append(fcf_table)
        story.append(Spacer(1, 0.4 * inch))

        # Disclaimer
        story.append(
            Paragraph(
                "DISCLAIMER: Este informe es solo para fines informativos y educativos. "
                "No constituye asesoramiento financiero ni recomendación de inversión. "
                "Las proyecciones y valoraciones son estimaciones sujetas a incertidumbre. "
                "Consulte con un asesor financiero profesional antes de tomar decisiones de inversión.",
                self.styles["Disclaimer"],
            )
        )

        story.append(Spacer(1, 0.2 * inch))

        story.append(
            Paragraph(
                f"Generado por DCF Valuation Platform - {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                self.styles["Disclaimer"],
            )
        )

        # Build PDF
        doc.build(story)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "wb") as f:
                f.write(pdf_bytes)

        return pdf_bytes


def generate_dcf_report(
    ticker: str,
    company_name: str,
    dcf_data: Dict[str, Any],
    output_path: Optional[str] = None,
) -> bytes:
    """
    Convenience function to generate a DCF report.

    Args:
        ticker: Stock ticker symbol
        company_name: Full company name
        dcf_data: Dictionary with DCF calculation data
        output_path: Optional file path to save PDF

    Returns:
        PDF content as bytes
    """
    generator = PDFReportGenerator()
    return generator.generate_report(ticker, company_name, dcf_data, output_path)
