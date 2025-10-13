"""
NASDAQ/NYSE Ticker Fetcher - Get all stocks from official sources.

Downloads official CSV files from NASDAQ/NYSE FTP servers.
100% free, no API key required, ~6,500+ companies.
"""

import requests
import csv
import io
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class NASDAQFetcher:
    """Fetch stock lists from NASDAQ and NYSE official sources."""

    # Official NASDAQ FTP endpoints (public, free)
    NASDAQ_URL = "https://api.nasdaq.com/api/screener/stocks"

    # Alternative: Direct CSV downloads
    NASDAQ_CSV = "ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt"
    OTHER_CSV = "ftp://ftp.nasdaqtrader.com/symboldirectory/otherlisted.txt"

    def __init__(self):
        """Initialize fetcher."""
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
            }
        )

    def get_nasdaq_api(
        self, exchange: str = "nasdaq", limit: int = 10000
    ) -> List[Dict]:
        """
        Get stocks from NASDAQ API (works without authentication).

        Args:
            exchange: Exchange filter (nasdaq, nyse, amex)
            limit: Maximum number of stocks

        Returns:
            List of stock dictionaries
        """
        try:
            url = f"{self.NASDAQ_URL}?tableonly=true&limit={limit}&exchange={exchange}"

            logger.info(f"Fetching {exchange.upper()} stocks from NASDAQ API...")

            response = self.session.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                rows = data.get("data", {}).get("table", {}).get("rows", [])

                stocks = []
                for row in rows:
                    stock = self._parse_nasdaq_row(row, exchange.upper())
                    if stock:
                        stocks.append(stock)

                logger.info(f"Fetched {len(stocks)} stocks from {exchange.upper()}")
                return stocks
            else:
                logger.warning(f"NASDAQ API returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching {exchange}: {e}")
            return []

    def _parse_nasdaq_row(self, row: Dict, exchange: str) -> Optional[Dict]:
        """
        Parse a row from NASDAQ API response.

        Args:
            row: Raw row data
            exchange: Exchange name

        Returns:
            Parsed stock dictionary
        """
        try:
            ticker = row.get("symbol", "").strip()
            if not ticker:
                return None

            return {
                "ticker": ticker,
                "name": row.get("name", "").strip(),
                "exchange": exchange,
                "sector": row.get("sector", "").strip(),
                "industry": row.get("industry", "").strip(),
                "market_cap": row.get("marketCap"),
                "country": row.get("country", "USA"),
                "source": f"NASDAQ API ({exchange})",
            }
        except Exception as e:
            logger.error(f"Error parsing row: {e}")
            return None

    def get_nasdaq_ftp(self) -> List[Dict]:
        """
        Get NASDAQ-listed stocks from FTP server.

        Returns:
            List of NASDAQ stock dictionaries
        """
        try:
            logger.info("Fetching NASDAQ stocks from FTP...")

            response = requests.get(self.NASDAQ_CSV, timeout=30)

            if response.status_code == 200:
                content = response.text
                reader = csv.DictReader(io.StringIO(content), delimiter="|")

                stocks = []
                for row in reader:
                    symbol = row.get("Symbol", "").strip()

                    # Skip test symbols and invalid tickers
                    if not symbol or symbol.startswith("$") or len(symbol) > 5:
                        continue

                    # Skip if marked as test
                    if row.get("Test Issue", "N") == "Y":
                        continue

                    stocks.append(
                        {
                            "ticker": symbol,
                            "name": row.get("Security Name", "").strip(),
                            "exchange": "NASDAQ",
                            "sector": "",
                            "industry": "",
                            "market_cap": None,
                            "country": "USA",
                            "source": "NASDAQ FTP",
                        }
                    )

                logger.info(f"Fetched {len(stocks)} NASDAQ stocks from FTP")
                return stocks
            else:
                logger.warning(f"FTP returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching NASDAQ FTP: {e}")
            return []

    def get_other_exchanges_ftp(self) -> List[Dict]:
        """
        Get NYSE, AMEX and other exchange stocks from FTP.

        Returns:
            List of stock dictionaries from other exchanges
        """
        try:
            logger.info("Fetching NYSE/AMEX stocks from FTP...")

            response = requests.get(self.OTHER_CSV, timeout=30)

            if response.status_code == 200:
                content = response.text
                reader = csv.DictReader(io.StringIO(content), delimiter="|")

                stocks = []
                for row in reader:
                    symbol = (
                        row.get("ACT Symbol", "").strip()
                        or row.get("NASDAQ Symbol", "").strip()
                    )

                    # Skip invalid tickers
                    if not symbol or len(symbol) > 5:
                        continue

                    # Skip if marked as test
                    if row.get("Test Issue", "N") == "Y":
                        continue

                    # Determine exchange
                    exchange_code = row.get("Exchange", "")
                    exchange_map = {
                        "A": "AMEX",
                        "N": "NYSE",
                        "P": "NYSE Arca",
                        "Z": "BATS",
                        "Q": "NASDAQ",
                    }
                    exchange = exchange_map.get(exchange_code, "OTHER")

                    stocks.append(
                        {
                            "ticker": symbol,
                            "name": row.get("Security Name", "").strip(),
                            "exchange": exchange,
                            "sector": "",
                            "industry": "",
                            "market_cap": None,
                            "country": "USA",
                            "source": f"{exchange} FTP",
                        }
                    )

                logger.info(f"Fetched {len(stocks)} NYSE/AMEX stocks from FTP")
                return stocks
            else:
                logger.warning(f"FTP returned {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching other exchanges FTP: {e}")
            return []

    def get_all_stocks(self, use_api: bool = True, use_ftp: bool = True) -> List[Dict]:
        """
        Get all available stocks from NASDAQ, NYSE, AMEX.

        Args:
            use_api: Use NASDAQ API (faster, more data)
            use_ftp: Use FTP servers (backup, more complete)

        Returns:
            Combined list of all stocks
        """
        all_stocks = []
        seen_tickers = set()

        # Try API first (has sector/industry data)
        if use_api:
            for exchange in ["nasdaq", "nyse", "amex"]:
                stocks = self.get_nasdaq_api(exchange)
                for stock in stocks:
                    ticker = stock["ticker"]
                    if ticker not in seen_tickers:
                        seen_tickers.add(ticker)
                        all_stocks.append(stock)

        # Fallback to FTP if API didn't work or for completeness
        if use_ftp and len(all_stocks) < 1000:
            logger.info("API returned few results, trying FTP...")

            nasdaq_ftp = self.get_nasdaq_ftp()
            for stock in nasdaq_ftp:
                ticker = stock["ticker"]
                if ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    all_stocks.append(stock)

            other_ftp = self.get_other_exchanges_ftp()
            for stock in other_ftp:
                ticker = stock["ticker"]
                if ticker not in seen_tickers:
                    seen_tickers.add(ticker)
                    all_stocks.append(stock)

        logger.info(f"Total unique stocks fetched: {len(all_stocks)}")
        return all_stocks


def get_nasdaq_fetcher() -> NASDAQFetcher:
    """Get NASDAQFetcher instance."""
    return NASDAQFetcher()
