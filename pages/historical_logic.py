"""
Lógica de datos históricos para Flask
"""

import yfinance as yf
import plotly.graph_objects as go
from pages.analysis_logic import perform_dcf_analysis


def get_historical_data(ticker: str):
    """
    Obtiene datos históricos de precio vs fair value.

    Args:
        ticker: Símbolo de la empresa

    Returns:
        dict: Diccionario con gráfico histórico
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period='1y')

        # Calcular fair value actual
        result = perform_dcf_analysis(ticker)
        fair_value = result['fair_value']

        # Crear gráfico
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
            title=f'{ticker} - Market Price vs Fair Value (Last 12 Months)',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            template='plotly_white',
            font=dict(family='Roboto'),
            height=500,
            hovermode='x unified',
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01
            )
        )

        return {
            'ticker': ticker,
            'fig': fig.to_html(include_plotlyjs=False, div_id='historical-chart')
        }
    except Exception as e:
        return {
            'ticker': ticker,
            'error': f'Error al obtener datos históricos: {str(e)}'
        }
