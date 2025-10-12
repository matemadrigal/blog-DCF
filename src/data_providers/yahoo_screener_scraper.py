"""
Yahoo Finance Screener Scraper - Get all available stocks.

Scrapes Yahoo Finance screener to get comprehensive list of all stocks
from NYSE, NASDAQ, AMEX, and international markets.
"""

import requests
import time
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class YahooScreenerScraper:
    """Scrape Yahoo Finance screener for comprehensive stock list."""

    BASE_URL = "https://query1.finance.yahoo.com/v1/finance/screener"

    # Predefined screeners for different exchanges
    SCREENERS = {
        "us_stocks": {
            "offset": 0,
            "size": 250,
            "sortField": "ticker",
            "sortType": "asc",
            "quoteType": "EQUITY",
            "query": {
                "operator": "and",
                "operands": [
                    {"operator": "eq", "operands": ["region", "us"]},
                    {
                        "operator": "or",
                        "operands": [
                            {"operator": "eq", "operands": ["exchange", "NYQ"]},  # NYSE
                            {
                                "operator": "eq",
                                "operands": ["exchange", "NMS"],
                            },  # NASDAQ
                            {"operator": "eq", "operands": ["exchange", "ASE"]},  # AMEX
                        ],
                    },
                ],
            },
            "userId": "",
            "userIdType": "guid",
        }
    }

    def __init__(self, max_workers: int = 5):
        """
        Initialize scraper.

        Args:
            max_workers: Number of concurrent requests
        """
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def _fetch_page(self, offset: int, size: int = 250) -> Optional[Dict]:
        """
        Fetch a single page of stocks.

        Args:
            offset: Starting offset for pagination
            size: Number of results per page

        Returns:
            API response with stock data
        """
        try:
            payload = self.SCREENERS["us_stocks"].copy()
            payload["offset"] = offset
            payload["size"] = size

            response = self.session.post(self.BASE_URL, json=payload, timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Status {response.status_code} for offset {offset}")
                return None

        except Exception as e:
            logger.error(f"Error fetching offset {offset}: {e}")
            return None

    def get_all_us_stocks(self, max_stocks: Optional[int] = None) -> List[Dict]:
        """
        Get all US stocks from NYSE, NASDAQ, AMEX.

        Args:
            max_stocks: Maximum number of stocks to fetch (None = all)

        Returns:
            List of stock dictionaries with ticker, name, exchange, sector
        """
        logger.info("Fetching US stocks from Yahoo Finance screener...")

        all_stocks = []
        offset = 0
        page_size = 250
        total_found = None

        # First request to get total count
        first_page = self._fetch_page(offset=0, size=page_size)
        if not first_page:
            logger.error("Failed to fetch first page")
            return all_stocks

        # Extract total count
        finance_data = first_page.get("finance", {})
        result = finance_data.get("result", [{}])[0]
        total_found = result.get("total", 0)

        logger.info(f"Found {total_found} total US stocks")

        # Process first page
        quotes = result.get("quotes", [])
        for quote in quotes:
            stock = self._parse_quote(quote)
            if stock:
                all_stocks.append(stock)

        # Determine how many pages to fetch
        if max_stocks:
            total_to_fetch = min(max_stocks, total_found)
        else:
            total_to_fetch = total_found

        total_pages = (total_to_fetch + page_size - 1) // page_size

        # Fetch remaining pages in parallel
        if total_pages > 1:
            logger.info(f"Fetching {total_pages - 1} more pages...")

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = []

                for page in range(1, total_pages):
                    offset = page * page_size
                    future = executor.submit(self._fetch_page, offset, page_size)
                    futures.append((page, future))
                    time.sleep(0.2)  # Rate limiting

                for page, future in futures:
                    try:
                        result = future.result(timeout=15)
                        if result:
                            finance_data = result.get("finance", {})
                            page_result = finance_data.get("result", [{}])[0]
                            quotes = page_result.get("quotes", [])

                            for quote in quotes:
                                stock = self._parse_quote(quote)
                                if stock:
                                    all_stocks.append(stock)

                            logger.info(
                                f"Page {page + 1}/{total_pages}: {len(quotes)} stocks"
                            )
                    except Exception as e:
                        logger.error(f"Error processing page {page}: {e}")

        logger.info(f"Successfully fetched {len(all_stocks)} US stocks")
        return all_stocks

    def _parse_quote(self, quote: Dict) -> Optional[Dict]:
        """
        Parse a quote from Yahoo Finance API response.

        Args:
            quote: Raw quote data from API

        Returns:
            Parsed stock dictionary
        """
        try:
            ticker = quote.get("symbol", "").strip()
            if not ticker:
                return None

            # Map Yahoo exchange codes to readable names
            exchange_map = {
                "NYQ": "NYSE",
                "NMS": "NASDAQ",
                "NAS": "NASDAQ",
                "ASE": "AMEX",
                "PNK": "OTC",
                "NGM": "NASDAQ",
            }

            exchange_code = quote.get("exchange", "")
            exchange = exchange_map.get(exchange_code, exchange_code)

            return {
                "ticker": ticker,
                "name": quote.get("longName") or quote.get("shortName", ""),
                "exchange": exchange,
                "sector": quote.get("sector", ""),
                "industry": quote.get("industry", ""),
                "market_cap": quote.get("marketCap"),
                "source": f"Yahoo Screener ({exchange})",
            }
        except Exception as e:
            logger.error(f"Error parsing quote: {e}")
            return None

    def get_international_adrs(self) -> List[Dict]:
        """
        Get international companies available as ADRs on US exchanges.

        Returns:
            List of international stock dictionaries
        """
        logger.info("Fetching international ADRs...")

        try:
            payload = {
                "offset": 0,
                "size": 250,
                "sortField": "ticker",
                "sortType": "asc",
                "quoteType": "EQUITY",
                "query": {
                    "operator": "and",
                    "operands": [
                        {"operator": "ne", "operands": ["region", "us"]},
                        {
                            "operator": "or",
                            "operands": [
                                {"operator": "eq", "operands": ["exchange", "NYQ"]},
                                {"operator": "eq", "operands": ["exchange", "NMS"]},
                            ],
                        },
                    ],
                },
                "userId": "",
                "userIdType": "guid",
            }

            response = self.session.post(self.BASE_URL, json=payload, timeout=10)

            if response.status_code == 200:
                result = response.json()
                finance_data = result.get("finance", {})
                page_result = finance_data.get("result", [{}])[0]
                quotes = page_result.get("quotes", [])

                adrs = []
                for quote in quotes:
                    stock = self._parse_quote(quote)
                    if stock:
                        stock["source"] = "Yahoo Screener (ADR)"
                        adrs.append(stock)

                logger.info(f"Found {len(adrs)} international ADRs")
                return adrs
            else:
                logger.warning(f"Failed to fetch ADRs: {response.status_code}")
                return []

        except Exception as e:
            logger.error(f"Error fetching ADRs: {e}")
            return []


def get_yahoo_screener() -> YahooScreenerScraper:
    """Get singleton YahooScreenerScraper instance."""
    return YahooScreenerScraper(max_workers=5)
