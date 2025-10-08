"""Historical Fair Value vs Market Price evolution."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from src.cache import DCFCache

st.set_page_config(page_title="Histórico - DCF", page_icon="📅", layout="wide")

st.title("📅 Evolución Histórica")
st.markdown("Analiza la evolución temporal del Fair Value vs Precio de Mercado.")


@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()

# Get all tickers
all_tickers = cache.get_all_tickers()

if not all_tickers:
    st.info("📌 No hay análisis guardados. Ve a **Análisis Individual** primero.")
    st.stop()

# Ticker selection
ticker = st.selectbox("Selecciona una empresa", options=all_tickers, index=0)

# Get historical data
dcf_history = cache.get_dcf_history(ticker)

if len(dcf_history) < 2:
    st.warning(
        f"📌 Solo hay {len(dcf_history)} cálculo(s) para {ticker}. Necesitas al menos 2 para ver la evolución histórica."
    )
    st.info("💡 **Tip**: Realiza cálculos periódicos para construir un historial.")

    if len(dcf_history) == 1:
        latest = dcf_history[0]
        st.markdown("### Último Cálculo")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Fecha", latest["calculation_date"])
        with col2:
            shares = latest.get("shares_outstanding", 0)
            fv = latest["fair_value"] / shares if shares > 0 else 0
            st.metric("Fair Value", f"${fv:.2f}" if fv > 0 else "N/A")
        with col3:
            mp = latest.get("market_price", 0)
            st.metric("Precio Mercado", f"${mp:.2f}" if mp > 0 else "N/A")

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
    st.warning("No hay datos suficientes para mostrar el histórico.")
    st.stop()


# Main chart: Fair Value vs Market Price
st.subheader(f"📈 {ticker} - Fair Value vs Precio de Mercado")

fig = go.Figure()

# Market Price
if any(p is not None for p in dcf_market_prices):
    fig.add_trace(
        go.Scatter(
            x=dcf_dates,
            y=dcf_market_prices,
            mode="lines+markers",
            name="Precio de Mercado",
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
    xaxis_title="Fecha",
    yaxis_title="Precio por Acción ($)",
    hovermode="x unified",
    height=500,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)

st.plotly_chart(fig, use_container_width=True)


# Upside/Downside evolution
st.markdown("---")
st.subheader("📊 Evolución del Upside/Downside")

fig2 = go.Figure()

valid_upsides = [(d, u) for d, u in zip(dcf_dates, dcf_upsides) if u is not None]
if valid_upsides:
    dates, upsides = zip(*valid_upsides)
    colors = ["green" if u > 0 else "red" for u in upsides]

    fig2.add_trace(
        go.Bar(x=dates, y=upsides, marker_color=colors, name="Upside/Downside")
    )

    fig2.add_hline(y=0, line_dash="dash", line_color="gray")
    fig2.add_hline(y=20, line_dash="dot", line_color="green", opacity=0.5)
    fig2.add_hline(y=-20, line_dash="dot", line_color="red", opacity=0.5)

    fig2.update_layout(
        xaxis_title="Fecha",
        yaxis_title="Upside/Downside (%)",
        height=400,
        showlegend=False,
    )

    st.plotly_chart(fig2, use_container_width=True)

    st.caption(
        "🟢 Línea verde: +20% (zona de compra) | 🔴 Línea roja: -20% (zona de venta)"
    )
else:
    st.info("No hay datos de upside/downside disponibles.")


# Statistics
st.markdown("---")
st.subheader("📊 Estadísticas Históricas")

col1, col2, col3, col4 = st.columns(4)

with col1:
    avg_fv = sum(dcf_fair_values) / len(dcf_fair_values)
    st.metric("Fair Value Promedio", f"${avg_fv:.2f}")

with col2:
    valid_prices = [p for p in dcf_market_prices if p is not None]
    if valid_prices:
        avg_price = sum(valid_prices) / len(valid_prices)
        st.metric("Precio Promedio", f"${avg_price:.2f}")
    else:
        st.metric("Precio Promedio", "N/A")

with col3:
    valid_ups = [u for u in dcf_upsides if u is not None]
    if valid_ups:
        avg_upside = sum(valid_ups) / len(valid_ups)
        st.metric("Upside Promedio", f"{avg_upside:+.1f}%")
    else:
        st.metric("Upside Promedio", "N/A")

with col4:
    st.metric("Cálculos Realizados", len(dcf_history))


# Historical table
st.markdown("---")
st.subheader("📋 Tabla Histórica")

table_data = []
for calc in dcf_history:
    shares = calc.get("shares_outstanding", 0)
    fv = calc["fair_value"] / shares if shares > 0 else 0
    mp = calc.get("market_price", 0)
    upside = ((fv - mp) / mp) * 100 if fv > 0 and mp > 0 else None

    table_data.append(
        {
            "Fecha": calc["calculation_date"],
            "Fair Value": f"${fv:.2f}" if fv > 0 else "N/A",
            "Precio Mercado": f"${mp:.2f}" if mp > 0 else "N/A",
            "Upside": f"{upside:+.1f}%" if upside is not None else "N/A",
            "r": f"{calc['discount_rate']:.1%}",
            "g": f"{calc['growth_rate']:.1%}",
        }
    )

df_history = pd.DataFrame(table_data)
st.dataframe(df_history, hide_index=True, use_container_width=True)
