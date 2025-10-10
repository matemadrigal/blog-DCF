"""
Enhanced PDF report generator with professional design and charts.

Generates sophisticated, visually appealing reports with:
- Professional color scheme
- Charts and visualizations
- KPI cards with visual appeal
- Scenario comparison tables
- Waterfall charts for FCF breakdown
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
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.graphics.shapes import Drawing, Rect
    from reportlab.graphics.charts.piecharts import Pie

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    colors = None  # Placeholder for when reportlab is not available


if REPORTLAB_AVAILABLE:

    class EnhancedPDFReportGenerator:
        """Generate professional PDF reports with charts and modern design."""

        # Professional color scheme
        COLORS = {
            "primary": colors.HexColor("#1e40af"),  # Blue
            "secondary": colors.HexColor("#0ea5e9"),  # Light blue
            "success": colors.HexColor("#22c55e"),  # Green
            "danger": colors.HexColor("#ef4444"),  # Red
            "warning": colors.HexColor("#f59e0b"),  # Orange
            "muted": colors.HexColor("#64748b"),  # Gray
            "light": colors.HexColor("#f8fafc"),  # Light gray
            "dark": colors.HexColor("#0f172a"),  # Dark blue
        }

        def __init__(self):
            if not REPORTLAB_AVAILABLE:
                raise ImportError(
                    "reportlab is required for PDF generation. "
                    "Install with: pip install reportlab"
                )

            self.styles = getSampleStyleSheet()
            self._setup_custom_styles()

        def _setup_custom_styles(self):
            """Setup custom paragraph styles with modern design."""
            # Main title
            self.styles.add(
                ParagraphStyle(
                    name="MainTitle",
                    parent=self.styles["Heading1"],
                    fontSize=32,
                    textColor=self.COLORS["primary"],
                    spaceAfter=10,
                    alignment=TA_LEFT,
                    fontName="Helvetica-Bold",
                )
            )

            # Company name
            self.styles.add(
                ParagraphStyle(
                    name="CompanyName",
                    parent=self.styles["Heading1"],
                    fontSize=24,
                    textColor=self.COLORS["dark"],
                    spaceAfter=20,
                    alignment=TA_LEFT,
                    fontName="Helvetica-Bold",
                )
            )

            # Section title
            self.styles.add(
                ParagraphStyle(
                    name="SectionTitle",
                    parent=self.styles["Heading2"],
                    fontSize=16,
                    textColor=self.COLORS["primary"],
                    spaceAfter=12,
                    spaceBefore=20,
                    fontName="Helvetica-Bold",
                    borderWidth=0,
                    borderColor=self.COLORS["primary"],
                    borderPadding=0,
                )
            )

            # Subsection
            self.styles.add(
                ParagraphStyle(
                    name="Subsection",
                    parent=self.styles["Heading3"],
                    fontSize=12,
                    textColor=self.COLORS["dark"],
                    spaceAfter=8,
                    spaceBefore=12,
                    fontName="Helvetica-Bold",
                )
            )

            # KPI label
            self.styles.add(
                ParagraphStyle(
                    name="KPILabel",
                    parent=self.styles["Normal"],
                    fontSize=9,
                    textColor=self.COLORS["muted"],
                    alignment=TA_CENTER,
                    fontName="Helvetica",
                )
            )

            # KPI value
            self.styles.add(
                ParagraphStyle(
                    name="KPIValue",
                    parent=self.styles["Normal"],
                    fontSize=18,
                    textColor=self.COLORS["dark"],
                    alignment=TA_CENTER,
                    fontName="Helvetica-Bold",
                )
            )

            # Disclaimer
            self.styles.add(
                ParagraphStyle(
                    name="Disclaimer",
                    parent=self.styles["Normal"],
                    fontSize=7,
                    textColor=self.COLORS["muted"],
                    alignment=TA_JUSTIFY,
                    spaceBefore=6,
                )
            )

            # Executive summary box
            self.styles.add(
                ParagraphStyle(
                    name="ExecutiveSummary",
                    parent=self.styles["Normal"],
                    fontSize=10,
                    textColor=self.COLORS["dark"],
                    alignment=TA_JUSTIFY,
                    spaceBefore=8,
                    spaceAfter=8,
                    leftIndent=12,
                    rightIndent=12,
                )
            )

            # Analyst note
            self.styles.add(
                ParagraphStyle(
                    name="AnalystNote",
                    parent=self.styles["Normal"],
                    fontSize=9,
                    textColor=self.COLORS["dark"],
                    alignment=TA_JUSTIFY,
                    spaceBefore=6,
                    leftIndent=10,
                )
            )

        def generate_report(
            self,
            ticker: str,
            company_name: str,
            dcf_data: Dict[str, Any],
            scenarios: Optional[Dict[str, Any]] = None,
            commentary: Optional[Dict[str, Any]] = None,
            output_path: Optional[str] = None,
        ) -> bytes:
            """
            Generate enhanced PDF report with charts and analyst commentary.

            Args:
                ticker: Stock ticker
                company_name: Company name
                dcf_data: DCF calculation data
                scenarios: Optional scenario analysis
                commentary: Optional analyst commentary (summary, multiples, notes)
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

            # Header section
            story.extend(self._build_header(ticker, company_name, dcf_data))

            # KPI cards
            story.extend(self._build_kpi_cards(dcf_data))

            # Recommendation badge
            story.extend(self._build_recommendation(dcf_data))

            story.append(Spacer(1, 0.3 * inch))

            # Executive summary from analyst (if provided)
            if commentary and commentary.get("summary"):
                story.extend(self._build_executive_summary(commentary["summary"]))

            # Parameters section
            story.extend(self._build_parameters_section(dcf_data))

            # FCF projections with chart
            story.extend(self._build_fcf_section(dcf_data))

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

        def _build_header(
            self, ticker: str, company_name: str, dcf_data: Dict[str, Any]
        ) -> List:
            """Build header section."""
            elements = []

            # Title
            elements.append(
                Paragraph("Informe de Valoración DCF", self.styles["MainTitle"])
            )

            # Company name and ticker
            elements.append(
                Paragraph(f"{company_name} ({ticker})", self.styles["CompanyName"])
            )

            # Date and price
            market_price = dcf_data.get("market_price", 0)
            date_str = datetime.now().strftime("%d/%m/%Y %H:%M")

            info_data = [
                ["Fecha:", date_str, "Precio de Mercado:", f"${market_price:.2f}"],
            ]

            info_table = Table(
                info_data, colWidths=[1 * inch, 1.5 * inch, 1.5 * inch, 1 * inch]
            )
            info_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("TEXTCOLOR", (0, 0), (0, -1), self.COLORS["muted"]),
                        ("TEXTCOLOR", (2, 0), (2, -1), self.COLORS["muted"]),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ]
                )
            )

            elements.append(info_table)
            elements.append(Spacer(1, 0.3 * inch))

            return elements

        def _build_kpi_cards(self, dcf_data: Dict[str, Any]) -> List:
            """Build KPI cards section."""
            elements = []

            fair_value = dcf_data.get("fair_value", 0)
            market_price = dcf_data.get("market_price", 0)
            shares = dcf_data.get("shares_outstanding", 0)
            fair_value_per_share = fair_value / shares if shares > 0 else 0

            # Calculate upside
            upside = 0
            if market_price > 0 and fair_value_per_share > 0:
                upside = ((fair_value_per_share - market_price) / market_price) * 100

            # KPI data
            kpis = [
                [
                    "Enterprise Value",
                    "Fair Value/Acción",
                    "Precio Mercado",
                    "Upside/Downside",
                ],
                [
                    (
                        f"${fair_value/1e9:.2f}B"
                        if fair_value > 1e9
                        else f"${fair_value/1e6:.0f}M"
                    ),
                    f"${fair_value_per_share:.2f}",
                    f"${market_price:.2f}",
                    f"{upside:+.1f}%",
                ],
            ]

            kpi_table = Table(kpis, colWidths=[1.25 * inch] * 4)

            # Color based on upside
            upside_color = (
                self.COLORS["success"]
                if upside > 20
                else self.COLORS["danger"] if upside < -20 else self.COLORS["muted"]
            )

            kpi_table.setStyle(
                TableStyle(
                    [
                        # Headers
                        ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["light"]),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, 0), 8),
                        ("TEXTCOLOR", (0, 0), (-1, 0), self.COLORS["muted"]),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                        # Values
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 1), (-1, -1), 14),
                        ("TEXTCOLOR", (0, 1), (2, 1), self.COLORS["dark"]),
                        ("TEXTCOLOR", (3, 1), (3, 1), upside_color),
                        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
                        ("TOPPADDING", (0, 1), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 1), (-1, -1), 12),
                        # Borders
                        ("BOX", (0, 0), (-1, -1), 1, self.COLORS["muted"]),
                        ("LINEBELOW", (0, 0), (-1, 0), 1, self.COLORS["muted"]),
                        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ]
                )
            )

            elements.append(kpi_table)
            elements.append(Spacer(1, 0.2 * inch))

            return elements

        def _build_recommendation(self, dcf_data: Dict[str, Any]) -> List:
            """Build recommendation badge."""
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
                    rec_text = "Acción infravalorada - Oportunidad de compra"
                elif upside < -20:
                    rec = "VENDER"
                    rec_color = self.COLORS["danger"]
                    rec_text = "Acción sobrevalorada - Riesgo de corrección"
                else:
                    rec = "MANTENER"
                    rec_color = self.COLORS["warning"]
                    rec_text = "Acción valorada razonablemente"

                rec_data = [["Recomendación:", rec, rec_text]]

                rec_table = Table(
                    rec_data, colWidths=[1.2 * inch, 1.2 * inch, 2.6 * inch]
                )
                rec_table.setStyle(
                    TableStyle(
                        [
                            ("FONTNAME", (0, 0), (0, 0), "Helvetica"),
                            ("FONTNAME", (1, 0), (1, 0), "Helvetica-Bold"),
                            ("FONTNAME", (2, 0), (2, 0), "Helvetica"),
                            ("FONTSIZE", (0, 0), (-1, -1), 10),
                            ("TEXTCOLOR", (1, 0), (1, 0), rec_color),
                            ("ALIGN", (0, 0), (0, 0), "RIGHT"),
                            ("ALIGN", (1, 0), (1, 0), "CENTER"),
                            ("ALIGN", (2, 0), (2, 0), "LEFT"),
                            (
                                "BACKGROUND",
                                (1, 0),
                                (1, 0),
                                colors.Color(
                                    rec_color.red,
                                    rec_color.green,
                                    rec_color.blue,
                                    alpha=0.1,
                                ),
                            ),
                            ("BOX", (1, 0), (1, 0), 2, rec_color),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ("LEFTPADDING", (1, 0), (1, 0), 12),
                            ("RIGHTPADDING", (1, 0), (1, 0), 12),
                        ]
                    )
                )

                elements.append(rec_table)

            return elements

        def _build_parameters_section(self, dcf_data: Dict[str, Any]) -> List:
            """Build parameters section."""
            elements = []

            elements.append(
                Paragraph("Parámetros del Modelo DCF", self.styles["SectionTitle"])
            )

            r = dcf_data.get("discount_rate", 0)
            g = dcf_data.get("growth_rate", 0)
            years = len(dcf_data.get("fcf_projections", []))
            shares = dcf_data.get("shares_outstanding", 0)

            params_data = [
                ["WACC (Tasa de Descuento)", f"{r:.2%}"],
                ["Tasa de Crecimiento Terminal (g)", f"{g:.2%}"],
                ["Horizonte de Proyección", f"{years} años"],
                [
                    "Acciones Diluidas",
                    f"{shares/1e9:.2f}B" if shares > 1e9 else f"{shares/1e6:.0f}M",
                ],
            ]

            params_table = Table(params_data, colWidths=[3.5 * inch, 1.5 * inch])
            params_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("TEXTCOLOR", (0, 0), (0, -1), self.COLORS["dark"]),
                        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
                        ("TEXTCOLOR", (1, 0), (1, -1), self.COLORS["primary"]),
                        ("ALIGN", (0, 0), (0, -1), "LEFT"),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["light"]),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )

            elements.append(params_table)
            elements.append(Spacer(1, 0.3 * inch))

            return elements

        def _build_fcf_section(self, dcf_data: Dict[str, Any]) -> List:
            """Build FCF projections section with chart."""
            elements = []

            elements.append(
                Paragraph("Proyecciones de Free Cash Flow", self.styles["SectionTitle"])
            )

            fcf_projections = dcf_data.get("fcf_projections", [])
            r = dcf_data.get("discount_rate", 0)
            g = dcf_data.get("growth_rate", 0)
            fair_value = dcf_data.get("fair_value", 0)

            # Build table
            fcf_data = [
                ["Año", "FCF Proyectado", "Valor Presente", "% del EV", ""],
            ]

            discounted_fcfs = []
            for i, fcf in enumerate(fcf_projections, 1):
                disc = fcf / ((1 + r) ** i)
                discounted_fcfs.append(disc)
                pct = (disc / fair_value) * 100 if fair_value > 0 else 0

                fcf_data.append(
                    [
                        str(i),
                        f"${fcf/1e6:.0f}M",
                        f"${disc/1e6:.0f}M",
                        f"{pct:.1f}%",
                        self._create_bar_indicator(pct, 4),
                    ]
                )

            # Terminal value
            if fcf_projections and r > g:
                terminal_fcf = fcf_projections[-1] * (1 + g)
                terminal_value = terminal_fcf / (r - g)
                disc_terminal = terminal_value / ((1 + r) ** len(fcf_projections))
                pct_terminal = (
                    (disc_terminal / fair_value) * 100 if fair_value > 0 else 0
                )

                fcf_data.append(
                    [
                        "Terminal",
                        f"${terminal_fcf/1e6:.0f}M",
                        f"${disc_terminal/1e6:.0f}M",
                        f"{pct_terminal:.1f}%",
                        self._create_bar_indicator(pct_terminal, 75),
                    ]
                )

            fcf_table = Table(
                fcf_data,
                colWidths=[0.7 * inch, 1.3 * inch, 1.3 * inch, 0.9 * inch, 0.8 * inch],
            )
            fcf_table.setStyle(
                TableStyle(
                    [
                        # Header
                        ("BACKGROUND", (0, 0), (-2, 0), self.COLORS["primary"]),
                        ("TEXTCOLOR", (0, 0), (-2, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 9),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        # Data
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("ALIGN", (0, 1), (0, -1), "CENTER"),
                        ("ALIGN", (1, 1), (3, -1), "RIGHT"),
                        # Terminal row highlighting
                        ("BACKGROUND", (0, -1), (-2, -1), colors.Color(1, 0.95, 0.8)),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                        # Grid
                        ("GRID", (0, 0), (-2, -1), 0.5, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        (
                            "ROWBACKGROUNDS",
                            (0, 1),
                            (-2, -2),
                            [colors.white, self.COLORS["light"]],
                        ),
                    ]
                )
            )

            elements.append(fcf_table)
            elements.append(Spacer(1, 0.3 * inch))

            return elements

        def _create_bar_indicator(self, value: float, max_value: float) -> Drawing:
            """Create a simple bar indicator for percentage visualization."""
            d = Drawing(50, 10)

            # Background bar
            d.add(Rect(0, 2, 48, 6, fillColor=colors.lightgrey, strokeColor=None))

            # Value bar (proportional)
            width = min((value / max_value) * 48, 48)
            bar_color = (
                self.COLORS["success"]
                if value < 10
                else self.COLORS["warning"] if value < 30 else self.COLORS["primary"]
            )
            d.add(Rect(0, 2, width, 6, fillColor=bar_color, strokeColor=None))

            return d

        def _build_scenarios_section(
            self, scenarios: Dict[str, Any], dcf_data: Dict[str, Any]
        ) -> List:
            """Build scenarios comparison section."""
            elements = []

            elements.append(
                Paragraph("Análisis de Escenarios", self.styles["SectionTitle"])
            )

            # Build scenarios table
            scenario_data = [
                ["Escenario", "Fair Value", "WACC", "g Terminal", "Probabilidad"],
            ]

            for name in ["pessimistic", "base", "optimistic"]:
                if name in scenarios:
                    data = scenarios[name]
                    display_name = {
                        "pessimistic": "Pesimista",
                        "base": "Base",
                        "optimistic": "Optimista",
                    }[name]

                    prob = getattr(data, "probability", 0) * 100

                    scenario_data.append(
                        [
                            display_name,
                            f"${data.fair_value_per_share:.2f}",
                            f"{data.wacc * 100:.2f}%",
                            f"{data.terminal_growth * 100:.2f}%",
                            f"{prob:.0f}%",
                        ]
                    )

            scenario_table = Table(scenario_data, colWidths=[1.2 * inch] * 5)
            scenario_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["secondary"]),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                        ("FONTSIZE", (0, 1), (-1, -1), 9),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        # Highlight base case
                        ("BACKGROUND", (0, 2), (-1, 2), colors.Color(0.9, 0.95, 1)),
                        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
                    ]
                )
            )

            elements.append(scenario_table)
            elements.append(Spacer(1, 0.3 * inch))

            return elements

        def _build_value_breakdown_chart(self, dcf_data: Dict[str, Any]) -> List:
            """Build pie chart showing value breakdown."""
            elements = []

            fcf_projections = dcf_data.get("fcf_projections", [])
            if not fcf_projections:
                return elements

            r = dcf_data.get("discount_rate", 0)
            g = dcf_data.get("growth_rate", 0)

            # Calculate PV of each year
            pv_years = sum(
                fcf / ((1 + r) ** (i + 1)) for i, fcf in enumerate(fcf_projections)
            )

            # Calculate terminal value
            if r > g:
                terminal_fcf = fcf_projections[-1] * (1 + g)
                terminal_value = terminal_fcf / (r - g)
                pv_terminal = terminal_value / ((1 + r) ** len(fcf_projections))
            else:
                pv_terminal = 0

            total = pv_years + pv_terminal

            if total > 0:
                elements.append(
                    Paragraph(
                        "Composición del Enterprise Value", self.styles["SectionTitle"]
                    )
                )

                # Create pie chart
                drawing = Drawing(400, 200)

                pc = Pie()
                pc.x = 150
                pc.y = 50
                pc.width = 120
                pc.height = 120
                pc.data = [pv_years, pv_terminal]
                pc.labels = [
                    f"Proyecciones\nexplícitas\n{(pv_years/total)*100:.1f}%",
                    f"Valor\nTerminal\n{(pv_terminal/total)*100:.1f}%",
                ]
                pc.slices.strokeWidth = 0.5
                pc.slices[0].fillColor = self.COLORS["secondary"]
                pc.slices[1].fillColor = self.COLORS["primary"]

                drawing.add(pc)
                elements.append(drawing)

            return elements

        def _build_executive_summary(self, summary: str) -> List:
            """Build executive summary section with analyst commentary."""
            elements = []

            elements.append(
                Paragraph("📋 Resumen Ejecutivo", self.styles["SectionTitle"])
            )

            # Create a styled box for the summary
            summary_data = [[Paragraph(summary, self.styles["ExecutiveSummary"])]]
            summary_table = Table(summary_data, colWidths=[6.5 * inch])
            summary_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), self.COLORS["light"]),
                        ("BOX", (0, 0), (-1, -1), 2, self.COLORS["primary"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 12),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                        ("TOPPADDING", (0, 0), (-1, -1), 12),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ]
                )
            )

            elements.append(summary_table)
            elements.append(Spacer(1, 0.2 * inch))

            return elements

        def _build_analyst_notes(self, notes: List[Dict[str, str]]) -> List:
            """Build analyst notes section with multiple notes."""
            elements = []

            elements.append(
                Paragraph("📝 Notas del Analista", self.styles["SectionTitle"])
            )

            for note in notes:
                title = note.get("title", "")
                text = note.get("text", "")
                tone = note.get("tone", "neutral")

                # Select color and icon based on tone
                if tone == "positive":
                    icon = "✅"
                    color = self.COLORS["success"]
                elif tone == "negative":
                    icon = "⚠️"
                    color = self.COLORS["danger"]
                else:
                    icon = "ℹ️"
                    color = self.COLORS["primary"]

                # Create note box
                note_title = f"<b>{icon} {title}</b>"
                note_content = [[Paragraph(note_title, self.styles["Normal"])]]
                note_content.append([Paragraph(text, self.styles["AnalystNote"])])

                note_table = Table(note_content, colWidths=[6.5 * inch])
                note_table.setStyle(
                    TableStyle(
                        [
                            ("BACKGROUND", (0, 0), (-1, 0), color),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                            ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                            ("BOX", (0, 0), (-1, -1), 1, color),
                            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("LEFTPADDING", (0, 0), (-1, -1), 10),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                            ("TOPPADDING", (0, 0), (-1, -1), 8),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                        ]
                    )
                )

                elements.append(note_table)
                elements.append(Spacer(1, 0.15 * inch))

            return elements

        def _build_multiples_section(self, multiples_text: str) -> List:
            """Build multiples commentary section."""
            elements = []

            elements.append(
                Paragraph("📊 Análisis de Múltiplos", self.styles["SectionTitle"])
            )

            multiples_data = [[Paragraph(multiples_text, self.styles["AnalystNote"])]]
            multiples_table = Table(multiples_data, colWidths=[6.5 * inch])
            multiples_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f0f9ff")),
                        ("BOX", (0, 0), (-1, -1), 1, self.COLORS["secondary"]),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ]
                )
            )

            elements.append(multiples_table)
            elements.append(Spacer(1, 0.2 * inch))

            return elements

        def _build_sensitivity_analysis(self, dcf_data: Dict[str, Any]) -> List:
            """Build sensitivity analysis matrix showing fair value at different WACC and g."""
            elements = []

            r = dcf_data.get("discount_rate", 0.08)
            g = dcf_data.get("growth_rate", 0.03)
            fcf_projections = dcf_data.get("fcf_projections", [])
            shares = dcf_data.get("shares_outstanding", 1)

            if not fcf_projections or shares == 0:
                return elements

            elements.append(
                Paragraph("📈 Análisis de Sensibilidad", self.styles["SectionTitle"])
            )
            elements.append(
                Paragraph(
                    "Valor razonable por acción según diferentes combinaciones de WACC y tasa de crecimiento terminal:",
                    self.styles["Normal"],
                )
            )
            elements.append(Spacer(1, 0.1 * inch))

            # Generate sensitivity matrix
            wacc_range = [r - 0.02, r - 0.01, r, r + 0.01, r + 0.02]
            g_range = [g - 0.01, g - 0.005, g, g + 0.005, g + 0.01]

            # Build table data
            header = ["WACC / g"] + [f"{g_val:.2%}" for g_val in g_range]
            table_data = [header]

            for wacc_val in wacc_range:
                row = [f"{wacc_val:.2%}"]
                for g_val in g_range:
                    if wacc_val > g_val:
                        # Calculate PV of explicit period
                        pv_years = sum(
                            fcf / ((1 + wacc_val) ** (i + 1))
                            for i, fcf in enumerate(fcf_projections)
                        )
                        # Calculate terminal value
                        terminal_fcf = fcf_projections[-1] * (1 + g_val)
                        terminal_value = terminal_fcf / (wacc_val - g_val)
                        pv_terminal = terminal_value / (
                            (1 + wacc_val) ** len(fcf_projections)
                        )
                        fair_value_per_share = (pv_years + pv_terminal) / shares
                        row.append(f"${fair_value_per_share:.2f}")
                    else:
                        row.append("N/A")
                table_data.append(row)

            # Create table
            sens_table = Table(table_data, colWidths=[1 * inch] + [1 * inch] * 5)

            # Base case coordinates (center of matrix)
            base_row = 3  # r in the middle
            base_col = 3  # g in the middle

            sens_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                        ("BACKGROUND", (0, 0), (-1, 0), self.COLORS["primary"]),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("BACKGROUND", (0, 1), (0, -1), self.COLORS["secondary"]),
                        ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
                        (
                            "BACKGROUND",
                            (base_col, base_row),
                            (base_col, base_row),
                            colors.HexColor("#fef3c7"),
                        ),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ]
                )
            )

            elements.append(sens_table)
            elements.append(Spacer(1, 0.2 * inch))

            return elements

        def _build_disclaimer(self) -> List:
            """Build disclaimer section."""
            elements = []

            elements.append(Spacer(1, 0.3 * inch))

            disclaimer_text = (
                "<b>DISCLAIMER:</b> Este informe es solo para fines informativos y educativos. "
                "No constituye asesoramiento financiero ni recomendación de inversión. "
                "Las proyecciones y valoraciones son estimaciones sujetas a incertidumbre. "
                "Consulte con un asesor financiero profesional antes de tomar decisiones de inversión."
            )

            elements.append(Paragraph(disclaimer_text, self.styles["Disclaimer"]))

            elements.append(Spacer(1, 0.1 * inch))

            footer_text = f"Generado por DCF Valuation Platform · {datetime.now().strftime('%d/%m/%Y %H:%M')} · Powered by Claude Code"
            elements.append(Paragraph(footer_text, self.styles["Disclaimer"]))

            return elements

    def generate_enhanced_dcf_report(
        ticker: str,
        company_name: str,
        dcf_data: Dict[str, Any],
        scenarios: Optional[Dict[str, Any]] = None,
        commentary: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> bytes:
        """
        Convenience function to generate enhanced DCF report.

        Args:
            ticker: Stock ticker
            company_name: Company name
            dcf_data: DCF data dictionary
            scenarios: Optional scenarios dict
            commentary: Optional analyst commentary dict
            output_path: Optional output path

        Returns:
            PDF bytes
        """
        generator = EnhancedPDFReportGenerator()
        return generator.generate_report(
            ticker, company_name, dcf_data, scenarios, commentary, output_path
        )

else:
    # Fallback when reportlab is not available
    class EnhancedPDFReportGenerator:
        """Placeholder class when reportlab is not available."""

        def __init__(self):
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install with: pip install reportlab"
            )

    def generate_enhanced_dcf_report(*args, **kwargs):
        """Placeholder function when reportlab is not available."""
        raise ImportError(
            "reportlab is required for PDF generation. "
            "Install with: pip install reportlab"
        )
