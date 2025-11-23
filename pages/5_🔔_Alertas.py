"""Alert Management Page - Watchlist and Notifications."""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

from src.cache import DCFCache
from src.alerts import AlertSystem, AlertType, AlertStatus, AlertCondition

st.set_page_config(
    page_title="Alerts - DCF",
    page_icon="🔔",
    layout="wide"
)

st.title("🔔 Alert System")
st.markdown("Configure alerts to receive notifications when your conditions are met.")


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
# SECTION 1: ACTIVE NOTIFICATIONS
# ============================================================================

st.subheader("🔥 Triggered Alerts")

triggered_alerts = alert_system.get_all_alerts(AlertStatus.TRIGGERED)

if triggered_alerts:
    for alert in triggered_alerts:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.warning(f"""
                **🔔 {alert.ticker}** - {alert.message}

                **Target Value:** ${alert.target_value:.2f} | **Current Value:** ${alert.current_value:.2f}

                Triggered: {alert.triggered_at.strftime('%Y-%m-%d %H:%M')}
                """)

            with col2:
                if st.button(f"✅ Mark as viewed", key=f"dismiss_{alert.id}"):
                    alert_system.dismiss_alert(alert.id)
                    st.rerun()

            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{alert.id}"):
                    alert_system.delete_alert(alert.id)
                    st.rerun()

        st.markdown("---")
else:
    st.info("📭 No triggered alerts. All quiet!")

st.markdown("---")

# ============================================================================
# SECTION 2: CREATE NEW ALERT
# ============================================================================

st.subheader("➕ Create New Alert")

col_form1, col_form2 = st.columns(2)

with col_form1:
    st.markdown("### 🎯 Alert Configuration")

    # Get available tickers from cache
    available_tickers = cache.get_all_tickers()

    if not available_tickers:
        st.warning("⚠️ No analyzed companies. Go to **Individual Analysis** to calculate at least one company first.")
        ticker_input = st.text_input("Or enter a ticker manually:", "AAPL").upper()
    else:
        ticker_option = st.radio(
            "Select company:",
            ["From list", "Enter manually"]
        )

        if ticker_option == "From list":
            ticker_input = st.selectbox("Ticker:", available_tickers)
        else:
            ticker_input = st.text_input("Ticker:", "AAPL").upper()

    # Alert type selection
    alert_type_option = st.selectbox(
        "Alert Type:",
        [
            "🎯 Target Price",
            "📈 Significant Upside Change",
            "💰 Price Reaches Value"
        ]
    )

with col_form2:
    st.markdown("### ⚙️ Parameters")

    if "Precio Objetivo" in alert_type_option:
        # Get current price
        try:
            stock = yf.Ticker(ticker_input)
            current_price = stock.info.get('currentPrice', 0)
            if current_price == 0:
                current_price = stock.info.get('regularMarketPrice', 0)

            st.metric("Current Price", f"${current_price:.2f}")
        except:
            current_price = 0
            st.info("Could not retrieve current price")

        target_price = st.number_input(
            "Target Price ($):",
            min_value=0.01,
            value=float(current_price * 1.1) if current_price > 0 else 100.0,
            step=1.0,
            help="The price you want to monitor"
        )

        condition = st.radio(
            "Alert when price is:",
            ["Above target", "Below target"]
        )

        alert_condition = AlertCondition.ABOVE if "Above" in condition else AlertCondition.BELOW

    elif "Significant" in alert_type_option:
        threshold = st.slider(
            "Minimum change to alert (%):",
            min_value=5.0,
            max_value=50.0,
            value=10.0,
            step=5.0,
            help="We will alert you when upside changes more than this percentage"
        )

        target_price = 0  # Will be set when checking
        alert_condition = AlertCondition.CHANGE_ABOVE

    else:  # Price Reaches Value
        target_price = st.number_input(
            "Value to Monitor ($):",
            min_value=0.01,
            value=100.0,
            step=1.0
        )

        alert_condition = AlertCondition.EQUALS

# Create button
if st.button("✅ Create Alert", type="primary", use_container_width=True):
    if ticker_input:
        try:
            if "Target Price" in alert_type_option:
                alert = alert_system.create_target_price_alert(
                    ticker=ticker_input,
                    target_price=target_price,
                    above=(alert_condition == AlertCondition.ABOVE)
                )
            elif "Significant" in alert_type_option:
                alert = alert_system.create_upside_change_alert(
                    ticker=ticker_input,
                    threshold=threshold
                )
            else:
                message = f"{ticker_input} reached ${target_price:.2f}"
                alert = alert_system.create_alert(
                    ticker=ticker_input,
                    alert_type=AlertType.TARGET_PRICE,
                    condition=alert_condition,
                    target_value=target_price,
                    message=message
                )

            st.success(f"✅ Alert created for {ticker_input}!")
            st.balloons()
            st.rerun()

        except Exception as e:
            st.error(f"Error creating alert: {e}")
    else:
        st.error("Please enter a valid ticker")

st.markdown("---")

# ============================================================================
# SECTION 3: ACTIVE ALERTS (WATCHLIST)
# ============================================================================

st.subheader("👁️ Watchlist - Active Alerts")

active_alerts = alert_system.get_all_alerts(AlertStatus.ACTIVE)

if active_alerts:
    # Stats
    col_stat1, col_stat2, col_stat3 = st.columns(3)

    with col_stat1:
        st.metric("Active Alerts", len(active_alerts))

    with col_stat2:
        unique_tickers = len(set(alert.ticker for alert in active_alerts))
        st.metric("Monitored Companies", unique_tickers)

    with col_stat3:
        target_price_alerts = len([a for a in active_alerts if a.alert_type == AlertType.TARGET_PRICE])
        st.metric("Price Alerts", target_price_alerts)

    st.markdown("---")

    # Table of active alerts
    alert_data = []
    for alert in active_alerts:
        alert_data.append({
            "Ticker": alert.ticker,
            "Type": "🎯 Price" if alert.alert_type == AlertType.TARGET_PRICE else "📈 Upside",
            "Condition": "Above" if alert.condition == AlertCondition.ABOVE else "Below",
            "Target Value": f"${alert.target_value:.2f}",
            "Created": alert.created_at.strftime('%Y-%m-%d %H:%M'),
            "ID": alert.id
        })

    df_alerts = pd.DataFrame(alert_data)

    # Display with actions
    for idx, row in df_alerts.iterrows():
        with st.container():
            col_info, col_actions = st.columns([4, 1])

            with col_info:
                st.markdown(f"""
                **{row['Ticker']}** - {row['Type']} | {row['Condition']} {row['Target Value']}

                Created: {row['Created']}
                """)

            with col_actions:
                if st.button("🗑️ Delete", key=f"del_active_{row['ID']}"):
                    alert_system.delete_alert(row['ID'])
                    st.rerun()

            st.markdown("---")

    # Export button
    st.markdown("### 📥 Export Alerts")
    csv_data = alert_system.export_to_csv()

    st.download_button(
        label="📥 Download CSV",
        data=csv_data,
        file_name=f"dcf_alerts_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )

else:
    st.info("📋 No active alerts. Create an alert above to start monitoring.")

st.markdown("---")

# ============================================================================
# SECTION 4: MANUALLY VERIFY ALERTS
# ============================================================================

with st.expander("🔍 Manually Verify Alerts"):
    st.markdown("""
    This function verifies all active alerts with current market prices.

    **Note:** Alerts are automatically verified when you calculate a DCF analysis.
    """)

    if st.button("🔄 Verify All Alerts Now"):
        with st.spinner("Verifying alerts..."):
            active_to_check = alert_system.get_all_alerts(AlertStatus.ACTIVE)

            if not active_to_check:
                st.info("No active alerts to verify")
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
                        st.warning(f"Error verifying {alert.ticker}: {e}")

                if all_triggered:
                    st.success(f"✅ {len(all_triggered)} alerts triggered!")
                    st.rerun()
                else:
                    st.info("✅ All alerts verified. None triggered.")

st.markdown("---")

# ============================================================================
# SECTION 5: HISTORY
# ============================================================================

with st.expander("📜 Alert History"):
    dismissed_alerts = alert_system.get_all_alerts(AlertStatus.DISMISSED)

    if dismissed_alerts:
        st.markdown(f"**Total:** {len(dismissed_alerts)} viewed alerts")

        for alert in dismissed_alerts[:10]:  # Show last 10
            st.text(f"{alert.ticker} - {alert.message} (Created: {alert.created_at.strftime('%Y-%m-%d')})")

        if len(dismissed_alerts) > 10:
            st.caption(f"Showing the last 10 of {len(dismissed_alerts)} alerts")
    else:
        st.info("No alert history")

# ============================================================================
# LEYENDA
# ============================================================================

with st.expander("📖 Help and Tips"):
    st.markdown("""
    ### Alert Types

    - **🎯 Target Price**: Alerts you when market price reaches your target
    - **📈 Significant Change**: Alerts you when upside changes more than X%
    - **💰 Price Reaches Value**: Alerts you when price reaches exactly a value

    ### How They Work

    1. **Create an alert** with your parameters
    2. **Automatic**: Alerts are verified when you calculate a DCF
    3. **Manual**: Use the "Verify All Alerts" button for immediate check
    4. **Notification**: Triggered alerts appear at the top in red

    ### Best Practices

    - ✅ Use price alerts for entry/exit strategies
    - ✅ Use upside change alerts to detect opportunities
    - ✅ Review triggered alerts regularly
    - ✅ Delete old or irrelevant alerts

    ### Export Data

    You can export all your alerts to CSV for analysis in Excel.
    """)
