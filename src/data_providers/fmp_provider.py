"""Financial Modeling Prep data provider."""

import requests
from datetime import datetime
from typing import Optional

from .base import DataProvider, FinancialData


class FinancialModelingPrepProvider(DataProvider):
    """Financial Modeling Prep data provider (requires API key)."""

    BASE_URL = "https://financialmodelingprep.com/api/v3"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize FMP provider."""
        super().__init__(api_key=api_key)

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return self.api_key is not None and self.api_key != ""

    def test_connection(self) -> bool:
        """Test FMP API connection."""
        if not self.is_available():
            return False
        try:
            url = f"{self.BASE_URL}/profile/AAPL"
            params = {"apikey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return isinstance(data, list) and len(data) > 0
        except Exception:
            return False

    def get_priority(self) -> int:
        """FMP has medium priority."""
        return 3

    def get_financial_data(
        self, ticker: str, years: int = 5
    ) -> Optional[FinancialData]:
        """
        Fetch financial data from Financial Modeling Prep.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data

        Returns:
            FinancialData object or None if failed
        """
        if not self.is_available():
            return None

        try:
            # Get company profile
            profile = self._get_profile(ticker)
            if not profile:
                return None

            # Get financial statements
            cash_flow = self._get_cash_flow(ticker, years)
            income = self._get_income_statement(ticker, years)
            balance = self._get_balance_sheet(ticker, years)

            # Extract basic info
            company_name = profile.get("companyName")
            current_price = profile.get("price")
            shares = profile.get("mktCap") and profile.get("price")
            if shares and current_price and current_price > 0:
                shares = int(profile.get("mktCap") / current_price)
            else:
                shares = None
            market_cap = profile.get("mktCap")

            # Parse cash flow data
            operating_cf = []
            capex = []
            fcf = []
            fiscal_years = []

            if cash_flow:
                for report in cash_flow[:years]:
                    ocf = report.get("operatingCashFlow")
                    if ocf:
                        operating_cf.append(float(ocf))

                    ce = report.get("capitalExpenditure")
                    if ce:
                        capex.append(float(ce))

                    free_cf = report.get("freeCashFlow")
                    if free_cf:
                        fcf.append(float(free_cf))

                    date = report.get("date") or report.get("calendarYear")
                    if date:
                        fiscal_years.append(str(date)[:4])

            # Parse income statement
            revenue = []
            net_income = []
            ebitda_list = []

            if income:
                for report in income[:years]:
                    rev = report.get("revenue")
                    if rev:
                        revenue.append(float(rev))

                    ni = report.get("netIncome")
                    if ni:
                        net_income.append(float(ni))

                    # EBITDA might not be directly available
                    ebitda = report.get("ebitda")
                    if ebitda:
                        ebitda_list.append(float(ebitda))

            # Parse balance sheet
            total_debt = None
            cash = None

            if balance:
                latest = balance[0]
                td = latest.get("totalDebt")
                if td:
                    total_debt = float(td)

                c = latest.get("cashAndCashEquivalents")
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
                data_source="Financial Modeling Prep",
                last_updated=datetime.now(),
                fiscal_years=fiscal_years if fiscal_years else None,
            )

            # Calculate completeness and confidence
            data.data_completeness = data.calculate_completeness()
            data.confidence_score = min(
                data.data_completeness, 97.0
            )  # High quality data

            return data

        except Exception as e:
            print(f"FMP error for {ticker}: {str(e)}")
            return None

    def _get_profile(self, ticker: str) -> Optional[dict]:
        """Get company profile."""
        try:
            url = f"{self.BASE_URL}/profile/{ticker}"
            params = {"apikey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data[0] if isinstance(data, list) and data else None
        except Exception:
            return None

    def _get_cash_flow(self, ticker: str, limit: int = 5) -> Optional[list]:
        """Get cash flow statement."""
        try:
            url = f"{self.BASE_URL}/cash-flow-statement/{ticker}"
            params = {"apikey": self.api_key, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data if isinstance(data, list) else None
        except Exception:
            return None

    def _get_income_statement(self, ticker: str, limit: int = 5) -> Optional[list]:
        """Get income statement."""
        try:
            url = f"{self.BASE_URL}/income-statement/{ticker}"
            params = {"apikey": self.api_key, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data if isinstance(data, list) else None
        except Exception:
            return None

    def _get_balance_sheet(self, ticker: str, limit: int = 5) -> Optional[list]:
        """Get balance sheet."""
        try:
            url = f"{self.BASE_URL}/balance-sheet-statement/{ticker}"
            params = {"apikey": self.api_key, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            return data if isinstance(data, list) else None
        except Exception:
            return None
