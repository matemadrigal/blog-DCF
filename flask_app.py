"""
Plataforma DCF - Aplicación Flask (sin Streamlit)
Aplicación completa de valoración DCF con menú funcional
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import os
import sys

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar módulos necesarios
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator
from src.data_providers.aggregator import DataAggregator
from src.cache.dcf_cache import DCFCache
from src.alerts.alert_manager import AlertManager
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

# Inicializar Flask
app = Flask(__name__,
            template_folder='templates',
            static_folder='assets')

# Configuración
app.config['SECRET_KEY'] = 'dcf-platform-secret-key-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Inicializar servicios globales
cache = DCFCache()
data_aggregator = DataAggregator()
alert_manager = AlertManager(cache)


@app.route('/')
def home():
    """Página principal con logo de Santander y mensaje de bienvenida."""
    return render_template('home.html',
                         page_title='DCF Platform - Santander',
                         current_page='home')


@app.route('/analisis', methods=['GET', 'POST'])
def analisis():
    """Página de análisis DCF individual."""
    result = None
    error = None

    if request.method == 'POST':
        ticker = request.form.get('ticker', '').upper().strip()
        wacc = float(request.form.get('wacc', 0.08))
        terminal_growth = float(request.form.get('terminal_growth', 0.035))
        years = int(request.form.get('years', 5))

        try:
            # Realizar análisis DCF
            from pages.analysis_logic import perform_dcf_analysis
            result = perform_dcf_analysis(ticker, wacc, terminal_growth, years)
        except Exception as e:
            error = str(e)

    return render_template('analisis.html',
                         page_title='Análisis DCF',
                         current_page='analisis',
                         result=result,
                         error=error)


@app.route('/dashboard')
def dashboard():
    """Dashboard ejecutivo con resumen de empresas analizadas."""
    # Obtener empresas del cache
    cached_companies = cache.get_all_cached_companies()

    # Calcular métricas agregadas
    total_companies = len(cached_companies)
    avg_upside = sum(c.get('upside', 0) for c in cached_companies) / max(total_companies, 1)
    total_alerts = len(alert_manager.get_active_alerts())

    stats = {
        'total_companies': total_companies,
        'avg_upside': avg_upside,
        'total_alerts': total_alerts,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    return render_template('dashboard.html',
                         page_title='Dashboard',
                         current_page='dashboard',
                         stats=stats,
                         companies=cached_companies)


@app.route('/comparador', methods=['GET', 'POST'])
def comparador():
    """Comparador de múltiples empresas."""
    comparison_data = None

    if request.method == 'POST':
        tickers = request.form.get('tickers', '').upper().split(',')
        tickers = [t.strip() for t in tickers if t.strip()]

        # Realizar comparación
        from pages.comparison_logic import compare_companies
        comparison_data = compare_companies(tickers)

    return render_template('comparador.html',
                         page_title='Comparador',
                         current_page='comparador',
                         comparison_data=comparison_data)


@app.route('/historico')
def historico():
    """Evolución histórica de valuaciones."""
    ticker = request.args.get('ticker', 'AAPL')

    # Obtener datos históricos
    from pages.historical_logic import get_historical_data
    historical_data = get_historical_data(ticker)

    return render_template('historico.html',
                         page_title='Histórico',
                         current_page='historico',
                         ticker=ticker,
                         historical_data=historical_data)


@app.route('/alertas', methods=['GET', 'POST'])
def alertas():
    """Sistema de alertas y notificaciones."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create':
            ticker = request.form.get('ticker', '').upper()
            target_price = float(request.form.get('target_price', 0))
            alert_manager.create_alert(ticker, target_price)
        elif action == 'dismiss':
            alert_id = request.form.get('alert_id')
            alert_manager.dismiss_alert(alert_id)

    active_alerts = alert_manager.get_active_alerts()
    triggered_alerts = alert_manager.get_triggered_alerts()

    return render_template('alertas.html',
                         page_title='Alertas',
                         current_page='alertas',
                         active_alerts=active_alerts,
                         triggered_alerts=triggered_alerts)


@app.route('/api/company/<ticker>')
def api_company_data(ticker):
    """API para obtener datos de una empresa."""
    try:
        ticker = ticker.upper()
        data = data_aggregator.get_company_data(ticker)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/dcf-calculate', methods=['POST'])
def api_dcf_calculate():
    """API para calcular DCF."""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        wacc = float(data.get('wacc', 0.08))
        terminal_growth = float(data.get('terminal_growth', 0.035))
        years = int(data.get('years', 5))

        # Realizar cálculo DCF
        from pages.analysis_logic import perform_dcf_analysis
        result = perform_dcf_analysis(ticker, wacc, terminal_growth, years)

        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.errorhandler(404)
def page_not_found(e):
    """Página de error 404."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Página de error 500."""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Crear directorios necesarios
    os.makedirs('templates', exist_ok=True)
    os.makedirs('assets', exist_ok=True)

    # Ejecutar aplicación
    app.run(host='0.0.0.0', port=8501, debug=True)
