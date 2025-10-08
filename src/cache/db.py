"""SQLite cache for DCF calculations and historical data."""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any
from contextlib import contextmanager


class DCFCache:
    """Manages persistent storage of DCF calculations and price data."""

    def __init__(self, db_path: str = "data/dcf_cache.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        """Initialize database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # DCF calculations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS dcf_calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    calculation_date TEXT NOT NULL,
                    fair_value REAL NOT NULL,
                    market_price REAL,
                    discount_rate REAL NOT NULL,
                    growth_rate REAL NOT NULL,
                    fcf_projections TEXT NOT NULL,
                    shares_outstanding REAL,
                    metadata TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(ticker, calculation_date)
                )
            """
            )

            # Price history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    date TEXT NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL NOT NULL,
                    volume INTEGER,
                    created_at TEXT NOT NULL,
                    UNIQUE(ticker, date)
                )
            """
            )

            # Create indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_dcf_ticker_date
                ON dcf_calculations(ticker, calculation_date DESC)
            """
            )
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_price_ticker_date
                ON price_history(ticker, date DESC)
            """
            )

    def save_dcf_calculation(
        self,
        ticker: str,
        fair_value: float,
        discount_rate: float,
        growth_rate: float,
        fcf_projections: List[float],
        market_price: Optional[float] = None,
        shares_outstanding: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        calculation_date: Optional[str] = None,
    ) -> int:
        """Save a DCF calculation to the cache."""
        if calculation_date is None:
            calculation_date = datetime.now().date().isoformat()

        created_at = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO dcf_calculations
                (ticker, calculation_date, fair_value, market_price,
                 discount_rate, growth_rate, fcf_projections,
                 shares_outstanding, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    ticker.upper(),
                    calculation_date,
                    fair_value,
                    market_price,
                    discount_rate,
                    growth_rate,
                    json.dumps(fcf_projections),
                    shares_outstanding,
                    json.dumps(metadata) if metadata else None,
                    created_at,
                ),
            )
            return cursor.lastrowid

    def get_latest_dcf(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get the most recent DCF calculation for a ticker."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM dcf_calculations
                WHERE ticker = ?
                ORDER BY calculation_date DESC
                LIMIT 1
            """,
                (ticker.upper(),),
            )

            row = cursor.fetchone()
            if row:
                return self._row_to_dict(row)
            return None

    def get_dcf_history(
        self, ticker: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get historical DCF calculations for a ticker."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = """
                SELECT * FROM dcf_calculations
                WHERE ticker = ?
                ORDER BY calculation_date DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (ticker.upper(),))
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def save_price_history(self, ticker: str, df_prices):
        """Save price history from a pandas DataFrame."""
        import pandas as pd

        if df_prices.empty:
            return

        created_at = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()

            for date, row in df_prices.iterrows():
                date_str = pd.to_datetime(date).date().isoformat()

                # Convert pandas Series to scalar values, handle NaN properly
                try:
                    open_val = None if pd.isna(row["Open"]) else float(row["Open"])
                except (KeyError, ValueError, TypeError):
                    open_val = None

                try:
                    high_val = None if pd.isna(row["High"]) else float(row["High"])
                except (KeyError, ValueError, TypeError):
                    high_val = None

                try:
                    low_val = None if pd.isna(row["Low"]) else float(row["Low"])
                except (KeyError, ValueError, TypeError):
                    low_val = None

                try:
                    close_val = float(row["Close"])
                    if pd.isna(close_val):
                        continue  # Skip rows without valid close price
                except (ValueError, TypeError):
                    continue

                try:
                    volume_val = None if pd.isna(row["Volume"]) else int(row["Volume"])
                except (KeyError, ValueError, TypeError):
                    volume_val = None

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO price_history
                    (ticker, date, open, high, low, close, volume, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        ticker.upper(),
                        date_str,
                        open_val,
                        high_val,
                        low_val,
                        close_val,
                        volume_val,
                        created_at,
                    ),
                )

    def get_price_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get price history for a ticker within date range."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT * FROM price_history WHERE ticker = ?"
            params = [ticker.upper()]

            if start_date:
                query += " AND date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND date <= ?"
                params.append(end_date)

            query += " ORDER BY date DESC"

            cursor.execute(query, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_all_tickers(self) -> List[str]:
        """Get list of all tickers with DCF calculations."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT ticker FROM dcf_calculations
                ORDER BY ticker
            """
            )
            return [row[0] for row in cursor.fetchall()]

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert SQLite Row to dictionary."""
        result = dict(row)

        # Parse JSON fields
        if "fcf_projections" in result and result["fcf_projections"]:
            result["fcf_projections"] = json.loads(result["fcf_projections"])

        if "metadata" in result and result["metadata"]:
            result["metadata"] = json.loads(result["metadata"])

        return result
