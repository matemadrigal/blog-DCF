"""Dashboard with overview of all analyzed companies - EXECUTIVE VERSION."""

import streamlit as st
from datetime import datetime

# Safe imports with error handling
try:
    import pandas as pd
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError as e:
    from src.utils.error_handler import handle_import_error
    missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
    handle_import_error(e, missing_module)
    st.stop()

from src.cache import DCFCache
from src.alerts import AlertSystem, AlertStatus

st.set_page_config(page_title="Dashboard - DCF", page_icon="💼", layout="wide")

# Load custom CSS
def load_css():
    import os
    css_paths = [
        "assets/custom.css",
        "./assets/custom.css",
        os.path.join(os.path.dirname(__file__), "..", "assets", "custom.css")
    ]
    
    css_content = None
    for path in css_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                css_content = f.read()
                break
        except FileNotFoundError:
            continue
    
    if css_content:
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)

load_css()

# Modern Header
st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="background: linear-gradient(135deg, #0066FF 0%, #00D4AA 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               font-size: 2.5rem; font-weight: 800; margin-bottom: 0.5rem;">
        Executive Dashboard
    </h1>
    <p style="color: #B4B9D1; font-size: 1.1rem;">
        Consolidated view of your DCF valuation portfolio with advanced analysis
    </p>
</div>
""", unsafe_allow_html=True)


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
    st.markdown(f"""
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;">
        <h3 style="color: #F59E0B; margin: 0 0 0.5rem 0;">🔔 {len(triggered_alerts)} Triggered Alerts</h3>
        <p style="color: #B4B9D1; margin: 0;">
            You have pending notifications. Go to the <strong>Alertas</strong> page to review them.
        </p>
    </div>
    """, unsafe_allow_html=True)

# Get all tickers
tickers = cache.get_all_tickers()

if not tickers:
    st.markdown("""
    <div style="background: rgba(0, 102, 255, 0.1); border: 1px solid #0066FF; 
                border-radius: 12px; padding: 2rem; text-align: center;">
        <h3 style="color: #0066FF; margin: 0 0 1rem 0;">📌 No saved analyses yet</h3>
        <p style="color: #B4B9D1; margin: 0;">
            Go to <strong>Individual Analysis</strong> to calculate your first DCF and start building your portfolio.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Build summary data
summary_data = []
total_investment_value = 0  # Assuming $100k per company (configurable)
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
            rec = "🟢 BUY"
            rec_category = "Buy"
        elif upside < -20:
            rec = "🔴 SELL"
            rec_category = "Sell"
        else:
            rec = "🟡 HOLD"
            rec_category = "Hold"

        summary_data.append(
            {
                "Ticker": ticker,
                "Company": (
                    latest.get("metadata", {}).get("company_name", ticker)
                    if latest.get("metadata")
                    else ticker
                ),
                "Fair Value": fair_value_per_share,
                "Market Price": market_price,
                "Upside": upside,
                "Upside_Formatted": f"{upside:+.1f}%" if upside != 0 else "N/A",
                "Recommendation": rec,
                "Recommendation_Categoria": rec_category,
                "ROI_Potencial_$": potential_roi_dollars,
                "Last Update": latest["calculation_date"],
                "r": latest['discount_rate'],
                "g": latest['growth_rate'],
            }
        )

if not summary_data:
    st.warning("Insufficient data to display the dashboard.")
    st.stop()

df_summary = pd.DataFrame(summary_data)

# ============================================================================
# SECTION 1: MAIN EXECUTIVE METRICS
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📈 Executive Summary</h2>
</div>
""", unsafe_allow_html=True)

# Calculate aggregated metrics
buy_count = sum(1 for d in summary_data if "BUY" in d["Recommendation"])
sell_count = sum(1 for d in summary_data if "SELL" in d["Recommendation"])
hold_count = sum(1 for d in summary_data if "HOLD" in d["Recommendation"])

# Best opportunity (highest positive upside)
best_opportunity = max(summary_data, key=lambda x: x["Upside"]) if summary_data else None
worst_opportunity = min(summary_data, key=lambda x: x["Upside"]) if summary_data else None

# Total potential ROI (only from buy opportunities)
total_potential_roi = sum(d["ROI_Potencial_$"] for d in summary_data if d["Upside"] > 20)
total_investment = len([d for d in summary_data if d["Upside"] > 20]) * investment_per_company
roi_percentage = (total_potential_roi / total_investment * 100) if total_investment > 0 else 0

# Average upside
avg_upside = sum(d["Upside"] for d in summary_data) / len(summary_data)

# Portfolio health (score from 0 to 100)
# Formula: % of BUY * 100 + % of HOLD * 50
portfolio_health = (buy_count / len(summary_data) * 100 + hold_count / len(summary_data) * 50)

# Display metrics in cards with modern design
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Potential ROI</div>
        <div class="metric-value" style="color: #00D4AA;">${total_potential_roi:,.0f}</div>
        <div style="color: #7C82A3; font-size: 0.85rem;">{roi_percentage:.1f}% ROI</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    ticker_display = best_opportunity["Ticker"] if best_opportunity else "N/A"
    upside_display = f"+{best_opportunity['Upside']:.1f}%" if best_opportunity else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Best Opportunity</div>
        <div class="metric-value" style="color: #0066FF;">{ticker_display}</div>
        <div style="color: #7C82A3; font-size: 0.85rem;">{upside_display}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Companies Analyzed</div>
        <div class="metric-value" style="color: #0066FF;">{len(tickers)}</div>
        <div style="color: #7C82A3; font-size: 0.85rem;">{buy_count} Buy</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Average Upside</div>
        <div class="metric-value" style="color: {'#00D4AA' if avg_upside > 0 else '#FF6B6B'};">{avg_upside:+.1f}%</div>
        <div style="color: #7C82A3; font-size: 0.85rem;">Portfolio average</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    health_color = "#00D4AA" if portfolio_health > 70 else "#F59E0B" if portfolio_health > 40 else "#FF6B6B"
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Portfolio Health</div>
        <div class="metric-value" style="color: {health_color};">{portfolio_health:.0f}/100</div>
        <div style="color: #7C82A3; font-size: 0.85rem;">Overall quality</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 2: EXECUTIVE VISUALIZATIONS
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📊 Executive Visualizations</h2>
</div>
""", unsafe_allow_html=True)

col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.markdown("""
    <div style="background: #1E2338; padding: 1.5rem; border-radius: 16px; border: 1px solid #2A2F4A; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; font-size: 1.25rem; margin: 0 0 1rem 0;">🥧 Opportunity Distribution</h3>
    </div>
    """, unsafe_allow_html=True)

    # Pie chart de distribución
    distribution_data = {
        'Recommendation': ['🟢 Buy', '🟡 Hold', '🔴 Sell'],
        'Cantidad': [buy_count, hold_count, sell_count],
        'Color': ['#00CC00', '#FFD700', '#FF4444']
    }

    fig_pie = go.Figure(data=[go.Pie(
        labels=distribution_data['Recommendation'],
        values=distribution_data['Cantidad'],
        marker=dict(colors=distribution_data['Color']),
        textinfo='label+percent+value',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>',
        hole=0.4  # Donut chart
    )])

    fig_pie.update_layout(
        showlegend=True,
        height=350,
        margin=dict(t=30, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#B4B9D1', size=12),
        legend=dict(font=dict(color='#B4B9D1'))
    )

    st.plotly_chart(fig_pie, use_container_width=True)

with col_chart2:
    st.markdown("""
    <div style="background: #1E2338; padding: 1.5rem; border-radius: 16px; border: 1px solid #2A2F4A; margin-bottom: 1rem;">
        <h3 style="color: #FFFFFF; font-size: 1.25rem; margin: 0 0 1rem 0;">📊 Upside by Company</h3>
    </div>
    """, unsafe_allow_html=True)

    # Bar chart upside
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
        yaxis=dict(zeroline=True, zerolinewidth=2, zerolinecolor='#2A2F4A'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#B4B9D1', size=12),
        xaxis=dict(gridcolor='#2A2F4A'),
        yaxis_gridcolor='#2A2F4A'
    )

    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 3: TOP 5 BEST OPPORTUNITIES
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">🏆 Top 5 Best Opportunities</h2>
</div>
""", unsafe_allow_html=True)

top5 = df_summary.nlargest(5, 'Upside')

# Create styled dataframe
for idx, row in top5.iterrows():
    rank = list(top5.index).index(idx) + 1
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
    upside_color = "#00D4AA" if row['Upside'] > 20 else "#F59E0B" if row['Upside'] > 0 else "#FF6B6B"
    rec_color = "#00D4AA" if "BUY" in row['Recommendation'] else "#F59E0B" if "HOLD" in row['Recommendation'] else "#FF6B6B"
    
    st.markdown(f"""
    <div style="background: #1E2338; border: 1px solid #2A2F4A; border-radius: 16px; 
                padding: 1.5rem; margin-bottom: 1rem; transition: all 0.3s ease;">
        <div style="display: flex; align-items: center; gap: 2rem;">
            <div style="font-size: 2rem; min-width: 60px;">{medal}</div>
            <div style="flex: 1;">
                <h3 style="color: #FFFFFF; margin: 0 0 0.25rem 0; font-size: 1.5rem;">{row['Ticker']}</h3>
                <p style="color: #7C82A3; margin: 0; font-size: 0.9rem;">{row['Company'] if row['Company'] != row['Ticker'] else ''}</p>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; flex: 2;">
                <div>
                    <div style="color: #7C82A3; font-size: 0.85rem; margin-bottom: 0.25rem;">Fair Value</div>
                    <div style="color: #FFFFFF; font-size: 1.25rem; font-weight: 600;">${row['Fair Value']:.2f}</div>
                </div>
                <div>
                    <div style="color: #7C82A3; font-size: 0.85rem; margin-bottom: 0.25rem;">Current Price</div>
                    <div style="color: #FFFFFF; font-size: 1.25rem; font-weight: 600;">${row['Market Price']:.2f}</div>
                </div>
                <div>
                    <div style="color: #7C82A3; font-size: 0.85rem; margin-bottom: 0.25rem;">Upside</div>
                    <div style="color: {upside_color}; font-size: 1.25rem; font-weight: 600;">{row['Upside']:+.1f}%</div>
                </div>
            </div>
            <div style="text-align: right; min-width: 150px;">
                <div style="color: {rec_color}; font-size: 1.1rem; font-weight: 600; margin-bottom: 0.25rem;">
                    {row['Recommendation'].replace('🟢 ', '').replace('🟡 ', '').replace('🔴 ', '')}
                </div>
                <div style="color: #7C82A3; font-size: 0.85rem;">r={row['r']:.1%}, g={row['g']:.1%}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# SECTION 4: DETAILED VALUATION TABLE
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📋 Detailed Valuation Table</h2>
</div>
""", unsafe_allow_html=True)

# Prepare display dataframe
df_display = df_summary.copy()
df_display['Fair Value'] = df_display['Fair Value'].apply(lambda x: f"${x:.2f}")
df_display['Market Price'] = df_display['Market Price'].apply(lambda x: f"${x:.2f}")
df_display['Potential ROI'] = df_display['ROI_Potencial_$'].apply(lambda x: f"${x:,.0f}" if x > 0 else "-")
df_display['r'] = df_display['r'].apply(lambda x: f"{x:.1%}")
df_display['g'] = df_display['g'].apply(lambda x: f"{x:.1%}")

# Select and reorder columns
df_display = df_display[[
    'Ticker', 'Company', 'Fair Value', 'Market Price',
    'Upside_Formatted', 'Potential ROI', 'Recommendation',
    'Last Update', 'r', 'g'
]]

df_display.columns = [
    'Ticker', 'Company', 'Fair Value', 'Market Price',
    'Upside', 'Potential ROI ($)', 'Recommendation',
    'Last Update', 'Rate r', 'Growth g'
]

st.dataframe(
    df_display,
    hide_index=True,
    use_container_width=True,
    column_config={
        "Ticker": st.column_config.TextColumn("Ticker", width="small"),
        "Company": st.column_config.TextColumn("Company", width="medium"),
        "Fair Value": st.column_config.TextColumn("Fair Value", width="small"),
        "Market Price": st.column_config.TextColumn("Market Price", width="small"),
        "Upside": st.column_config.TextColumn("Upside", width="small"),
        "Potential ROI ($)": st.column_config.TextColumn("Potential ROI", width="small"),
        "Recommendation": st.column_config.TextColumn("Recommendation", width="medium"),
        "Last Update": st.column_config.DateColumn("Last Update", width="small"),
    },
)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# SECTION 5: INSIGHTS AND RECOMMENDATIONS
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">💡 Insights and Recommendations</h2>
</div>
""", unsafe_allow_html=True)

insights_col1, insights_col2 = st.columns(2)

with insights_col1:
    st.markdown("### 🎯 Featured Opportunities")

    if buy_count > 0:
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; 
                    border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
            <h4 style="color: #10B981; margin: 0 0 0.75rem 0;">✅ Buy Opportunities</h4>
            <p style="color: #B4B9D1; margin: 0.5rem 0;">
                <strong>{buy_count} companies</strong> show buy opportunities with upside >20%.
            </p>
            <p style="color: #B4B9D1; margin: 0.5rem 0;">
                <strong>Best opportunity:</strong> {best_opportunity['Ticker']} with <strong style="color: #10B981;">{best_opportunity['Upside']:+.1f}%</strong> upside.
            </p>
            <p style="color: #B4B9D1; margin: 0.5rem 0;">
                <strong>Total potential ROI:</strong> <strong style="color: #10B981;">${total_potential_roi:,.0f}</strong> ({roi_percentage:.1f}%)
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(0, 102, 255, 0.1); border: 1px solid #0066FF; 
                    border-radius: 12px; padding: 1.5rem;">
            <p style="color: #B4B9D1; margin: 0;">
                No clear buy opportunities at this time (upside >20%).
            </p>
        </div>
        """, unsafe_allow_html=True)

    if sell_count > 0:
        st.markdown(f"""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                    border-radius: 12px; padding: 1.5rem; margin-top: 1rem;">
            <h4 style="color: #F59E0B; margin: 0 0 0.75rem 0;">⚠️ Companys Sobrevaluadas</h4>
            <p style="color: #B4B9D1; margin: 0.5rem 0;">
                <strong>{sell_count} companies</strong> may be overvalued (downside >20%).
            </p>
            <p style="color: #B4B9D1; margin: 0.5rem 0;">
                Consider reviewing: <strong>{', '.join([d['Ticker'] for d in summary_data if 'SELL' in d['Recommendation']])}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

with insights_col2:
    st.markdown("### 📊 Portfolio Analysis")

    # Portfolio composition
    st.markdown(f"""
    <div style="background: #1E2338; border: 1px solid #2A2F4A; border-radius: 12px; padding: 1.5rem;">
        <h4 style="color: #FFFFFF; margin: 0 0 1rem 0;">Portfolio Composition</h4>
        <div style="color: #B4B9D1; line-height: 2;">
            <div>🟢 <strong>Buy:</strong> {buy_count} ({buy_count/len(summary_data)*100:.0f}%)</div>
            <div>🟡 <strong>Hold:</strong> {hold_count} ({hold_count/len(summary_data)*100:.0f}%)</div>
            <div>🔴 <strong>Sell:</strong> {sell_count} ({sell_count/len(summary_data)*100:.0f}%)</div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #2A2F4A;">
            <div style="color: #7C82A3; font-size: 0.9rem; margin-bottom: 0.25rem;">Portfolio Health</div>
            <div style="color: {health_color}; font-size: 1.5rem; font-weight: 600;">{portfolio_health:.0f}/100</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if portfolio_health > 70:
        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid #10B981; 
                    border-radius: 12px; padding: 1rem; margin-top: 1rem;">
            <p style="color: #10B981; margin: 0;">✅ Healthy portfolio with good investment opportunities.</p>
        </div>
        """, unsafe_allow_html=True)
    elif portfolio_health > 40:
        st.markdown("""
        <div style="background: rgba(0, 102, 255, 0.1); border: 1px solid #0066FF; 
                    border-radius: 12px; padding: 1rem; margin-top: 1rem;">
            <p style="color: #0066FF; margin: 0;">⚠️ Balanced portfolio. Consider diversifying more.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                    border-radius: 12px; padding: 1rem; margin-top: 1rem;">
            <p style="color: #F59E0B; margin: 0;">🔴 Portfolio with few opportunities. Look for new companies to analyze.</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ============================================================================
# EXCEL EXPORT
# ============================================================================

st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📥 Export Portfolio to Excel</h2>
</div>
""", unsafe_allow_html=True)

export_col1, export_col2 = st.columns([2, 1])

with export_col1:
    st.markdown("""
    **Export your entire portfolio to Excel** with professional formatting:
    - 📊 Resumen completo de todas las companies
    - 📈 Key metrics and recommendations
    - 💰 Calculated potential ROI
    - 🎨 Professional colors and formatting
    """)

with export_col2:
    st.metric("Companies to Export", len(summary_data))

if st.button("📥 Export Dashboard to Excel", type="primary", use_container_width=True):
    try:
        from src.reports.excel_exporter import export_dashboard_to_excel

        with st.spinner("Generating Excel file from dashboard..."):
            excel_file = export_dashboard_to_excel(summary_data)

            st.download_button(
                label="⬇️ Download Portfolio Excel",
                data=excel_file,
                file_name=f"DCF_Portfolio_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.success(f"✅ Portfolio exported: {len(summary_data)} companies en Excel!")

    except Exception as e:
        st.error(f"Error exporting: {e}")
        st.info("Make sure openpyxl is installed: pip install openpyxl")

st.markdown("---")

# ============================================================================
# LEYENDA
# ============================================================================

with st.expander("📖 Legend and Notes"):
    st.markdown("""
    ### Recomendaciones
    - 🟢 **BUY**: Fair Value >20% above market price
    - 🟡 **HOLD**: Fair Value between -20% and +20% of market price
    - 🔴 **SELL**: Fair Value >20% below market price

    ### Métricas
    - **Potential ROI**: Potential gain assuming $100,000 investment per company
    - **Portfolio Health**: Score of 0-100 based on opportunity quality
    - **Average Upside**: Average of upside/downside of all companies

    ### Notas
    - Calculations are based on entered DCF parameters (r and g)
    - Market prices may have changed since last calculation
    - This tool is for educational and informational purposes only
    """)
