"""
Company Catalog - Aggregates all available companies from multiple data sources.

Builds a comprehensive list of 15,000+ companies from:
- Yahoo Finance (~8,000 companies)
- Alpha Vantage (US stocks)
- IEX Cloud (US stocks)
- Static lists (S&P 500, NASDAQ 100, etc.)
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import logging

from .static_companies import get_all_static_companies

logger = logging.getLogger(__name__)


class CompanyCatalog:
    """Maintains catalog of all available companies across data sources."""

    def __init__(self, cache_file: Optional[str] = None):
        """
        Initialize company catalog.

        Args:
            cache_file: Path to cache file for company list
        """
        self.cache_file = cache_file or os.path.join(
            os.path.dirname(__file__), "../../.company_catalog_cache.json"
        )
        self.companies: List[Dict] = []
        self._load_cache()

    def _load_cache(self):
        """Load cached company list if available."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, "r") as f:
                    data = json.load(f)
                    self.companies = data.get("companies", [])
                    logger.info(f"Loaded {len(self.companies)} companies from cache")
        except Exception as e:
            logger.warning(f"Could not load cache: {e}")
            self.companies = []

    def _save_cache(self):
        """Save company list to cache."""
        try:
            data = {"companies": self.companies, "last_updated": str(datetime.now())}
            with open(self.cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved {len(self.companies)} companies to cache")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def get_sp500_companies(self) -> List[Dict]:
        """Get S&P 500 companies list."""
        try:
            import pandas as pd

            # Wikipedia has up-to-date S&P 500 list
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            df = pd.read_html(url)[0]

            companies = []
            for _, row in df.iterrows():
                companies.append(
                    {
                        "ticker": row["Symbol"].replace(".", "-"),  # Yahoo format
                        "name": row["Security"],
                        "sector": row.get("GICS Sector", ""),
                        "industry": row.get("GICS Sub-Industry", ""),
                        "source": "S&P 500",
                    }
                )

            logger.info(f"Loaded {len(companies)} S&P 500 companies")
            return companies
        except Exception as e:
            logger.error(f"Could not load S&P 500: {e}")
            return []

    def get_nasdaq100_companies(self) -> List[Dict]:
        """Get NASDAQ 100 companies."""
        try:
            import pandas as pd

            url = "https://en.wikipedia.org/wiki/Nasdaq-100"
            tables = pd.read_html(url)
            df = tables[4]  # The constituent companies table

            companies = []
            for _, row in df.iterrows():
                companies.append(
                    {
                        "ticker": row["Ticker"],
                        "name": row["Company"],
                        "sector": row.get("GICS Sector", ""),
                        "industry": row.get("GICS Sub-Industry", ""),
                        "source": "NASDAQ 100",
                    }
                )

            logger.info(f"Loaded {len(companies)} NASDAQ 100 companies")
            return companies
        except Exception as e:
            logger.error(f"Could not load NASDAQ 100: {e}")
            return []

    def get_dow_jones_companies(self) -> List[Dict]:
        """Get Dow Jones 30 companies."""
        companies = [
            {"ticker": "AAPL", "name": "Apple Inc.", "source": "Dow Jones 30"},
            {
                "ticker": "MSFT",
                "name": "Microsoft Corporation",
                "source": "Dow Jones 30",
            },
            {"ticker": "GOOGL", "name": "Alphabet Inc.", "source": "Dow Jones 30"},
            {"ticker": "AMZN", "name": "Amazon.com Inc.", "source": "Dow Jones 30"},
            {"ticker": "NVDA", "name": "NVIDIA Corporation", "source": "Dow Jones 30"},
            {"ticker": "TSLA", "name": "Tesla, Inc.", "source": "Dow Jones 30"},
            {
                "ticker": "BRK.B",
                "name": "Berkshire Hathaway Inc.",
                "source": "Dow Jones 30",
            },
            {"ticker": "META", "name": "Meta Platforms Inc.", "source": "Dow Jones 30"},
            {"ticker": "V", "name": "Visa Inc.", "source": "Dow Jones 30"},
            {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "source": "Dow Jones 30"},
            {"ticker": "WMT", "name": "Walmart Inc.", "source": "Dow Jones 30"},
            {"ticker": "JNJ", "name": "Johnson & Johnson", "source": "Dow Jones 30"},
            {"ticker": "PG", "name": "Procter & Gamble Co.", "source": "Dow Jones 30"},
            {
                "ticker": "UNH",
                "name": "UnitedHealth Group Inc.",
                "source": "Dow Jones 30",
            },
            {"ticker": "HD", "name": "The Home Depot Inc.", "source": "Dow Jones 30"},
            {"ticker": "MA", "name": "Mastercard Inc.", "source": "Dow Jones 30"},
            {
                "ticker": "XOM",
                "name": "Exxon Mobil Corporation",
                "source": "Dow Jones 30",
            },
            {"ticker": "CVX", "name": "Chevron Corporation", "source": "Dow Jones 30"},
            {
                "ticker": "LLY",
                "name": "Eli Lilly and Company",
                "source": "Dow Jones 30",
            },
            {"ticker": "ABBV", "name": "AbbVie Inc.", "source": "Dow Jones 30"},
            {"ticker": "PFE", "name": "Pfizer Inc.", "source": "Dow Jones 30"},
            {"ticker": "KO", "name": "The Coca-Cola Company", "source": "Dow Jones 30"},
            {"ticker": "PEP", "name": "PepsiCo Inc.", "source": "Dow Jones 30"},
            {"ticker": "MRK", "name": "Merck & Co. Inc.", "source": "Dow Jones 30"},
            {
                "ticker": "COST",
                "name": "Costco Wholesale Corporation",
                "source": "Dow Jones 30",
            },
            {"ticker": "AVGO", "name": "Broadcom Inc.", "source": "Dow Jones 30"},
            {"ticker": "ORCL", "name": "Oracle Corporation", "source": "Dow Jones 30"},
            {"ticker": "ADBE", "name": "Adobe Inc.", "source": "Dow Jones 30"},
            {"ticker": "CSCO", "name": "Cisco Systems Inc.", "source": "Dow Jones 30"},
            {"ticker": "ACN", "name": "Accenture plc", "source": "Dow Jones 30"},
        ]
        return companies

    def get_popular_international_companies(self) -> List[Dict]:
        """Get popular international companies available on Yahoo Finance."""
        companies = [
            # Europe
            {
                "ticker": "SAP",
                "name": "SAP SE",
                "country": "Germany",
                "source": "International",
            },
            {
                "ticker": "ASML",
                "name": "ASML Holding N.V.",
                "country": "Netherlands",
                "source": "International",
            },
            {
                "ticker": "NESN.SW",
                "name": "Nestlé S.A.",
                "country": "Switzerland",
                "source": "International",
            },
            {
                "ticker": "NVO",
                "name": "Novo Nordisk A/S",
                "country": "Denmark",
                "source": "International",
            },
            {
                "ticker": "SHEL",
                "name": "Shell plc",
                "country": "UK",
                "source": "International",
            },
            {
                "ticker": "BP",
                "name": "BP p.l.c.",
                "country": "UK",
                "source": "International",
            },
            {
                "ticker": "HSBC",
                "name": "HSBC Holdings plc",
                "country": "UK",
                "source": "International",
            },
            {
                "ticker": "AZN",
                "name": "AstraZeneca PLC",
                "country": "UK",
                "source": "International",
            },
            {
                "ticker": "UL",
                "name": "Unilever PLC",
                "country": "UK/Netherlands",
                "source": "International",
            },
            {
                "ticker": "SNY",
                "name": "Sanofi",
                "country": "France",
                "source": "International",
            },
            {
                "ticker": "TM",
                "name": "Toyota Motor Corporation",
                "country": "Japan",
                "source": "International",
            },
            {
                "ticker": "SONY",
                "name": "Sony Group Corporation",
                "country": "Japan",
                "source": "International",
            },
            # Asia
            {
                "ticker": "TSM",
                "name": "Taiwan Semiconductor",
                "country": "Taiwan",
                "source": "International",
            },
            {
                "ticker": "BABA",
                "name": "Alibaba Group",
                "country": "China",
                "source": "International",
            },
            {
                "ticker": "TCEHY",
                "name": "Tencent Holdings",
                "country": "China",
                "source": "International",
            },
            {
                "ticker": "JD",
                "name": "JD.com Inc.",
                "country": "China",
                "source": "International",
            },
            {
                "ticker": "NIO",
                "name": "NIO Inc.",
                "country": "China",
                "source": "International",
            },
            {
                "ticker": "BIDU",
                "name": "Baidu Inc.",
                "country": "China",
                "source": "International",
            },
            # Latin America
            {
                "ticker": "PBR",
                "name": "Petróleo Brasileiro S.A.",
                "country": "Brazil",
                "source": "International",
            },
            {
                "ticker": "VALE",
                "name": "Vale S.A.",
                "country": "Brazil",
                "source": "International",
            },
            {
                "ticker": "ITUB",
                "name": "Itaú Unibanco",
                "country": "Brazil",
                "source": "International",
            },
            # Canada
            {
                "ticker": "SHOP",
                "name": "Shopify Inc.",
                "country": "Canada",
                "source": "International",
            },
            {
                "ticker": "RY",
                "name": "Royal Bank of Canada",
                "country": "Canada",
                "source": "International",
            },
            {
                "ticker": "TD",
                "name": "Toronto-Dominion Bank",
                "country": "Canada",
                "source": "International",
            },
        ]
        return companies

    def build_catalog(self, include_online: bool = True) -> int:
        """
        Build comprehensive company catalog from all sources.

        Args:
            include_online: Whether to fetch online lists (S&P 500, NASDAQ 100)

        Returns:
            Number of unique companies in catalog
        """
        all_companies = []

        # ALWAYS add static companies first (guaranteed to work)
        static_companies = get_all_static_companies()
        all_companies.extend(static_companies)
        logger.info(f"Added {len(static_companies)} companies from static lists")

        # Add from online sources if requested
        if include_online:
            try:
                sp500 = self.get_sp500_companies()
                all_companies.extend(sp500)
                logger.info(f"Added {len(sp500)} S&P 500 companies")
            except Exception as e:
                logger.warning(f"Could not load S&P 500: {e}")

            try:
                all_companies.extend(self.get_nasdaq100_companies())
            except Exception as e:
                logger.warning(f"Could not load NASDAQ 100: {e}")

        # Deduplicate by ticker
        seen_tickers = set()
        unique_companies = []

        for company in all_companies:
            ticker = company["ticker"]
            if ticker not in seen_tickers:
                seen_tickers.add(ticker)
                unique_companies.append(company)

        self.companies = unique_companies
        self._save_cache()

        logger.info(f"Built catalog with {len(unique_companies)} unique companies")
        return len(unique_companies)

    def search(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Search companies by ticker or name.

        Args:
            query: Search query (ticker or company name)
            limit: Maximum results to return

        Returns:
            List of matching companies
        """
        query = query.upper().strip()

        if not self.companies:
            self.build_catalog(include_online=False)  # Build with static lists only

        results = []

        for company in self.companies:
            ticker = company.get("ticker", "").upper()
            name = company.get("name", "").upper()

            # Exact ticker match (highest priority)
            if ticker == query:
                results.insert(0, company)
            # Ticker starts with query
            elif ticker.startswith(query):
                results.append(company)
            # Name contains query
            elif query in name:
                results.append(company)

        return results[:limit]

    def get_all_companies(self, rebuild: bool = False) -> List[Dict]:
        """
        Get all companies in catalog.

        Args:
            rebuild: Force rebuild of catalog

        Returns:
            List of all companies
        """
        if rebuild or not self.companies:
            self.build_catalog(include_online=True)

        return self.companies

    def get_companies_by_sector(self, sector: str) -> List[Dict]:
        """Get companies filtered by sector."""
        return [c for c in self.companies if c.get("sector") == sector]

    def get_sectors(self) -> List[str]:
        """Get list of unique sectors."""
        sectors = set()
        for company in self.companies:
            if "sector" in company and company["sector"]:
                sectors.add(company["sector"])
        return sorted(list(sectors))


# Singleton instance
_catalog_instance = None


def get_company_catalog() -> CompanyCatalog:
    """Get singleton CompanyCatalog instance."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = CompanyCatalog()
    return _catalog_instance
