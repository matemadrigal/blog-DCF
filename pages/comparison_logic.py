"""
Lógica de comparación de empresas para Flask
"""

from pages.analysis_logic import perform_dcf_analysis


def compare_companies(tickers: list):
    """
    Compara múltiples empresas.

    Args:
        tickers: Lista de tickers a comparar

    Returns:
        list: Lista de diccionarios con datos de cada empresa
    """
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
        except Exception as e:
            # Si falla una empresa, continúa con la siguiente
            print(f"Error al analizar {ticker}: {str(e)}")
            continue
    return results
