"""
Advanced HTML Report Generator with Professional Financial Design.

Features:
- Bloomberg/Goldman Sachs inspired design (deep blue theme)
- Interactive Plotly charts (waterfall, sensitivity, DCF breakdown)
- Advanced financial tables with color coding
- Optimized for print (Ctrl+P → PDF)
- Individual chart export (PNG/SVG high-resolution)
- Responsive design with Tailwind CSS
- Jinja2 templates for maintainability
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import plotly.io as pio

    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape

    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False

from src.reports.report_calculations import (
    ReportCalculations,
    DCFReportData,
)


class AdvancedHTMLGenerator:
    """
    Professional financial report generator with advanced visualizations.

    Design Philosophy:
    - Inspired by Bloomberg Terminal and Goldman Sachs equity research
    - Deep blue color scheme (#0A1929 primary, #1E3A5F accents)
    - Clean typography (Inter font family)
    - Print-optimized CSS
    - Interactive charts that gracefully degrade in print
    """

    # Color Palette (Financial Professional Theme)
    COLORS = {
        "primary_dark": "#0A1929",  # Deep navy blue
        "primary": "#1E3A5F",  # Medium blue
        "primary_light": "#2E4A6F",  # Light blue
        "accent": "#2E7D32",  # Green (positive)
        "danger": "#C62828",  # Red (negative)
        "warning": "#F57C00",  # Orange (hold)
        "gold": "#F9A825",  # Gold (premium)
        "muted": "#64748B",  # Gray
        "border": "#E2E8F0",  # Light gray
        "bg_light": "#F8FAFC",  # Off-white
        "bg_card": "#FFFFFF",  # White
    }

    def __init__(self):
        """Initialize generator with templates directory."""
        if not PLOTLY_AVAILABLE:
            raise ImportError("plotly required: pip install plotly kaleido")
        if not JINJA2_AVAILABLE:
            raise ImportError("jinja2 required: pip install jinja2")

        # Setup templates directory
        self.templates_dir = Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)

        # Setup output directory for charts
        self.charts_dir = Path("output") / "charts"
        self.charts_dir.mkdir(parents=True, exist_ok=True)

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )

        # Register custom filters
        self.env.filters["format_currency"] = self._filter_currency
        self.env.filters["format_percent"] = self._filter_percent
        self.env.filters["format_large"] = self._filter_large_number

    def generate_dcf_report(
        self,
        dcf_data: DCFReportData,
        output_path: Optional[str] = None,
        include_charts: bool = True,
    ) -> str:
        """
        Generate comprehensive DCF report HTML.

        Args:
            dcf_data: DCFReportData with all valuation information
            output_path: Optional path to save HTML file
            include_charts: Whether to generate interactive charts

        Returns:
            HTML content as string
        """
        # Generate charts if requested
        charts = {}
        if include_charts:
            charts = self._generate_all_charts(dcf_data)

        # Build context for template
        context = self._build_dcf_context(dcf_data, charts)

        # Render HTML
        html = self._render_template("dcf_report.html", context)

        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html, encoding="utf-8")

        return html

    def _generate_all_charts(self, dcf_data: DCFReportData) -> Dict[str, str]:
        """
        Generate all charts and return as dict of {chart_name: html_div}.

        Charts generated:
        1. DCF Waterfall Chart (FCF buildup to equity value)
        2. Sensitivity Analysis Heatmap (WACC vs Terminal Growth)
        3. Value Breakdown Pie Chart
        4. FCF Projection with Growth Rates
        """
        charts = {}

        # 1. DCF Waterfall Chart
        charts["waterfall"] = self._create_waterfall_chart(dcf_data)

        # 2. Sensitivity Analysis
        charts["sensitivity"] = self._create_sensitivity_chart(dcf_data)

        # 3. Value Breakdown
        charts["value_breakdown"] = self._create_value_breakdown_chart(dcf_data)

        # 4. FCF Projections
        if dcf_data.fcf_projections:
            charts["fcf_projection"] = self._create_fcf_projection_chart(dcf_data)

        return charts

    def _create_waterfall_chart(self, dcf_data: DCFReportData) -> str:
        """
        Create DCF waterfall chart showing value buildup.

        Flow: PV(FCF Years 1-5) + Terminal Value = Enterprise Value - Net Debt = Equity Value
        """
        # Calculate components
        pv_fcf_projections = 0
        if dcf_data.fcf_projections:
            for i, fcf in enumerate(dcf_data.fcf_projections, 1):
                pv = fcf / ((1 + dcf_data.wacc) ** i)
                pv_fcf_projections += pv

        terminal_value_pv = dcf_data.terminal_value / (
            (1 + dcf_data.wacc) ** dcf_data.projection_years
        )
        enterprise_value = pv_fcf_projections + terminal_value_pv
        net_debt = dcf_data.total_debt - dcf_data.cash
        equity_value = dcf_data.fair_value_total

        # Waterfall data
        labels = [
            "PV FCF<br>(Years 1-5)",
            "PV Terminal<br>Value",
            "Enterprise<br>Value",
            f"{'Less' if net_debt > 0 else 'Add'}<br>Net Debt",
            "Equity<br>Value",
        ]

        values = [
            pv_fcf_projections / 1e9,  # Billions
            terminal_value_pv / 1e9,
            0,  # Total (calculated by waterfall)
            -net_debt / 1e9 if net_debt > 0 else abs(net_debt) / 1e9,
            0,  # Total (calculated by waterfall)
        ]

        measures = ["relative", "relative", "total", "relative", "total"]

        fig = go.Figure(
            go.Waterfall(
                name="DCF Components",
                orientation="v",
                measure=measures,
                x=labels,
                y=values,
                text=[f"${v:.1f}B" for v in values],
                textposition="outside",
                connector={"line": {"color": self.COLORS["border"]}},
                increasing={"marker": {"color": self.COLORS["accent"]}},
                decreasing={"marker": {"color": self.COLORS["danger"]}},
                totals={"marker": {"color": self.COLORS["primary"]}},
            )
        )

        fig.update_layout(
            title={
                "text": "DCF Waterfall Analysis",
                "font": {"size": 18, "color": self.COLORS["primary_dark"]},
            },
            showlegend=False,
            paper_bgcolor="white",
            plot_bgcolor="white",
            font={"family": "Inter, sans-serif"},
            yaxis={"title": "Value ($B)", "gridcolor": self.COLORS["border"]},
            height=400,
            margin=dict(l=50, r=50, t=80, b=50),
        )

        return fig.to_html(
            include_plotlyjs="cdn",
            div_id="waterfall_chart",
            config={
                "displayModeBar": True,
                "toImageButtonOptions": {"height": 600, "width": 1000},
            },
        )

    def _create_sensitivity_chart(self, dcf_data: DCFReportData) -> str:
        """
        Create sensitivity analysis heatmap (WACC vs Terminal Growth).

        Shows how fair value per share changes with different assumptions.
        """
        # Define ranges
        wacc_base = dcf_data.wacc
        g_base = dcf_data.terminal_growth

        wacc_range = [
            wacc_base * 0.8,
            wacc_base * 0.9,
            wacc_base,
            wacc_base * 1.1,
            wacc_base * 1.2,
        ]
        g_range = [
            g_base - 0.02,
            g_base - 0.01,
            g_base,
            g_base + 0.01,
            g_base + 0.02,
        ]

        # Calculate fair values for each combination
        z_values = []
        for g in g_range:
            row = []
            for wacc in wacc_range:
                if wacc <= g:
                    row.append(None)  # Invalid (WACC must be > g)
                else:
                    # Simplified calculation (should use full DCF in production)
                    # Fair Value ≈ FCF × (1+g) / (WACC - g) / shares
                    implied_fv = (
                        dcf_data.base_fcf * (1 + g) / (wacc - g)
                    ) / dcf_data.shares_outstanding
                    row.append(implied_fv)
            z_values.append(row)

        fig = go.Figure(
            data=go.Heatmap(
                z=z_values,
                x=[f"{w:.1%}" for w in wacc_range],
                y=[f"{g:.1%}" for g in g_range],
                text=[[f"${v:.0f}" if v else "N/A" for v in row] for row in z_values],
                texttemplate="%{text}",
                textfont={"size": 10},
                colorscale=[
                    [0, self.COLORS["danger"]],
                    [0.5, self.COLORS["warning"]],
                    [1, self.COLORS["accent"]],
                ],
                showscale=True,
                colorbar={"title": "Fair Value<br>per Share ($)"},
            )
        )

        fig.update_layout(
            title={
                "text": "Sensitivity Analysis: Fair Value per Share",
                "font": {"size": 18, "color": self.COLORS["primary_dark"]},
            },
            xaxis={"title": "WACC (Discount Rate)", "side": "bottom"},
            yaxis={"title": "Terminal Growth Rate"},
            paper_bgcolor="white",
            plot_bgcolor="white",
            font={"family": "Inter, sans-serif"},
            height=400,
            margin=dict(l=80, r=80, t=80, b=80),
        )

        # Add marker for base case
        fig.add_annotation(
            x=f"{wacc_base:.1%}",
            y=f"{g_base:.1%}",
            text="Base<br>Case",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor=self.COLORS["primary_dark"],
            ax=-40,
            ay=-40,
            font={"size": 12, "color": self.COLORS["primary_dark"]},
            bgcolor="white",
            bordercolor=self.COLORS["primary_dark"],
            borderwidth=2,
        )

        return fig.to_html(
            include_plotlyjs="cdn",
            div_id="sensitivity_chart",
            config={"displayModeBar": True},
        )

    def _create_value_breakdown_chart(self, dcf_data: DCFReportData) -> str:
        """Create pie chart showing value composition."""
        # Calculate components
        pv_fcf_projections = 0
        if dcf_data.fcf_projections:
            for i, fcf in enumerate(dcf_data.fcf_projections, 1):
                pv = fcf / ((1 + dcf_data.wacc) ** i)
                pv_fcf_projections += pv

        terminal_value_pv = dcf_data.terminal_value / (
            (1 + dcf_data.wacc) ** dcf_data.projection_years
        )

        labels = ["PV of Projected FCF", "PV of Terminal Value"]
        values = [pv_fcf_projections, terminal_value_pv]
        colors = [self.COLORS["primary"], self.COLORS["primary_light"]]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker={"colors": colors, "line": {"color": "white", "width": 2}},
                    textinfo="label+percent",
                    textfont={"size": 12},
                    hovertemplate="<b>%{label}</b><br>$%{value:.2f}B<br>%{percent}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title={
                "text": "Enterprise Value Composition",
                "font": {"size": 18, "color": self.COLORS["primary_dark"]},
            },
            showlegend=True,
            legend={"orientation": "h", "y": -0.1},
            paper_bgcolor="white",
            font={"family": "Inter, sans-serif"},
            height=400,
            margin=dict(l=50, r=50, t=80, b=80),
        )

        return fig.to_html(
            include_plotlyjs="cdn",
            div_id="value_breakdown_chart",
            config={"displayModeBar": True},
        )

    def _create_fcf_projection_chart(self, dcf_data: DCFReportData) -> str:
        """Create bar chart with FCF projections and growth rates."""
        if not dcf_data.fcf_projections:
            return ""

        years = list(range(1, len(dcf_data.fcf_projections) + 1))
        fcf_values = [fcf / 1e9 for fcf in dcf_data.fcf_projections]  # Billions

        # Calculate year-over-year growth rates
        growth_rates = []
        for i in range(len(dcf_data.fcf_projections)):
            if i == 0:
                # First year growth vs base FCF
                growth = (
                    (dcf_data.fcf_projections[0] - dcf_data.base_fcf)
                    / dcf_data.base_fcf
                    if dcf_data.base_fcf != 0
                    else 0
                )
            else:
                growth = (
                    (dcf_data.fcf_projections[i] - dcf_data.fcf_projections[i - 1])
                    / dcf_data.fcf_projections[i - 1]
                    if dcf_data.fcf_projections[i - 1] != 0
                    else 0
                )
            growth_rates.append(growth * 100)

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add FCF bars
        fig.add_trace(
            go.Bar(
                name="Free Cash Flow",
                x=years,
                y=fcf_values,
                text=[f"${v:.1f}B" for v in fcf_values],
                textposition="outside",
                marker={"color": self.COLORS["primary"]},
            ),
            secondary_y=False,
        )

        # Add growth rate line
        fig.add_trace(
            go.Scatter(
                name="YoY Growth",
                x=years,
                y=growth_rates,
                mode="lines+markers",
                line={"color": self.COLORS["accent"], "width": 3},
                marker={"size": 8},
                text=[f"{g:+.1f}%" for g in growth_rates],
                textposition="top center",
            ),
            secondary_y=True,
        )

        fig.update_layout(
            title={
                "text": "Free Cash Flow Projections",
                "font": {"size": 18, "color": self.COLORS["primary_dark"]},
            },
            paper_bgcolor="white",
            plot_bgcolor="white",
            font={"family": "Inter, sans-serif"},
            legend={"orientation": "h", "y": -0.15},
            height=400,
            margin=dict(l=50, r=50, t=80, b=80),
        )

        fig.update_xaxes(title_text="Year", gridcolor=self.COLORS["border"])
        fig.update_yaxes(
            title_text="FCF ($B)", secondary_y=False, gridcolor=self.COLORS["border"]
        )
        fig.update_yaxes(title_text="Growth Rate (%)", secondary_y=True, showgrid=False)

        return fig.to_html(
            include_plotlyjs="cdn",
            div_id="fcf_projection_chart",
            config={"displayModeBar": True},
        )

    def _build_dcf_context(
        self, dcf_data: DCFReportData, charts: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build context dictionary for template rendering."""
        # Calculate metrics
        upside = ReportCalculations.calculate_upside(
            dcf_data.fair_value_per_share, dcf_data.market_price
        )
        recommendation, rec_color = ReportCalculations.get_recommendation(upside)

        # Validate model
        warnings = ReportCalculations.validate_dcf_sanity(dcf_data)

        context = {
            "meta": {
                "ticker": dcf_data.ticker,
                "company_name": dcf_data.company_name,
                "sector": dcf_data.sector,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "report_type": "DCF Valuation Report",
            },
            "valuation": {
                "fair_value_per_share": dcf_data.fair_value_per_share,
                "market_price": dcf_data.market_price,
                "upside_pct": upside,
                "recommendation": recommendation.value,
                "recommendation_color": rec_color.value,
                "market_cap": dcf_data.market_cap,
                "enterprise_value": dcf_data.enterprise_value,
            },
            "dcf_params": {
                "wacc": dcf_data.wacc,
                "terminal_growth": dcf_data.terminal_growth,
                "projection_years": dcf_data.projection_years,
                "base_fcf": dcf_data.base_fcf,
            },
            "balance_sheet": {
                "total_debt": dcf_data.total_debt,
                "cash": dcf_data.cash,
                "net_debt": dcf_data.total_debt - dcf_data.cash,
            },
            "charts": charts,
            "warnings": warnings,
            "colors": self.COLORS,
        }

        return context

    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render Jinja2 template with context."""
        # Create template if it doesn't exist
        template_path = self.templates_dir / template_name
        if not template_path.exists():
            self._create_default_template(template_path)

        template = self.env.get_template(template_name)
        return template.render(**context)

    def _create_default_template(self, template_path: Path):
        """Create default professional financial template."""
        template_content = self._get_professional_template()
        template_path.write_text(template_content, encoding="utf-8")

    def _get_professional_template(self) -> str:
        """Get professional HTML template with Tailwind-inspired CSS."""
        return """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ meta.report_type }} - {{ meta.ticker }}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        /* Professional Financial Theme - Inspired by Bloomberg/Goldman Sachs */
        :root {
            --primary-dark: {{ colors.primary_dark }};
            --primary: {{ colors.primary }};
            --primary-light: {{ colors.primary_light }};
            --accent: {{ colors.accent }};
            --danger: {{ colors.danger }};
            --warning: {{ colors.warning }};
            --gold: {{ colors.gold }};
            --muted: {{ colors.muted }};
            --border: {{ colors.border }};
            --bg-light: {{ colors.bg_light }};
            --bg-card: {{ colors.bg_card }};
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg-light);
            color: var(--primary-dark);
            line-height: 1.6;
            font-size: 14px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        /* Header Section */
        .report-header {
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
            color: white;
            padding: 40px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(10, 25, 41, 0.2);
        }

        .report-title {
            font-size: 32px;
            font-weight: 800;
            margin-bottom: 8px;
            letter-spacing: -0.5px;
        }

        .report-subtitle {
            font-size: 18px;
            opacity: 0.9;
            font-weight: 400;
        }

        .report-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }

        .meta-item {
            font-size: 13px;
            opacity: 0.8;
        }

        /* KPI Cards */
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .kpi-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        }

        .kpi-label {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            color: var(--muted);
            font-weight: 600;
            margin-bottom: 8px;
        }

        .kpi-value {
            font-size: 28px;
            font-weight: 800;
            color: var(--primary-dark);
            margin-bottom: 4px;
        }

        .kpi-subvalue {
            font-size: 13px;
            color: var(--muted);
        }

        /* Recommendation Badge */
        .recommendation-badge {
            display: inline-block;
            padding: 8px 16px;
            border-radius: 6px;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 0.5px;
        }

        .badge-success {
            background: #D1F4E0;
            color: var(--accent);
        }

        .badge-warning {
            background: #FFE8CC;
            color: var(--warning);
        }

        .badge-danger {
            background: #FFE0E0;
            color: var(--danger);
        }

        /* Section */
        .section {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        }

        .section-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--primary-dark);
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid var(--primary);
        }

        /* Charts */
        .chart-container {
            margin: 20px 0;
            border-radius: 8px;
            overflow: hidden;
        }

        /* Table */
        .financial-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }

        .financial-table thead {
            background: var(--primary-dark);
            color: white;
        }

        .financial-table th {
            padding: 12px 16px;
            text-align: right;
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .financial-table th:first-child {
            text-align: left;
        }

        .financial-table td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            text-align: right;
        }

        .financial-table td:first-child {
            text-align: left;
            font-weight: 600;
        }

        .financial-table tbody tr:hover {
            background: var(--bg-light);
        }

        /* Warning Box */
        .warning-box {
            background: #FFF4E6;
            border-left: 4px solid var(--warning);
            padding: 16px 20px;
            border-radius: 8px;
            margin: 20px 0;
        }

        .warning-box-title {
            font-weight: 700;
            color: var(--warning);
            margin-bottom: 8px;
        }

        .warning-item {
            font-size: 13px;
            color: #8B5A00;
            margin: 4px 0;
        }

        /* Footer */
        .report-footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px dashed var(--border);
            text-align: center;
            font-size: 11px;
            color: var(--muted);
        }

        /* Print Styles */
        @media print {
            body {
                background: white;
            }

            .container {
                max-width: 100%;
                padding: 0;
            }

            .section {
                page-break-inside: avoid;
                box-shadow: none;
            }

            .kpi-card {
                box-shadow: none;
            }

            .chart-container {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="report-header">
            <div class="report-title">{{ meta.ticker }} - {{ meta.company_name }}</div>
            <div class="report-subtitle">{{ meta.report_type }}</div>
            <div class="report-meta">
                <div class="meta-item">{{ meta.sector }}</div>
                <div class="meta-item">Generated: {{ meta.date }}</div>
            </div>
        </div>

        <!-- KPI Grid -->
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Fair Value / Share</div>
                <div class="kpi-value">{{ valuation.fair_value_per_share | format_currency }}</div>
                <div class="kpi-subvalue">Current: {{ valuation.market_price | format_currency }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Upside / Downside</div>
                <div class="kpi-value" style="color: {% if valuation.upside_pct > 0 %}var(--accent){% else %}var(--danger){% endif %}">
                    {{ valuation.upside_pct | format_percent }}
                </div>
                <div class="kpi-subvalue">
                    <span class="recommendation-badge badge-{{ valuation.recommendation_color }}">
                        {{ valuation.recommendation }}
                    </span>
                </div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Enterprise Value</div>
                <div class="kpi-value">{{ valuation.enterprise_value | format_large }}</div>
                <div class="kpi-subvalue">Market Cap: {{ valuation.market_cap | format_large }}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">WACC / Terminal Growth</div>
                <div class="kpi-value">{{ dcf_params.wacc | format_percent }}</div>
                <div class="kpi-subvalue">g = {{ dcf_params.terminal_growth | format_percent }}</div>
            </div>
        </div>

        <!-- Warnings (if any) -->
        {% if warnings %}
        <div class="warning-box">
            <div class="warning-box-title">⚠️ Model Validation Warnings</div>
            {% for warning in warnings %}
            <div class="warning-item">{{ warning }}</div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- DCF Waterfall Chart -->
        {% if charts.waterfall %}
        <div class="section">
            <div class="section-title">DCF Waterfall Analysis</div>
            <div class="chart-container">
                {{ charts.waterfall | safe }}
            </div>
        </div>
        {% endif %}

        <!-- Sensitivity Analysis -->
        {% if charts.sensitivity %}
        <div class="section">
            <div class="section-title">Sensitivity Analysis</div>
            <div class="chart-container">
                {{ charts.sensitivity | safe }}
            </div>
        </div>
        {% endif %}

        <!-- Value Breakdown -->
        {% if charts.value_breakdown %}
        <div class="section">
            <div class="section-title">Enterprise Value Composition</div>
            <div class="chart-container">
                {{ charts.value_breakdown | safe }}
            </div>
        </div>
        {% endif %}

        <!-- FCF Projections -->
        {% if charts.fcf_projection %}
        <div class="section">
            <div class="section-title">Free Cash Flow Projections</div>
            <div class="chart-container">
                {{ charts.fcf_projection | safe }}
            </div>
        </div>
        {% endif %}

        <!-- DCF Parameters Table -->
        <div class="section">
            <div class="section-title">Valuation Parameters</div>
            <table class="financial-table">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                        <th>Notes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>WACC</td>
                        <td>{{ dcf_params.wacc | format_percent }}</td>
                        <td>Weighted Average Cost of Capital</td>
                    </tr>
                    <tr>
                        <td>Terminal Growth Rate</td>
                        <td>{{ dcf_params.terminal_growth | format_percent }}</td>
                        <td>Perpetuity growth assumption</td>
                    </tr>
                    <tr>
                        <td>Projection Period</td>
                        <td>{{ dcf_params.projection_years }} years</td>
                        <td>Explicit forecast period</td>
                    </tr>
                    <tr>
                        <td>Base FCF</td>
                        <td>{{ dcf_params.base_fcf | format_large }}</td>
                        <td>Latest year free cash flow</td>
                    </tr>
                    <tr>
                        <td>Total Debt</td>
                        <td>{{ balance_sheet.total_debt | format_large }}</td>
                        <td>Interest-bearing debt</td>
                    </tr>
                    <tr>
                        <td>Cash & Equivalents</td>
                        <td>{{ balance_sheet.cash | format_large }}</td>
                        <td>Liquid assets</td>
                    </tr>
                    <tr>
                        <td>Net Debt</td>
                        <td>{{ balance_sheet.net_debt | format_large }}</td>
                        <td>Total Debt - Cash</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- Footer -->
        <div class="report-footer">
            <div>DISCLAIMER: This report is for educational purposes only and does not constitute investment advice.</div>
            <div>DCF valuation based on {{ dcf_params.projection_years }}-year projection with {{ dcf_params.terminal_growth | format_percent }} terminal growth.</div>
            <div>Generated with Claude Code DCF Platform · {{ meta.date }}</div>
        </div>
    </div>
</body>
</html>
"""

    # Template filters
    def _filter_currency(self, value: float) -> str:
        """Format as currency."""
        return f"${value:,.2f}"

    def _filter_percent(self, value: float) -> str:
        """Format as percentage."""
        if abs(value) < 1:  # Decimal format (0.08 = 8%)
            value = value * 100
        return f"{value:.2f}%"

    def _filter_large_number(self, value: float) -> str:
        """Format large numbers (billions/millions)."""
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.1f}M"
        else:
            return f"${value:,.0f}"


# Convenience function
def generate_professional_report(
    dcf_data: DCFReportData,
    output_path: str = "output/dcf_report.html",
) -> str:
    """
    Quick function to generate professional HTML report.

    Args:
        dcf_data: DCFReportData with valuation information
        output_path: Where to save the HTML file

    Returns:
        HTML content as string
    """
    generator = AdvancedHTMLGenerator()
    return generator.generate_dcf_report(dcf_data, output_path=output_path)
