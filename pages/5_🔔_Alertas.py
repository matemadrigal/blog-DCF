"""Alert Management Page - Watchlist and Notifications."""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

from src.cache import DCFCache
from src.alerts import AlertSystem, AlertType, AlertStatus, AlertCondition

st.set_page_config(
    page_title="Alertas - DCF",
    page_icon="🔔",
    layout="wide"
)

st.title("🔔 Sistema de Alertas")
st.markdown("Configura alertas para recibir notificaciones cuando se cumplan tus condiciones.")


# Initialize cache and alert system
@st.cache_resource
def get_cache():
    return DCFCache()


@st.cache_resource
def get_alert_system():
    cache = get_cache()
    return AlertSystem(cache)


cache = get_cache()
alert_system = get_alert_system()

# ============================================================================
# SECCIÓN 1: NOTIFICACIONES ACTIVAS
# ============================================================================

st.subheader("🔥 Alertas Disparadas")

triggered_alerts = alert_system.get_all_alerts(AlertStatus.TRIGGERED)

if triggered_alerts:
    for alert in triggered_alerts:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.warning(f"""
                **🔔 {alert.ticker}** - {alert.message}

                **Valor Objetivo:** ${alert.target_value:.2f} | **Valor Actual:** ${alert.current_value:.2f}

                Disparado: {alert.triggered_at.strftime('%Y-%m-%d %H:%M')}
                """)

            with col2:
                if st.button(f"✅ Marcar vista", key=f"dismiss_{alert.id}"):
                    alert_system.dismiss_alert(alert.id)
                    st.rerun()

            with col3:
                if st.button(f"🗑️ Eliminar", key=f"delete_{alert.id}"):
                    alert_system.delete_alert(alert.id)
                    st.rerun()

        st.markdown("---")
else:
    st.info("📭 No hay alertas disparadas. ¡Todo tranquilo!")

st.markdown("---")

# ============================================================================
# SECCIÓN 2: CREAR NUEVA ALERTA
# ============================================================================

st.subheader("➕ Crear Nueva Alerta")

col_form1, col_form2 = st.columns(2)

with col_form1:
    st.markdown("### 🎯 Configuración de Alerta")

    # Get available tickers from cache
    available_tickers = cache.get_all_tickers()

    if not available_tickers:
        st.warning("⚠️ No hay empresas analizadas. Ve a **Análisis Individual** para calcular al menos una empresa primero.")
        ticker_input = st.text_input("O ingresa un ticker manualmente:", "AAPL").upper()
    else:
        ticker_option = st.radio(
            "Seleccionar empresa:",
            ["De la lista", "Ingresar manualmente"]
        )

        if ticker_option == "De la lista":
            ticker_input = st.selectbox("Ticker:", available_tickers)
        else:
            ticker_input = st.text_input("Ticker:", "AAPL").upper()

    # Alert type selection
    alert_type_option = st.selectbox(
        "Tipo de Alerta:",
        [
            "🎯 Precio Objetivo (Target Price)",
            "📈 Cambio Significativo en Upside",
            "💰 Precio Alcanza Valor"
        ]
    )

with col_form2:
    st.markdown("### ⚙️ Parámetros")

    if "Precio Objetivo" in alert_type_option:
        # Get current price
        try:
            stock = yf.Ticker(ticker_input)
            current_price = stock.info.get('currentPrice', 0)
            if current_price == 0:
                current_price = stock.info.get('regularMarketPrice', 0)

            st.metric("Precio Actual", f"${current_price:.2f}")
        except:
            current_price = 0
            st.info("No se pudo obtener el precio actual")

        target_price = st.number_input(
            "Precio Objetivo ($):",
            min_value=0.01,
            value=float(current_price * 1.1) if current_price > 0 else 100.0,
            step=1.0,
            help="El precio que quieres monitorear"
        )

        condition = st.radio(
            "Alertar cuando el precio esté:",
            ["Por encima del objetivo", "Por debajo del objetivo"]
        )

        alert_condition = AlertCondition.ABOVE if "encima" in condition else AlertCondition.BELOW

    elif "Cambio Significativo" in alert_type_option:
        threshold = st.slider(
            "Cambio mínimo para alertar (%):",
            min_value=5.0,
            max_value=50.0,
            value=10.0,
            step=5.0,
            help="Te alertaremos cuando el upside cambie más de este porcentaje"
        )

        target_price = 0  # Will be set when checking
        alert_condition = AlertCondition.CHANGE_ABOVE

    else:  # Precio Alcanza Valor
        target_price = st.number_input(
            "Valor a Monitorear ($):",
            min_value=0.01,
            value=100.0,
            step=1.0
        )

        alert_condition = AlertCondition.EQUALS

# Create button
if st.button("✅ Crear Alerta", type="primary", use_container_width=True):
    if ticker_input:
        try:
            if "Precio Objetivo" in alert_type_option:
                alert = alert_system.create_target_price_alert(
                    ticker=ticker_input,
                    target_price=target_price,
                    above=(alert_condition == AlertCondition.ABOVE)
                )
            elif "Cambio Significativo" in alert_type_option:
                alert = alert_system.create_upside_change_alert(
                    ticker=ticker_input,
                    threshold=threshold
                )
            else:
                message = f"{ticker_input} alcanzó ${target_price:.2f}"
                alert = alert_system.create_alert(
                    ticker=ticker_input,
                    alert_type=AlertType.TARGET_PRICE,
                    condition=alert_condition,
                    target_value=target_price,
                    message=message
                )

            st.success(f"✅ Alerta creada para {ticker_input}!")
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error(f"Error al crear alerta: {e}")
    else:
        st.error("Por favor ingresa un ticker válido")

st.markdown("---")

# ============================================================================
# SECCIÓN 3: ALERTAS ACTIVAS (WATCHLIST)
# ============================================================================

st.subheader("👁️ Watchlist - Alertas Activas")

active_alerts = alert_system.get_all_alerts(AlertStatus.ACTIVE)

if active_alerts:
    # Stats
    col_stat1, col_stat2, col_stat3 = st.columns(3)

    with col_stat1:
        st.metric("Alertas Activas", len(active_alerts))

    with col_stat2:
        unique_tickers = len(set(alert.ticker for alert in active_alerts))
        st.metric("Empresas Monitoreadas", unique_tickers)

    with col_stat3:
        target_price_alerts = len([a for a in active_alerts if a.alert_type == AlertType.TARGET_PRICE])
        st.metric("Alertas de Precio", target_price_alerts)

    st.markdown("---")

    # Table of active alerts
    alert_data = []
    for alert in active_alerts:
        alert_data.append({
            "Ticker": alert.ticker,
            "Tipo": "🎯 Precio" if alert.alert_type == AlertType.TARGET_PRICE else "📈 Upside",
            "Condición": "Por encima" if alert.condition == AlertCondition.ABOVE else "Por debajo",
            "Valor Objetivo": f"${alert.target_value:.2f}",
            "Creado": alert.created_at.strftime('%Y-%m-%d %H:%M'),
            "ID": alert.id
        })

    df_alerts = pd.DataFrame(alert_data)

    # Display with actions
    for idx, row in df_alerts.iterrows():
        with st.container():
            col_info, col_actions = st.columns([4, 1])

            with col_info:
                st.markdown(f"""
                **{row['Ticker']}** - {row['Tipo']} | {row['Condición']} de {row['Valor Objetivo']}

                Creado: {row['Creado']}
                """)

            with col_actions:
                if st.button("🗑️ Eliminar", key=f"del_active_{row['ID']}"):
                    alert_system.delete_alert(row['ID'])
                    st.rerun()

            st.markdown("---")

    # Export button
    st.markdown("### 📥 Exportar Alertas")
    csv_data = alert_system.export_to_csv()

    st.download_button(
        label="📥 Descargar CSV",
        data=csv_data,
        file_name=f"alertas_dcf_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.info("📋 No hay alertas activas. Crea una alerta arriba para empezar a monitorear.")

st.markdown("---")

# ============================================================================
# SECCIÓN 4: VERIFICAR ALERTAS MANUALMENTE
# ============================================================================

with st.expander("🔍 Verificar Alertas Manualmente"):
    st.markdown("""
    Esta función verifica todas las alertas activas con los precios actuales del mercado.

    **Nota:** Las alertas se verifican automáticamente cuando calculas un análisis DCF.
    """)

    if st.button("🔄 Verificar Todas las Alertas Ahora"):
        with st.spinner("Verificando alertas..."):
            active_to_check = alert_system.get_all_alerts(AlertStatus.ACTIVE)

            if not active_to_check:
                st.info("No hay alertas activas para verificar")
            else:
                all_triggered = []

                for alert in active_to_check:
                    try:
                        # Get current price
                        stock = yf.Ticker(alert.ticker)
                        current_price = stock.info.get('currentPrice', 0)
                        if current_price == 0:
                            current_price = stock.info.get('regularMarketPrice', 0)

                        # Check if alert should trigger
                        triggered = alert_system.check_alerts(
                            ticker=alert.ticker,
                            current_price=current_price
                        )

                        all_triggered.extend(triggered)

                    except Exception as e:
                        st.warning(f"Error verificando {alert.ticker}: {e}")

                if all_triggered:
                    st.success(f"✅ {len(all_triggered)} alertas disparadas!")
                    st.rerun()
                else:
                    st.info("✅ Todas las alertas verificadas. Ninguna disparada.")

st.markdown("---")

# ============================================================================
# SECCIÓN 5: HISTORIAL
# ============================================================================

with st.expander("📜 Historial de Alertas"):
    dismissed_alerts = alert_system.get_all_alerts(AlertStatus.DISMISSED)

    if dismissed_alerts:
        st.markdown(f"**Total:** {len(dismissed_alerts)} alertas vistas")

        for alert in dismissed_alerts[:10]:  # Show last 10
            st.text(f"{alert.ticker} - {alert.message} (Creado: {alert.created_at.strftime('%Y-%m-%d')})")

        if len(dismissed_alerts) > 10:
            st.caption(f"Mostrando las últimas 10 de {len(dismissed_alerts)} alertas")
    else:
        st.info("No hay historial de alertas")

# ============================================================================
# LEYENDA
# ============================================================================

with st.expander("📖 Ayuda y Consejos"):
    st.markdown("""
    ### Tipos de Alertas

    - **🎯 Precio Objetivo**: Te alerta cuando el precio de mercado alcanza tu objetivo
    - **📈 Cambio Significativo**: Te alerta cuando el upside cambia más de X%
    - **💰 Precio Alcanza Valor**: Te alerta cuando el precio llega exactamente a un valor

    ### Cómo Funcionan

    1. **Crea una alerta** con tus parámetros
    2. **Automático**: Las alertas se verifican cuando calculas un DCF
    3. **Manual**: Usa el botón "Verificar Todas las Alertas" para check inmediato
    4. **Notificación**: Las alertas disparadas aparecen arriba en rojo

    ### Mejores Prácticas

    - ✅ Usa alertas de precio para estrategias de entrada/salida
    - ✅ Usa alertas de cambio de upside para detectar oportunidades
    - ✅ Revisa alertas disparadas regularmente
    - ✅ Elimina alertas antiguas o irrelevantes

    ### Exportar Datos

    Puedes exportar todas tus alertas a CSV para análisis en Excel.
    """)
