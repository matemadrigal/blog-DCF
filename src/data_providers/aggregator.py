"""Data aggregator for intelligent multi-source data fetching."""

import os
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st

from .base import DataProvider, FinancialData
from .yahoo_provider import YahooFinanceProvider
from .alpha_vantage_provider import AlphaVantageProvider
from .fmp_provider import FinancialModelingPrepProvider


class DataAggregator:
    """
    Intelligent data aggregator that fetches from multiple sources.

    Features:
    - Tries multiple providers in priority order
    - Merges data from different sources
    - Selects best quality data
    - Falls back to alternative sources on failure
    """

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize aggregator with API keys.

        Args:
            config: Dictionary with API keys
                    {'alpha_vantage': 'key', 'fmp': 'key'}
        """
        config = config or {}

        # Initialize all providers
        self.providers: List[DataProvider] = [
            YahooFinanceProvider(),
            AlphaVantageProvider(api_key=config.get("alpha_vantage")),
            FinancialModelingPrepProvider(api_key=config.get("fmp")),
        ]

        # Filter only available providers and sort by priority
        self.providers = [p for p in self.providers if p.is_available()]
        self.providers.sort(key=lambda p: p.get_priority())

    def get_available_providers(self) -> List[str]:
        """Get list of available provider names."""
        return [p.name for p in self.providers]

    def test_all_connections(self) -> Dict[str, bool]:
        """Test all provider connections."""
        results = {}
        for provider in self.providers:
            results[provider.name] = provider.test_connection()
        return results

    def get_financial_data(
        self,
        ticker: str,
        years: int = 5,
        strategy: str = "best_quality",
    ) -> Optional[FinancialData]:
        """
        Fetch financial data using intelligent strategy.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data
            strategy: Strategy to use:
                     - 'first_available': Use first working provider
                     - 'best_quality': Try all and pick highest quality
                     - 'merge': Merge data from multiple sources

        Returns:
            FinancialData object or None if all providers fail
        """
        if not self.providers:
            return None

        if strategy == "first_available":
            return self._fetch_first_available(ticker, years)
        elif strategy == "best_quality":
            return self._fetch_best_quality(ticker, years)
        elif strategy == "merge":
            return self._fetch_and_merge(ticker, years)
        else:
            return self._fetch_first_available(ticker, years)

    def _fetch_first_available(
        self, ticker: str, years: int
    ) -> Optional[FinancialData]:
        """Fetch from first available provider."""
        for provider in self.providers:
            try:
                data = provider.get_financial_data(ticker, years)
                if data:
                    return data
            except Exception as e:
                print(f"{provider.name} failed: {str(e)}")
                continue
        return None

    def _fetch_best_quality(self, ticker: str, years: int) -> Optional[FinancialData]:
        """Fetch from all providers and return best quality."""
        results = []

        # Fetch from all providers in parallel
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            future_to_provider = {
                executor.submit(p.get_financial_data, ticker, years): p
                for p in self.providers
            }

            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    data = future.result(timeout=15)
                    if data:
                        results.append(data)
                except Exception as e:
                    print(f"{provider.name} failed: {str(e)}")

        if not results:
            return None

        # Sort by confidence score (descending) and completeness
        results.sort(
            key=lambda x: (x.confidence_score, x.data_completeness), reverse=True
        )

        return results[0]

    def _fetch_and_merge(self, ticker: str, years: int) -> Optional[FinancialData]:
        """Fetch from all providers and intelligently merge data."""
        results = []

        # Fetch from all providers in parallel
        with ThreadPoolExecutor(max_workers=len(self.providers)) as executor:
            future_to_provider = {
                executor.submit(p.get_financial_data, ticker, years): p
                for p in self.providers
            }

            for future in as_completed(future_to_provider):
                provider = future_to_provider[future]
                try:
                    data = future.result(timeout=15)
                    if data:
                        results.append(data)
                except Exception as e:
                    print(f"{provider.name} failed: {str(e)}")

        if not results:
            return None

        # If only one result, return it
        if len(results) == 1:
            return results[0]

        # Merge results intelligently
        return self._merge_results(results, ticker)

    def _merge_results(
        self, results: List[FinancialData], ticker: str
    ) -> FinancialData:
        """
        Merge multiple FinancialData objects intelligently.

        Strategy:
        - Use data with highest confidence for each field
        - Prioritize completeness
        - Combine sources information
        """
        # Sort by confidence
        results.sort(key=lambda x: x.confidence_score, reverse=True)

        # Start with best result as base
        merged = FinancialData(ticker=ticker.upper())
        sources = []

        # Fields to merge (pick best available)
        fields = [
            "company_name",
            "current_price",
            "shares_outstanding",
            "market_cap",
            "operating_cash_flow",
            "capital_expenditure",
            "free_cash_flow",
            "revenue",
            "net_income",
            "ebitda",
            "total_debt",
            "cash_and_equivalents",
            "fiscal_years",
        ]

        for field in fields:
            # Find first non-None value with highest confidence
            for data in results:
                value = getattr(data, field, None)
                if value is not None:
                    setattr(merged, field, value)
                    if data.data_source not in sources:
                        sources.append(data.data_source)
                    break

        merged.data_source = " + ".join(sources)
        merged.data_completeness = merged.calculate_completeness()
        merged.confidence_score = sum(r.confidence_score for r in results) / len(
            results
        )

        return merged


@st.cache_resource
def get_data_aggregator() -> DataAggregator:
    """
    Get cached DataAggregator instance.

    Reads API keys from Streamlit secrets or environment variables.
    """
    config = {}

    # Try Streamlit secrets first
    try:
        if "alpha_vantage" in st.secrets:
            config["alpha_vantage"] = st.secrets["alpha_vantage"]
        if "fmp" in st.secrets:
            config["fmp"] = st.secrets["fmp"]
    except Exception:
        pass

    # Fall back to environment variables
    if "alpha_vantage" not in config:
        config["alpha_vantage"] = os.getenv("ALPHA_VANTAGE_API_KEY")
    if "fmp" not in config:
        config["fmp"] = os.getenv("FMP_API_KEY")

    return DataAggregator(config)
