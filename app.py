"""Minimal Streamlit app for blog-DCF: download price data and a DCF tool.

This file is intentionally small and self-contained. It uses yfinance to fetch
historical price data and the DCF function from src.dcf.model.
"""

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

from src.dcf.model import dcf_value


st.set_page_config(page_title="blog-DCF demo", layout="wide")


st.title("blog-DCF — Demo de datos financieros")
st.markdown("Pequeña app para descargar datos con yfinance y mostrarlos con Streamlit.")


# Sidebar
st.sidebar.header("Parámetros")
default_ticker = "AAPL"
if "ticker" not in st.session_state:
    st.session_state["ticker"] = default_ticker

ticker = (
    st.sidebar.text_input("Ticker (Yahoo Finance)", value=st.session_state["ticker"])
    or default_ticker
)
st.session_state["ticker"] = ticker

today = date.today()
start_date = st.sidebar.date_input("Fecha inicio", today - timedelta(days=365))
end_date = st.sidebar.date_input("Fecha fin", today)
interval = st.sidebar.selectbox("Intervalo", ["1d", "1wk", "1mo"], index=0)


@st.cache_data
def load_data(ticker: str, start: date, end: date, interval: str) -> pd.DataFrame:
    df = yf.download(
        ticker,
        start=start,
        end=end + timedelta(days=1),
        interval=interval,
        progress=False,
    )
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index)
    return df


df = load_data(ticker, start_date, end_date, interval)

if df.empty:
    st.warning(
        "No hay datos para ese ticker/rango. Prueba con otro símbolo o amplía el rango de fechas."
    )
else:
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader(f"Precio de cierre — {ticker}")
        st.line_chart(df["Close"], width="stretch")
        st.subheader("Volumen")
        st.bar_chart(df["Volume"], width="stretch")

    with c2:
        st.subheader("Estadísticas básicas")
        stats = pd.DataFrame(df["Close"].describe()).T
        st.table(stats)

    st.subheader("Datos (tabla)")
    st.dataframe(df.tail(200))


st.markdown("---")
st.markdown(
    "Hecho con: pandas, yfinance, streamlit. Modifica `requirements.txt` si necesitas versiones diferentes."
)


with st.expander("Herramienta DCF", expanded=False):
    st.write("Introduce FCFs manualmente o intenta autocompletar desde Yahoo Finance.")
    mode = st.radio("Modo", ["Manual", "Autocompletar"], index=0)
    years = st.number_input("Años de proyección", min_value=1, max_value=20, value=5)
    r = st.number_input(
        "Tasa de descuento (r)",
        min_value=0.0,
        max_value=1.0,
        value=0.10,
        step=0.005,
        format="%.3f",
    )
    g = st.number_input(
        "Crecimiento terminal (g)",
        min_value=-0.1,
        max_value=0.2,
        value=0.02,
        step=0.001,
        format="%.3f",
    )
    shares = st.number_input("Shares outstanding (opcional)", min_value=0, value=0)

    autofill = []
    if mode == "Autocompletar":
        try:
            t = yf.Ticker(ticker)
            cashflow = t.cashflow
            if not cashflow.empty:
                cols = list(cashflow.columns)[:years]
                for c in cols:
                    # best-effort extraction
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

    fcf_inputs = []
    for i in range(1, years + 1):
        default = autofill[i - 1] if i <= len(autofill) else 0.0
        val = st.number_input(
            f"FCF año {i}", value=float(default), format="%.2f", key=f"fcf_{i}"
        )
        fcf_inputs.append(float(val))

    if r <= g:
        st.error("r debe ser mayor que g (r > g). Ajusta los parámetros.")
    else:
        pv = dcf_value(fcf_inputs, r, g)
        discounted = [cf / ((1 + r) ** i) for i, cf in enumerate(fcf_inputs, start=1)]
        terminal = fcf_inputs[-1] * (1 + g) / (r - g) if fcf_inputs else 0.0
        disc_terminal = terminal / ((1 + r) ** len(fcf_inputs)) if fcf_inputs else 0.0

        st.metric("PV total", f"{pv:,.2f}")
        if shares > 0:
            st.metric("Valor por acción", f"{pv / shares:,.4f}")

        rows = []
        for i, (cf, dcf_c) in enumerate(zip(fcf_inputs, discounted), start=1):
            rows.append({"year": i, "fcf": cf, "discounted": dcf_c})
        if terminal != 0:
            rows.append(
                {
                    "year": f"TV@{len(fcf_inputs)}",
                    "fcf": terminal,
                    "discounted": disc_terminal,
                }
            )

        res_df = pd.DataFrame(rows)
        st.table(res_df)
        st.bar_chart(res_df.set_index("year")["discounted"], width="stretch")
