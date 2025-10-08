"""Individual company DCF analysis with Fair Value vs Market Price comparison."""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime

from src.dcf.model import dcf_value
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.projections import (
    predict_growth_rate_linear_regression,
    apply_growth_rates_to_base,
)
from src.cache import DCFCache
from src.data_providers.aggregator import get_data_aggregator
from src.companies import get_sp500_companies, get_all_sectors
from src.companies.fcf_scanner import get_fcf_scanner


st.set_page_config(
    page_title="Análisis Individual - DCF", page_icon="📈", layout="wide"
)

st.title("📈 Análisis Individual")
st.markdown(
    "Calcula el Fair Value de una acción mediante DCF y compáralo con el precio de mercado."
)


# Initialize cache and data aggregator
@st.cache_resource
def get_cache():
    return DCFCache()


cache = get_cache()
aggregator = get_data_aggregator()
fcf_scanner = get_fcf_scanner()


# Sidebar inputs
st.sidebar.header("Selección de Empresa")

# Company selection mode
selection_mode = st.sidebar.radio(
    "Modo de selección",
    ["Búsqueda manual", "Lista con filtros"],
    help="Elige cómo quieres seleccionar la empresa",
)

if selection_mode == "Búsqueda manual":
    # Original text input
    ticker = st.sidebar.text_input("Ticker (Yahoo Finance)", value="AAPL").upper()

else:
    # List with filters
    st.sidebar.subheader("Filtros")

    # Get all companies
    companies = get_sp500_companies()
    all_sectors = get_all_sectors()

    # Search filter
    search_query = st.sidebar.text_input(
        "🔍 Buscar",
        placeholder="Ej: Apple, MSFT, Tech...",
        help="Busca por ticker o nombre de empresa",
    )

    # Sector filter
    sector_filter = st.sidebar.selectbox(
        "Sector", ["Todos"] + all_sectors, help="Filtra por sector"
    )

    # Alphabetical filter
    alpha_filter = st.sidebar.selectbox(
        "Letra inicial",
        ["Todas"] + list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
        help="Filtra por primera letra del ticker",
    )

    # FCF sorting
    fcf_sort = st.sidebar.selectbox(
        "Ordenar por FCF",
        ["Sin ordenar", "FCF más alto", "FCF más bajo"],
        help="Ordena empresas por su FCF del año base",
    )

    # Apply filters
    filtered_companies = companies.copy()

    # Search filter
    if search_query:
        filtered_companies = [
            c
            for c in filtered_companies
            if (
                search_query.lower() in c["ticker"].lower()
                or search_query.lower() in c["name"].lower()
                or search_query.lower() in c["sector"].lower()
            )
        ]

    # Sector filter
    if sector_filter != "Todos":
        filtered_companies = [
            c for c in filtered_companies if c["sector"] == sector_filter
        ]

    # Alphabetical filter
    if alpha_filter != "Todas":
        filtered_companies = [
            c for c in filtered_companies if c["ticker"].startswith(alpha_filter)
        ]

    # FCF sorting
    if fcf_sort != "Sin ordenar":
        # Scan companies if needed
        if st.sidebar.button("🔄 Actualizar FCF de empresas filtradas"):
            with st.spinner(f"Escaneando {len(filtered_companies)} empresas..."):
                progress_bar = st.sidebar.progress(0)
                status_text = st.sidebar.empty()

                def progress_callback(current, total, ticker):
                    progress_bar.progress(current / total)
                    status_text.text(f"Escaneando {ticker}... ({current}/{total})")

                tickers = [c["ticker"] for c in filtered_companies]
                fcf_scanner.scan_companies(tickers, progress_callback)

                progress_bar.empty()
                status_text.empty()
                st.sidebar.success(f"✅ {len(filtered_companies)} empresas escaneadas")

        # Add FCF to companies
        for company in filtered_companies:
            cached_fcf = fcf_scanner.get_cached_fcf(company["ticker"])
            company["fcf"] = cached_fcf if cached_fcf is not None else 0.0

        # Sort by FCF
        if fcf_sort == "FCF más alto":
            filtered_companies.sort(key=lambda x: x.get("fcf", 0), reverse=True)
        elif fcf_sort == "FCF más bajo":
            filtered_companies.sort(key=lambda x: x.get("fcf", 0))

    # Display filtered companies
    st.sidebar.markdown(f"**{len(filtered_companies)} empresas encontradas**")

    # Create display options
    display_options = []
    for c in filtered_companies:
        fcf_display = ""
        if "fcf" in c and c["fcf"] > 0:
            fcf_b = c["fcf"] / 1e9
            fcf_display = f" (FCF: ${fcf_b:.1f}B)"

        display_text = f"{c['ticker']} - {c['name']}{fcf_display}"
        display_options.append(display_text)

    if display_options:
        selected_display = st.sidebar.selectbox(
            "Selecciona empresa", display_options, help="Lista de empresas filtradas"
        )

        # Extract ticker from selection
        ticker = selected_display.split(" - ")[0]
    else:
        st.sidebar.warning("⚠️ No se encontraron empresas con estos filtros")
        ticker = "AAPL"

st.sidebar.markdown("---")
st.sidebar.subheader("Parámetros DCF")

# Data source selection
available_providers = aggregator.get_available_providers()
if len(available_providers) > 1:
    st.sidebar.info(f"📡 Fuentes disponibles: {', '.join(available_providers)}")
    data_strategy = st.sidebar.selectbox(
        "Estrategia de datos",
        ["best_quality", "first_available", "merge"],
        format_func=lambda x: {
            "best_quality": "Mejor Calidad",
            "first_available": "Primera Disponible",
            "merge": "Combinar Fuentes",
        }[x],
        help="best_quality: Compara todas las fuentes y elige la mejor\nfirst_available: Usa la primera que funcione\nmerge: Combina datos de múltiples fuentes",
    )
else:
    data_strategy = "first_available"
    st.sidebar.info(
        f"📡 Usando: {available_providers[0] if available_providers else 'Yahoo Finance'}"
    )

mode = st.sidebar.radio(
    "Modo FCF", ["Manual", "Autocompletar", "Multi-fuente"], index=0
)

# DCF Model Selection
use_enhanced_model = st.sidebar.checkbox(
    "🚀 Usar Modelo DCF Mejorado",
    value=True,
    help="Modelo mejorado con:\n- Crecimiento escalonado (10-25%, 10-15%, 3-8%)\n- WACC 8.5%\n- Equity Value (EV + Cash - Debt)\n- Shares diluidas",
)

years = st.sidebar.number_input(
    "Años de proyección", min_value=1, max_value=20, value=5
)

if use_enhanced_model:
    r = st.sidebar.number_input(
        "WACC (Tasa de descuento)",
        min_value=0.0,
        max_value=0.30,
        value=0.085,
        step=0.005,
        format="%.3f",
        help="Weighted Average Cost of Capital (defecto 8.5%)",
    )
    g = st.sidebar.number_input(
        "Crecimiento terminal (g)",
        min_value=0.0,
        max_value=0.10,
        value=0.03,
        step=0.005,
        format="%.3f",
        help="Crecimiento perpetuo terminal (defecto 3%)",
    )
else:
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
    "Shares outstanding",
    min_value=0,
    value=0,
    help="Dejar en 0 para autocompletar (diluted shares)",
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


@st.cache_data(ttl=3600)
def get_balance_sheet_data(ticker: str):
    """
    Get balance sheet data (cash, debt) from Yahoo Finance.

    Returns:
        tuple: (cash, total_debt)
    """
    try:
        t = yf.Ticker(ticker)
        info = t.info
        balance_sheet = t.balance_sheet

        cash = None
        total_debt = None

        # Try to get from balance sheet first
        if not balance_sheet.empty:
            col = balance_sheet.columns[0]  # Most recent
            for idx in balance_sheet.index:
                name = str(idx).lower()

                # Cash
                if cash is None and (
                    "cash and cash equivalents" in name
                    or ("cash" in name and "short" in name)
                ):
                    val = balance_sheet.loc[idx, col]
                    if val is not None and not str(val).lower() == "nan":
                        cash = float(val)

                # Debt
                if total_debt is None:
                    if "total debt" in name:
                        val = balance_sheet.loc[idx, col]
                        if val is not None and not str(val).lower() == "nan":
                            total_debt = float(val)
                    elif "long term debt" in name or "long-term debt" in name:
                        val = balance_sheet.loc[idx, col]
                        if val is not None and not str(val).lower() == "nan":
                            total_debt = float(val)

        # Fallback to info dict
        if cash is None:
            cash = info.get("totalCash", 0.0)
        if total_debt is None:
            total_debt = info.get("totalDebt", 0.0)

        return float(cash) if cash else 0.0, float(total_debt) if total_debt else 0.0

    except Exception as e:
        st.warning(f"⚠️ Error al obtener balance: {str(e)}")
        return 0.0, 0.0


@st.cache_data(ttl=3600)
def get_base_fcf_from_yahoo(ticker: str):
    """
    Get base year FCF from Yahoo Finance using unified calculation.

    Returns:
        tuple: (base_fcf, historical_fcf_list) or (0.0, [])

    Formula: FCF = Operating Cash Flow - |Capital Expenditure|
    """
    try:
        t = yf.Ticker(ticker)
        cashflow = t.cashflow

        if cashflow.empty:
            return 0.0, []

        historical_fcf = []

        # Get up to 5 years of historical data
        cols = list(cashflow.columns)[:5]
        for c in cols:
            op = None
            capex = None
            for idx in cashflow.index:
                name = str(idx).lower()
                # Look for Operating Cash Flow
                if "operating cash flow" in name and op is None:
                    op = cashflow.loc[idx, c]
                # Look for Capital Expenditure
                if (
                    "capital expenditure" in name or "purchase of ppe" in name
                ) and capex is None:
                    capex = cashflow.loc[idx, c]

            if op is not None and capex is not None:
                # CAPEX is usually negative, use abs to ensure correct subtraction
                fcf = float(op - abs(capex))
                historical_fcf.append(fcf)

        # Most recent year is first in Yahoo Finance
        base_fcf = historical_fcf[0] if historical_fcf else 0.0

        return base_fcf, historical_fcf

    except Exception as e:
        st.error(f"❌ Error al obtener FCF base: {str(e)}")
        return 0.0, []


# Main content
df_prices = load_price_data(ticker)
info = get_ticker_info(ticker)

if df_prices.empty:
    st.error(f"❌ No se encontraron datos para {ticker}")
    st.stop()

current_price = float(df_prices["Close"].iloc[-1])
company_name = info.get("longName", ticker)

# Get balance sheet data (cash, debt) for enhanced model
cash, total_debt = get_balance_sheet_data(ticker)

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

# Get base year FCF (most recent historical data)
base_fcf = 0.0
historical_fcf = []

# Autofill logic for growth rates
autofill_growth_rates = []
data_source_used = None

if mode == "Multi-fuente":
    # Use multi-source aggregator
    with st.spinner("🔍 Buscando datos en múltiples fuentes..."):
        financial_data = aggregator.get_financial_data(
            ticker, years, strategy=data_strategy
        )
        if financial_data:
            # Calculate or get FCF
            fcf_data = financial_data.calculate_fcf()
            if fcf_data:
                historical_fcf = fcf_data
                # Yahoo Finance orders data from newest to oldest, so first element is most recent
                base_fcf = fcf_data[0] if fcf_data else 0.0
                data_source_used = financial_data.data_source

                # Calculate growth rates using linear regression
                # Need to reverse for regression (oldest to newest)
                autofill_growth_rates = predict_growth_rate_linear_regression(
                    list(reversed(fcf_data)), years
                )

                # Update company info if available
                if financial_data.company_name:
                    company_name = financial_data.company_name
                if financial_data.current_price:
                    current_price = financial_data.current_price
                if financial_data.shares_outstanding and shares == 0:
                    shares = financial_data.shares_outstanding

                # Show data quality metrics
                base_fcf_display = (
                    f"${base_fcf/1e9:.2f}B"
                    if base_fcf > 1e9
                    else f"${base_fcf/1e6:.2f}M"
                )
                st.success(
                    f"✅ Datos obtenidos de {financial_data.data_source} | "
                    f"FCF Base: {base_fcf_display} | "
                    f"Completitud: {financial_data.data_completeness:.1f}% | "
                    f"Confianza: {financial_data.confidence_score:.1f}%"
                )
            else:
                st.warning(
                    "⚠️ No se pudieron calcular FCF desde multi-fuentes. Usando Yahoo Finance..."
                )

elif mode == "Autocompletar":
    # Use unified Yahoo Finance calculation
    with st.spinner("🔍 Obteniendo datos desde Yahoo Finance..."):
        base_fcf, historical_fcf = get_base_fcf_from_yahoo(ticker)

        if historical_fcf:
            # Predict growth rates using linear regression
            autofill_growth_rates = predict_growth_rate_linear_regression(
                list(reversed(historical_fcf)), years
            )
            data_source_used = "Yahoo Finance"

            st.success(
                f"✅ Calculados % de crecimiento basados en {len(historical_fcf)} años históricos (FCF Base: ${base_fcf/1e9:.2f}B)"
                if base_fcf > 1e9
                else f"✅ Calculados % de crecimiento basados en {len(historical_fcf)} años históricos (FCF Base: ${base_fcf/1e6:.2f}M)"
            )
        else:
            st.warning("⚠️ No se encontraron datos de Operating Cash Flow y CAPEX")

# Display base FCF information
if base_fcf > 0:
    st.info(
        f"📊 **Año Base FCF**: ${base_fcf/1e9:.2f}B"
        if base_fcf > 1e9
        else (
            f"📊 **Año Base FCF**: ${base_fcf/1e6:.2f}M"
            if base_fcf > 1e6
            else f"📊 **Año Base FCF**: ${base_fcf:,.0f}"
        )
    )

# Growth rate inputs
growth_rate_cols = st.columns(years)
growth_rate_inputs = []

for i in range(years):
    with growth_rate_cols[i]:
        default_rate = (
            autofill_growth_rates[i] * 100 if i < len(autofill_growth_rates) else 2.0
        )
        val = st.number_input(
            f"Año {i+1}",
            value=float(default_rate),
            format="%.2f",
            step=0.5,
            key=f"growth_{i}",
            help=f"% de crecimiento respecto al año {i if i > 0 else 'base'}",
        )
        growth_rate_inputs.append(float(val) / 100)  # Convert to decimal


# Apply growth rates to base FCF to get projected FCF
if base_fcf == 0 and mode == "Manual":
    # Manual mode: fetch base FCF from Yahoo but allow user to edit
    suggested_base_fcf, _ = get_base_fcf_from_yahoo(ticker)

    base_fcf = st.number_input(
        "FCF Año Base",
        value=float(suggested_base_fcf),
        format="%.0f",
        help=(
            f"FCF del año más reciente. Autocompletado: ${suggested_base_fcf/1e9:.2f}B"
            if suggested_base_fcf > 1e9
            else (
                f"FCF del año más reciente. Autocompletado: ${suggested_base_fcf/1e6:.2f}M"
                if suggested_base_fcf > 1e6
                else "FCF del año más reciente (año 0)"
            )
        ),
    )

# Calculate projected FCF from growth rates
fcf_inputs = apply_growth_rates_to_base(base_fcf, growth_rate_inputs)

# DCF Calculation
st.markdown("---")
st.subheader("💰 Valoración DCF")

if r <= g:
    st.error("⚠️ La tasa de descuento (r) debe ser mayor que g. Ajusta los parámetros.")
    st.stop()

if base_fcf == 0:
    st.error("❌ Error en el cálculo: float division by zero")
    st.warning(
        "⚠️ Necesitas un valor base de FCF. Prueba con modo 'Autocompletar' o 'Multi-fuente'."
    )
    st.stop()

try:
    if use_enhanced_model:
        # Use Enhanced DCF Model
        enhanced_model = EnhancedDCFModel(wacc=r, terminal_growth=g)

        # Perform full DCF valuation
        dcf_result = enhanced_model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf if historical_fcf else [base_fcf],
            cash=cash,
            debt=total_debt,
            diluted_shares=shares,
            years=years,
            custom_growth_rates=(
                None
                if mode == "Autocompletar" or mode == "Multi-fuente"
                else growth_rate_inputs
            ),
        )

        fair_value_total = dcf_result["enterprise_value"]
        equity_value = dcf_result["equity_value"]
        fair_value_per_share = dcf_result["fair_value_per_share"]
        fcf_inputs = dcf_result["projected_fcf"]
        growth_rate_inputs = dcf_result["growth_rates"]

    else:
        # Use Original DCF Model
        fair_value_total = dcf_value(fcf_inputs, r, g)
        equity_value = fair_value_total  # Old model doesn't adjust for cash/debt
        fair_value_per_share = fair_value_total / shares if shares > 0 else 0
        dcf_result = None

    # Save to cache
    cache.save_dcf_calculation(
        ticker=ticker,
        fair_value=equity_value if use_enhanced_model else fair_value_total,
        discount_rate=r,
        growth_rate=g,
        fcf_projections=fcf_inputs,
        market_price=current_price,
        shares_outstanding=shares,
        metadata={
            "company_name": company_name,
            "mode": mode,
            "base_fcf": base_fcf,
            "growth_rates": growth_rate_inputs,
            "enhanced_model": use_enhanced_model,
            "cash": cash if use_enhanced_model else None,
            "debt": total_debt if use_enhanced_model else None,
        },
    )

    # Results
    if use_enhanced_model:
        # Show Enhanced Model results with Equity Value
        col1, col2, col3, col4, col5 = st.columns(5)
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
            st.metric(
                "Equity Value",
                (
                    f"${equity_value/1e9:.2f}B"
                    if equity_value > 1e9
                    else f"${equity_value/1e6:.2f}M"
                ),
                help="EV + Cash - Debt",
            )
        with col3:
            if fair_value_per_share > 0:
                st.metric("Fair Value / Acción", f"${fair_value_per_share:.2f}")
            else:
                st.info("Añade shares outstanding")
        with col4:
            st.metric("Precio Mercado", f"${current_price:.2f}")
        with col5:
            if fair_value_per_share > 0:
                upside = ((fair_value_per_share - current_price) / current_price) * 100
                st.metric(
                    "Upside/Downside",
                    f"{upside:+.1f}%",
                    delta=f"${fair_value_per_share - current_price:.2f}",
                    delta_color="normal" if upside > 0 else "inverse",
                )

        # Show balance sheet adjustments
        st.markdown("##### Ajustes de Balance")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "💰 Cash", f"${cash/1e9:.2f}B" if cash > 1e9 else f"${cash/1e6:.2f}M"
            )
        with col2:
            st.metric(
                "🏦 Deuda Total",
                (
                    f"${total_debt/1e9:.2f}B"
                    if total_debt > 1e9
                    else f"${total_debt/1e6:.2f}M"
                ),
            )
        with col3:
            net_cash = cash - total_debt
            st.metric(
                "Net Cash/(Debt)",
                (
                    f"${abs(net_cash)/1e9:.2f}B"
                    if abs(net_cash) > 1e9
                    else f"${abs(net_cash)/1e6:.2f}M"
                ),
                delta="Positivo" if net_cash > 0 else "Negativo",
                delta_color="normal" if net_cash > 0 else "inverse",
            )

    else:
        # Show Original Model results
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
    for i, (cf, dcf_c, gr) in enumerate(
        zip(fcf_inputs, discounted, growth_rate_inputs), start=1
    ):
        rows.append(
            {
                "Año": i,
                "Crecimiento": gr * 100,  # Show as percentage
                "FCF Proyectado": cf,
                "Valor Presente": dcf_c,
                "% del Total": (dcf_c / fair_value_total) * 100,
            }
        )
    if terminal != 0:
        rows.append(
            {
                "Año": "Terminal",
                "Crecimiento": g * 100,
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
                    "Crecimiento": "{:+.2f}%",
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
