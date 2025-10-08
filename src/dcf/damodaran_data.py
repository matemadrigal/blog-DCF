"""
Damodaran data integration for industry betas and cost of capital.

Data source: Aswath Damodaran (NYU Stern)
https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datacurrent.html
"""

from typing import Optional, Dict
import yfinance as yf


class DamodaranData:
    """
    Integration with Damodaran industry data (January 2025).

    Data is hardcoded from Damodaran's 2025 datasets for key industries.
    For production, this could fetch from Excel files or API.
    """

    # Risk-free rate and market parameters (as of January 2025)
    # Source: Damodaran Data Update 2025
    RISK_FREE_RATE = 0.0445  # 10Y Treasury ~4.45%
    MARKET_RETURN = 0.0892  # Total market cost of equity
    EQUITY_RISK_PREMIUM = MARKET_RETURN - RISK_FREE_RATE  # ~4.47%

    # Industry data: {industry_key: {beta, unlevered_beta, debt_ratio, tax_rate, cost_of_equity, wacc}}
    # Source: https://www.stern.nyu.edu/~adamodar/pc/datasets/betas.xls (Jan 2025)
    INDUSTRY_DATA = {
        # Technology
        "software": {
            "beta": 1.19,
            "unlevered_beta": 1.14,
            "debt_ratio": 0.05,
            "tax_rate": 0.146,
            "cost_of_equity": 0.0978,
            "wacc": 0.0941,
        },
        "semiconductor": {
            "beta": 1.37,
            "unlevered_beta": 1.30,
            "debt_ratio": 0.087,
            "tax_rate": 0.126,
            "cost_of_equity": 0.1058,
            "wacc": 0.0997,
        },
        "computer_services": {
            "beta": 1.15,
            "unlevered_beta": 1.10,
            "debt_ratio": 0.067,
            "tax_rate": 0.159,
            "cost_of_equity": 0.0959,
            "wacc": 0.0917,
        },
        "internet": {
            "beta": 1.24,
            "unlevered_beta": 1.19,
            "debt_ratio": 0.066,
            "tax_rate": 0.135,
            "cost_of_equity": 0.0999,
            "wacc": 0.0956,
        },
        # Consumer
        "retail": {
            "beta": 1.03,
            "unlevered_beta": 0.89,
            "debt_ratio": 0.247,
            "tax_rate": 0.179,
            "cost_of_equity": 0.0906,
            "wacc": 0.0781,
        },
        "beverage": {
            "beta": 0.72,
            "unlevered_beta": 0.63,
            "debt_ratio": 0.218,
            "tax_rate": 0.186,
            "cost_of_equity": 0.0767,
            "wacc": 0.0691,
        },
        "food_processing": {
            "beta": 0.72,
            "unlevered_beta": 0.62,
            "debt_ratio": 0.257,
            "tax_rate": 0.189,
            "cost_of_equity": 0.0767,
            "wacc": 0.0677,
        },
        # Healthcare
        "pharmaceutical": {
            "beta": 0.86,
            "unlevered_beta": 0.81,
            "debt_ratio": 0.094,
            "tax_rate": 0.097,
            "cost_of_equity": 0.0830,
            "wacc": 0.0790,
        },
        "healthcare": {
            "beta": 0.92,
            "unlevered_beta": 0.84,
            "debt_ratio": 0.147,
            "tax_rate": 0.172,
            "cost_of_equity": 0.0856,
            "wacc": 0.0792,
        },
        "biotechnology": {
            "beta": 1.14,
            "unlevered_beta": 1.13,
            "debt_ratio": 0.022,
            "tax_rate": 0.009,
            "cost_of_equity": 0.0954,
            "wacc": 0.0938,
        },
        # Financials
        "bank": {
            "beta": 1.12,
            "unlevered_beta": 0.45,
            "debt_ratio": 2.494,
            "tax_rate": 0.189,
            "cost_of_equity": 0.0945,
            "wacc": 0.0599,
        },
        "insurance": {
            "beta": 0.87,
            "unlevered_beta": 0.58,
            "debt_ratio": 0.785,
            "tax_rate": 0.163,
            "cost_of_equity": 0.0834,
            "wacc": 0.0676,
        },
        # Energy & Utilities
        "oil_gas": {
            "beta": 1.16,
            "unlevered_beta": 0.94,
            "debt_ratio": 0.354,
            "tax_rate": 0.169,
            "cost_of_equity": 0.0963,
            "wacc": 0.0808,
        },
        "utility": {
            "beta": 0.60,
            "unlevered_beta": 0.39,
            "debt_ratio": 0.854,
            "tax_rate": 0.193,
            "cost_of_equity": 0.0713,
            "wacc": 0.0569,
        },
        # Industrial
        "manufacturing": {
            "beta": 0.97,
            "unlevered_beta": 0.82,
            "debt_ratio": 0.279,
            "tax_rate": 0.181,
            "cost_of_equity": 0.0879,
            "wacc": 0.0764,
        },
        "aerospace": {
            "beta": 1.08,
            "unlevered_beta": 0.88,
            "debt_ratio": 0.355,
            "tax_rate": 0.142,
            "cost_of_equity": 0.0928,
            "wacc": 0.0774,
        },
        # Default/Market
        "market": {
            "beta": 1.00,
            "unlevered_beta": 0.83,
            "debt_ratio": 0.310,
            "tax_rate": 0.177,
            "cost_of_equity": 0.0892,
            "wacc": 0.0759,
        },
    }

    # Mapping from Yahoo Finance sectors/industries to Damodaran categories
    SECTOR_MAPPING = {
        # Technology sectors
        "technology": "software",
        "software": "software",
        "information technology": "software",
        "semiconductors": "semiconductor",
        "semiconductor": "semiconductor",
        "computer hardware": "computer_services",
        "internet": "internet",
        "internet content & information": "internet",
        # Consumer sectors
        "consumer cyclical": "retail",
        "consumer defensive": "food_processing",
        "retail": "retail",
        "beverages": "beverage",
        "food products": "food_processing",
        # Healthcare
        "healthcare": "healthcare",
        "drug manufacturers": "pharmaceutical",
        "pharmaceuticals": "pharmaceutical",
        "biotechnology": "biotechnology",
        # Financial
        "financial services": "bank",
        "financial": "bank",
        "banks": "bank",
        "insurance": "insurance",
        # Energy
        "energy": "oil_gas",
        "oil & gas": "oil_gas",
        # Utilities
        "utilities": "utility",
        # Industrial
        "industrials": "manufacturing",
        "aerospace & defense": "aerospace",
    }

    @classmethod
    def get_industry_key(cls, ticker: str) -> str:
        """
        Map a ticker to Damodaran industry key.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Industry key for Damodaran data
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Try sector first
            sector = info.get("sector", "").lower()
            if sector in cls.SECTOR_MAPPING:
                return cls.SECTOR_MAPPING[sector]

            # Try industry
            industry = info.get("industry", "").lower()
            for key, damodaran_key in cls.SECTOR_MAPPING.items():
                if key in industry:
                    return damodaran_key

            # Default to market
            return "market"

        except Exception:
            return "market"

    @classmethod
    def get_industry_data(cls, ticker: str) -> Dict[str, float]:
        """
        Get Damodaran industry data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with industry beta, cost of equity, WACC, etc.
        """
        industry_key = cls.get_industry_key(ticker)
        data = cls.INDUSTRY_DATA.get(industry_key, cls.INDUSTRY_DATA["market"])

        return {
            "industry": industry_key,
            "beta": data["beta"],
            "unlevered_beta": data["unlevered_beta"],
            "debt_ratio": data["debt_ratio"],
            "tax_rate": data["tax_rate"],
            "cost_of_equity": data["cost_of_equity"],
            "wacc": data["wacc"],
            "risk_free_rate": cls.RISK_FREE_RATE,
            "equity_risk_premium": cls.EQUITY_RISK_PREMIUM,
        }

    @classmethod
    def get_levered_beta(
        cls, unlevered_beta: float, debt_to_equity: float, tax_rate: float
    ) -> float:
        """
        Calculate levered beta from unlevered beta.

        Formula: βL = βU × [1 + (1 - T) × (D/E)]

        Args:
            unlevered_beta: Unlevered (asset) beta
            debt_to_equity: Debt-to-Equity ratio
            tax_rate: Corporate tax rate

        Returns:
            Levered (equity) beta
        """
        return unlevered_beta * (1 + (1 - tax_rate) * debt_to_equity)

    @classmethod
    def get_cost_of_equity(
        cls, beta: float, risk_free_rate: Optional[float] = None
    ) -> float:
        """
        Calculate cost of equity using CAPM.

        Formula: Re = Rf + β × ERP

        Args:
            beta: Levered beta
            risk_free_rate: Risk-free rate (uses Damodaran default if None)

        Returns:
            Cost of equity
        """
        rf = risk_free_rate if risk_free_rate is not None else cls.RISK_FREE_RATE
        return rf + (beta * cls.EQUITY_RISK_PREMIUM)

    @classmethod
    def get_terminal_growth(cls, ticker: str) -> float:
        """
        Get terminal growth rate based on Damodaran's methodology.

        Terminal growth should not exceed long-term GDP growth + inflation.
        Damodaran suggests:
        - US GDP long-term growth: ~2.5%
        - Inflation target: ~2%
        - Total: ~4.5% maximum

        Industry adjustments:
        - Mature, stable industries: GDP growth rate (2.5%)
        - Growing industries: GDP + moderate premium (3-3.5%)
        - High-growth industries: GDP + higher premium (3.5%)
        - Never exceed 4% (conservative for perpetuity)

        Args:
            ticker: Stock ticker

        Returns:
            Terminal growth rate (perpetual)
        """
        industry_key = cls.get_industry_key(ticker)

        # Terminal growth by industry based on Damodaran's framework
        # These represent perpetual growth rates (conservative)
        # Rule: Terminal growth ≤ GDP growth + small premium
        terminal_growth_map = {
            # High-growth tech (but mature at terminal phase)
            "software": 0.035,  # 3.5% (GDP + innovation premium)
            "semiconductor": 0.035,  # 3.5% (cyclical but growing)
            "internet": 0.035,  # 3.5% (network effects)
            "computer_services": 0.03,  # 3.0% (competitive market)
            # Consumer (mature, stable)
            "retail": 0.025,  # 2.5% (GDP growth, competitive)
            "beverage": 0.025,  # 2.5% (mature, stable)
            "food_processing": 0.025,  # 2.5% (mature, stable)
            # Healthcare (aging demographics)
            "pharmaceutical": 0.03,  # 3.0% (GDP + demographics)
            "healthcare": 0.03,  # 3.0% (GDP + demographics)
            "biotechnology": 0.035,  # 3.5% (innovation premium)
            # Financials (GDP linked)
            "bank": 0.025,  # 2.5% (GDP growth)
            "insurance": 0.025,  # 2.5% (GDP growth)
            # Energy & Utilities (very mature)
            "oil_gas": 0.02,  # 2.0% (below GDP, energy transition)
            "utility": 0.02,  # 2.0% (regulated, stable)
            # Industrial (GDP linked)
            "manufacturing": 0.025,  # 2.5% (GDP growth)
            "aerospace": 0.025,  # 2.5% (GDP growth)
            # Market average
            "market": 0.025,  # 2.5% (US GDP long-term)
        }

        return terminal_growth_map.get(industry_key, 0.025)
