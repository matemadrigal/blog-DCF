"""
Executive Summary PDF Generator with enhanced features.

NEW FEATURES (Mejora #18):
1. ✅ Primera página con resumen ejecutivo de 1 minuto
2. ✅ Gráficos de alta calidad (vectoriales SVG)
3. ✅ Sección de recomendación ultra-destacada
4. ✅ Branding personalizable (logo, colores corporativos)
5. ✅ Comparación automática con S&P 500

"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
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
        PageBreak,
        Image,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, String, Line
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    import yfinance as yf

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


if REPORTLAB_AVAILABLE:
    # Import base class
    from src.reports.enhanced_pdf_generator import EnhancedPDFReportGenerator

    class ExecutivePDFReportGenerator(EnhancedPDFReportGenerator):
        """
        Executive-level PDF report generator with:
        - Executive summary cover page
        - S&P 500 benchmark comparison
        - High-quality vectorial charts
        - Custom branding support
        """

        def __init__(self, branding: Optional[Dict[str, Any]] = None):
            """
            Initialize with optional custom branding.

            Args:
                branding: Dict with keys:
                    - logo_path: Path to logo image (PNG/JPG)
                    - primary_color: Hex color for headings
                    - secondary_color: Hex color for accents
                    - company_name: Name for footer
            """
            super().__init__()

            # Apply custom branding if provided
            if branding:
                self._apply_branding(branding)

            self.branding = branding or {}

        def _apply_branding(self, branding: Dict[str, Any]):
            """Apply custom brand colors to color scheme."""
            if "primary_color" in branding:
                self.COLORS["primary"] = colors.HexColor(branding["primary_color"])
            if "secondary_color" in branding:
                self.COLORS["secondary"] = colors.HexColor(branding["secondary_color"])

        def generate_executive_report(
            self,
            ticker: str,
            company_name: str,
            dcf_data: Dict[str, Any],
            scenarios: Optional[Dict[str, Any]] = None,
            commentary: Optional[Dict[str, Any]] = None,
            output_path: Optional[str] = None,
        ) -> bytes:
            """
            Generate executive-level PDF report with cover page and benchmarks.

            Args:
                ticker: Stock ticker
                company_name: Company name
                dcf_data: DCF calculation data
                scenarios: Optional scenario analysis
                commentary: Optional analyst commentary
                output_path: Optional output path

            Returns:
                PDF bytes
            """
            buffer = io.BytesIO()

            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.75 * inch,
                bottomMargin=0.75 * inch,
            )

            story = []

            # ===== PAGE 1: EXECUTIVE SUMMARY COVER =====
            story.extend(
                self._build_executive_cover_page(
                    ticker, company_name, dcf_data, scenarios
                )
            )

            story.append(PageBreak())

            # ===== PAGE 2+: DETAILED ANALYSIS =====

            # Header section
            story.extend(self._build_header(ticker, company_name, dcf_data))

            # KPI cards
            story.extend(self._build_kpi_cards(dcf_data))

            # Ultra-prominent recommendation
            story.extend(self._build_ultra_prominent_recommendation(dcf_data))

            story.append(Spacer(1, 0.3 * inch))

            # === S&P 500 COMPARISON (NEW!) ===
            story.extend(self._build_sp500_comparison(ticker, dcf_data))

            # Executive summary from analyst (if provided)
            if commentary and commentary.get("summary"):
                story.extend(self._build_executive_summary(commentary["summary"]))

            # Parameters section
            story.extend(self._build_parameters_section(dcf_data))

            # FCF projections with HIGH-QUALITY VECTOR CHART
            story.extend(self._build_fcf_section_with_vector_chart(dcf_data))

            # Value breakdown chart
            story.extend(self._build_value_breakdown_chart(dcf_data))

            # Scenarios if available
            if scenarios:
                story.extend(self._build_scenarios_section(scenarios, dcf_data))

            # Sensitivity analysis chart
            story.extend(self._build_sensitivity_analysis(dcf_data))

            # Analyst notes (if provided)
            if commentary and commentary.get("notes"):
                story.extend(self._build_analyst_notes(commentary["notes"]))

            # Multiples commentary (if provided)
            if commentary and commentary.get("multiples"):
                story.extend(self._build_multiples_section(commentary["multiples"]))

            # Disclaimer
            story.extend(self._build_disclaimer())

            # Build PDF
            doc.build(story)

            pdf_bytes = buffer.getvalue()
            buffer.close()

            if output_path:
                Path(output_path).write_bytes(pdf_bytes)

            return pdf_bytes

        def _build_executive_cover_page(
            self,
            ticker: str,
            company_name: str,
            dcf_data: Dict[str, Any],
            scenarios: Optional[Dict[str, Any]] = None,
        ) -> List:
            """
            Build executive summary cover page (1-minute read).

            Key components:
            - Company logo/title
            - One-sentence verdict
            - Key metrics at a glance
            - Quick recommendation
            - Risk/reward snapshot
            """
            elements = []

            # Logo (if provided in branding)
            if self.branding.get("logo_path"):
                try:
                    logo = Image(self.branding["logo_path"], width=1.5*inch, height=0.75*inch)
                    elements.append(logo)
                    elements.append(Spacer(1, 0.2 * inch))
                except Exception:
                    pass  # Skip logo if file doesn't exist

            # Title
            elements.append(
                Paragraph(
                    "RESUMEN EJECUTIVO",
                    ParagraphStyle(
                        name="CoverTitle",
                        fontSize=36,
                        textColor=self.COLORS["primary"],
                        spaceAfter=10,
                        alignment=TA_CENTER,
                        fontName="Helvetica-Bold",
                    ),
                )
            )

            # Company name
            elements.append(
                Paragraph(
                    f"{company_name} ({ticker})",
                    ParagraphStyle(
                        name="CoverCompany",
                        fontSize=24,
                        textColor=self.COLORS["dark"],
                        spaceAfter=30,
                        alignment=TA_CENTER,
                        fontName="Helvetica",
                    ),
                )
            )

            # Date
            date_str = datetime.now().strftime("%d de %B, %Y")
            elements.append(
                Paragraph(
                    date_str,
                    ParagraphStyle(
                        name="CoverDate",
                        fontSize=12,
                        textColor=self.COLORS["muted"],
                        spaceAfter=40,
                        alignment=TA_CENTER,
                    ),
                )
            )

            # === ONE-SENTENCE VERDICT ===
            market_price = dcf_data.get("market_price", 0)
            shares = dcf_data.get("shares_outstanding", 0)
            fair_value = dcf_data.get("fair_value", 0)
            fair_value_per_share = fair_value / shares if shares > 0 else 0

            upside = 0
            if market_price > 0 and fair_value_per_share > 0:
                upside = ((fair_value_per_share - market_price) / market_price) * 100

            # Generate verdict
            if upside > 30:
                verdict = f"🎯 <b>OPORTUNIDAD EXCEPCIONAL</b>: {company_name} está cotizando {abs(upside):.0f}% por debajo de su valor intrínseco."
                verdict_color = self.COLORS["success"]
            elif upside > 10:
                verdict = f"📈 <b>OPORTUNIDAD</b>: {company_name} presenta un potencial alcista del {upside:.0f}%."
                verdict_color = self.COLORS["success"]
            elif upside < -30:
                verdict = f"⚠️ <b>SOBREVALORADO</b>: {company_name} cotiza {abs(upside):.0f}% por encima de su valor razonable."
                verdict_color = self.COLORS["danger"]
            elif upside < -10:
                verdict = f"📉 <b>RIESGO DE CORRECCIÓN</b>: {company_name} muestra una sobrevaloración del {abs(upside):.0f}%."
                verdict_color = self.COLORS["danger"]
            else:
                verdict = f"⚖️ <b>VALORACIÓN RAZONABLE</b>: {company_name} cotiza cerca de su fair value."
                verdict_color = self.COLORS["warning"]

            verdict_data = [[Paragraph(verdict, self.styles["ExecutiveSummary"])]]
            verdict_table = Table(verdict_data, colWidths=[6.5 * inch])
            verdict_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), verdict_color),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                    ("LEFTPADDING", (0, 0), (-1, -1), 20),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ])
            )

            elements.append(verdict_table)
            elements.append(Spacer(1, 0.4 * inch))

            # === KEY METRICS AT A GLANCE ===
            wacc = dcf_data.get("discount_rate", 0)
            growth = dcf_data.get("growth_rate", 0)

            metrics_data = [
                ["PRECIO ACTUAL", "FAIR VALUE", "UPSIDE", "WACC", "g"],
                [
                    f"${market_price:.2f}",
                    f"${fair_value_per_share:.2f}",
                    f"{upside:+.1f}%",
                    f"{wacc*100:.1f}%",
                    f"{growth*100:.1f}%",
                ],
            ]

            metrics_table = Table(metrics_data, colWidths=[1.3 * inch] * 5)
            metrics_table.setStyle(
                TableStyle([
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 9),
                    ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["light"]),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.COLORS["muted"]),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 1), (-1, 1), 16),
                    ("TEXTCOLOR", (0, 1), (1, 1), self.COLORS["dark"]),
                    ("TEXTCOLOR", (2, 1), (2, 1), verdict_color),
                    ("ALIGN", (0, 1), (-1, 1), "CENTER"),
                    ("GRID", (0, 0), (-1, -1), 1, self.COLORS["muted"]),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ])
            )

            elements.append(metrics_table)
            elements.append(Spacer(1, 0.4 * inch))

            # === RECOMMENDATION BOX ===
            if upside > 20:
                rec = "STRONG BUY"
                rec_icon = "🚀"
                rec_text = "Recomendación: COMPRA FUERTE"
                rec_detail = "Oportunidad significativa de apreciación."
            elif upside > 10:
                rec = "BUY"
                rec_icon = "📈"
                rec_text = "Recomendación: COMPRA"
                rec_detail = "Potencial alcista favorable."
            elif upside < -20:
                rec = "STRONG SELL"
                rec_icon = "⚠️"
                rec_text = "Recomendación: VENTA FUERTE"
                rec_detail = "Riesgo de corrección significativo."
            elif upside < -10:
                rec = "SELL"
                rec_icon = "📉"
                rec_text = "Recomendación: VENTA"
                rec_detail = "Sobrevaloración detectada."
            else:
                rec = "HOLD"
                rec_icon = "⚖️"
                rec_text = "Recomendación: MANTENER"
                rec_detail = "Valoración razonable actual."

            rec_full = f"<b>{rec_icon} {rec_text}</b><br/>{rec_detail}"
            rec_data = [[Paragraph(rec_full, self.styles["ExecutiveSummary"])]]
            rec_table = Table(rec_data, colWidths=[6.5 * inch])
            rec_table.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 3, verdict_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 20),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                    ("TOPPADDING", (0, 0), (-1, -1), 15),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 15),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ])
            )

            elements.append(rec_table)
            elements.append(Spacer(1, 0.4 * inch))

            # === RISK/REWARD SNAPSHOT ===
            if scenarios:
                elements.append(
                    Paragraph("Escenarios de Valoración", self.styles["Subsection"])
                )

                scenario_data = [["", "Pesimista", "Base", "Optimista"]]

                # Extract scenario values
                if "pessimistic" in scenarios:
                    pess_fv = scenarios["pessimistic"].fair_value_per_share
                else:
                    pess_fv = fair_value_per_share * 0.85

                if "base" in scenarios:
                    base_fv = scenarios["base"].fair_value_per_share
                else:
                    base_fv = fair_value_per_share

                if "optimistic" in scenarios:
                    opt_fv = scenarios["optimistic"].fair_value_per_share
                else:
                    opt_fv = fair_value_per_share * 1.15

                scenario_data.append([
                    "Fair Value",
                    f"${pess_fv:.2f}",
                    f"${base_fv:.2f}",
                    f"${opt_fv:.2f}",
                ])

                pess_upside = ((pess_fv - market_price) / market_price * 100) if market_price > 0 else 0
                base_upside = upside
                opt_upside = ((opt_fv - market_price) / market_price * 100) if market_price > 0 else 0

                scenario_data.append([
                    "Upside",
                    f"{pess_upside:+.0f}%",
                    f"{base_upside:+.0f}%",
                    f"{opt_upside:+.0f}%",
                ])

                scenario_table = Table(scenario_data, colWidths=[1.625 * inch] * 4)
                scenario_table.setStyle(
                    TableStyle([
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["secondary"]),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ("BACKGROUND", (0, 1), (0, -1), self.COLORS["light"]),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                    ])
                )

                elements.append(scenario_table)

            # Footer note
            elements.append(Spacer(1, 0.5 * inch))
            footer_note = (
                "Este resumen ejecutivo presenta los hallazgos clave del análisis DCF. "
                "Para detalles técnicos, metodología y supuestos, consulte las páginas siguientes."
            )
            elements.append(
                Paragraph(
                    footer_note,
                    ParagraphStyle(
                        name="CoverFooter",
                        fontSize=9,
                        textColor=self.COLORS["muted"],
                        alignment=TA_JUSTIFY,
                        spaceBefore=20,
                    ),
                )
            )

            return elements

        def _build_ultra_prominent_recommendation(self, dcf_data: Dict[str, Any]) -> List:
            """Build ULTRA-prominent recommendation section (bigger than base class)."""
            elements = []

            market_price = dcf_data.get("market_price", 0)
            shares = dcf_data.get("shares_outstanding", 0)
            fair_value = dcf_data.get("fair_value", 0)
            fair_value_per_share = fair_value / shares if shares > 0 else 0

            if market_price > 0 and fair_value_per_share > 0:
                upside = ((fair_value_per_share - market_price) / market_price) * 100

                if upside > 20:
                    rec = "COMPRAR"
                    rec_color = self.COLORS["success"]
                    rec_icon = "🚀"
                    rec_text = "OPORTUNIDAD DE COMPRA FUERTE"
                elif upside > 0:
                    rec = "COMPRAR"
                    rec_color = self.COLORS["success"]
                    rec_icon = "📈"
                    rec_text = "Oportunidad de compra - Infravalorado"
                elif upside < -20:
                    rec = "VENDER"
                    rec_color = self.COLORS["danger"]
                    rec_icon = "⚠️"
                    rec_text = "RIESGO SIGNIFICATIVO - Sobrevalorado"
                elif upside < 0:
                    rec = "VENDER"
                    rec_color = self.COLORS["danger"]
                    rec_icon = "📉"
                    rec_text = "Riesgo de corrección - Sobrevalorado"
                else:
                    rec = "MANTENER"
                    rec_color = self.COLORS["warning"]
                    rec_icon = "⚖️"
                    rec_text = "Valoración razonable"

                rec_full = f"<b><font size=14>{rec_icon} {rec}</font></b><br/><font size=10>{rec_text}</font>"

                rec_data = [[Paragraph(rec_full, self.styles["ExecutiveSummary"])]]
                rec_table = Table(rec_data, colWidths=[6.5 * inch])
                rec_table.setStyle(
                    TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), rec_color),
                        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
                        ("LEFTPADDING", (0, 0), (-1, -1), 30),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 30),
                        ("TOPPADDING", (0, 0), (-1, -1), 20),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ])
                )

                elements.append(rec_table)

            return elements

        def _build_sp500_comparison(self, ticker: str, dcf_data: Dict[str, Any]) -> List:
            """
            Build S&P 500 comparison section (NEW FEATURE!).

            Compares:
            - YTD performance
            - 1Y performance
            - Volatility (beta)
            """
            elements = []

            try:
                # Fetch S&P 500 data
                sp500 = yf.Ticker("^GSPC")
                stock = yf.Ticker(ticker)

                # Get historical data (1 year)
                hist_sp500 = sp500.history(period="1y")
                hist_stock = stock.history(period="1y")

                if not hist_sp500.empty and not hist_stock.empty:
                    # Calculate returns
                    sp500_ytd = ((hist_sp500['Close'][-1] / hist_sp500['Close'][0]) - 1) * 100
                    stock_ytd = ((hist_stock['Close'][-1] / hist_stock['Close'][0]) - 1) * 100

                    # Relative performance
                    relative_perf = stock_ytd - sp500_ytd

                    elements.append(
                        Paragraph("📊 Comparación con S&P 500", self.styles["SectionTitle"])
                    )

                    # Performance comparison table
                    perf_data = [
                        ["Métrica", ticker, "S&P 500", "Relativo"],
                        [
                            "Rendimiento 1 Año",
                            f"{stock_ytd:+.1f}%",
                            f"{sp500_ytd:+.1f}%",
                            f"{relative_perf:+.1f}%",
                        ],
                    ]

                    # Add beta if available
                    beta = dcf_data.get("beta", None)
                    if beta:
                        perf_data.append([
                            "Beta (Volatilidad)",
                            f"{beta:.2f}",
                            "1.00",
                            f"{(beta - 1)*100:+.0f}%",
                        ])

                    perf_table = Table(perf_data, colWidths=[1.625 * inch] * 4)

                    # Color relative performance
                    rel_perf_color = self.COLORS["success"] if relative_perf > 0 else self.COLORS["danger"]

                    perf_table.setStyle(
                        TableStyle([
                            ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("TEXTCOLOR", (3, 1), (3, -1), rel_perf_color),
                            ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ])
                    )

                    elements.append(perf_table)

                    # Interpretation
                    if relative_perf > 10:
                        interp = f"✅ {ticker} ha superado significativamente al S&P 500 (+{relative_perf:.0f}%)"
                    elif relative_perf > 0:
                        interp = f"✅ {ticker} ha superado al S&P 500 (+{relative_perf:.0f}%)"
                    elif relative_perf > -10:
                        interp = f"⚖️ {ticker} ha tenido un desempeño similar al S&P 500 ({relative_perf:+.0f}%)"
                    else:
                        interp = f"❌ {ticker} ha tenido un desempeño inferior al S&P 500 ({relative_perf:+.0f}%)"

                    elements.append(Spacer(1, 0.1 * inch))
                    elements.append(Paragraph(interp, self.styles["AnalystNote"]))
                    elements.append(Spacer(1, 0.3 * inch))

            except Exception as e:
                # Silently skip if data unavailable
                pass

            return elements

        def _build_fcf_section_with_vector_chart(self, dcf_data: Dict[str, Any]) -> List:
            """
            Build FCF section with HIGH-QUALITY VECTORIAL CHART (NEW!).

            Uses ReportLab's vector graphics instead of raster images.
            """
            elements = []

            elements.append(
                Paragraph("Proyecciones de Free Cash Flow", self.styles["SectionTitle"])
            )

            fcf_projections = dcf_data.get("fcf_projections", [])
            r = dcf_data.get("discount_rate", 0)

            if not fcf_projections:
                return elements

            # Build VECTORIAL bar chart
            drawing = Drawing(500, 200)

            bc = VerticalBarChart()
            bc.x = 50
            bc.y = 50
            bc.height = 125
            bc.width = 400
            bc.data = [[fcf / 1e9 for fcf in fcf_projections]]  # Convert to billions
            bc.categoryAxis.categoryNames = [f"Año {i+1}" for i in range(len(fcf_projections))]

            # Styling
            bc.bars[0].fillColor = self.COLORS["primary"]
            bc.valueAxis.valueMin = 0
            bc.valueAxis.valueMax = max(fcf_projections) / 1e9 * 1.2
            bc.valueAxis.valueStep = max(fcf_projections) / 1e9 * 0.2
            bc.categoryAxis.labels.boxAnchor = 'n'
            bc.categoryAxis.labels.dy = -5
            bc.categoryAxis.labels.angle = 0
            bc.categoryAxis.labels.fontName = 'Helvetica'
            bc.categoryAxis.labels.fontSize = 8

            # Add title
            title = String(250, 180, "Free Cash Flow Proyectado (Billones $)", textAnchor='middle')
            title.fontName = 'Helvetica-Bold'
            title.fontSize = 10
            title.fillColor = self.COLORS["dark"]

            drawing.add(bc)
            drawing.add(title)

            elements.append(drawing)
            elements.append(Spacer(1, 0.3 * inch))

            # Also add table for numerical details
            elements.extend(self._build_fcf_section(dcf_data))

            return elements


def generate_executive_dcf_report(
    ticker: str,
    company_name: str,
    dcf_data: Dict[str, Any],
    scenarios: Optional[Dict[str, Any]] = None,
    commentary: Optional[Dict[str, Any]] = None,
    branding: Optional[Dict[str, Any]] = None,
    output_path: Optional[str] = None,
) -> bytes:
    """
    Convenience function to generate executive DCF report.

    Args:
        ticker: Stock ticker
        company_name: Company name
        dcf_data: DCF data dictionary
        scenarios: Optional scenarios dict
        commentary: Optional analyst commentary dict
        branding: Optional branding dict (logo_path, colors, company_name)
        output_path: Optional output path

    Returns:
        PDF bytes
    """
    generator = ExecutivePDFReportGenerator(branding=branding)
    return generator.generate_executive_report(
        ticker, company_name, dcf_data, scenarios, commentary, output_path
    )

else:
    # Fallback when reportlab is not available
    class ExecutivePDFReportGenerator:
        """Placeholder class when reportlab is not available."""

        def __init__(self, branding=None):
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )

    def generate_executive_dcf_report(*args, **kwargs):
        """Placeholder function when reportlab is not available."""
        raise ImportError(
            "reportlab is required for PDF generation. "
            "Install with: pip install reportlab"
        )
