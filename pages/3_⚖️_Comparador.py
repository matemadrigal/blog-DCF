"""Compare multiple companies side by side."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.cache import DCFCache

st.set_page_config(page_title="Comparador - DCF", page_icon="⚖️", layout="wide")

st.title("⚖️ Comparador de Empresas")
st.markdown("Compara múltiples empresas lado a lado.")


@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()

# Get all tickers
all_tickers = cache.get_all_tickers()

if not all_tickers:
    st.info("📌 No hay análisis guardados. Ve a **Análisis Individual** primero.")
    st.stop()

# Selection
selected_tickers = st.multiselect(
    "Selecciona empresas para comparar (máximo 5)",
    options=all_tickers,
    default=all_tickers[: min(3, len(all_tickers))],
    max_selections=5,
)

if not selected_tickers:
    st.warning("Selecciona al menos una empresa.")
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
                "Precio Mercado": market_price,
                "Upside (%)": upside,
                "Tasa Descuento (r)": latest["discount_rate"] * 100,
                "Crecimiento (g)": latest["growth_rate"] * 100,
                "Enterprise Value (M)": fair_value_total / 1e6,
            }
        )

if comparison_data:
    df_comp = pd.DataFrame(comparison_data)

    # Table
    st.subheader("📊 Comparación")
    st.dataframe(
        df_comp.style.format(
            {
                "Fair Value": "${:.2f}",
                "Precio Mercado": "${:.2f}",
                "Upside (%)": "{:+.1f}%",
                "Tasa Descuento (r)": "{:.1f}%",
                "Crecimiento (g)": "{:.1f}%",
                "Enterprise Value (M)": "${:,.0f}M",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    # Charts
    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fair Value vs Precio de Mercado")
        fig1 = go.Figure(
            data=[
                go.Bar(
                    name="Fair Value",
                    x=df_comp["Ticker"],
                    y=df_comp["Fair Value"],
                    marker_color="#ff7f0e",
                ),
                go.Bar(
                    name="Precio Mercado",
                    x=df_comp["Ticker"],
                    y=df_comp["Precio Mercado"],
                    marker_color="#1f77b4",
                ),
            ]
        )
        fig1.update_layout(
            barmode="group", yaxis_title="Precio por Acción ($)", height=400
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("Upside/Downside Potencial")
        colors = ["green" if x > 0 else "red" for x in df_comp["Upside (%)"]]
        fig2 = go.Figure(
            data=[
                go.Bar(
                    x=df_comp["Ticker"], y=df_comp["Upside (%)"], marker_color=colors
                )
            ]
        )
        fig2.update_layout(yaxis_title="Upside/Downside (%)", height=400)
        fig2.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig2, use_container_width=True)

    # Enterprise Value comparison
    st.markdown("---")
    st.subheader("Tamaño de Empresa (Enterprise Value)")
    fig3 = go.Figure(
        data=[
            go.Bar(
                x=df_comp["Ticker"],
                y=df_comp["Enterprise Value (M)"],
                marker_color="#2ca02c",
            )
        ]
    )
    fig3.update_layout(yaxis_title="Enterprise Value (Millones $)", height=400)
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.warning("No hay datos para las empresas seleccionadas.")
