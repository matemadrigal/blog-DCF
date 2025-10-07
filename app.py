import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="blog-DCF demo", layout="wide")

st.title("blog-DCF — Demo de datos financieros")
st.markdown("Pequeña app para descargar datos con yfinance y mostrarlos con Streamlit.")

# Sidebar
st.sidebar.header("Parámetros")
default_ticker = "AAPL"
if "ticker" not in st.session_state:
    st.session_state["ticker"] = default_ticker

ticker = st.sidebar.text_input("Ticker (Yahoo Finance)", value=st.session_state["ticker"]) or default_ticker
st.session_state["ticker"] = ticker

today = date.today()
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Fecha inicio", default_start)
end_date = st.sidebar.date_input("Fecha fin", today)

interval = st.sidebar.selectbox("Intervalo", ["1d", "1wk", "1mo"], index=0)

@st.cache_data(show_spinner=False)
def load_data(ticker: str, start: date, end: date, interval: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, start=start, end=end + timedelta(days=1), interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        return df
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return pd.DataFrame()

# Load
with st.spinner("Descargando datos..."):
    df = load_data(ticker, start_date, end_date, interval)

if df.empty:
    st.warning("No hay datos para ese ticker/rango. Prueba con otro símbolo o amplía el rango de fechas.")
else:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader(f"Precio de cierre — {ticker}")
        st.line_chart(df["Close"], use_container_width=True)

        st.subheader("Volumen")
        st.bar_chart(df["Volume"], use_container_width=True)

    with col2:
        st.subheader("Estadísticas básicas")
        stats = df["Close"].describe().to_frame().T
        st.table(stats)

    st.subheader("Datos (tabla)")
    st.dataframe(df.tail(200))

st.markdown("---")
st.markdown("Hecho con: pandas, yfinance, streamlit. Modifica `requirements.txt` si necesitas versiones diferentes.")
