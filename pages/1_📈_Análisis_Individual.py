"""Individual company DCF analysis with Fair Value vs Market Price comparison."""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date, timedelta, datetime

from src.dcf.model import dcf_value
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
from src.dcf.sensitivity_analysis import SensitivityAnalyzer
from src.dcf.projections import (
    predict_growth_rate_linear_regression,
    apply_growth_rates_to_base,
)
from src.cache import DCFCache
from src.data_providers.aggregator import get_data_aggregator
from src.companies import get_sp500_companies, get_all_sectors
from src.companies.fcf_scanner import get_fcf_scanner
from src.utils.data_fetcher import (
    get_shares_outstanding,
    get_balance_sheet_data as get_balance_data_robust,
    validate_dcf_inputs,
)
from src.core.intelligent_selector import IntelligentDataSelector


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


@st.cache_resource
def get_intelligent_selector():
    """Get cached intelligent data selector."""
    aggregator = get_data_aggregator()
    cache = get_cache()
    return IntelligentDataSelector(data_aggregator=aggregator, cache_manager=cache)


cache = get_cache()
aggregator = get_data_aggregator()
fcf_scanner = get_fcf_scanner()
intelligent_selector = get_intelligent_selector()


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

# ✅ INTELLIGENT MODE: System automatically selects best options
# No need for user to choose Manual/Autocompletar/Multi-fuente
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Configuración Inteligente")
st.sidebar.info(
    """
**El sistema selecciona automáticamente:**
- ✅ Mejor fuente de datos disponible
- ✅ Método óptimo de cálculo
- ✅ WACC dinámico con CAPM
- ✅ Terminal growth por empresa
- ✅ Normalización si es necesaria

*Sin configuración manual requerida.*
"""
)

# Advanced options (collapsed by default)
with st.sidebar.expander("⚙️ Opciones Avanzadas (opcional)"):
    st.caption("El sistema usa valores óptimos por defecto")

    # WACC calculation method
    st.markdown("**Método de cálculo WACC:**")
    wacc_method = st.radio(
        "Selecciona el método",
        ["company_specific", "industry_damodaran", "custom"],
        format_func=lambda x: {
            "company_specific": "🔬 Calculado (CAPM + estructura capital real)",
            "industry_damodaran": "🏭 Promedio industria (Damodaran)",
            "custom": "✏️ Personalizado (manual)",
        }[x],
        help=(
            "• **Calculado**: Usa beta, deuda y equity de la empresa específica\n"
            "• **Industria Damodaran**: Usa WACC promedio del sector según Damodaran\n"
            "• **Personalizado**: Ingresa tu propio WACC"
        ),
    )

    custom_wacc = None
    if wacc_method == "custom":
        custom_wacc = st.number_input(
            "WACC personalizado",
            min_value=0.01,
            max_value=0.30,
            value=0.08,
            step=0.01,
            format="%.2f",
        )

    # Allow override of terminal growth
    use_custom_g = st.checkbox("Personalizar terminal growth", value=False)
    custom_g = None
    if use_custom_g:
        custom_g = st.number_input(
            "Terminal growth personalizado",
            min_value=0.01,
            max_value=0.10,
            value=0.035,
            step=0.005,
            format="%.3f",
        )

# Set intelligent defaults (always use best model)
use_enhanced_model = True
use_dynamic_wacc = True if wacc_method != "custom" else False
use_industry_wacc = True if wacc_method == "industry_damodaran" else False
normalize_fcf = None  # Let intelligent selector decide
normalization_method = None  # Let intelligent selector decide

years = st.sidebar.number_input(
    "Años de proyección", min_value=1, max_value=20, value=5
)

# Handle WACC based on selected method
if wacc_method == "custom":
    r = custom_wacc
else:
    r = None  # Will be calculated dynamically

# Terminal growth
if use_custom_g:
    g = custom_g
else:
    g = 0.035  # Default, will be overridden by intelligent calculation

# Store shares input in session state to persist user changes
if "shares_input" not in st.session_state:
    st.session_state.shares_input = 0

shares_input = st.sidebar.number_input(
    "Shares outstanding",
    min_value=0,
    value=st.session_state.shares_input,
    help="Dejar en 0 para autocompletar (diluted shares). Puedes ingresar el valor manualmente.",
    key="shares_input_widget",
)

# Update session state when user changes value
if shares_input != st.session_state.shares_input:
    st.session_state.shares_input = shares_input


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

# Get shares outstanding with robust fallback
shares, shares_source = get_shares_outstanding(ticker, shares_input)

# Get balance sheet data (cash, debt) with robust fallback
cash, total_debt, balance_sources = get_balance_data_robust(ticker)

# Header with company info
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(f"{company_name} ({ticker})")
with col2:
    st.metric("Precio Actual", f"${current_price:.2f}")
with col3:
    if shares > 0:
        st.metric(
            "Shares",
            f"{shares/1e9:.2f}B" if shares > 1e9 else f"{shares/1e6:.2f}M",
            help=f"Fuente: {shares_source}",
        )
    else:
        st.error("⚠️ No shares data")

# Show data sources in an expander
with st.expander("📊 Ver fuentes de datos"):
    st.markdown("**Shares Outstanding:**")
    st.caption(f"✓ {shares_source}")
    if shares > 0:
        st.caption(f"  Valor: {shares:,}")

    st.markdown("**Balance Sheet:**")
    st.caption(f"✓ Cash: {balance_sources['cash']}")
    st.caption(
        f"  Valor: ${cash/1e9:.2f}B" if cash > 1e9 else f"  Valor: ${cash/1e6:.2f}M"
    )
    st.caption(f"✓ Debt: {balance_sources['debt']}")
    st.caption(
        f"  Valor: ${total_debt/1e9:.2f}B"
        if total_debt > 1e9
        else f"  Valor: ${total_debt/1e6:.2f}M"
    )


# FCF Input Section
st.markdown("---")
st.subheader("📊 Proyecciones de Free Cash Flow")

# ✅ INTELLIGENT FCF FETCH: System automatically selects best source
with st.spinner("🤖 Seleccionando mejor fuente de datos disponible..."):
    base_fcf, historical_fcf, fcf_quality = intelligent_selector.get_best_fcf_data(
        ticker, years
    )

# Show data quality badge and source
quality_badge = intelligent_selector.get_quality_badge(fcf_quality)
quality_explanation = intelligent_selector.get_explanation(fcf_quality)

col_quality, col_fcf = st.columns([1, 2])
with col_quality:
    st.metric(
        "Calidad de Datos",
        quality_badge,
        help="Indicador de confianza de los datos obtenidos",
    )

with col_fcf:
    if base_fcf > 0:
        fcf_display = (
            f"${base_fcf/1e9:.2f}B"
            if base_fcf > 1e9
            else f"${base_fcf/1e6:.2f}M" if base_fcf > 1e6 else f"${base_fcf:,.0f}"
        )
        st.metric("FCF Base", fcf_display, help=f"Fuente: {fcf_quality.source}")
    else:
        st.error("No se pudo obtener FCF")

# Show detailed quality info in expander
with st.expander("🔍 Ver detalles de calidad de datos"):
    st.markdown(quality_explanation)

# Calculate growth rates intelligently
autofill_growth_rates = []
if historical_fcf and len(historical_fcf) >= 2:
    autofill_growth_rates = predict_growth_rate_linear_regression(
        list(reversed(historical_fcf)), years
    )

# Decide if normalization is needed
if normalize_fcf is None and historical_fcf:
    normalize_fcf = intelligent_selector.should_normalize_fcf(historical_fcf)

# Decide best normalization method
if normalize_fcf and normalization_method is None:
    normalization_method = intelligent_selector.get_best_normalization_method(
        historical_fcf
    )

data_source_used = fcf_quality.source

# Display base FCF information
if base_fcf > 0:
    fcf_display = (
        f"${base_fcf/1e9:.2f}B"
        if base_fcf > 1e9
        else (f"${base_fcf/1e6:.2f}M" if base_fcf > 1e6 else f"${base_fcf:,.0f}")
    )

    # Show historical FCF if available
    if historical_fcf and len(historical_fcf) > 1:
        hist_display = " | ".join(
            [
                f"${f/1e9:.1f}B" if f > 1e9 else f"${f/1e6:.1f}M"
                for f in historical_fcf[:4]
            ]
        )
        st.info(
            f"📊 **FCF Base**: {fcf_display} | **Histórico** (últimos años): {hist_display}"
        )

        # Show normalization info if enabled
        if normalize_fcf and normalization_method != "current":
            from src.dcf.enhanced_model import EnhancedDCFModel

            temp_model = EnhancedDCFModel()
            normalized_fcf = temp_model.normalize_base_fcf(
                historical_fcf, method=normalization_method
            )
            norm_display = (
                f"${normalized_fcf/1e9:.2f}B"
                if normalized_fcf > 1e9
                else f"${normalized_fcf/1e6:.2f}M"
            )
            diff_pct = ((normalized_fcf - base_fcf) / base_fcf) * 100
            st.success(
                f"🎯 **FCF Normalizado** ({normalization_method}): {norm_display} ({diff_pct:+.1f}% vs año actual)"
            )
    else:
        st.info(f"📊 **Año Base FCF**: {fcf_display}")

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


# Calculate projected FCF from growth rates
fcf_inputs = apply_growth_rates_to_base(base_fcf, growth_rate_inputs)

# DCF Calculation
st.markdown("---")
st.subheader("💰 Valoración DCF")

# Validate all inputs before proceeding
try:
    # Calculate dynamic WACC if enabled
    wacc_components = None
    terminal_growth_info = None
    if use_enhanced_model and use_dynamic_wacc:
        wacc_calc = WACCCalculator()
        wacc_components = wacc_calc.calculate_wacc(
            ticker,
            use_net_debt=True,
            adjust_for_growth=True,
            use_industry_wacc=use_industry_wacc,
        )
        r = wacc_components["wacc"]

        # Get company-specific terminal growth
        terminal_growth_info = wacc_calc.calculate_company_terminal_growth(
            ticker, use_company_specific=True
        )
        g_calculated = terminal_growth_info["terminal_growth"]

        # Use the higher of user input or calculated
        g = max(g, g_calculated)

        # Display WACC breakdown
        st.sidebar.markdown("---")

        # Show WACC method being used
        if wacc_method == "company_specific":
            st.sidebar.markdown("**🔬 WACC Calculado (CAPM)**")
        elif wacc_method == "industry_damodaran":
            st.sidebar.markdown("**🏭 WACC Industria (Damodaran)**")
        else:
            st.sidebar.markdown("**✏️ WACC Personalizado**")

        # Show industry info if available
        if wacc_components.get("using_industry_wacc"):
            st.sidebar.success(f"Industria: {wacc_components['industry']}")
            st.sidebar.metric(
                "WACC",
                f"{r:.2%}",
                help=f"WACC promedio del sector {wacc_components['industry']}",
            )
            st.sidebar.caption(f"• Beta Industria: {wacc_components['beta']:.2f}")
            st.sidebar.caption(
                f"• Cost of Equity: {wacc_components['cost_of_equity']:.2%}"
            )
            st.sidebar.caption(
                f"• E/V: {wacc_components['equity_weight']:.1%} | D/V: {wacc_components['debt_weight']:.1%}"
            )
        else:
            st.sidebar.metric(
                "WACC",
                f"{r:.2%}",
                help=f"Beta empresa: {wacc_components.get('beta', 'N/A')}",
            )

            if wacc_components.get("beta"):
                st.sidebar.caption(
                    f"• Cost of Equity: {wacc_components['cost_of_equity']:.2%}"
                )
                st.sidebar.caption(
                    f"• After-tax Cost of Debt: {wacc_components['after_tax_cost_of_debt']:.2%}"
                )
                st.sidebar.caption(
                    f"• E/V: {wacc_components['equity_weight']:.1%} | D/V: {wacc_components['debt_weight']:.1%}"
                )

                # Show industry WACC for comparison
                if wacc_components.get("industry_wacc"):
                    st.sidebar.info(
                        f"📊 Comparación - WACC Industria ({wacc_components['industry']}): {wacc_components['industry_wacc']:.2%}"
                    )

        # Show terminal growth calculation
        st.sidebar.markdown("---")
        st.sidebar.markdown("**📈 Terminal Growth (g)**")
        st.sidebar.metric("Terminal Growth", f"{g:.2%}")

        if (
            terminal_growth_info
            and terminal_growth_info.get("method") == "company_specific"
        ):
            with st.sidebar.expander("🔍 Ver cálculo detallado"):
                st.markdown(terminal_growth_info["justification"])

    # Comprehensive input validation
    is_valid, validation_errors = validate_dcf_inputs(
        base_fcf=base_fcf,
        wacc=r if r is not None else 0.08,
        terminal_growth=g,
        shares=shares,
        cash=cash,
        debt=total_debt,
    )

    if not is_valid:
        st.error("❌ Errores de validación detectados:")
        for error in validation_errors:
            st.warning(f"⚠️ {error}")

        # Show suggestions
        st.info(
            """
        **Sugerencias:**
        - Si el FCF es 0, prueba con modo 'Autocompletar' o 'Multi-fuente'
        - Si shares = 0, ingresa el número de acciones manualmente en el sidebar
        - Si WACC ≤ g, reduce el terminal growth o aumenta WACC
        - Verifica que los datos del ticker sean correctos
        """
        )
        st.stop()

    # Additional WACC validation
    if r is None or r <= g:
        st.error(
            f"⚠️ La tasa de descuento (r={r:.2%}) debe ser mayor que g ({g:.2%}). Ajusta los parámetros."
        )
        st.stop()

    if use_enhanced_model:
        # Use Enhanced DCF Model
        enhanced_model = EnhancedDCFModel(wacc=r, terminal_growth=g)

        # Check if user manually changed any growth rate
        user_modified_growth = False
        if len(growth_rate_inputs) == len(autofill_growth_rates):
            for i in range(len(growth_rate_inputs)):
                # Check if user input differs from autofill (with small tolerance for rounding)
                if abs(growth_rate_inputs[i] - autofill_growth_rates[i]) > 0.001:
                    user_modified_growth = True
                    break

        # Perform full DCF valuation
        dcf_result = enhanced_model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf if historical_fcf else [base_fcf],
            cash=cash,
            debt=total_debt,
            diluted_shares=shares,
            years=years,
            custom_growth_rates=(
                growth_rate_inputs if user_modified_growth else None
            ),  # Use custom if user changed
            normalize_base=normalize_fcf,
            normalization_method=normalization_method,
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
            "mode": "intelligent",  # New intelligent mode
            "base_fcf": base_fcf,
            "growth_rates": growth_rate_inputs,
            "enhanced_model": use_enhanced_model,
            "cash": cash if use_enhanced_model else None,
            "debt": total_debt if use_enhanced_model else None,
            "data_quality": fcf_quality.confidence,
        },
    )

    # === SENSITIVITY ANALYSIS SECTION ===
    st.markdown("---")
    st.subheader("📊 Análisis de Sensibilidad")

    # Run sensitivity analysis
    sensitivity_analyzer = SensitivityAnalyzer()

    with st.spinner("Calculando escenarios..."):
        scenarios = sensitivity_analyzer.calculate_scenarios(
            enhanced_model=(
                enhanced_model
                if use_enhanced_model
                else EnhancedDCFModel(wacc=r, terminal_growth=g)
            ),
            base_fcf=base_fcf,
            historical_fcf=historical_fcf if historical_fcf else [base_fcf],
            cash=cash,
            debt=total_debt,
            diluted_shares=shares,
            base_wacc=r,
            base_terminal_growth=g,
            years=years,
            normalize_base=normalize_fcf if normalize_fcf is not None else True,
            normalization_method=(
                normalization_method if normalization_method else "weighted_average"
            ),
        )

    # Display scenario results
    st.markdown("### 🎯 Escenarios de Valoración")

    col_pess, col_base, col_opt = st.columns(3)

    with col_pess:
        pess = scenarios["pessimistic"]
        pess_change = (
            (pess.fair_value_per_share - current_price) / current_price
        ) * 100
        st.metric(
            "🔴 Pesimista",
            f"${pess.fair_value_per_share:.2f}",
            delta=f"{pess_change:+.1f}%",
            help=f"WACC: {pess.wacc:.2%} | Terminal g: {pess.terminal_growth:.2%}",
        )
        st.caption(f"WACC: {pess.wacc:.2%}")
        st.caption(f"Terminal g: {pess.terminal_growth:.2%}")
        st.caption(f"Promedio crecimiento FCF: {np.mean(pess.growth_rates):.1%}")

    with col_base:
        base_scenario = scenarios["base"]
        base_change = (
            (base_scenario.fair_value_per_share - current_price) / current_price
        ) * 100
        st.metric(
            "🟡 Caso Base",
            f"${base_scenario.fair_value_per_share:.2f}",
            delta=f"{base_change:+.1f}%",
            help=f"WACC: {base_scenario.wacc:.2%} | Terminal g: {base_scenario.terminal_growth:.2%}",
        )
        st.caption(f"WACC: {base_scenario.wacc:.2%}")
        st.caption(f"Terminal g: {base_scenario.terminal_growth:.2%}")
        st.caption(
            f"Promedio crecimiento FCF: {np.mean(base_scenario.growth_rates):.1%}"
        )

    with col_opt:
        opt = scenarios["optimistic"]
        opt_change = ((opt.fair_value_per_share - current_price) / current_price) * 100
        st.metric(
            "🟢 Optimista",
            f"${opt.fair_value_per_share:.2f}",
            delta=f"{opt_change:+.1f}%",
            help=f"WACC: {opt.wacc:.2%} | Terminal g: {opt.terminal_growth:.2%}",
        )
        st.caption(f"WACC: {opt.wacc:.2%}")
        st.caption(f"Terminal g: {opt.terminal_growth:.2%}")
        st.caption(f"Promedio crecimiento FCF: {np.mean(opt.growth_rates):.1%}")

    # Calculate probability-weighted value
    prob_weighted = sensitivity_analyzer.calculate_probability_weighted_value(scenarios)
    min_val, median_val, max_val = sensitivity_analyzer.calculate_value_range(scenarios)

    st.markdown("---")
    st.markdown("### 📈 Resumen Estadístico")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Valor Esperado (Probabilístico)",
            f"${prob_weighted:.2f}",
            help="Ponderado: 25% pesimista, 50% base, 25% optimista",
        )

    with col2:
        range_pct = ((max_val - min_val) / median_val) * 100
        st.metric(
            "Rango de Valoración",
            f"${min_val:.2f} - ${max_val:.2f}",
            delta=f"±{range_pct/2:.1f}%",
            help="Rango entre escenario pesimista y optimista",
        )

    with col3:
        st.metric("Precio de Mercado", f"${current_price:.2f}")

    with col4:
        # Check if price is within range
        if current_price < min_val:
            status = "🟢 Subvaluada"
            status_delta = f"{((min_val - current_price) / current_price) * 100:.1f}%"
        elif current_price > max_val:
            status = "🔴 Sobrevaluada"
            status_delta = f"{((current_price - max_val) / current_price) * 100:.1f}%"
        else:
            status = "🟡 En rango"
            status_delta = "Dentro del rango"

        st.metric("Evaluación", status, delta=status_delta)

    # Visualization: Scenario comparison chart
    st.markdown("---")
    st.markdown("### 📊 Comparación Visual de Escenarios")

    fig_scenarios = go.Figure()

    # Add bars for each scenario
    scenario_names = ["Pesimista", "Base", "Optimista"]
    scenario_values = [
        scenarios["pessimistic"].fair_value_per_share,
        scenarios["base"].fair_value_per_share,
        scenarios["optimistic"].fair_value_per_share,
    ]
    scenario_colors = ["#ef5350", "#ffa726", "#66bb6a"]

    fig_scenarios.add_trace(
        go.Bar(
            x=scenario_names,
            y=scenario_values,
            marker_color=scenario_colors,
            text=[f"${v:.2f}" for v in scenario_values],
            textposition="outside",
            name="Fair Value",
        )
    )

    # Add current price line
    fig_scenarios.add_hline(
        y=current_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Precio Actual: ${current_price:.2f}",
        annotation_position="right",
    )

    # Add probability-weighted value line
    fig_scenarios.add_hline(
        y=prob_weighted,
        line_dash="dot",
        line_color="purple",
        annotation_text=f"Valor Esperado: ${prob_weighted:.2f}",
        annotation_position="left",
    )

    fig_scenarios.update_layout(
        title="Fair Value por Escenario vs Precio Actual",
        yaxis_title="Fair Value por Acción ($)",
        showlegend=False,
        height=450,
    )

    st.plotly_chart(fig_scenarios, use_container_width=True)

    # Detailed scenario breakdown in expander
    with st.expander("🔍 Ver detalles completos de cada escenario"):
        for scenario_key, scenario_name in [
            ("pessimistic", "Pesimista"),
            ("base", "Caso Base"),
            ("optimistic", "Optimista"),
        ]:
            sc = scenarios[scenario_key]
            st.markdown(f"**{scenario_name}**")

            cols = st.columns(4)
            cols[0].metric("Fair Value/Acción", f"${sc.fair_value_per_share:.2f}")
            cols[1].metric(
                "Enterprise Value",
                (
                    f"${sc.enterprise_value/1e9:.2f}B"
                    if sc.enterprise_value > 1e9
                    else f"${sc.enterprise_value/1e6:.2f}M"
                ),
            )
            cols[2].metric("WACC", f"{sc.wacc:.2%}")
            cols[3].metric("Terminal Growth", f"{sc.terminal_growth:.2%}")

            st.caption(
                f"Tasas de crecimiento FCF: {', '.join([f'{g:.1%}' for g in sc.growth_rates])}"
            )
            st.markdown("---")

    st.markdown("---")

    # Results
    if use_enhanced_model:
        # Show Enhanced Model results with Equity Value
        st.subheader("💰 Valoración DCF - Caso Base Detallado")

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
