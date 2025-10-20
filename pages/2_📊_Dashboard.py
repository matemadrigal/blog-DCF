"""Dashboard with overview of all analyzed companies - EXECUTIVE VERSION."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

from src.cache import DCFCache
from src.alerts import AlertSystem, AlertStatus

st.set_page_config(page_title="Dashboard - DCF", page_icon="📊", layout="wide")

st.title("📊 Dashboard Ejecutivo")
st.markdown("Vista consolidada de tu portafolio de valoraciones DCF.")


@st.cache_resource
def get_cache():
    return DCFCache()


@st.cache_resource
def get_alert_system():
    cache = get_cache()
    return AlertSystem(cache)


cache = get_cache()
alert_system = get_alert_system()

# Check for triggered alerts
triggered_alerts = alert_system.get_all_alerts(AlertStatus.TRIGGERED)
if triggered_alerts:
    st.warning(f"""
    🔔 **{len(triggered_alerts)} Alertas Disparadas!**

    Tienes notificaciones pendientes. Ve a la página de **🔔 Alertas** para revisarlas.
    """)
    st.markdown("---")

# Get all tickers
tickers = cache.get_all_tickers()

if not tickers:
    st.info(
        "📌 No hay análisis guardados aún. Ve a **Análisis Individual** para calcular tu primer DCF."
    )
    st.stop()

# Build summary data
summary_data = []
total_investment_value = 0  # Assumiendo $100k por empresa (configurable)
investment_per_company = 100000  # $100k por defecto

for ticker in tickers:
    latest = cache.get_latest_dcf(ticker)
    if latest:
        shares = latest.get("shares_outstanding", 0)
        fair_value_total = latest["fair_value"]
        market_price = latest.get("market_price", 0)

        fair_value_per_share = fair_value_total / shares if shares > 0 else 0

        upside = 0
        if fair_value_per_share > 0 and market_price > 0:
            upside = ((fair_value_per_share - market_price) / market_price) * 100

        # Calculate potential ROI in dollars
        potential_roi_dollars = (investment_per_company * upside / 100) if upside > 0 else 0

        # Recommendation
        if upside > 20:
            rec = "🟢 COMPRAR"
            rec_category = "Comprar"
        elif upside < -20:
            rec = "🔴 VENDER"
            rec_category = "Vender"
        else:
            rec = "🟡 MANTENER"
            rec_category = "Mantener"

        summary_data.append(
            {
                "Ticker": ticker,
                "Empresa": (
                    latest.get("metadata", {}).get("company_name", ticker)
                    if latest.get("metadata")
                    else ticker
                ),
                "Fair Value": fair_value_per_share,
                "Precio Mercado": market_price,
                "Upside": upside,
                "Upside_Formatted": f"{upside:+.1f}%" if upside != 0 else "N/A",
                "Recomendación": rec,
                "Recomendación_Categoria": rec_category,
                "ROI_Potencial_$": potential_roi_dollars,
                "Última Actualización": latest["calculation_date"],
                "r": latest['discount_rate'],
                "g": latest['growth_rate'],
            }
        )

if not summary_data:
    st.warning("No hay datos suficientes para mostrar el dashboard.")
    st.stop()

df_summary = pd.DataFrame(summary_data)

# ============================================================================
# SECCIÓN 1: MÉTRICAS EJECUTIVAS PRINCIPALES
# ============================================================================

st.subheader("📈 Resumen Ejecutivo")

# Calcular métricas agregadas
buy_count = sum(1 for d in summary_data if "COMPRAR" in d["Recomendación"])
sell_count = sum(1 for d in summary_data if "VENDER" in d["Recomendación"])
hold_count = sum(1 for d in summary_data if "MANTENER" in d["Recomendación"])

# Mejor oportunidad (mayor upside positivo)
best_opportunity = max(summary_data, key=lambda x: x["Upside"]) if summary_data else None
worst_opportunity = min(summary_data, key=lambda x: x["Upside"]) if summary_data else None

# ROI potencial total (solo de oportunidades de compra)
total_potential_roi = sum(d["ROI_Potencial_$"] for d in summary_data if d["Upside"] > 20)
total_investment = len([d for d in summary_data if d["Upside"] > 20]) * investment_per_company
roi_percentage = (total_potential_roi / total_investment * 100) if total_investment > 0 else 0

# Upside promedio
avg_upside = sum(d["Upside"] for d in summary_data) / len(summary_data)

# Salud del portafolio (score de 0 a 100)
# Fórmula: % de COMPRAR * 100 + % de MANTENER * 50
portfolio_health = (buy_count / len(summary_data) * 100 + hold_count / len(summary_data) * 50)

# Display métricas en cards
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "💰 ROI Potencial",
        f"${total_potential_roi:,.0f}",
        f"{roi_percentage:.1f}%" if total_investment > 0 else "N/A",
        help=f"Potencial de ganancia si inviertes ${investment_per_company:,} en cada oportunidad de COMPRA"
    )

with col2:
    st.metric(
        "🎯 Mejor Oportunidad",
        best_opportunity["Ticker"] if best_opportunity else "N/A",
        f"+{best_opportunity['Upside']:.1f}%" if best_opportunity else "N/A",
        help="Empresa con mayor upside potencial"
    )

with col3:
    st.metric(
        "📊 Empresas Analizadas",
        len(tickers),
        f"{buy_count} Comprar",
        help="Total de empresas en tu portafolio de análisis"
    )

with col4:
    st.metric(
        "📈 Upside Promedio",
        f"{avg_upside:+.1f}%",
        delta_color="normal",
        help="Upside promedio de todas las empresas analizadas"
    )

with col5:
    # Color code health score
    health_emoji = "🟢" if portfolio_health > 70 else "🟡" if portfolio_health > 40 else "🔴"
    st.metric(
        "💪 Salud Portafolio",
        f"{health_emoji} {portfolio_health:.0f}/100",
        help="Indicador de calidad del portafolio (100 = todas COMPRAR, 50 = todas MANTENER, 0 = todas VENDER)"
    )

st.markdown("---")

# ============================================================================
# SECCIÓN 2: VISUALIZACIONES EJECUTIVAS
# ============================================================================

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("🥧 Distribución de Oportunidades")

    # Pie chart de distribución
    distribution_data = {
        'Recomendación': ['🟢 Comprar', '🟡 Mantener', '🔴 Vender'],
        'Cantidad': [buy_count, hold_count, sell_count],
        'Color': ['#00CC00', '#FFD700', '#FF4444']
    }

    fig_pie = go.Figure(data=[go.Pie(
        labels=distribution_data['Recomendación'],
        values=distribution_data['Cantidad'],
        marker=dict(colors=distribution_data['Color']),
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>',
        hole=0.4  # Donut chart
    )])

    fig_pie.update_layout(
        showlegend=True,
        height=350,
        margin=dict(t=30, b=0, l=0, r=0)
    )

    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.subheader("📊 Upside por Empresa")

    # Bar chart de upside
    df_sorted = df_summary.sort_values('Upside', ascending=False)

    # Color code bars
    colors = ['#00CC00' if x > 20 else '#FFD700' if x > -20 else '#FF4444' for x in df_sorted['Upside']]

    fig_bar = go.Figure(data=[go.Bar(
        x=df_sorted['Ticker'],
        y=df_sorted['Upside'],
        marker_color=colors,
        text=df_sorted['Upside'].apply(lambda x: f"{x:+.1f}%"),
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Upside: %{y:.1f}%<extra></extra>'
    )])

    fig_bar.update_layout(
        xaxis_title="",
        yaxis_title="Upside (%)",
        height=350,
        margin=dict(t=30, b=0, l=0, r=0),
        showlegend=False,
        yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='gray')
    )

    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ============================================================================
# SECCIÓN 3: TOP 5 MEJORES OPORTUNIDADES
# ============================================================================

st.subheader("🏆 Top 5 Mejores Oportunidades")

top5 = df_summary.nlargest(5, 'Upside')

# Create styled dataframe
for idx, row in top5.iterrows():
    with st.container():
        col_rank, col_ticker, col_metrics, col_action = st.columns([0.5, 1.5, 3, 1.5])

        with col_rank:
            rank = list(top5.index).index(idx) + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
            st.markdown(f"### {medal}")

        with col_ticker:
            st.markdown(f"### {row['Ticker']}")
            if row['Empresa'] != row['Ticker']:
                st.caption(row['Empresa'])

        with col_metrics:
            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.metric("Fair Value", f"${row['Fair Value']:.2f}")

            with metric_col2:
                st.metric("Precio Actual", f"${row['Precio Mercado']:.2f}")

            with metric_col3:
                upside_color = "🟢" if row['Upside'] > 20 else "🟡" if row['Upside'] > 0 else "🔴"
                st.metric(
                    "Upside",
                    f"{upside_color} {row['Upside']:+.1f}%",
                    help=f"ROI potencial: ${row['ROI_Potencial_$']:,.0f}"
                )

        with col_action:
            st.markdown(f"### {row['Recomendación']}")
            st.caption(f"r={row['r']:.1%}, g={row['g']:.1%}")

        st.markdown("---")

# ============================================================================
# SECCIÓN 4: TABLA COMPLETA DETALLADA
# ============================================================================

st.subheader("📋 Tabla Detallada de Valoraciones")

# Prepare display dataframe
df_display = df_summary.copy()
df_display['Fair Value'] = df_display['Fair Value'].apply(lambda x: f"${x:.2f}")
df_display['Precio Mercado'] = df_display['Precio Mercado'].apply(lambda x: f"${x:.2f}")
df_display['ROI Potencial'] = df_display['ROI_Potencial_$'].apply(lambda x: f"${x:,.0f}" if x > 0 else "-")
df_display['r'] = df_display['r'].apply(lambda x: f"{x:.1%}")
df_display['g'] = df_display['g'].apply(lambda x: f"{x:.1%}")

# Select and reorder columns
df_display = df_display[[
    'Ticker', 'Empresa', 'Fair Value', 'Precio Mercado',
    'Upside_Formatted', 'ROI Potencial', 'Recomendación',
    'Última Actualización', 'r', 'g'
]]

df_display.columns = [
    'Ticker', 'Empresa', 'Fair Value', 'Precio Mercado',
    'Upside', 'ROI Potencial ($)', 'Recomendación',
    'Última Actualización', 'Tasa r', 'Crecimiento g'
]

st.dataframe(
    df_display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Empresa": st.column_config.TextColumn("Empresa", width="medium"),
        "Fair Value": st.column_config.TextColumn("Fair Value", width="small"),
        "Precio Mercado": st.column_config.TextColumn("Precio Mercado", width="small"),
        "Upside": st.column_config.TextColumn("Upside", width="small"),
        "ROI Potencial ($)": st.column_config.TextColumn("ROI Potencial", width="small"),
        "Recomendación": st.column_config.TextColumn("Recomendación", width="medium"),
        "Última Actualización": st.column_config.DateColumn("Última Actualización", width="small"),
    },
)

st.markdown("---")

# ============================================================================
# SECCIÓN 5: INSIGHTS Y RECOMENDACIONES
# ============================================================================

st.subheader("💡 Insights y Recomendaciones")

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.markdown("### 🎯 Oportunidades Destacadas")

    if buy_count > 0:
        st.success(f"""
        **{buy_count} empresas** muestran oportunidades de compra con upside >20%.

        **Mejor oportunidad:** {best_opportunity['Ticker']} con **{best_opportunity['Upside']:+.1f}%** de upside.

        **ROI potencial total:** ${total_potential_roi:,.0f} ({roi_percentage:.1f}%)
        """)
    else:
        st.info("No hay oportunidades de compra claras en este momento (upside >20%).")

    if sell_count > 0:
        st.warning(f"""
        ⚠️ **{sell_count} empresas** podrían estar sobrevaluadas (downside >20%).

        Considera revisar: {', '.join([d['Ticker'] for d in summary_data if 'VENDER' in d['Recomendación']])}
        """)

with insights_col2:
    st.markdown("### 📊 Análisis del Portafolio")

    # Portfolio composition
    st.markdown(f"""
    **Composición:**
    - 🟢 Comprar: {buy_count} ({buy_count/len(summary_data)*100:.0f}%)
    - 🟡 Mantener: {hold_count} ({hold_count/len(summary_data)*100:.0f}%)
    - 🔴 Vender: {sell_count} ({sell_count/len(summary_data)*100:.0f}%)

    **Salud del Portafolio:** {portfolio_health:.0f}/100
    """)

    if portfolio_health > 70:
        st.success("✅ Portafolio saludable con buenas oportunidades de inversión.")
    elif portfolio_health > 40:
        st.info("⚠️ Portafolio balanceado. Considera diversificar más.")
    else:
        st.warning("🔴 Portafolio con pocas oportunidades. Busca nuevas empresas para analizar.")

st.markdown("---")

# ============================================================================
# EXCEL EXPORT
# ============================================================================

st.subheader("📥 Exportar Portafolio a Excel")

export_col1, export_col2 = st.columns([2, 1])

with export_col1:
    st.markdown("""
    **Exporta todo tu portafolio a Excel** con formato profesional:
    - 📊 Resumen completo de todas las empresas
    - 📈 Métricas clave y recomendaciones
    - 💰 ROI potencial calculado
    - 🎨 Colores y formato profesional
    """)

with export_col2:
    st.metric("Empresas a Exportar", len(summary_data))

if st.button("📥 Exportar Dashboard a Excel", type="primary", use_container_width=True):
    try:
        from src.reports.excel_exporter import export_dashboard_to_excel

        with st.spinner("Generando archivo Excel del dashboard..."):
            excel_file = export_dashboard_to_excel(summary_data)

            st.download_button(
                label="⬇️ Descargar Portfolio Excel",
                data=excel_file,
                file_name=f"DCF_Portfolio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.success(f"✅ Portafolio exportado: {len(summary_data)} empresas en Excel!")

    except Exception as e:
        st.error(f"Error al exportar: {e}")
        st.info("Asegúrate de que openpyxl esté instalado: pip install openpyxl")

st.markdown("---")

# ============================================================================
# LEYENDA
# ============================================================================

with st.expander("📖 Leyenda y Notas"):
    st.markdown("""
    ### Recomendaciones
    - 🟢 **COMPRAR**: Fair Value >20% por encima del precio de mercado
    - 🟡 **MANTENER**: Fair Value entre -20% y +20% del precio de mercado
    - 🔴 **VENDER**: Fair Value >20% por debajo del precio de mercado

    ### Métricas
    - **ROI Potencial**: Ganancia potencial asumiendo inversión de $100,000 por empresa
    - **Salud del Portafolio**: Score de 0-100 basado en calidad de oportunidades
    - **Upside Promedio**: Promedio del upside/downside de todas las empresas

    ### Notas
    - Los cálculos están basados en los parámetros DCF ingresados (r y g)
    - Los precios de mercado pueden haber cambiado desde el último cálculo
    - Esta herramienta es solo para fines educativos e informativos
    """)
