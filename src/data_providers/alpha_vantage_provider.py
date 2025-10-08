"""Alpha Vantage data provider."""

import requests
from datetime import datetime
from typing import Optional

from .base import DataProvider, FinancialData


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage data provider (requires API key)."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Alpha Vantage provider."""
        super().__init__(api_key=api_key)

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.api_key != ""

    def test_connection(self) -> bool:
        """Test Alpha Vantage API connection."""
        if not self.is_available():
            return False
        try:
            params = {
                "function": "OVERVIEW",
                "symbol": "AAPL",
                "apikey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return "Symbol" in data
        except Exception:
            return False

    def get_priority(self) -> int:
        """Alpha Vantage has medium-high priority."""
        return 2

    def get_financial_data(
        self, ticker: str, years: int = 5
    ) -> Optional[FinancialData]:
        """
        Fetch financial data from Alpha Vantage.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data

        Returns:
            FinancialData object or None if failed
        """
        if not self.is_available():
            return None

        try:
            # Get company overview
            overview = self._get_overview(ticker)
            if not overview:
                return None

            # Get cash flow statement
            cash_flow = self._get_cash_flow(ticker)

            # Get income statement
            income = self._get_income_statement(ticker)

            # Get balance sheet
            balance = self._get_balance_sheet(ticker)

            # Extract basic info
            company_name = overview.get("Name")
            shares = (
                int(overview.get("SharesOutstanding", 0))
                if overview.get("SharesOutstanding")
                else None
            )
            market_cap = (
                int(overview.get("MarketCapitalization", 0))
                if overview.get("MarketCapitalization")
                else None
            )

            # Parse cash flow data
            operating_cf = []
            capex = []
            fiscal_years = []

            if cash_flow:
                reports = cash_flow.get("annualReports", [])[:years]
                for report in reports:
                    ocf = report.get("operatingCashflow")
                    if ocf:
                        operating_cf.append(float(ocf))

                    ce = report.get("capitalExpenditures")
                    if ce:
                        capex.append(float(ce))

                    fy = report.get("fiscalDateEnding")
                    if fy:
                        fiscal_years.append(fy[:4])  # Year only

            # Parse income statement
            revenue = []
            net_income = []
            ebitda_list = []

            if income:
                reports = income.get("annualReports", [])[:years]
                for report in reports:
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

            if balance:
                reports = balance.get("annualReports", [])
                if reports:
                    latest = reports[0]
                    td = latest.get("shortLongTermDebtTotal") or latest.get(
                        "longTermDebt"
                    )
                    if td:
                        total_debt = float(td)

                    c = latest.get("cashAndCashEquivalentsAtCarryingValue")
                    if c:
                        cash = float(c)

            # Get current price (from overview or separate call)
            current_price = None
            price_data = self._get_quote(ticker)
            if price_data:
                current_price = float(price_data.get("05. price", 0))

            # Create FinancialData object
            data = FinancialData(
                ticker=ticker.upper(),
                company_name=company_name,
                current_price=current_price,
                shares_outstanding=shares,
                market_cap=market_cap,
                operating_cash_flow=operating_cf if operating_cf else None,
                capital_expenditure=capex if capex else None,
                free_cash_flow=None,  # Calculate from OCF and CAPEX
                revenue=revenue if revenue else None,
                net_income=net_income if net_income else None,
                ebitda=ebitda_list if ebitda_list else None,
                total_debt=total_debt,
                cash_and_equivalents=cash,
                data_source="Alpha Vantage",
                last_updated=datetime.now(),
                fiscal_years=fiscal_years if fiscal_years else None,
            )

            # Calculate completeness and confidence
            data.data_completeness = data.calculate_completeness()
            data.confidence_score = min(data.data_completeness, 98.0)  # High quality

            return data

        except Exception as e:
            print(f"Alpha Vantage error for {ticker}: {str(e)}")
            return None

    def _get_overview(self, ticker: str) -> Optional[dict]:
        """Get company overview."""
        try:
            params = {"function": "OVERVIEW", "symbol": ticker, "apikey": self.api_key}
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return data if "Symbol" in data else None
        except Exception:
            return None

    def _get_cash_flow(self, ticker: str) -> Optional[dict]:
        """Get cash flow statement."""
        try:
            params = {
                "function": "CASH_FLOW",
                "symbol": ticker,
                "apikey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return data if "annualReports" in data else None
        except Exception:
            return None

    def _get_income_statement(self, ticker: str) -> Optional[dict]:
        """Get income statement."""
        try:
            params = {
                "function": "INCOME_STATEMENT",
                "symbol": ticker,
                "apikey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return data if "annualReports" in data else None
        except Exception:
            return None

    def _get_balance_sheet(self, ticker: str) -> Optional[dict]:
        """Get balance sheet."""
        try:
            params = {
                "function": "BALANCE_SHEET",
                "symbol": ticker,
                "apikey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return data if "annualReports" in data else None
        except Exception:
            return None

    def _get_quote(self, ticker: str) -> Optional[dict]:
        """Get current quote."""
        try:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": ticker,
                "apikey": self.api_key,
            }
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            return data.get("Global Quote")
        except Exception:
            return None
