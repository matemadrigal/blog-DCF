"""Yahoo Finance data provider."""

import yfinance as yf
from datetime import datetime
from typing import Optional

from .base import DataProvider, FinancialData


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider (no API key required)."""

    def __init__(self):
        """Initialize Yahoo Finance provider."""
        super().__init__(api_key=None)

    def is_available(self) -> bool:
        """Yahoo Finance is always available."""
        return True

    def test_connection(self) -> bool:
        """Test Yahoo Finance connection."""
        try:
            ticker = yf.Ticker("AAPL")
            info = ticker.info
            return "symbol" in info or "currentPrice" in info
        except Exception:
            return False

    def get_priority(self) -> int:
        """Yahoo Finance has secondary priority (reliable backup source)."""
        return 2  # Changed from 1 to 2 - now SECONDARY source (FMP is primary)

    def get_financial_data(
        self, ticker: str, years: int = 5
    ) -> Optional[FinancialData]:
        """
        Fetch financial data from Yahoo Finance.

        Args:
            ticker: Stock ticker symbol
            years: Number of years of historical data

        Returns:
            FinancialData object or None if failed
        """
        try:
            t = yf.Ticker(ticker)
            info = t.info
            cashflow = t.cashflow
            income_stmt = t.income_stmt
            balance_sheet = t.balance_sheet

            # Basic info
            company_name = info.get("longName") or info.get("shortName")
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")

            # Get diluted shares (prefer sharesOutstanding, fallback to basic shares)
            shares = info.get("sharesOutstanding")
            market_cap = info.get("marketCap")

            # Extract cash flow data
            operating_cf = []
            capex = []
            fcf = []

            if not cashflow.empty:
                cols = list(cashflow.columns)[:years]
                for col in cols:
                    # Operating Cash Flow
                    for idx in cashflow.index:
                        name = str(idx).lower()
                        if "operating cash flow" in name:
                            val = cashflow.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                operating_cf.append(float(val))
                            break

                    # Capital Expenditure (not stock repurchase!)
                    for idx in cashflow.index:
                        name = str(idx).lower()
                        if "capital expenditure" in name or "purchase of ppe" in name:
                            val = cashflow.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                capex.append(float(val))
                            break

                    # Free Cash Flow (if available)
                    for idx in cashflow.index:
                        name = str(idx).lower()
                        if "free" in name and "cash" in name:
                            val = cashflow.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                fcf.append(float(val))
                            break

            # Extract income statement data
            revenue = []
            net_income = []
            ebitda_list = []

            if not income_stmt.empty:
                cols = list(income_stmt.columns)[:years]
                for col in cols:
                    # Revenue
                    for idx in income_stmt.index:
                        name = str(idx).lower()
                        if "total revenue" in name or name == "revenue":
                            val = income_stmt.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                revenue.append(float(val))
                            break

                    # Net Income
                    for idx in income_stmt.index:
                        name = str(idx).lower()
                        if "net income" in name:
                            val = income_stmt.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                net_income.append(float(val))
                            break

                    # EBITDA
                    for idx in income_stmt.index:
                        name = str(idx).lower()
                        if "ebitda" in name:
                            val = income_stmt.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                ebitda_list.append(float(val))
                            break

            # Extract balance sheet data (most recent quarter)
            total_debt = None
            cash = None

            if not balance_sheet.empty:
                col = balance_sheet.columns[0]  # Most recent quarter
                for idx in balance_sheet.index:
                    name = str(idx).lower()

                    # Total Debt (long-term + short-term)
                    if total_debt is None:
                        if "total debt" in name or name == "total debt":
                            val = balance_sheet.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                total_debt = float(val)
                        elif (
                            "long term debt" in name or "long-term debt" in name
                        ) and "long term debt" in name:
                            val = balance_sheet.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                total_debt = float(val)

                    # Cash and Cash Equivalents
                    if cash is None:
                        if ("cash and cash equivalents" in name) or (
                            "cash" in name and "short" in name
                        ):
                            val = balance_sheet.loc[idx, col]
                            if val is not None and not str(val).lower() == "nan":
                                cash = float(val)

            # Fallback to info dict if not found in balance sheet
            if total_debt is None:
                total_debt = info.get("totalDebt", 0.0)
            if cash is None:
                cash = info.get("totalCash", 0.0)

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
                data_source="Yahoo Finance",
                last_updated=datetime.now(),
                fiscal_years=(
                    [str(col.year) for col in cashflow.columns[:years]]
                    if not cashflow.empty
                    else None
                ),
            )

            # Calculate completeness and confidence
            data.data_completeness = data.calculate_completeness()
            data.confidence_score = min(
                data.data_completeness, 95.0
            )  # Yahoo is reliable but capped

            return data

        except Exception as e:
            print(f"Yahoo Finance error for {ticker}: {str(e)}")
            return None
