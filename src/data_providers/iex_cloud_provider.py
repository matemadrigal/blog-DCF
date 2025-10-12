"""
IEX Cloud Data Provider

Free tier: 50,000 calls/month
Coverage: US stocks, ETFs, mutual funds
API: https://iexcloud.io/docs/api/
"""

import requests
from typing import Optional, List, Dict
from datetime import datetime
import logging

from .base import DataProvider, FinancialData

logger = logging.getLogger(__name__)


class IEXCloudProvider(DataProvider):
    """IEX Cloud data provider (free tier available)."""

    BASE_URL = "https://cloud.iexapis.com/stable"
    SANDBOX_URL = "https://sandbox.iexapis.com/stable"

    def __init__(self, api_key: Optional[str] = None, use_sandbox: bool = False):
        """
        Initialize IEX Cloud provider.

        Args:
            api_key: IEX Cloud API key (free tier available)
            use_sandbox: Use sandbox environment for testing
        """
        super().__init__(api_key=api_key)
        self.base_url = self.SANDBOX_URL if use_sandbox else self.BASE_URL

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.api_key != ""

    def test_connection(self) -> bool:
        """Test IEX Cloud API connection."""
        if not self.is_available():
            return False
        try:
            url = f"{self.base_url}/stock/AAPL/quote"
            params = {"token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def get_priority(self) -> int:
        """IEX Cloud has medium-low priority (free tier limits)."""
        return 4  # After FMP(1), Yahoo(2), Alpha Vantage(3)

    def get_financial_data(
        self, ticker: str, years: int = 5
    ) -> Optional[FinancialData]:
        """
        Fetch financial data from IEX Cloud.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data

        Returns:
            FinancialData object or None if failed
        """
        if not self.is_available():
            return None

        try:
            # Get company info
            company = self._get_company(ticker)
            if not company:
                return None

            # Get quote
            quote = self._get_quote(ticker)

            # Get financials
            income = self._get_income_statement(ticker, years)
            cash_flow = self._get_cash_flow(ticker, years)
            balance = self._get_balance_sheet(ticker, years)

            # Extract basic info
            company_name = company.get("companyName")
            current_price = quote.get("latestPrice") if quote else None
            shares = company.get("sharesOutstanding") if company else None
            market_cap = quote.get("marketCap") if quote else None

            # Parse cash flow data
            operating_cf = []
            capex = []
            fcf = []
            fiscal_years = []

            if cash_flow and "cashflow" in cash_flow:
                for report in cash_flow["cashflow"][:years]:
                    ocf = report.get("cashFlow")
                    if ocf:
                        operating_cf.append(float(ocf))

                    ce = report.get("capitalExpenditures")
                    if ce:
                        capex.append(float(ce))

                    # Calculate FCF
                    if ocf and ce:
                        fcf.append(float(ocf) - abs(float(ce)))

                    date = report.get("fiscalDate")
                    if date:
                        fiscal_years.append(str(date)[:4])

            # Parse income statement
            revenue = []
            net_income = []
            ebitda_list = []

            if income and "income" in income:
                for report in income["income"][:years]:
                    rev = report.get("totalRevenue")
                    if rev:
                        revenue.append(float(rev))

                    ni = report.get("netIncome")
                    if ni:
                        net_income.append(float(ni))

                    ebitda = report.get("ebitda")
                    if ebitda:
                        ebitda_list.append(float(ebitda))

            # Parse balance sheet
            total_debt = None
            cash = None

            if balance and "balancesheet" in balance:
                latest = balance["balancesheet"][0]
                td = latest.get("totalDebt")
                if td:
                    total_debt = float(td)

                c = latest.get("currentCash")
                if c:
                    cash = float(c)

            # Create FinancialData object
            data = FinancialData(
                ticker=ticker.upper(),
                company_name=company_name,
                current_price=current_price,
                shares_outstanding=shares,
                market_cap=market_cap,
                operating_cash_flow=operating_cf if operating_cf else None,
                capital_expenditure=capex if capex else None,
                free_cash_flow=fcf if fcf else None,
                revenue=revenue if revenue else None,
                net_income=net_income if net_income else None,
                ebitda=ebitda_list if ebitda_list else None,
                total_debt=total_debt,
                cash_and_equivalents=cash,
                data_source="IEX Cloud",
                last_updated=datetime.now(),
                fiscal_years=fiscal_years if fiscal_years else None,
            )

            # Calculate completeness and confidence
            data.data_completeness = data.calculate_completeness()
            data.confidence_score = min(data.data_completeness, 92.0)  # Good quality

            return data

        except Exception as e:
            logger.error(f"IEX Cloud error for {ticker}: {str(e)}")
            return None

    def _get_company(self, ticker: str) -> Optional[dict]:
        """Get company information."""
        try:
            url = f"{self.base_url}/stock/{ticker}/company"
            params = {"token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def _get_quote(self, ticker: str) -> Optional[dict]:
        """Get real-time quote."""
        try:
            url = f"{self.base_url}/stock/{ticker}/quote"
            params = {"token": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def _get_cash_flow(self, ticker: str, period: int = 4) -> Optional[dict]:
        """Get cash flow statement."""
        try:
            url = f"{self.base_url}/stock/{ticker}/cash-flow"
            params = {"token": self.api_key, "period": "annual", "last": period}
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def _get_income_statement(self, ticker: str, period: int = 4) -> Optional[dict]:
        """Get income statement."""
        try:
            url = f"{self.base_url}/stock/{ticker}/income"
            params = {"token": self.api_key, "period": "annual", "last": period}
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def _get_balance_sheet(self, ticker: str, period: int = 4) -> Optional[dict]:
        """Get balance sheet."""
        try:
            url = f"{self.base_url}/stock/{ticker}/balance-sheet"
            params = {"token": self.api_key, "period": "annual", "last": period}
            response = requests.get(url, params=params, timeout=10)
            return response.json() if response.status_code == 200 else None
        except Exception:
            return None

    def search_companies(self, query: str) -> List[Dict]:
        """
        Search for companies by name or symbol.

        Args:
            query: Search query

        Returns:
            List of matching companies
        """
        try:
            url = f"{self.base_url}/search/{query}"
            params = {"token": self.api_key}
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
            return []
        except Exception:
            return []
