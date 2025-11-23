"""Historical Fair Value vs Market Price evolution."""

import streamlit as st
from datetime import datetime

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

st.set_page_config(page_title="Histórico - DCF", page_icon="💼", layout="wide")

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
        Historical Evolution
    </h1>
    <p style="color: #B4B9D1; font-size: 1.1rem;">
        Analyze the temporal evolution of Fair Value vs Market Price
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

# Ticker selection
ticker = st.selectbox("Select a company", options=all_tickers, index=0)

# Get historical data
dcf_history = cache.get_dcf_history(ticker)

if len(dcf_history) < 2:
    st.markdown(f"""
    <div style="background: rgba(245, 158, 11, 0.1); border: 1px solid #F59E0B; 
                border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem;">
        <h4 style="color: #F59E0B; margin: 0 0 0.5rem 0;">📌 Insufficient Data</h4>
        <p style="color: #B4B9D1; margin: 0.5rem 0;">
            Only <strong>{len(dcf_history)} calculation(s)</strong> for {ticker}. You need at least 2 to see historical evolution.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div style="background: rgba(0, 102, 255, 0.1); border: 1px solid #0066FF; 
                border-radius: 12px; padding: 1.5rem;">
        <p style="color: #0066FF; margin: 0;">💡 <strong>Tip:</strong> Perform periodic calculations to build a history.</p>
    </div>
    """, unsafe_allow_html=True)

    if len(dcf_history) == 1:
        latest = dcf_history[0]
        st.markdown("### Último Cálculo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Date", latest["calculation_date"])
        with col2:
            shares = latest.get("shares_outstanding", 0)
            fv = latest["fair_value"] / shares if shares > 0 else 0
            st.metric("Fair Value", f"${fv:.2f}" if fv > 0 else "N/A")
        with col3:
            mp = latest.get("market_price", 0)
            st.metric("Market Price", f"${mp:.2f}" if mp > 0 else "N/A")

    st.stop()

# Prepare data
dcf_dates = []
dcf_fair_values = []
dcf_market_prices = []
dcf_upsides = []

for calc in reversed(dcf_history):  # Reverse to get chronological order
    date = datetime.fromisoformat(calc["calculation_date"])
    shares = calc.get("shares_outstanding", 0)
    fair_value = calc["fair_value"] / shares if shares > 0 else 0
    market_price = calc.get("market_price", 0)

    if fair_value > 0:
        dcf_dates.append(date)
        dcf_fair_values.append(fair_value)
        dcf_market_prices.append(market_price if market_price > 0 else None)

        if market_price > 0:
            upside = ((fair_value - market_price) / market_price) * 100
            dcf_upsides.append(upside)
        else:
            dcf_upsides.append(None)


if not dcf_dates:
    st.warning("Insufficient data to display historical data.")
    st.stop()


# Main chart: Fair Value vs Market Price
st.markdown(f"""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📈 {ticker} - Fair Value vs Market Price</h2>
</div>
""", unsafe_allow_html=True)

fig = go.Figure()

# Market Price
if any(p is not None for p in dcf_market_prices):
    fig.add_trace(
        go.Scatter(
            x=dcf_dates,
            y=dcf_market_prices,
            mode="lines+markers",
            name="Market Price",
            line=dict(color="#1f77b4", width=2),
            marker=dict(size=6),
        )
    )

# Fair Value
fig.add_trace(
    go.Scatter(
        x=dcf_dates,
        y=dcf_fair_values,
        mode="lines+markers",
        name="Fair Value (DCF)",
        line=dict(color="#ff7f0e", width=2, dash="dash"),
        marker=dict(size=8),
    )
)

fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Price per Share ($)",
    hovermode="x unified",
    height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#B4B9D1', size=12),
    xaxis=dict(gridcolor='#2A2F4A'),
    yaxis=dict(gridcolor='#2A2F4A')
)

st.plotly_chart(fig, use_container_width=True)


# Upside/Downside evolution
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📊 Upside/Downside Evolution</h2>
</div>
""", unsafe_allow_html=True)

fig2 = go.Figure()

valid_upsides = [(d, u) for d, u in zip(dcf_dates, dcf_upsides) if u is not None]
if valid_upsides:
    dates, upsides = zip(*valid_upsides)
    colors = ["green" if u > 0 else "red" for u in upsides]

    fig2.add_trace(
        go.Bar(x=dates, y=upsides, marker_color=colors, name="Upside/Downside")
    )

    fig2.add_hline(y=0, line_dash="dash", line_color="#2A2F4A")
    fig2.add_hline(y=20, line_dash="dot", line_color="#10B981", opacity=0.5)
    fig2.add_hline(y=-20, line_dash="dot", line_color="#EF4444", opacity=0.5)

    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="Upside/Downside (%)",
        height=400,
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#B4B9D1', size=12),
        xaxis=dict(gridcolor='#2A2F4A'),
        yaxis=dict(gridcolor='#2A2F4A')
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "🟢 Green line: +20% (buy zone) | 🔴 Red line: -20% (sell zone)"
    )
else:
    st.info("No upside/downside data available.")


# Statistics
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📊 Historical Statistics</h2>
</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_fv = sum(dcf_fair_values) / len(dcf_fair_values)
    st.metric("Average Fair Value", f"${avg_fv:.2f}")

with col2:
    valid_prices = [p for p in dcf_market_prices if p is not None]
    if valid_prices:
        avg_price = sum(valid_prices) / len(valid_prices)
        st.metric("Average Price", f"${avg_price:.2f}")
    else:
        st.metric("Average Price", "N/A")

with col3:
    valid_ups = [u for u in dcf_upsides if u is not None]
    if valid_ups:
        avg_upside = sum(valid_ups) / len(valid_ups)
        st.metric("Average Upside", f"{avg_upside:+.1f}%")
    else:
        st.metric("Average Upside", "N/A")

with col4:
    st.metric("Calculations Performed", len(dcf_history))


# Historical table
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div style="margin: 2rem 0 1.5rem 0;">
    <h2 style="color: #FFFFFF; font-size: 1.75rem; font-weight: 700;">📋 Historical Table</h2>
</div>
""", unsafe_allow_html=True)

table_data = []
for calc in dcf_history:
    shares = calc.get("shares_outstanding", 0)
    fv = calc["fair_value"] / shares if shares > 0 else 0
    mp = calc.get("market_price", 0)
    upside = ((fv - mp) / mp) * 100 if fv > 0 and mp > 0 else None

    table_data.append(
        {
            "Date": calc["calculation_date"],
            "Fair Value": f"${fv:.2f}" if fv > 0 else "N/A",
            "Market Price": f"${mp:.2f}" if mp > 0 else "N/A",
            "Upside": f"{upside:+.1f}%" if upside is not None else "N/A",
            "r": f"{calc['discount_rate']:.1%}",
            "g": f"{calc['growth_rate']:.1%}",
        }
    )

df_history = pd.DataFrame(table_data)
st.dataframe(df_history, hide_index=True, use_container_width=True)
