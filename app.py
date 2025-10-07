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
default_start = today - timedelta(days=365)
start_date = st.sidebar.date_input("Fecha inicio", default_start)
end_date = st.sidebar.date_input("Fecha fin", today)

interval = st.sidebar.selectbox("Intervalo", ["1d", "1wk", "1mo"], index=0)


@st.cache_data(show_spinner=False)
def load_data(ticker: str, start: date, end: date, interval: str) -> pd.DataFrame:
    try:
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
    except Exception as e:
        st.error(f"Error descargando datos: {e}")
        return pd.DataFrame()


# Load
with st.spinner("Descargando datos..."):
    df = load_data(ticker, start_date, end_date, interval)

if df.empty:
    st.warning(
        "No hay datos para ese ticker/rango. Prueba con otro símbolo o amplía el rango de fechas."
    )
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
st.markdown(
    "Hecho con: pandas, yfinance, streamlit. Modifica `requirements.txt` si necesitas versiones diferentes."
)

# ------------------------------
# DCF valuation section
# ------------------------------
st.markdown("## Valoración DCF")

with st.expander("Abrir herramienta DCF", expanded=False):
    st.write(
        "Calcula un valor aproximado por DCF. Puedes introducir flujos de caja libres manualmente o autocompletar desde los datos financieros de Yahoo (cuando estén disponibles)."
    )

    col_a, col_b = st.columns([1, 2])
    with col_a:
        dcf_mode = st.radio(
            "Modo de entrada", ["Manual", "Autocompletar desde histórico"], index=0
        )
        years = st.number_input(
            "Años de proyección", min_value=1, max_value=20, value=5
        )
        discount_rate = st.number_input(
            "Tasa de descuento (r)",
            min_value=0.0,
            max_value=1.0,
            value=0.10,
            step=0.005,
            format="%.3f",
        )
        terminal_growth = st.number_input(
            "Crecimiento terminal (g)",
            min_value=-0.1,
            max_value=0.2,
            value=0.02,
            step=0.001,
            format="%.3f",
        )
        shares = st.number_input("Shares outstanding (opcional)", min_value=0, value=0)

    with col_b:
        st.markdown("**Entradas / Flujo de caja libre (FCF)**")

        autofilled = []
        if dcf_mode == "Autocompletar desde histórico":
            try:
                t = yf.Ticker(ticker)
                cashflow = t.cashflow
                # Try to compute FCF = Operating Cash Flow - Capital Expenditures
                if not cashflow.empty:
                    # cashflow columns are periods; take most recent `years` columns
                    cols = list(cashflow.columns)[:years]
                    for c in cols:
                        op = None
                        capex = None
                        for candidate in [
                            "Total Cash From Operating Activities",
                            "Total cash from operating activities",
                            "Net cash provided by operating activities",
                            "Operating Cash Flow",
                        ]:
                            if candidate in cashflow.index:
                                op = cashflow.loc[candidate, c]
                                break
                        for candidate in [
                            "Capital Expenditures",
                            "Capital Expenditure",
                            "Capital Expenditures (CAPEX)",
                        ]:
                            if candidate in cashflow.index:
                                capex = cashflow.loc[candidate, c]
                                break
                        if op is not None and capex is not None:
                            # capex usually negative in yfinance, so subtracting is correct
                            fcf_val = float(op - capex)
                        else:
                            fcf_val = None
                        autofilled.append(fcf_val)
                # fallback: try info.freeCashflow
                if not any(autofilled):
                    info = t.info
                    maybe = info.get("freeCashflow")
                    if maybe:
                        # fill with the same value as a rough estimate
                        autofilled = [float(maybe)] * years
            except Exception:
                autofilled = []

        # Build inputs (prefill with autofill values when available)
        manual_inputs = []
        for i in range(1, years + 1):
            default_val = None
            if (
                dcf_mode == "Autocompletar desde histórico"
                and i <= len(autofilled)
                and autofilled[i - 1] is not None
            ):
                default_val = autofilled[i - 1]
            if default_val is None:
                default_val = 0.0
            v = st.number_input(
                f"FCF año {i}", value=float(default_val), format="%.2f", key=f"fcf_{i}"
            )
            manual_inputs.append(float(v))

    # Validate rates
    if discount_rate <= terminal_growth:
        st.error(
            "La tasa de descuento debe ser mayor que el crecimiento terminal (r > g). Cambia los valores para continuar."
        )
    else:
        # Compute DCF
        pv = dcf_value(manual_inputs, discount_rate, terminal_growth)
        # compute per-year discounted contributions
        discounted = []
        for i, cf in enumerate(manual_inputs, start=1):
            discounted.append(cf / ((1 + discount_rate) ** i))
        # terminal
        if len(manual_inputs) > 0:
            last_cf = manual_inputs[-1]
            terminal = (
                last_cf * (1 + terminal_growth) / (discount_rate - terminal_growth)
            )
            discounted_terminal = terminal / ((1 + discount_rate) ** len(manual_inputs))
        else:
            terminal = 0.0
            discounted_terminal = 0.0

        st.subheader("Resultados DCF")
        col_r1, col_r2 = st.columns([1, 1])
        with col_r1:
            st.metric("Valor presente (PV) total", f"{pv:,.2f}")
            if shares > 0:
                st.metric("Valor por acción (estimado)", f"{(pv / shares):,.4f}")
        with col_r2:
            st.write("Terminal value (descontado):")
            st.write(f"{discounted_terminal:,.2f}")

        # Table of results
        rows = []
        for i, (cf, dcf_c) in enumerate(zip(manual_inputs, discounted), start=1):
            rows.append({"year": i, "fcf": cf, "discounted": dcf_c})
        if terminal != 0:
            rows.append(
                {
                    "year": f"TV@{len(manual_inputs)}",
                    "fcf": terminal,
                    "discounted": discounted_terminal,
                }
            )

        result_df = pd.DataFrame(rows)
        st.table(result_df)
        st.bar_chart(result_df.set_index("year")["discounted"])
