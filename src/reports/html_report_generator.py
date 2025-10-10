"""
Professional HTML Report Generator for DCF Valuation.

Generates sophisticated, professional-looking reports with:
- Executive summary with KPIs
- Scenario analysis
- Detailed FCF projections
- Valuation multiples
- Analyst commentary (editable)
- Assumptions documentation
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


class HTMLReportGenerator:
    """Generate professional HTML reports for DCF analysis with analyst commentary."""

    def __init__(self):
        """Initialize the report generator."""
        self.report_dir = Path(__file__).parent / "templates"
        self.assets_dir = Path(__file__).parent / "assets"
        self.report_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)

    def generate_report(
        self,
        ticker: str,
        company_name: str,
        dcf_result: Dict[str, Any],
        scenarios: Dict[str, Any],
        market_price: float,
        commentary: Optional[Dict[str, Any]] = None,
        output_path: Optional[str] = None,
    ) -> str:
        """
        Generate comprehensive HTML report.

        Args:
            ticker: Stock ticker
            company_name: Full company name
            dcf_result: DCF calculation results from enhanced_model
            scenarios: Scenario analysis results (pessimistic, base, optimistic)
            market_price: Current market price
            commentary: Optional analyst commentary dict with keys:
                - summary: Executive summary comment
                - multiples: Comment on valuation multiples
                - notes: List of {title, text, tone} for detailed notes
            output_path: Where to save the HTML file

        Returns:
            HTML content as string
        """
        # Build context for template
        context = self._build_context(
            ticker, company_name, dcf_result, scenarios, market_price, commentary
        )

        # Generate HTML
        html = self._render_html(context)

        # Save to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(html, encoding="utf-8")

        return html

    def _build_context(
        self,
        ticker: str,
        company_name: str,
        dcf_result: Dict[str, Any],
        scenarios: Dict[str, Any],
        market_price: float,
        commentary: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Build context dictionary for template rendering."""

        # Extract data from dcf_result
        fair_value_per_share = dcf_result.get("fair_value_per_share", 0)
        enterprise_value = dcf_result.get("enterprise_value", 0)
        equity_value = dcf_result.get("equity_value", 0)
        wacc = dcf_result.get("wacc", 0)
        terminal_growth = dcf_result.get("terminal_growth", 0)
        projected_fcf = dcf_result.get("projected_fcf", [])
        growth_rates = dcf_result.get("growth_rates", [])
        diluted_shares = dcf_result.get("diluted_shares", 0)
        cash = dcf_result.get("cash", 0)
        debt = dcf_result.get("debt", 0)

        # Calculate upside/downside
        if market_price > 0 and fair_value_per_share > 0:
            upside_pct = ((fair_value_per_share - market_price) / market_price) * 100
        else:
            upside_pct = 0

        # Determine recommendation
        if upside_pct > 20:
            recommendation = "COMPRAR"
            reco_class = "buy"
        elif upside_pct < -20:
            recommendation = "VENDER"
            reco_class = "sell"
        else:
            recommendation = "MANTENER"
            reco_class = "hold"

        # Format scenarios
        scenario_list = []
        for name, data in scenarios.items():
            if name in ["pessimistic", "base", "optimistic"]:
                display_name = {
                    "pessimistic": "Pesimista",
                    "base": "Base",
                    "optimistic": "Optimista",
                }[name]
                scenario_list.append(
                    {
                        "name": display_name,
                        "fair_value": f"{data.fair_value_per_share:.2f}",
                        "wacc_pct": f"{data.wacc * 100:.2f}",
                        "g_pct": f"{data.terminal_growth * 100:.2f}",
                    }
                )

        # Calculate FCF projections with present values
        fcf_rows = []
        total_pv = enterprise_value
        for i, (fcf, growth) in enumerate(zip(projected_fcf, growth_rates), 1):
            pv = fcf / ((1 + wacc) ** i)
            fcf_rows.append(
                {
                    "year": i,
                    "fcf_mil": f"{fcf / 1e6:,.0f}",
                    "vp_mil": f"{pv / 1e6:,.0f}",
                    "weight_pct": (
                        f"{(pv / total_pv) * 100:.1f}" if total_pv > 0 else "0.0"
                    ),
                }
            )

        # Terminal value
        if projected_fcf:
            terminal_fcf = projected_fcf[-1] * (1 + terminal_growth)
            terminal_value = terminal_fcf / (wacc - terminal_growth)
            terminal_pv = terminal_value / ((1 + wacc) ** len(projected_fcf))
        else:
            terminal_fcf = 0
            terminal_pv = 0

        # Get valuation multiples if available
        multiples = dcf_result.get("valuation_metrics", {})
        ev_ebitda = multiples.get("ev_ebitda", "N/A")
        pe = multiples.get("pe_ratio", "N/A")
        pb = multiples.get("pb_ratio", "N/A")

        if isinstance(ev_ebitda, (int, float)):
            ev_ebitda = f"{ev_ebitda:.1f}"
        if isinstance(pe, (int, float)):
            pe = f"{pe:.1f}"
        if isinstance(pb, (int, float)):
            pb = f"{pb:.1f}"

        # Build commentary
        if commentary is None:
            commentary = {}

        default_summary = self._generate_default_summary(
            fair_value_per_share, market_price, upside_pct
        )
        default_multiples_comment = self._generate_default_multiples_comment(
            ev_ebitda, pe, pb
        )

        commentary_dict = {
            "summary": commentary.get("summary", default_summary),
            "multiples": commentary.get("multiples", default_multiples_comment),
            "notes": commentary.get("notes", []),
        }

        # Build assumptions
        assumptions = {
            "operating": [
                (
                    f"Crecimiento FCF promedio: {sum(growth_rates)/len(growth_rates)*100:.1f}%"
                    if growth_rates
                    else "N/A"
                ),
                f"WACC (tasa de descuento): {wacc*100:.2f}%",
                f"Tasa de crecimiento terminal: {terminal_growth*100:.2f}%",
            ],
            "capital": [
                (
                    f"Deuda neta: ${(debt - cash)/1e9:.2f}B"
                    if debt > cash
                    else f"Caja neta: ${(cash - debt)/1e9:.2f}B"
                ),
                (
                    f"Acciones diluidas: {diluted_shares/1e9:.2f}B"
                    if diluted_shares > 1e9
                    else f"{diluted_shares/1e6:.0f}M"
                ),
                f"Método: {'WACC calculado (CAPM)' if 'wacc_components' in dcf_result else 'WACC personalizado'}",
            ],
        }

        # Build context
        context = {
            "meta": {
                "symbol": ticker,
                "name": company_name,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "price": f"{market_price:.2f}",
                "shares_mil": f"{diluted_shares/1e6:,.0f}",
            },
            "summary": {
                "ev_bil": f"{enterprise_value/1e9:.2f}",
                "eq_bil": f"{equity_value/1e9:.2f}",
                "fv_per_share": f"{fair_value_per_share:.2f}",
                "upside_pct": f"{upside_pct:+.1f}",
                "recommendation": recommendation,
                "reco_class": reco_class,
            },
            "dcf": {
                "wacc_pct": f"{wacc*100:.2f}",
                "g_pct": f"{terminal_growth*100:.2f}",
                "horizon": len(projected_fcf),
            },
            "scenarios": scenario_list,
            "flows": {
                "rows": fcf_rows,
                "terminal_fcf_mil": f"{terminal_fcf/1e6:,.0f}",
                "terminal_vp_mil": f"{terminal_pv/1e6:,.0f}",
                "terminal_weight_pct": (
                    f"{(terminal_pv/total_pv)*100:.1f}" if total_pv > 0 else "0.0"
                ),
            },
            "multiples": {"ev_ebitda": ev_ebitda, "pe": pe, "pb": pb},
            "assumptions": assumptions,
            "commentary": commentary_dict,
        }

        return context

    def _generate_default_summary(
        self, fair_value: float, market_price: float, upside: float
    ) -> str:
        """Generate default executive summary based on valuation."""
        if upside > 20:
            return f"Nuestra valoración indica una oportunidad significativa. El precio objetivo de ${fair_value:.2f} representa un potencial alcista del {upside:.1f}%, sugiriendo que el mercado está subvalorando los fundamentales de la empresa."
        elif upside < -20:
            return f"El análisis muestra que la acción cotiza por encima de su valor intrínseco. Con un precio justo de ${fair_value:.2f} vs precio actual de ${market_price:.2f}, existe un riesgo de corrección del {abs(upside):.1f}%."
        else:
            return f"La acción está valorada razonablemente según nuestro modelo DCF. El precio de mercado de ${market_price:.2f} está cerca de nuestro valor justo de ${fair_value:.2f}, con una diferencia del {upside:+.1f}%."

    def _generate_default_multiples_comment(
        self, ev_ebitda: str, pe: str, pb: str
    ) -> str:
        """Generate default comment on valuation multiples."""
        if ev_ebitda == "N/A" or pe == "N/A":
            return "Múltiplos de valoración no disponibles con los datos actuales."

        try:
            ev_ebitda_val = float(ev_ebitda)
            pe_val = float(pe) if pe != "N/A" else None

            comments = []
            if ev_ebitda_val > 20:
                comments.append(
                    f"EV/EBITDA de {ev_ebitda_val:.1f}x indica valoración premium"
                )
            elif ev_ebitda_val > 15:
                comments.append(
                    f"EV/EBITDA de {ev_ebitda_val:.1f}x está en línea con empresas de calidad"
                )
            else:
                comments.append(
                    f"EV/EBITDA de {ev_ebitda_val:.1f}x sugiere valoración atractiva"
                )

            if pe_val and pe_val > 30:
                comments.append(
                    f"P/E de {pe_val:.1f}x refleja expectativas de crecimiento elevadas"
                )
            elif pe_val:
                comments.append(f"P/E de {pe_val:.1f}x está en rango razonable")

            return ". ".join(comments) + "."
        except Exception:
            return "Múltiplos en línea con peers del sector."

    def _render_html(self, context: Dict[str, Any]) -> str:
        """Render HTML from context dictionary."""

        # Get CSS
        css = self._get_css()

        # Build HTML manually (simple template engine)
        html = f"""<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>Informe DCF – {context['meta']['symbol']}</title>
    <style>{css}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <div class="h-title">Informe de Valoración DCF</div>
                <div class="h-meta">{context['meta']['name']} ({context['meta']['symbol']}) · {context['meta']['date']}</div>
            </div>
            <div class="h-meta">
                <div>Precio mercado: <b>${context['meta']['price']}</b></div>
                <div>Recomendación: <span class="badge {context['summary']['reco_class']}">{context['summary']['recommendation']}</span></div>
            </div>
        </div>

        <div class="kpis">
            <div class="card"><h4>Enterprise Value</h4><div class="big">${context['summary']['ev_bil']}B</div></div>
            <div class="card"><h4>Equity Value</h4><div class="big">${context['summary']['eq_bil']}B</div></div>
            <div class="card"><h4>Fair Value / Acción</h4><div class="big">${context['summary']['fv_per_share']}</div></div>
            <div class="card"><h4>Upside/Downside</h4><div class="big">{context['summary']['upside_pct']}%</div></div>
        </div>

        <div class="section">
            <h3>Resumen Ejecutivo</h3>
            <div class="grid-3">
                <div class="card">
                    <h4>Parámetros DCF</h4>
                    <div>WACC: <b>{context['dcf']['wacc_pct']}%</b></div>
                    <div>g terminal: <b>{context['dcf']['g_pct']}%</b></div>
                    <div>Años de proyección: <b>{context['dcf']['horizon']}</b></div>
                    <div>Acciones diluidas: <b>{context['meta']['shares_mil']}M</b></div>
                </div>
                <div class="card">
                    <h4>Escenarios</h4>
                    {''.join([f'<div class="tag">{sc["name"]}: ${sc["fair_value"]} (WACC {sc["wacc_pct"]}%, g {sc["g_pct"]}%)</div>' for sc in context['scenarios']])}
                </div>
                <div class="card">
                    <h4>Comentario del analista</h4>
                    <div class="note">{context['commentary']['summary']}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h3>Proyecciones de Free Cash Flow</h3>
            <table class="table">
                <thead><tr><th>Año</th><th>FCF proyectado</th><th>Valor Presente</th><th>% del total</th></tr></thead>
                <tbody>
                {''.join([f'<tr><td>{r["year"]}</td><td>${r["fcf_mil"]}M</td><td>${r["vp_mil"]}M</td><td>{r["weight_pct"]}%</td></tr>' for r in context['flows']['rows']])}
                <tr><td><b>Terminal</b></td><td>${context['flows']['terminal_fcf_mil']}M</td><td>${context['flows']['terminal_vp_mil']}M</td><td>{context['flows']['terminal_weight_pct']}%</td></tr>
                </tbody>
            </table>
            <div class="note">Nota: cifras en millones salvo indicación.</div>
        </div>

        <div class="section">
            <h3>Valoración Relativa (Múltiplos)</h3>
            <div class="grid-3">
                <div class="card"><h4>EV/EBITDA</h4><div class="big">{context['multiples']['ev_ebitda']}×</div></div>
                <div class="card"><h4>P/E</h4><div class="big">{context['multiples']['pe']}×</div></div>
                <div class="card"><h4>P/B</h4><div class="big">{context['multiples']['pb']}×</div></div>
            </div>
            <div class="card" style="margin-top:10px">
                <h4>Comentario de múltiplos</h4>
                <div class="note">{context['commentary']['multiples']}</div>
            </div>
        </div>

        {'<div class="section"><h3>Notas del Analista</h3>' + ''.join([f'<div class="callout {note.get("tone", "")}"<b>{note["title"]}</b><br>{note["text"]}</div>' for note in context['commentary']['notes']]) + '</div>' if context['commentary']['notes'] else ''}

        <div class="section">
            <h3>Supuestos Clave</h3>
            <div class="grid-2">
                <div class="card">
                    <h4>Drivers operativos</h4>
                    <ul>{''.join([f'<li>{item}</li>' for item in context['assumptions']['operating']])}</ul>
                </div>
                <div class="card">
                    <h4>Estructura de capital</h4>
                    <ul>{''.join([f'<li>{item}</li>' for item in context['assumptions']['capital']])}</ul>
                </div>
            </div>
        </div>

        <div class="disclaimer">
            DISCLAIMER: Informe educativo; no es recomendación de inversión. Metodología DCF (Gordon) con horizonte {context['dcf']['horizon']} años.
            Generado con Claude Code DCF Platform · {context['meta']['date']}
        </div>
    </div>
</body>
</html>"""

        return html

    def _get_css(self) -> str:
        """Get CSS styling for the report."""
        return """
:root{
  --bg:#ffffff; --fg:#0f172a; --muted:#64748b; --accent:#0ea5e9; --accent-2:#22c55e;
  --danger:#ef4444; --card:#f8fafc; --border:#e2e8f0;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:var(--bg);color:var(--fg);font:14px/1.45 "Inter",system-ui,-apple-system,Segoe UI,Roboto,Arial}
.container{width:880px;margin:28px auto;padding:0 8px}
.header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:18px;border-bottom:1px solid var(--border);padding-bottom:14px}
.h-title{font-size:28px;font-weight:800;letter-spacing:.2px}
.h-meta{color:var(--muted);font-size:12px;text-align:right}
.badge{display:inline-block;padding:4px 8px;border-radius:999px;font-weight:700;font-size:12px}
.badge.sell{background:#fee2e2;color:#991b1b}
.badge.buy{background:#dcfce7;color:#166534}
.badge.hold{background:#e2e8f0;color:#111827}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:16px 0}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:12px}
.card h4{margin:0 0 8px 0;font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}
.card .big{font-size:22px;font-weight:800}
.section{margin:22px 0}
.section h3{margin:0 0 10px 0;font-size:16px}
.table{width:100%;border-collapse:collapse;font-size:13px}
.table th,.table td{border:1px solid var(--border);padding:8px 10px;text-align:right}
.table th:first-child,.table td:first-child{text-align:left}
.note{color:var(--muted);font-size:12px;margin-top:6px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px}
.disclaimer{margin-top:24px;color:var(--muted);font-size:11px;border-top:1px dashed var(--border);padding-top:10px}
.callout{border-left:4px solid var(--accent);background:#e6f6fe;padding:10px 12px;border-radius:8px;margin-bottom:8px}
.callout.negative{border-left-color:var(--danger);background:#feecec}
.callout.positive{border-left-color:var(--accent-2);background:#eafcf2}
.tag{display:inline-block;background:#eef2ff;color:#3730a3;border:1px solid #e0e7ff;padding:2px 6px;margin:2px;border-radius:6px;font-size:11px}
hr{border:0;border-top:1px solid var(--border);margin:16px 0}
"""
