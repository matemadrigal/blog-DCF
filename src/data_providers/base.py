"""Base classes for data providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class FinancialData:
    """Standardized financial data structure."""

    ticker: str
    company_name: Optional[str] = None
    current_price: Optional[float] = None
    shares_outstanding: Optional[int] = None
    market_cap: Optional[float] = None

    # Cash Flow data
    operating_cash_flow: Optional[List[float]] = None
    capital_expenditure: Optional[List[float]] = None
    free_cash_flow: Optional[List[float]] = None

    # Income Statement
    revenue: Optional[List[float]] = None
    net_income: Optional[List[float]] = None
    ebitda: Optional[List[float]] = None

    # Balance Sheet
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None

    # Metadata
    data_source: Optional[str] = None
    last_updated: Optional[datetime] = None
    fiscal_years: Optional[List[str]] = None

    # Quality metrics
    data_completeness: float = 0.0  # 0-100%
    confidence_score: float = 0.0  # 0-100%

    def calculate_fcf(self) -> Optional[List[float]]:
        """Calculate Free Cash Flow from operating cash flow and capex."""
        if self.operating_cash_flow and self.capital_expenditure:
            if len(self.operating_cash_flow) == len(self.capital_expenditure):
                return [
                    ocf - abs(capex)
                    for ocf, capex in zip(
                        self.operating_cash_flow, self.capital_expenditure
                    )
                ]
        return self.free_cash_flow

    def calculate_completeness(self) -> float:
        """Calculate data completeness percentage."""
        fields = [
            self.company_name,
            self.current_price,
            self.shares_outstanding,
            self.operating_cash_flow,
            self.capital_expenditure,
            self.revenue,
            self.net_income,
            self.total_debt,
            self.cash_and_equivalents,
        ]
        filled = sum(1 for f in fields if f is not None)
        return (filled / len(fields)) * 100


class DataProvider(ABC):
    """Abstract base class for financial data providers."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize provider with optional API key."""
        self.api_key = api_key
        self.name = self.__class__.__name__

    @abstractmethod
    def get_financial_data(
        self, ticker: str, years: int = 5
    ) -> Optional[FinancialData]:
        """
        Fetch financial data for a given ticker.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data

        Returns:
            FinancialData object or None if failed
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test API connection."""
        pass

    def get_priority(self) -> int:
        """
        Get provider priority (lower is better).

        Returns:
            Priority number (1 = highest priority)
        """
        return 10  # Default low priority
