"""Company database with S&P 500 companies and metadata."""

from typing import List, Dict, Optional
import pandas as pd


# Top S&P 500 companies by market cap with sectors
SP500_COMPANIES = [
    # Technology
    {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
    {"ticker": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
    {"ticker": "GOOGL", "name": "Alphabet Inc. (Google)", "sector": "Technology"},
    {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Technology"},
    {
        "ticker": "META",
        "name": "Meta Platforms Inc. (Facebook)",
        "sector": "Technology",
    },
    {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Automotive/Technology"},
    {"ticker": "AVGO", "name": "Broadcom Inc.", "sector": "Technology"},
    {"ticker": "ORCL", "name": "Oracle Corporation", "sector": "Technology"},
    {"ticker": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
    {"ticker": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
    {"ticker": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"ticker": "INTC", "name": "Intel Corporation", "sector": "Technology"},
    {"ticker": "IBM", "name": "IBM", "sector": "Technology"},
    # Financial Services
    {
        "ticker": "BRK.B",
        "name": "Berkshire Hathaway Inc.",
        "sector": "Financial Services",
    },
    {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services"},
    {"ticker": "V", "name": "Visa Inc.", "sector": "Financial Services"},
    {"ticker": "MA", "name": "Mastercard Inc.", "sector": "Financial Services"},
    {"ticker": "BAC", "name": "Bank of America Corp.", "sector": "Financial Services"},
    {"ticker": "WFC", "name": "Wells Fargo & Company", "sector": "Financial Services"},
    {
        "ticker": "GS",
        "name": "Goldman Sachs Group Inc.",
        "sector": "Financial Services",
    },
    {"ticker": "MS", "name": "Morgan Stanley", "sector": "Financial Services"},
    {"ticker": "BLK", "name": "BlackRock Inc.", "sector": "Financial Services"},
    {"ticker": "C", "name": "Citigroup Inc.", "sector": "Financial Services"},
    # Healthcare
    {"ticker": "LLY", "name": "Eli Lilly and Company", "sector": "Healthcare"},
    {"ticker": "UNH", "name": "UnitedHealth Group Inc.", "sector": "Healthcare"},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare"},
    {"ticker": "ABBV", "name": "AbbVie Inc.", "sector": "Healthcare"},
    {"ticker": "MRK", "name": "Merck & Co. Inc.", "sector": "Healthcare"},
    {"ticker": "PFE", "name": "Pfizer Inc.", "sector": "Healthcare"},
    {"ticker": "TMO", "name": "Thermo Fisher Scientific", "sector": "Healthcare"},
    {"ticker": "ABT", "name": "Abbott Laboratories", "sector": "Healthcare"},
    {"ticker": "DHR", "name": "Danaher Corporation", "sector": "Healthcare"},
    {"ticker": "CVS", "name": "CVS Health Corporation", "sector": "Healthcare"},
    # Consumer
    {"ticker": "WMT", "name": "Walmart Inc.", "sector": "Consumer/Retail"},
    {"ticker": "HD", "name": "Home Depot Inc.", "sector": "Consumer/Retail"},
    {"ticker": "PG", "name": "Procter & Gamble Co.", "sector": "Consumer Goods"},
    {"ticker": "KO", "name": "Coca-Cola Company", "sector": "Consumer Goods"},
    {"ticker": "PEP", "name": "PepsiCo Inc.", "sector": "Consumer Goods"},
    {"ticker": "COST", "name": "Costco Wholesale Corp.", "sector": "Consumer/Retail"},
    {
        "ticker": "MCD",
        "name": "McDonald's Corporation",
        "sector": "Consumer/Restaurants",
    },
    {"ticker": "NKE", "name": "Nike Inc.", "sector": "Consumer Goods"},
    {
        "ticker": "SBUX",
        "name": "Starbucks Corporation",
        "sector": "Consumer/Restaurants",
    },
    {"ticker": "TGT", "name": "Target Corporation", "sector": "Consumer/Retail"},
    # Communication Services
    {"ticker": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services"},
    {
        "ticker": "DIS",
        "name": "Walt Disney Company",
        "sector": "Communication Services",
    },
    {
        "ticker": "CMCSA",
        "name": "Comcast Corporation",
        "sector": "Communication Services",
    },
    {"ticker": "T", "name": "AT&T Inc.", "sector": "Communication Services"},
    {
        "ticker": "VZ",
        "name": "Verizon Communications",
        "sector": "Communication Services",
    },
    # Industrial
    {"ticker": "BA", "name": "Boeing Company", "sector": "Industrial/Aerospace"},
    {"ticker": "CAT", "name": "Caterpillar Inc.", "sector": "Industrial"},
    {"ticker": "GE", "name": "General Electric Company", "sector": "Industrial"},
    {
        "ticker": "UPS",
        "name": "United Parcel Service",
        "sector": "Industrial/Logistics",
    },
    {"ticker": "HON", "name": "Honeywell International", "sector": "Industrial"},
    # Energy
    {"ticker": "XOM", "name": "Exxon Mobil Corporation", "sector": "Energy"},
    {"ticker": "CVX", "name": "Chevron Corporation", "sector": "Energy"},
    {"ticker": "COP", "name": "ConocoPhillips", "sector": "Energy"},
    {"ticker": "SLB", "name": "Schlumberger Limited", "sector": "Energy"},
    # Other
    {"ticker": "SPY", "name": "SPDR S&P 500 ETF", "sector": "ETF"},
]


def get_sp500_companies() -> List[Dict[str, str]]:
    """
    Get list of S&P 500 companies.

    Returns:
        List of dictionaries with ticker, name, and sector
    """
    return SP500_COMPANIES.copy()


def get_company_info(ticker: str) -> Optional[Dict[str, str]]:
    """
    Get company information by ticker.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dictionary with company info or None if not found
    """
    ticker = ticker.upper()
    for company in SP500_COMPANIES:
        if company["ticker"] == ticker:
            return company.copy()
    return None


def search_companies(query: str) -> List[Dict[str, str]]:
    """
    Search companies by ticker or name.

    Args:
        query: Search query (ticker or company name)

    Returns:
        List of matching companies
    """
    query = query.lower()
    results = []

    for company in SP500_COMPANIES:
        if query in company["ticker"].lower() or query in company["name"].lower():
            results.append(company.copy())

    return results


def get_companies_by_sector(sector: str) -> List[Dict[str, str]]:
    """
    Get all companies in a specific sector.

    Args:
        sector: Sector name

    Returns:
        List of companies in that sector
    """
    return [c for c in SP500_COMPANIES if c["sector"] == sector]


def get_all_sectors() -> List[str]:
    """
    Get list of all unique sectors.

    Returns:
        Sorted list of sector names
    """
    sectors = set(c["sector"] for c in SP500_COMPANIES)
    return sorted(list(sectors))


def get_companies_dataframe() -> pd.DataFrame:
    """
    Get companies as a pandas DataFrame.

    Returns:
        DataFrame with ticker, name, sector columns
    """
    return pd.DataFrame(SP500_COMPANIES)
