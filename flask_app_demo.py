"""
Plataforma DCF - Aplicación Flask (Versión Demo)
Versión simplificada para demostración sin dependencias complejas
"""

from flask import Flask, render_template, request, jsonify
import os

# Inicializar Flask
app = Flask(__name__,
            template_folder='templates',
            static_folder='assets')

# Configuración
app.config['SECRET_KEY'] = 'dcf-platform-secret-key-2024'


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

        # Datos de demo (en producción usaría perform_dcf_analysis)
        result = {
            'ticker': ticker,
            'company_name': f'{ticker} Inc.',
            'current_price': 150.00,
            'fair_value': 175.50,
            'upside_downside': 17.00,
            'market_cap': 2500000000,
            'enterprise_value': 2800000000,
            'equity_value': 2700000000,
            'cash': 100000000,
            'debt': 200000000,
            'shares_outstanding': 15000000,
            'wacc': wacc,
            'terminal_growth': terminal_growth,
            'last_fcf': 250000000,
            'projected_fcf': [295000000, 348250000, 411735000, 486399300, 574991874],
            'growth_rates': [0.18, 0.15, 0.12, 0.10, 0.08],
            'fig_fcf': '<div>Gráfico de FCF (requiere Plotly)</div>',
            'fig_waterfall': '<div>Gráfico Waterfall (requiere Plotly)</div>',
            'fig_sensitivity': '<div>Análisis de Sensibilidad (requiere Plotly)</div>',
        }

    return render_template('analisis.html',
                         page_title='Análisis DCF',
                         current_page='analisis',
                         result=result,
                         error=error)


@app.route('/dashboard')
def dashboard():
    """Dashboard ejecutivo con resumen de empresas analizadas."""
    # Datos de demo
    cached_companies = [
        {'ticker': 'AAPL', 'company_name': 'Apple Inc.', 'current_price': 180.00, 'fair_value': 195.00, 'upside': 8.33, 'date': '2024-11-29'},
        {'ticker': 'MSFT', 'company_name': 'Microsoft Corporation', 'current_price': 370.00, 'fair_value': 410.00, 'upside': 10.81, 'date': '2024-11-29'},
        {'ticker': 'GOOGL', 'company_name': 'Alphabet Inc.', 'current_price': 140.00, 'fair_value': 165.00, 'upside': 17.86, 'date': '2024-11-29'},
    ]

    stats = {
        'total_companies': len(cached_companies),
        'avg_upside': sum(c.get('upside', 0) for c in cached_companies) / max(len(cached_companies), 1),
        'total_alerts': 2,
        'last_update': '2024-11-29 11:45:00'
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

        # Datos de demo
        comparison_data = [
            {'ticker': t, 'company_name': f'{t} Inc.', 'current_price': 150.00 + i*50,
             'fair_value': 175.00 + i*60, 'upside_downside': 16.67 - i*2, 'market_cap': 2500000000 + i*500000000}
            for i, t in enumerate(tickers[:5])
        ]

    return render_template('comparador.html',
                         page_title='Comparador',
                         current_page='comparador',
                         comparison_data=comparison_data)


@app.route('/historico')
def historico():
    """Evolución histórica de valuaciones."""
    ticker = request.args.get('ticker', 'AAPL')

    # Datos de demo
    historical_data = {
        'ticker': ticker,
        'fig': '<div style="padding: 2rem; text-align: center; background: #f5f5f5; border-radius: 8px;">Gráfico histórico disponible con Plotly instalado</div>'
    }

    return render_template('historico.html',
                         page_title='Histórico',
                         current_page='historico',
                         ticker=ticker,
                         historical_data=historical_data)


@app.route('/alertas', methods=['GET', 'POST'])
def alertas():
    """Sistema de alertas y notificaciones."""
    if request.method == 'POST':
        # Procesar formulario (demo)
        pass

    # Datos de demo
    active_alerts = [
        {'id': 1, 'ticker': 'AAPL', 'target_price': 200.00, 'created_at': '2024-11-28'},
        {'id': 2, 'ticker': 'MSFT', 'target_price': 400.00, 'created_at': '2024-11-27'},
    ]

    triggered_alerts = [
        {'ticker': 'GOOGL', 'target_price': 140.00, 'current_price': 142.50, 'triggered_at': '2024-11-29'},
    ]

    return render_template('alertas.html',
                         page_title='Alertas',
                         current_page='alertas',
                         active_alerts=active_alerts,
                         triggered_alerts=triggered_alerts)


@app.errorhandler(404)
def page_not_found(e):
    """Página de error 404."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Página de error 500."""
    return render_template('500.html'), 500


if __name__ == '__main__':
    # Ejecutar aplicación
    print("=" * 60)
    print("🚀 DCF Platform - Flask Application")
    print("=" * 60)
    print("✓ Streamlit eliminado completamente")
    print("✓ Menú navbar funcional")
    print("✓ Logo de Santander en página principal")
    print("✓ Mensaje: 'Bienvenidos, amigos del Banco Santander'")
    print("=" * 60)
    print("📍 Servidor corriendo en: http://localhost:8501")
    print("=" * 60)
    print("\nNavegación disponible:")
    print("  • Home:       http://localhost:8501/")
    print("  • Análisis:   http://localhost:8501/analisis")
    print("  • Dashboard:  http://localhost:8501/dashboard")
    print("  • Comparador: http://localhost:8501/comparador")
    print("  • Histórico:  http://localhost:8501/historico")
    print("  • Alertas:    http://localhost:8501/alertas")
    print("=" * 60)

    app.run(host='0.0.0.0', port=8501, debug=True)
