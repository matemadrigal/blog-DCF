"""Individual company DCF analysis with Fair Value vs Market Price comparison."""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime

from src.dcf.model import dcf_value
from src.cache import DCFCache


st.set_page_config(
    page_title="Análisis Individual - DCF", page_icon="📈", layout="wide"
)

st.title("📈 Análisis Individual")
st.markdown(
    "Calcula el Fair Value de una acción mediante DCF y compáralo con el precio de mercado."
)


# Initialize cache
@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()


# Sidebar inputs
st.sidebar.header("Parámetros")
ticker = st.sidebar.text_input("Ticker (Yahoo Finance)", value="AAPL").upper()

st.sidebar.subheader("Parámetros DCF")
mode = st.sidebar.radio("Modo FCF", ["Manual", "Autocompletar"], index=0)
years = st.sidebar.number_input(
    "Años de proyección", min_value=1, max_value=20, value=5
)
r = st.sidebar.number_input(
    "Tasa de descuento (r)",
    min_value=0.0,
    max_value=1.0,
    value=0.10,
    step=0.005,
    format="%.3f",
)
g = st.sidebar.number_input(
    "Crecimiento terminal (g)",
    min_value=-0.1,
    max_value=0.2,
    value=0.02,
    step=0.001,
    format="%.3f",
)
shares = st.sidebar.number_input(
    "Shares outstanding", min_value=0, value=0, help="Dejar en 0 para autocompletar"
)


# Data fetching
@st.cache_data(ttl=3600)
def load_price_data(ticker: str, days: int = 365) -> pd.DataFrame:
    """Load price data from Yahoo Finance."""
    end = date.today()
    start = end - timedelta(days=days)
    df = yf.download(ticker, start=start, end=end + timedelta(days=1), progress=False)
    if not df.empty:
        df.index = pd.to_datetime(df.index)
        # Save to cache
        cache.save_price_history(ticker, df)
    return df


@st.cache_data(ttl=3600)
def get_ticker_info(ticker: str):
    """Get ticker info from Yahoo Finance."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return info
    except Exception:
        return {}


# Main content
df_prices = load_price_data(ticker)
info = get_ticker_info(ticker)

if df_prices.empty:
    st.error(f"❌ No se encontraron datos para {ticker}")
    st.stop()

current_price = float(df_prices["Close"].iloc[-1])
company_name = info.get("longName", ticker)

# Header with company info
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"{company_name} ({ticker})")
with col2:
    st.metric("Precio Actual", f"${current_price:.2f}")
with col3:
    if shares == 0 and "sharesOutstanding" in info:
        shares = info["sharesOutstanding"]
    if shares > 0:
        st.metric(
            "Shares", f"{shares/1e9:.2f}B" if shares > 1e9 else f"{shares/1e6:.2f}M"
        )


# FCF Input Section
st.markdown("---")
st.subheader("📊 Proyecciones de Free Cash Flow")

# Autofill logic
autofill = []
if mode == "Autocompletar":
    try:
        t = yf.Ticker(ticker)
        cashflow = t.cashflow
        if not cashflow.empty:
            cols = list(cashflow.columns)[:years]
            for c in cols:
                op = None
                capex = None
                for idx in cashflow.index:
                    name = str(idx).lower()
                    if "operat" in name and op is None:
                        op = cashflow.loc[idx, c]
                    if "capital" in name and capex is None:
                        capex = cashflow.loc[idx, c]
                if op is not None and capex is not None:
                    autofill.append(float(op - capex))
    except Exception:
        autofill = []

fcf_cols = st.columns(years)
fcf_inputs = []
for i in range(years):
    with fcf_cols[i]:
        default = autofill[i] if i < len(autofill) else 0.0
        val = st.number_input(
            f"Año {i+1}",
            value=float(default),
            format="%.0f",
            key=f"fcf_{i}",
            help=f"FCF proyectado año {i+1}",
        )
        fcf_inputs.append(float(val))


# DCF Calculation
st.markdown("---")
st.subheader("💰 Valoración DCF")

if r <= g:
    st.error("⚠️ La tasa de descuento (r) debe ser mayor que g. Ajusta los parámetros.")
    st.stop()

try:
    fair_value_total = dcf_value(fcf_inputs, r, g)
    fair_value_per_share = fair_value_total / shares if shares > 0 else 0

    # Save to cache
    cache.save_dcf_calculation(
        ticker=ticker,
        fair_value=fair_value_total,
        discount_rate=r,
        growth_rate=g,
        fcf_projections=fcf_inputs,
        market_price=current_price,
        shares_outstanding=shares,
        metadata={"company_name": company_name, "mode": mode},
    )

    # Results
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Enterprise Value",
            (
                f"${fair_value_total/1e9:.2f}B"
                if fair_value_total > 1e9
                else f"${fair_value_total/1e6:.2f}M"
            ),
        )
    with col2:
        if fair_value_per_share > 0:
            st.metric("Fair Value / Acción", f"${fair_value_per_share:.2f}")
        else:
            st.info("Añade shares outstanding")
    with col3:
        st.metric("Precio Mercado", f"${current_price:.2f}")
    with col4:
        if fair_value_per_share > 0:
            upside = ((fair_value_per_share - current_price) / current_price) * 100
            st.metric(
                "Upside/Downside",
                f"{upside:+.1f}%",
                delta=f"${fair_value_per_share - current_price:.2f}",
                delta_color="normal" if upside > 0 else "inverse",
            )

    # DCF Breakdown
    st.markdown("#### Desglose del DCF")
    discounted = [cf / ((1 + r) ** i) for i, cf in enumerate(fcf_inputs, start=1)]
    terminal = fcf_inputs[-1] * (1 + g) / (r - g) if fcf_inputs else 0.0
    disc_terminal = terminal / ((1 + r) ** len(fcf_inputs)) if fcf_inputs else 0.0

    rows = []
    for i, (cf, dcf_c) in enumerate(zip(fcf_inputs, discounted), start=1):
        rows.append(
            {
                "Año": i,
                "FCF Proyectado": cf,
                "Valor Presente": dcf_c,
                "% del Total": (dcf_c / fair_value_total) * 100,
            }
        )
    if terminal != 0:
        rows.append(
            {
                "Año": "Terminal",
                "FCF Proyectado": terminal,
                "Valor Presente": disc_terminal,
                "% del Total": (disc_terminal / fair_value_total) * 100,
            }
        )

    df_dcf = pd.DataFrame(rows)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(
            df_dcf.style.format(
                {
                    "FCF Proyectado": "${:,.0f}",
                    "Valor Presente": "${:,.0f}",
                    "% del Total": "{:.1f}%",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    with col2:
        fig_dcf = go.Figure(
            data=[
                go.Bar(
                    x=df_dcf["Año"].astype(str),
                    y=df_dcf["Valor Presente"],
                    marker_color=["#1f77b4"] * (len(df_dcf) - 1) + ["#ff7f0e"],
                    text=df_dcf["Valor Presente"].apply(
                        lambda x: f"${x/1e9:.2f}B" if x > 1e9 else f"${x/1e6:.1f}M"
                    ),
                    textposition="outside",
                )
            ]
        )
        fig_dcf.update_layout(
            title="Contribución al Valor Presente",
            xaxis_title="Año",
            yaxis_title="Valor Presente ($)",
            showlegend=False,
            height=400,
        )
        st.plotly_chart(fig_dcf, use_container_width=True)

    # Fair Value vs Market Price Chart
    st.markdown("---")
    st.subheader("📊 Fair Value vs Precio de Mercado (Histórico)")

    # Get historical DCF calculations
    dcf_history = cache.get_dcf_history(ticker, limit=90)

    if len(dcf_history) > 1:
        # Prepare data
        dcf_dates = [
            datetime.fromisoformat(calc["calculation_date"]) for calc in dcf_history
        ]
        dcf_values = [
            (
                calc["fair_value"] / calc["shares_outstanding"]
                if calc.get("shares_outstanding")
                else 0
            )
            for calc in dcf_history
        ]

        # Filter valid values
        valid_data = [(d, v) for d, v in zip(dcf_dates, dcf_values) if v > 0]
        if valid_data:
            dcf_dates, dcf_values = zip(*valid_data)
        else:
            dcf_dates, dcf_values = [], []

        # Price history for same period
        if dcf_dates:
            min_date = min(dcf_dates).date()
            price_hist = cache.get_price_history(
                ticker, start_date=min_date.isoformat()
            )
            price_dates = [datetime.fromisoformat(p["date"]) for p in price_hist]
            price_values = [p["close"] for p in price_hist]
        else:
            price_dates, price_values = [], []

        # Create chart
        fig = go.Figure()

        if price_dates:
            fig.add_trace(
                go.Scatter(
                    x=price_dates,
                    y=price_values,
                    mode="lines",
                    name="Precio de Mercado",
                    line=dict(color="#1f77b4", width=2),
                )
            )

        if dcf_dates:
            fig.add_trace(
                go.Scatter(
                    x=dcf_dates,
                    y=dcf_values,
                    mode="lines+markers",
                    name="Fair Value (DCF)",
                    line=dict(color="#ff7f0e", width=2, dash="dash"),
                    marker=dict(size=8),
                )
            )

        fig.update_layout(
            title=f"{ticker} - Fair Value vs Precio de Mercado",
            xaxis_title="Fecha",
            yaxis_title="Precio por Acción ($)",
            hovermode="x unified",
            height=500,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        )

        st.plotly_chart(fig, use_container_width=True)

        # Analysis
        if dcf_values and price_values:
            avg_fv = sum(dcf_values) / len(dcf_values)
            avg_price = sum(price_values) / len(price_values)
            avg_premium = ((avg_price - avg_fv) / avg_fv) * 100

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fair Value Promedio", f"${avg_fv:.2f}")
            with col2:
                st.metric("Precio Promedio", f"${avg_price:.2f}")
            with col3:
                st.metric("Premium/Descuento Promedio", f"{avg_premium:+.1f}%")
    else:
        st.info(
            "📌 Necesitas al menos 2 cálculos históricos para ver el gráfico. Vuelve mañana o calcula con diferentes parámetros."
        )

        # Show current comparison
        if fair_value_per_share > 0:
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=["Fair Value", "Precio Mercado"],
                        y=[fair_value_per_share, current_price],
                        marker_color=["#ff7f0e", "#1f77b4"],
                        text=[f"${fair_value_per_share:.2f}", f"${current_price:.2f}"],
                        textposition="outside",
                    )
                ]
            )
            fig.update_layout(
                title="Comparación Actual",
                yaxis_title="Precio ($)",
                showlegend=False,
                height=400,
            )
            st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Error en el cálculo: {str(e)}")

# Export section
st.markdown("---")
st.subheader("📄 Exportar Informe")

col1, col2 = st.columns(2)

with col1:
    if st.button("💾 Guardar Análisis en Base de Datos"):
        st.success(f"✅ Análisis de {ticker} guardado en la base de datos")
        st.balloons()

with col2:
    try:
        from src.reports import generate_dcf_report

        if st.button("📥 Descargar Informe PDF"):
            pdf_data = {
                "fair_value": fair_value_total,
                "market_price": current_price,
                "shares_outstanding": shares,
                "discount_rate": r,
                "growth_rate": g,
                "fcf_projections": fcf_inputs,
            }

            pdf_bytes = generate_dcf_report(ticker, company_name, pdf_data)

            st.download_button(
                label="⬇️ Descargar PDF",
                data=pdf_bytes,
                file_name=f"DCF_Report_{ticker}_{date.today().isoformat()}.pdf",
                mime="application/pdf",
            )
            st.success("✅ Informe PDF generado correctamente")

    except ImportError:
        st.warning("⚠️ Para generar PDFs instala: pip install reportlab")
