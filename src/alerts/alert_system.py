"""Alert System for DCF Valuation Platform.

This module provides a comprehensive alert system to notify users about:
- Target price reached
- Significant price changes
- Upside/downside changes
- Watchlist monitoring
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any
import json


class AlertType(Enum):
    """Types of alerts."""
    TARGET_PRICE = "target_price"
    PRICE_CHANGE = "price_change"
    UPSIDE_CHANGE = "upside_change"
    WATCHLIST = "watchlist"
    CUSTOM = "custom"


class AlertStatus(Enum):
    """Status of alerts."""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class AlertCondition(Enum):
    """Alert condition operators."""
    ABOVE = "above"
    BELOW = "below"
    EQUALS = "equals"
    CHANGE_ABOVE = "change_above"
    CHANGE_BELOW = "change_below"


@dataclass
class Alert:
    """Represents a single alert."""
    id: str
    ticker: str
    alert_type: AlertType
    condition: AlertCondition
    target_value: float
    current_value: float
    status: AlertStatus
    created_at: datetime
    triggered_at: Optional[datetime] = None
    message: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Convert string enums to proper Enum types."""
        if isinstance(self.alert_type, str):
            self.alert_type = AlertType(self.alert_type)
        if isinstance(self.condition, str):
            self.condition = AlertCondition(self.condition)
        if isinstance(self.status, str):
            self.status = AlertStatus(self.status)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.triggered_at, str) and self.triggered_at:
            self.triggered_at = datetime.fromisoformat(self.triggered_at)
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary."""
        data = asdict(self)
        data['alert_type'] = self.alert_type.value
        data['condition'] = self.condition.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['triggered_at'] = self.triggered_at.isoformat() if self.triggered_at else None
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create alert from dictionary."""
        return cls(**data)

    def check_condition(self, current_value: float) -> bool:
        """Check if alert condition is met."""
        self.current_value = current_value

        if self.condition == AlertCondition.ABOVE:
            return current_value >= self.target_value
        elif self.condition == AlertCondition.BELOW:
            return current_value <= self.target_value
        elif self.condition == AlertCondition.EQUALS:
            return abs(current_value - self.target_value) < 0.01
        elif self.condition == AlertCondition.CHANGE_ABOVE:
            change = ((current_value - self.target_value) / self.target_value) * 100
            return change >= self.metadata.get('change_threshold', 10)
        elif self.condition == AlertCondition.CHANGE_BELOW:
            change = ((current_value - self.target_value) / self.target_value) * 100
            return change <= -self.metadata.get('change_threshold', 10)

        return False

    def trigger(self):
        """Mark alert as triggered."""
        self.status = AlertStatus.TRIGGERED
        self.triggered_at = datetime.now()

    def dismiss(self):
        """Dismiss the alert."""
        self.status = AlertStatus.DISMISSED


class AlertSystem:
    """Manages alerts for the DCF platform."""

    def __init__(self, cache_manager):
        """Initialize alert system.

        Args:
            cache_manager: DCFCache instance for persistence
        """
        self.cache = cache_manager
        self._ensure_alerts_table()

    def _ensure_alerts_table(self):
        """Ensure alerts table exists in database."""
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alerts (
                        id TEXT PRIMARY KEY,
                        ticker TEXT NOT NULL,
                        alert_type TEXT NOT NULL,
                        condition TEXT NOT NULL,
                        target_value REAL NOT NULL,
                        current_value REAL,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        triggered_at TEXT,
                        message TEXT,
                        metadata TEXT,
                        FOREIGN KEY (ticker) REFERENCES dcf_calculations (ticker)
                    )
                """)

                # Create index for faster queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_ticker ON alerts(ticker)
                """)
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status)
                """)
        except Exception as e:
            print(f"Error creating alerts table: {e}")

    def create_alert(
        self,
        ticker: str,
        alert_type: AlertType,
        condition: AlertCondition,
        target_value: float,
        message: str = "",
        metadata: Dict[str, Any] = None
    ) -> Alert:
        """Create a new alert.

        Args:
            ticker: Stock ticker symbol
            alert_type: Type of alert
            condition: Alert condition
            target_value: Target value to trigger alert
            message: Custom message
            metadata: Additional metadata

        Returns:
            Created Alert object
        """
        alert_id = f"{ticker}_{alert_type.value}_{datetime.now().timestamp()}"

        alert = Alert(
            id=alert_id,
            ticker=ticker.upper(),
            alert_type=alert_type,
            condition=condition,
            target_value=target_value,
            current_value=0.0,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            message=message,
            metadata=metadata or {}
        )

        self._save_alert(alert)
        return alert

    def _save_alert(self, alert: Alert):
        """Save alert to database."""
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alerts
                    (id, ticker, alert_type, condition, target_value, current_value,
                     status, created_at, triggered_at, message, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.id,
                    alert.ticker,
                    alert.alert_type.value,
                    alert.condition.value,
                    alert.target_value,
                    alert.current_value,
                    alert.status.value,
                    alert.created_at.isoformat(),
                    alert.triggered_at.isoformat() if alert.triggered_at else None,
                    alert.message,
                    json.dumps(alert.metadata)
                ))
        except Exception as e:
            print(f"Error saving alert: {e}")

    def get_all_alerts(self, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Get all alerts, optionally filtered by status.

        Args:
            status: Filter by alert status (optional)

        Returns:
            List of Alert objects
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()

                if status:
                    cursor.execute("""
                        SELECT * FROM alerts WHERE status = ? ORDER BY created_at DESC
                    """, (status.value,))
                else:
                    cursor.execute("""
                        SELECT * FROM alerts ORDER BY created_at DESC
                    """)

                rows = cursor.fetchall()
                alerts = []

                for row in rows:
                    alert_data = {
                        'id': row[0],
                        'ticker': row[1],
                        'alert_type': row[2],
                        'condition': row[3],
                        'target_value': row[4],
                        'current_value': row[5] or 0.0,
                        'status': row[6],
                        'created_at': row[7],
                        'triggered_at': row[8],
                        'message': row[9] or "",
                        'metadata': json.loads(row[10]) if row[10] else {}
                    }
                    alerts.append(Alert.from_dict(alert_data))

                return alerts
        except Exception as e:
            print(f"Error getting alerts: {e}")
            return []

    def get_alerts_by_ticker(self, ticker: str, status: Optional[AlertStatus] = None) -> List[Alert]:
        """Get alerts for a specific ticker.

        Args:
            ticker: Stock ticker symbol
            status: Filter by alert status (optional)

        Returns:
            List of Alert objects
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()

                if status:
                    cursor.execute("""
                        SELECT * FROM alerts
                        WHERE ticker = ? AND status = ?
                        ORDER BY created_at DESC
                    """, (ticker.upper(), status.value))
                else:
                    cursor.execute("""
                        SELECT * FROM alerts
                        WHERE ticker = ?
                        ORDER BY created_at DESC
                    """, (ticker.upper(),))

                rows = cursor.fetchall()
                alerts = []

                for row in rows:
                    alert_data = {
                        'id': row[0],
                        'ticker': row[1],
                        'alert_type': row[2],
                        'condition': row[3],
                        'target_value': row[4],
                        'current_value': row[5] or 0.0,
                        'status': row[6],
                        'created_at': row[7],
                        'triggered_at': row[8],
                        'message': row[9] or "",
                        'metadata': json.loads(row[10]) if row[10] else {}
                    }
                    alerts.append(Alert.from_dict(alert_data))

                return alerts
        
        except Exception as e:
            print(f"Error getting alerts for {ticker}: {e}")
            return []

    def check_alerts(self, ticker: str, current_price: float, current_upside: float = None) -> List[Alert]:
        """Check if any alerts should be triggered for a ticker.

        Args:
            ticker: Stock ticker symbol
            current_price: Current market price
            current_upside: Current upside percentage (optional)

        Returns:
            List of triggered alerts
        """
        active_alerts = self.get_alerts_by_ticker(ticker, AlertStatus.ACTIVE)
        triggered_alerts = []

        for alert in active_alerts:
            should_trigger = False

            if alert.alert_type == AlertType.TARGET_PRICE:
                should_trigger = alert.check_condition(current_price)

            elif alert.alert_type == AlertType.UPSIDE_CHANGE and current_upside is not None:
                should_trigger = alert.check_condition(current_upside)

            if should_trigger:
                alert.trigger()
                self._save_alert(alert)
                triggered_alerts.append(alert)

        return triggered_alerts

    def dismiss_alert(self, alert_id: str):
        """Dismiss an alert.

        Args:
            alert_id: Alert ID to dismiss
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE alerts SET status = ? WHERE id = ?
                """, (AlertStatus.DISMISSED.value, alert_id))
            
        
        except Exception as e:
            print(f"Error dismissing alert: {e}")

    def delete_alert(self, alert_id: str):
        """Delete an alert permanently.

        Args:
            alert_id: Alert ID to delete
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
            
        
        except Exception as e:
            print(f"Error deleting alert: {e}")

    def get_triggered_count(self) -> int:
        """Get count of triggered alerts.

        Returns:
            Number of triggered alerts
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts WHERE status = ?
                """, (AlertStatus.TRIGGERED.value,))
                return cursor.fetchone()[0]
        
        except Exception as e:
            print(f"Error getting triggered count: {e}")
            return 0

    def get_active_count(self) -> int:
        """Get count of active alerts.

        Returns:
            Number of active alerts
        """
        try:
            with self.cache._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM alerts WHERE status = ?
                """, (AlertStatus.ACTIVE.value,))
                return cursor.fetchone()[0]
        
        except Exception as e:
            print(f"Error getting active count: {e}")
            return 0

    def create_target_price_alert(self, ticker: str, target_price: float, above: bool = True) -> Alert:
        """Create a target price alert (convenience method).

        Args:
            ticker: Stock ticker
            target_price: Target price value
            above: True for "above", False for "below"

        Returns:
            Created Alert object
        """
        condition = AlertCondition.ABOVE if above else AlertCondition.BELOW
        direction = "por encima" if above else "por debajo"
        message = f"{ticker} alcanzó ${target_price:.2f} ({direction} del objetivo)"

        return self.create_alert(
            ticker=ticker,
            alert_type=AlertType.TARGET_PRICE,
            condition=condition,
            target_value=target_price,
            message=message
        )

    def create_upside_change_alert(self, ticker: str, threshold: float = 10.0) -> Alert:
        """Create an upside change alert (convenience method).

        Args:
            ticker: Stock ticker
            threshold: Change threshold percentage (default 10%)

        Returns:
            Created Alert object
        """
        message = f"{ticker} tuvo un cambio significativo (>{threshold}%) en su upside"

        return self.create_alert(
            ticker=ticker,
            alert_type=AlertType.UPSIDE_CHANGE,
            condition=AlertCondition.CHANGE_ABOVE,
            target_value=0,  # Will be updated when checked
            message=message,
            metadata={'change_threshold': threshold}
        )

    def export_to_csv(self) -> str:
        """Export all alerts to CSV format.

        Returns:
            CSV string
        """
        alerts = self.get_all_alerts()

        if not alerts:
            return "No hay alertas para exportar"

        # CSV header
        csv_lines = ["Ticker,Tipo,Condición,Valor Objetivo,Valor Actual,Estado,Creado,Disparado,Mensaje"]

        # CSV rows
        for alert in alerts:
            row = [
                alert.ticker,
                alert.alert_type.value,
                alert.condition.value,
                f"{alert.target_value:.2f}",
                f"{alert.current_value:.2f}",
                alert.status.value,
                alert.created_at.strftime("%Y-%m-%d %H:%M"),
                alert.triggered_at.strftime("%Y-%m-%d %H:%M") if alert.triggered_at else "",
                alert.message
            ]
            csv_lines.append(",".join(row))

        return "\n".join(csv_lines)
