"""FCF scanner for multiple companies with caching."""

import yfinance as yf
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os

try:
    import streamlit as st

    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False


class FCFScanner:
    """Scan and cache FCF data for multiple companies."""

    def __init__(self, cache_file: str = ".fcf_cache.json"):
        """Initialize FCF scanner with cache file."""
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def _is_cache_valid(self, ticker: str, max_age_hours: int = 24) -> bool:
        """Check if cached data is still valid."""
        if ticker not in self.cache:
            return False

        cache_time = datetime.fromisoformat(
            self.cache[ticker].get("timestamp", "2000-01-01")
        )
        age = datetime.now() - cache_time

        return age < timedelta(hours=max_age_hours)

    def get_base_fcf(self, ticker: str) -> Tuple[float, Optional[str]]:
        """
        Get base FCF for a ticker (with caching).

        Returns:
            Tuple of (base_fcf, error_message)
        """
        # Check cache first
        if self._is_cache_valid(ticker):
            cached_data = self.cache[ticker]
            return cached_data.get("base_fcf", 0.0), None

        # Fetch from Yahoo Finance
        try:
            t = yf.Ticker(ticker)
            cashflow = t.cashflow

            if cashflow.empty:
                error_msg = "No cash flow data"
                self._update_cache(ticker, 0.0, error_msg)
                return 0.0, error_msg

            # Get most recent year
            col = cashflow.columns[0]
            op = None
            capex = None

            for idx in cashflow.index:
                name = str(idx).lower()
                if "operating cash flow" in name and op is None:
                    op = cashflow.loc[idx, col]
                if (
                    "capital expenditure" in name or "purchase of ppe" in name
                ) and capex is None:
                    capex = cashflow.loc[idx, col]

            if op is not None and capex is not None:
                base_fcf = float(op - abs(capex))
                self._update_cache(ticker, base_fcf, None)
                return base_fcf, None
            else:
                error_msg = "Missing OCF or CAPEX"
                self._update_cache(ticker, 0.0, error_msg)
                return 0.0, error_msg

        except Exception as e:
            error_msg = str(e)
            self._update_cache(ticker, 0.0, error_msg)
            return 0.0, error_msg

    def _update_cache(self, ticker: str, base_fcf: float, error: Optional[str]):
        """Update cache for a ticker."""
        self.cache[ticker] = {
            "base_fcf": base_fcf,
            "error": error,
            "timestamp": datetime.now().isoformat(),
        }
        self._save_cache()

    def scan_companies(
        self, tickers: List[str], progress_callback=None
    ) -> Dict[str, Dict]:
        """
        Scan multiple companies for their FCF.

        Args:
            tickers: List of ticker symbols
            progress_callback: Optional callback function(current, total, ticker)

        Returns:
            Dictionary with ticker as key and data dict as value
        """
        results = {}

        for i, ticker in enumerate(tickers):
            if progress_callback:
                progress_callback(i + 1, len(tickers), ticker)

            base_fcf, error = self.get_base_fcf(ticker)
            results[ticker] = {"base_fcf": base_fcf, "error": error, "ticker": ticker}

        return results

    def get_cached_fcf(self, ticker: str) -> Optional[float]:
        """
        Get cached FCF without fetching (fast).

        Returns:
            Cached FCF or None if not in cache
        """
        if ticker in self.cache:
            return self.cache[ticker].get("base_fcf")
        return None

    def clear_cache(self):
        """Clear all cached data."""
        self.cache = {}
        self._save_cache()


def get_fcf_scanner() -> FCFScanner:
    """Get cached FCF scanner instance."""
    if HAS_STREAMLIT:

        @st.cache_resource
        def _cached_scanner():
            return FCFScanner()

        return _cached_scanner()
    else:
        return FCFScanner()
