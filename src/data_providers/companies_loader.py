"""Dynamic company loader from JSON file - replaces static Python lists."""

import json
import logging
from pathlib import Path
from typing import Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


class CompanyLoader:
    """Load and manage company data from JSON file."""

    def __init__(self, json_path: Optional[Path] = None):
        """
        Initialize company loader.

        Args:
            json_path: Path to companies JSON file. If None, uses default location.
        """
        if json_path is None:
            base_dir = Path(__file__).parent.parent.parent
            json_path = base_dir / "data" / "companies.json"

        self.json_path = json_path
        self._companies: Optional[list[dict]] = None

    def load_companies(self) -> list[dict]:
        """
        Load companies from JSON file.

        Returns:
            List of company dictionaries with ticker, name, and sector

        Raises:
            FileNotFoundError: If JSON file doesn't exist
            json.JSONDecodeError: If JSON file is invalid
        """
        if self._companies is not None:
            return self._companies

        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self._companies = json.load(f)
            logger.info(f"Loaded {len(self._companies)} companies from {self.json_path}")
            return self._companies
        except FileNotFoundError:
            logger.error(f"Companies file not found: {self.json_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in companies file: {e}")
            raise

    def get_company_by_ticker(self, ticker: str) -> Optional[dict]:
        """
        Get company information by ticker symbol.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Company dictionary or None if not found
        """
        companies = self.load_companies()
        ticker_upper = ticker.upper()

        for company in companies:
            if company["ticker"] == ticker_upper:
                return company

        return None

    def get_companies_by_sector(self, sector: str) -> list[dict]:
        """
        Get all companies in a specific sector.

        Args:
            sector: Sector name

        Returns:
            List of companies in the sector
        """
        companies = self.load_companies()
        return [c for c in companies if c["sector"].lower() == sector.lower()]

    def get_all_sectors(self) -> list[str]:
        """
        Get list of all unique sectors.

        Returns:
            Sorted list of sector names
        """
        companies = self.load_companies()
        sectors = {c["sector"] for c in companies}
        return sorted(sectors)

    def search_companies(self, query: str) -> list[dict]:
        """
        Search companies by ticker or name.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching companies
        """
        companies = self.load_companies()
        query_lower = query.lower()

        matches = []
        for company in companies:
            if (query_lower in company["ticker"].lower() or
                query_lower in company["name"].lower()):
                matches.append(company)

        return matches

    def reload(self) -> None:
        """Force reload companies from JSON file."""
        self._companies = None
        self.load_companies()


# Singleton instance
_company_loader: Optional[CompanyLoader] = None


@lru_cache(maxsize=1)
def get_company_loader() -> CompanyLoader:
    """Get or create singleton company loader instance."""
    global _company_loader
    if _company_loader is None:
        _company_loader = CompanyLoader()
    return _company_loader
