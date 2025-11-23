"""Compare multiple companies side by side."""

import streamlit as st

# Safe imports with error handling
try:
    import pandas as pd
    import plotly.graph_objects as go
except ImportError as e:
    from src.utils.error_handler import handle_import_error
    missing_module = str(e).split("'")[1] if "'" in str(e) else "unknown"
    handle_import_error(e, missing_module)
    st.stop()

from src.cache import DCFCache

st.set_page_config(page_title="Comparador - DCF", page_icon="💼", layout="wide")

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
        Comparador de Companys
    </h1>
    <p style="color: #B4B9D1; font-size: 1.1rem;">
        Compara múltiples companies lado a lado para identificar las mejores oportunidades
    </p>
</div>
""", unsafe_allow_html=True)


@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()

# Get all tickers
all_tickers = cache.get_all_tickers()

if not all_tickers:
    st.markdown("""
    <div style="background: rgba(0, 102, 255, 0.1); border: 1px solid #0066FF; 
                border-radius: 12px; padding: 2rem; text-align: center;">
        <h3 style="color: #0066FF; margin: 0 0 1rem 0;">📌 No saved analyses</h3>
        <p style="color: #B4B9D1; margin: 0;">
            Go to <strong>Individual Analysis</strong> first to create company analyses.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Selection
st.markdown("""
<div style="background: #1E2338; padding: 1.5rem; border-radius: 16px; border: 1px solid #2A2F4A; margin-bottom: 2rem;">
    <h3 style="color: #FFFFFF; font-size: 1.25rem; margin: 0 0 1rem 0;">Company Selection</h3>
""", unsafe_allow_html=True)

selected_tickers = st.multiselect(
    "Selecciona companies para comparar (máximo 5)",
    options=all_tickers,
    default=all_tickers[: min(3, len(all_tickers))],
    max_selections=5,
    label_visibility="collapsed"
)

st.markdown("</div>", unsafe_allow_html=True)

if not selected_tickers:
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                border-radius: 12px; padding: 1.5rem;">
        <p style="color: #F59E0B; margin: 0;">⚠️ Select at least one company para comparar.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# Comparison data
comparison_data = []

for ticker in selected_tickers:
    latest = cache.get_latest_dcf(ticker)
    if latest:
        shares = latest.get("shares_outstanding", 0)
        fair_value_total = latest["fair_value"]
        market_price = latest.get("market_price", 0)
        fair_value_per_share = fair_value_total / shares if shares > 0 else 0
        upside = (
            ((fair_value_per_share - market_price) / market_price) * 100
            if fair_value_per_share > 0 and market_price > 0
            else 0
        )

        comparison_data.append(
            {
                "Ticker": ticker,
                "Fair Value": fair_value_per_share,
                "Market Price": market_price,
                "Upside (%)": upside,
                "Tasa Descuento (r)": latest["discount_rate"] * 100,
                "Growth (g)": latest["growth_rate"] * 100,
                "Enterprise Value (M)": fair_value_total / 1e6,
            }
        )

if comparison_data:
    df_comp = pd.DataFrame(comparison_data)

    # Table
    st.markdown("""
    <div style="margin: 2rem 0 1.5rem 0;">
        <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📊 Metric Comparison</h2>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(
        df_comp.style.format(
            {
                "Fair Value": "${:.2f}",
                "Market Price": "${:.2f}",
                "Upside (%)": "{:+.1f}%",
                "Tasa Descuento (r)": "{:.1f}%",
                "Growth (g)": "{:.1f}%",
                "Enterprise Value (M)": "${:,.0f}M",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    # Charts
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style="background: #1E2338; padding: 1.5rem; border-radius: 16px; border: 1px solid #2A2F4A; margin-bottom: 1rem;">
            <h3 style="color: #FFFFFF; font-size: 1.25rem; margin: 0 0 1rem 0;">Fair Value vs Market Price</h3>
        </div>
        """, unsafe_allow_html=True)
        fig1 = go.Figure(
            data=[
                go.Bar(
                    name="Fair Value",
                    x=df_comp["Ticker"],
                    y=df_comp["Fair Value"],
                    marker_color="#ff7f0e",
                ),
                go.Bar(
                    name="Market Price",
                    x=df_comp["Ticker"],
                    y=df_comp["Market Price"],
                    marker_color="#1f77b4",
                ),
            ]
        )
        fig1.update_layout(
            barmode="group", yaxis_title="Price per Share ($)", height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#B4B9D1', size=12),
            xaxis=dict(gridcolor='#2A2F4A'),
            yaxis=dict(gridcolor='#2A2F4A')
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("""
        <div style="background: #1E2338; padding: 1.5rem; border-radius: 16px; border: 1px solid #2A2F4A; margin-bottom: 1rem;">
            <h3 style="color: #FFFFFF; font-size: 1.25rem; margin: 0 0 1rem 0;">Upside/Downside Potencial</h3>
        </div>
        """, unsafe_allow_html=True)
        colors = ["green" if x > 0 else "red" for x in df_comp["Upside (%)"]]
        fig2 = go.Figure(
            data=[
                go.Bar(
                    x=df_comp["Ticker"], y=df_comp["Upside (%)"], marker_color=colors
                )
            ]
        )
        fig2.update_layout(
            yaxis_title="Upside/Downside (%)", height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#B4B9D1', size=12),
            xaxis=dict(gridcolor='#2A2F4A'),
            yaxis=dict(gridcolor='#2A2F4A')
        )
        fig2.add_hline(y=0, line_dash="dash", line_color="#2A2F4A")
        st.plotly_chart(fig2, use_container_width=True)

    # Enterprise Value comparison
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="margin: 2rem 0 1.5rem 0;">
        <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">Company Size (Enterprise Value)</h2>
    </div>
    """, unsafe_allow_html=True)
    fig3 = go.Figure(
        data=[
            go.Bar(
                x=df_comp["Ticker"],
                y=df_comp["Enterprise Value (M)"],
                marker_color="#2ca02c",
            )
        ]
    )
    fig3.update_layout(
        yaxis_title="Enterprise Value (Millones $)", height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#B4B9D1', size=12),
        xaxis=dict(gridcolor='#2A2F4A'),
        yaxis=dict(gridcolor='#2A2F4A')
    )
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.markdown("""
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                border-radius: 12px; padding: 1.5rem;">
        <p style="color: #F59E0B; margin: 0;">⚠️ No data for selected companies.</p>
    </div>
    """, unsafe_allow_html=True)
