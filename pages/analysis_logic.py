"""
Lógica de análisis DCF para Flask
Extraída y adaptada desde la página de Streamlit
"""

import yfinance as yf
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
from src.data_providers.aggregator import DataAggregator
from src.dcf.model import dcf_value
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json


def perform_dcf_analysis(ticker: str, wacc: float = 0.08, terminal_growth: float = 0.035, years: int = 5):
    """
    Realiza un análisis DCF completo de una empresa.

    Args:
        ticker: Símbolo de la empresa (ej: AAPL)
        wacc: WACC personalizado (por defecto 8%)
        terminal_growth: Tasa de crecimiento terminal (por defecto 3.5%)
        years: Años de proyección (por defecto 5)

    Returns:
        dict: Diccionario con resultados del análisis
    """
    # Inicializar servicios
    data_aggregator = DataAggregator()
    wacc_calculator = WACCCalculator()
    dcf_model = EnhancedDCFModel(wacc=wacc, terminal_growth=terminal_growth)

    # Obtener datos de la empresa
    stock = yf.Ticker(ticker)
    info = stock.info

    # Obtener datos financieros
    financials = stock.financials
    cash_flow = stock.cashflow
    balance_sheet = stock.balance_sheet

    # Extraer métricas clave
    try:
        # Precio actual
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))

        # Shares outstanding
        shares_outstanding = info.get('sharesOutstanding', 0)

        # Market cap
        market_cap = current_price * shares_outstanding

        # Obtener FCF histórico
        historical_fcf = []
        if 'Free Cash Flow' in cash_flow.index:
            historical_fcf = cash_flow.loc['Free Cash Flow'].dropna().tolist()
        elif 'Operating Cash Flow' in cash_flow.index and 'Capital Expenditure' in cash_flow.index:
            ocf = cash_flow.loc['Operating Cash Flow'].dropna()
            capex = cash_flow.loc['Capital Expenditure'].dropna()
            historical_fcf = (ocf + capex).tolist()  # CapEx es negativo

        # Último FCF
        last_fcf = historical_fcf[0] if historical_fcf else 0

        # Calcular tasas de crecimiento
        growth_rates = dcf_model.calculate_tiered_growth_rates(historical_fcf, years)

        # Proyectar FCF
        projected_fcf = []
        current_fcf = last_fcf
        for growth_rate in growth_rates:
            current_fcf = current_fcf * (1 + growth_rate)
            projected_fcf.append(current_fcf)

        # Calcular DCF value
        dcf_enterprise_value = dcf_value(
            cash_flows=projected_fcf,
            discount_rate=wacc,
            perpetuity_growth=terminal_growth,
            use_mid_year_convention=True
        )

        # Obtener Cash y Debt
        cash = 0
        debt = 0
        if not balance_sheet.empty:
            if 'Cash And Cash Equivalents' in balance_sheet.index:
                cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
            if 'Total Debt' in balance_sheet.index:
                debt = balance_sheet.loc['Total Debt'].iloc[0]

        # Calcular Equity Value
        equity_value = dcf_enterprise_value + cash - debt

        # Fair value por acción
        fair_value_per_share = equity_value / shares_outstanding if shares_outstanding > 0 else 0

        # Upside/Downside
        upside_downside = ((fair_value_per_share - current_price) / current_price * 100) if current_price > 0 else 0

        # Gráfico de proyección FCF
        fig_fcf = go.Figure()
        years_labels = [f'Year {i+1}' for i in range(years)]

        fig_fcf.add_trace(go.Bar(
            x=years_labels,
            y=projected_fcf,
            name='Projected FCF',
            marker_color='#9ED85C'
        ))

        fig_fcf.update_layout(
            title='Free Cash Flow Projection',
            xaxis_title='Year',
            yaxis_title='FCF ($)',
            template='plotly_white',
            font=dict(family='Roboto'),
            height=400
        )

        # Gráfico Waterfall
        terminal_value = projected_fcf[-1] * (1 + terminal_growth) / (wacc - terminal_growth)
        pv_fcf = sum([fcf / ((1 + wacc) ** (i + 0.5)) for i, fcf in enumerate(projected_fcf)])
        pv_tv = terminal_value / ((1 + wacc) ** (years - 0.5))

        fig_waterfall = go.Figure(go.Waterfall(
            name="DCF Components",
            orientation="v",
            x=['PV of FCF', 'PV of TV', 'Enterprise Value', 'Cash', 'Debt', 'Equity Value'],
            y=[pv_fcf, pv_tv, 0, cash, -debt, 0],
            measure=['relative', 'relative', 'total', 'relative', 'relative', 'total'],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            marker={"color": ["#9ED85C", "#9ED85C", "#7AB83A", "#B8E986", "#EC0000", "#7AB83A"]}
        ))

        fig_waterfall.update_layout(
            title='DCF Waterfall Chart',
            yaxis_title='Value ($)',
            template='plotly_white',
            font=dict(family='Roboto'),
            height=400
        )

        # Análisis de sensibilidad (WACC vs Terminal Growth)
        wacc_range = [wacc - 0.02, wacc - 0.01, wacc, wacc + 0.01, wacc + 0.02]
        growth_range = [terminal_growth - 0.01, terminal_growth - 0.005, terminal_growth,
                       terminal_growth + 0.005, terminal_growth + 0.01]

        sensitivity_matrix = []
        for g in growth_range:
            row = []
            for w in wacc_range:
                try:
                    val = dcf_value(projected_fcf, w, g, True)
                    equity_val = val + cash - debt
                    fair_val = equity_val / shares_outstanding if shares_outstanding > 0 else 0
                    row.append(fair_val)
                except:
                    row.append(0)
            sensitivity_matrix.append(row)

        fig_sensitivity = go.Figure(data=go.Heatmap(
            z=sensitivity_matrix,
            x=[f'{w:.1%}' for w in wacc_range],
            y=[f'{g:.1%}' for g in growth_range],
            colorscale='RdYlGn',
            text=[[f'${val:,.2f}' for val in row] for row in sensitivity_matrix],
            texttemplate='%{text}',
            textfont={"size": 10},
        ))

        fig_sensitivity.update_layout(
            title='Sensitivity Analysis: Fair Value per Share',
            xaxis_title='WACC',
            yaxis_title='Terminal Growth',
            template='plotly_white',
            font=dict(family='Roboto'),
            height=400
        )

        # Retornar resultados
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'current_price': current_price,
            'fair_value': fair_value_per_share,
            'upside_downside': upside_downside,
            'market_cap': market_cap,
            'enterprise_value': dcf_enterprise_value,
            'equity_value': equity_value,
            'cash': cash,
            'debt': debt,
            'shares_outstanding': shares_outstanding,
            'wacc': wacc,
            'terminal_growth': terminal_growth,
            'last_fcf': last_fcf,
            'projected_fcf': projected_fcf,
            'growth_rates': growth_rates,
            'fig_fcf': fig_fcf.to_html(include_plotlyjs=False, div_id='fcf-chart'),
            'fig_waterfall': fig_waterfall.to_html(include_plotlyjs=False, div_id='waterfall-chart'),
            'fig_sensitivity': fig_sensitivity.to_html(include_plotlyjs=False, div_id='sensitivity-chart'),
        }

    except Exception as e:
        raise Exception(f"Error en análisis DCF: {str(e)}")


def compare_companies(tickers: list):
    """Compara múltiples empresas."""
    results = []
    for ticker in tickers:
        try:
            result = perform_dcf_analysis(ticker)
            results.append({
                'ticker': ticker,
                'company_name': result['company_name'],
                'current_price': result['current_price'],
                'fair_value': result['fair_value'],
                'upside_downside': result['upside_downside'],
                'market_cap': result['market_cap']
            })
        except:
            continue
    return results


def get_historical_data(ticker: str):
    """Obtiene datos históricos de precio vs fair value."""
    stock = yf.Ticker(ticker)
    hist = stock.history(period='1y')

    # Simplificación: asumimos fair value constante (último cálculo)
    try:
        result = perform_dcf_analysis(ticker)
        fair_value = result['fair_value']

        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=hist.index,
            y=hist['Close'],
            name='Market Price',
            line=dict(color='#EC0000', width=2)
        ))

        fig.add_trace(go.Scatter(
            x=hist.index,
            y=[fair_value] * len(hist),
            name='Fair Value (DCF)',
            line=dict(color='#7AB83A', width=2, dash='dash')
        ))

        fig.update_layout(
            title=f'{ticker} - Market Price vs Fair Value',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_white',
            font=dict(family='Roboto'),
            height=500,
            hovermode='x unified'
        )

        return {
            'ticker': ticker,
            'fig': fig.to_html(include_plotlyjs=False, div_id='historical-chart')
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e)
        }
