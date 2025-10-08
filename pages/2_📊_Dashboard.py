"""Dashboard with overview of all analyzed companies."""

import streamlit as st
import pandas as pd

from src.cache import DCFCache

st.set_page_config(page_title="Dashboard - DCF", page_icon="📊", layout="wide")

st.title("📊 Dashboard")
st.markdown("Resumen ejecutivo de todas las empresas analizadas.")


@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()

# Get all tickers
tickers = cache.get_all_tickers()

if not tickers:
    st.info(
        "📌 No hay análisis guardados aún. Ve a **Análisis Individual** para calcular tu primer DCF."
    )
    st.stop()

# Build summary table
summary_data = []

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

        # Recommendation
        if upside > 20:
            rec = "🟢 COMPRAR"
        elif upside < -20:
            rec = "🔴 VENDER"
        else:
            rec = "🟡 MANTENER"

        summary_data.append(
            {
                "Ticker": ticker,
                "Empresa": (
                    latest.get("metadata", {}).get("company_name", ticker)
                    if latest.get("metadata")
                    else ticker
                ),
                "Fair Value": (
                    f"${fair_value_per_share:.2f}"
                    if fair_value_per_share > 0
                    else "N/A"
                ),
                "Precio Mercado": f"${market_price:.2f}" if market_price > 0 else "N/A",
                "Upside/Downside": f"{upside:+.1f}%" if upside != 0 else "N/A",
                "Recomendación": rec,
                "Última Actualización": latest["calculation_date"],
                "r": f"{latest['discount_rate']:.1%}",
                "g": f"{latest['growth_rate']:.1%}",
            }
        )

if summary_data:
    df_summary = pd.DataFrame(summary_data)

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Empresas Analizadas", len(tickers))
    with col2:
        buy_count = sum(1 for d in summary_data if "COMPRAR" in d["Recomendación"])
        st.metric("Oportunidades de Compra", buy_count)
    with col3:
        sell_count = sum(1 for d in summary_data if "VENDER" in d["Recomendación"])
        st.metric("Señales de Venta", sell_count)
    with col4:
        hold_count = sum(1 for d in summary_data if "MANTENER" in d["Recomendación"])
        st.metric("Mantener", hold_count)

    st.markdown("---")

    # Summary table
    st.subheader("📋 Resumen de Valoraciones")

    st.dataframe(
        df_summary,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Ticker": st.column_config.TextColumn("Ticker", width="small"),
            "Empresa": st.column_config.TextColumn("Empresa", width="medium"),
            "Fair Value": st.column_config.TextColumn("Fair Value", width="small"),
            "Precio Mercado": st.column_config.TextColumn(
                "Precio Mercado", width="small"
            ),
            "Upside/Downside": st.column_config.TextColumn(
                "Upside/Downside", width="small"
            ),
            "Recomendación": st.column_config.TextColumn(
                "Recomendación", width="medium"
            ),
            "Última Actualización": st.column_config.DateColumn(
                "Última Actualización", width="small"
            ),
        },
    )

    st.markdown("---")
    st.markdown("**Leyenda:**")
    st.markdown("- 🟢 **COMPRAR**: Fair Value >20% por encima del precio de mercado")
    st.markdown("- 🟡 **MANTENER**: Fair Value entre -20% y +20% del precio de mercado")
    st.markdown("- 🔴 **VENDER**: Fair Value >20% por debajo del precio de mercado")

else:
    st.warning("No hay datos suficientes para mostrar el dashboard.")
