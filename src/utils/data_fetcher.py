"""
Robust data fetching utilities with exhaustive error handling.

This module provides bulletproof data extraction from multiple sources
with fallbacks, validation, and comprehensive error handling.
"""

import yfinance as yf
import pandas as pd
from typing import Optional, Tuple, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataFetchError(Exception):
    """Custom exception for data fetching errors."""

    pass


def safe_get_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert any value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    if value is None:
        return default

    try:
        # Handle pandas types
        if hasattr(value, "item"):
            value = value.item()

        # Convert to float
        result = float(value)

        # Check for NaN, inf
        if pd.isna(result) or result == float("inf") or result == float("-inf"):
            return default

        return result
    except (ValueError, TypeError, OverflowError):
        return default


def safe_get_int(value: Any, default: int = 0) -> int:
    """
    Safely convert any value to int.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Int value or default
    """
    if value is None:
        return default

    try:
        # Handle pandas types
        if hasattr(value, "item"):
            value = value.item()

        # Convert to int
        result = int(float(value))  # float first to handle "1.5e9" strings

        # Check for unreasonably large/small values
        if abs(result) > 1e15:  # Sanity check
            return default

        return result
    except (ValueError, TypeError, OverflowError):
        return default


def get_shares_outstanding(ticker: str, user_input: int = 0) -> Tuple[int, str]:
    """
    Get shares outstanding with multiple fallback methods.

    Priority:
    1. User manual input (if > 0)
    2. Yahoo Finance info.sharesOutstanding
    3. Yahoo Finance info.impliedSharesOutstanding
    4. Calculate from market cap and price
    5. Balance sheet common stock outstanding

    Args:
        ticker: Stock ticker symbol
        user_input: Manual user input (0 = fetch automatically)

    Returns:
        Tuple of (shares_outstanding, data_source)
    """
    # Priority 1: User manual input
    if user_input > 0:
        return user_input, "Manual"

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Priority 2: Direct from info
        shares = safe_get_int(info.get("sharesOutstanding"))
        if shares > 0:
            return shares, "Yahoo Finance (sharesOutstanding)"

        # Priority 3: Implied shares
        shares = safe_get_int(info.get("impliedSharesOutstanding"))
        if shares > 0:
            return shares, "Yahoo Finance (implied)"

        # Priority 4: Calculate from market cap and price
        market_cap = safe_get_float(info.get("marketCap"))
        current_price = safe_get_float(info.get("currentPrice"))

        if market_cap > 0 and current_price > 0:
            shares = int(market_cap / current_price)
            if shares > 0:
                return shares, "Calculated (market cap / price)"

        # Priority 5: From balance sheet
        try:
            balance_sheet = stock.balance_sheet
            if not balance_sheet.empty:
                col = balance_sheet.columns[0]  # Most recent
                for idx in balance_sheet.index:
                    name = str(idx).lower()
                    if "common stock shares outstanding" in name or (
                        "shares outstanding" in name
                    ):
                        val = balance_sheet.loc[idx, col]
                        shares = safe_get_int(val)
                        if shares > 0:
                            return shares, "Balance Sheet"
        except Exception as e:
            logger.warning(f"Could not read balance sheet for {ticker}: {e}")

        # No shares found
        return 0, "Not found"

    except Exception as e:
        logger.error(f"Error fetching shares for {ticker}: {e}")
        return 0, f"Error: {str(e)}"


def get_balance_sheet_data(
    ticker: str, user_cash: Optional[float] = None, user_debt: Optional[float] = None
) -> Tuple[float, float, Dict[str, str]]:
    """
    Get balance sheet data with fallbacks and validation.

    Args:
        ticker: Stock ticker
        user_cash: Manual cash input (None = fetch automatically)
        user_debt: Manual debt input (None = fetch automatically)

    Returns:
        Tuple of (cash, total_debt, sources_dict)
    """
    sources = {"cash": "Not found", "debt": "Not found"}

    # Priority 1: Use manual inputs if provided
    if user_cash is not None and user_cash >= 0:
        cash = user_cash
        sources["cash"] = "Manual"
    else:
        cash = None

    if user_debt is not None and user_debt >= 0:
        total_debt = user_debt
        sources["debt"] = "Manual"
    else:
        total_debt = None

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        balance_sheet = stock.balance_sheet

        # Fetch cash if not manually provided
        if cash is None:
            # Try balance sheet first
            if not balance_sheet.empty:
                col = balance_sheet.columns[0]
                for idx in balance_sheet.index:
                    name = str(idx).lower()
                    if "cash and cash equivalents" in name or (
                        "cash" in name and "short" in name
                    ):
                        val = balance_sheet.loc[idx, col]
                        cash_val = safe_get_float(val)
                        if cash_val > 0:
                            cash = cash_val
                            sources["cash"] = "Balance Sheet"
                            break

            # Fallback to info dict
            if cash is None:
                cash = safe_get_float(info.get("totalCash"))
                if cash > 0:
                    sources["cash"] = "Yahoo Finance (totalCash)"
                else:
                    cash = safe_get_float(info.get("cash"))
                    if cash > 0:
                        sources["cash"] = "Yahoo Finance (cash)"
                    else:
                        cash = 0.0
                        sources["cash"] = "Not found (defaulted to 0)"

        # Fetch debt if not manually provided
        if total_debt is None:
            # Try balance sheet first
            if not balance_sheet.empty:
                col = balance_sheet.columns[0]
                for idx in balance_sheet.index:
                    name = str(idx).lower()
                    if "total debt" in name:
                        val = balance_sheet.loc[idx, col]
                        debt_val = safe_get_float(val)
                        if debt_val > 0:
                            total_debt = debt_val
                            sources["debt"] = "Balance Sheet (total debt)"
                            break
                    elif "long term debt" in name or "long-term debt" in name:
                        val = balance_sheet.loc[idx, col]
                        debt_val = safe_get_float(val)
                        if debt_val > 0 and total_debt is None:
                            total_debt = debt_val
                            sources["debt"] = "Balance Sheet (long-term debt)"

            # Fallback to info dict
            if total_debt is None:
                total_debt = safe_get_float(info.get("totalDebt"))
                if total_debt > 0:
                    sources["debt"] = "Yahoo Finance (totalDebt)"
                else:
                    total_debt = safe_get_float(info.get("longTermDebt"))
                    if total_debt > 0:
                        sources["debt"] = "Yahoo Finance (longTermDebt)"
                    else:
                        total_debt = 0.0
                        sources["debt"] = "Not found (defaulted to 0)"

        return cash, total_debt, sources

    except Exception as e:
        logger.error(f"Error fetching balance sheet for {ticker}: {e}")
        # Return safe defaults
        cash = cash if cash is not None else 0.0
        total_debt = total_debt if total_debt is not None else 0.0
        sources["error"] = str(e)
        return cash, total_debt, sources


def get_fcf_data(
    ticker: str, max_years: int = 5
) -> Tuple[float, List[float], Dict[str, Any]]:
    """
    Get Free Cash Flow data with robust error handling.

    Priority:
    1. Direct "Free Cash Flow" from Yahoo Finance (most accurate)
    2. Calculate: Operating Cash Flow - Purchase of PPE (operational CAPEX only)
    3. Fallback: Operating Cash Flow - |Capital Expenditure| (includes acquisitions)

    Args:
        ticker: Stock ticker
        max_years: Maximum years of historical data to fetch

    Returns:
        Tuple of (base_fcf, historical_fcf_list, metadata_dict)
    """
    metadata = {
        "success": False,
        "years_found": 0,
        "data_source": "None",
        "errors": [],
    }

    try:
        stock = yf.Ticker(ticker)
        cashflow = stock.cashflow

        if cashflow.empty:
            metadata["errors"].append("Cash flow statement is empty")
            return 0.0, [], metadata

        historical_fcf = []

        # Get up to max_years of historical data
        cols = list(cashflow.columns)[:max_years]

        for i, col in enumerate(cols):
            fcf = None
            operating_cf = None
            ppe_capex = None
            total_capex = None

            for idx in cashflow.index:
                name = str(idx).lower()

                # Priority 1: Direct Free Cash Flow (Yahoo's calculation)
                if "free cash flow" == name and fcf is None:
                    val = cashflow.loc[idx, col]
                    fcf = safe_get_float(val)

                # Priority 2: Operating Cash Flow
                if "operating cash flow" in name and operating_cf is None:
                    val = cashflow.loc[idx, col]
                    operating_cf = safe_get_float(val)

                # Priority 3a: Purchase of PPE (operational CAPEX only - preferred)
                if (
                    "purchase of ppe" in name or "net ppe purchase" in name
                ) and ppe_capex is None:
                    val = cashflow.loc[idx, col]
                    ppe_capex = safe_get_float(val)

                # Priority 3b: Total Capital Expenditure (includes acquisitions - fallback)
                if "capital expenditure" in name and total_capex is None:
                    val = cashflow.loc[idx, col]
                    total_capex = safe_get_float(val)

            # Use FCF in order of priority
            if operating_cf is not None and ppe_capex is not None:
                # Priority 1: OCF - PPE CAPEX (operational only, excludes M&A) - PREFERRED
                calculated_fcf = operating_cf - abs(ppe_capex)
                historical_fcf.append(calculated_fcf)
                if i == 0:
                    metadata["data_source"] = "Operating CF - Purchase of PPE"
            elif fcf is not None and fcf != 0:
                # Priority 2: Use direct FCF from Yahoo (may include M&A)
                historical_fcf.append(fcf)
                if i == 0:
                    metadata["data_source"] = "Direct Free Cash Flow (Yahoo)"
                    metadata["errors"].append(
                        "Using Yahoo's FCF which may include M&A investments"
                    )
            elif operating_cf is not None and total_capex is not None:
                # Priority 3: OCF - Total CAPEX (includes acquisitions)
                calculated_fcf = operating_cf - abs(total_capex)
                historical_fcf.append(calculated_fcf)
                if i == 0:
                    metadata["data_source"] = "Operating CF - Capital Expenditure"
                    metadata["errors"].append(
                        "Using total CAPEX (includes M&A); FCF may be understated"
                    )
            elif operating_cf is not None:
                # Last resort: Use operating CF (very conservative)
                historical_fcf.append(operating_cf)
                if i == 0:
                    metadata["errors"].append(
                        "CAPEX not found, using Operating CF directly"
                    )
                    metadata["data_source"] = "Operating CF only (no CAPEX adjustment)"

        # Most recent year is first
        base_fcf = historical_fcf[0] if historical_fcf else 0.0

        metadata["success"] = len(historical_fcf) > 0
        metadata["years_found"] = len(historical_fcf)

        return base_fcf, historical_fcf, metadata

    except Exception as e:
        logger.error(f"Error fetching FCF for {ticker}: {e}")
        metadata["errors"].append(f"Exception: {str(e)}")
        return 0.0, [], metadata


def get_current_price(ticker: str) -> Tuple[float, str]:
    """
    Get current stock price with fallbacks.

    Args:
        ticker: Stock ticker

    Returns:
        Tuple of (price, data_source)
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Priority 1: Current price
        price = safe_get_float(info.get("currentPrice"))
        if price > 0:
            return price, "Yahoo Finance (currentPrice)"

        # Priority 2: Regular market price
        price = safe_get_float(info.get("regularMarketPrice"))
        if price > 0:
            return price, "Yahoo Finance (regularMarketPrice)"

        # Priority 3: Previous close
        price = safe_get_float(info.get("previousClose"))
        if price > 0:
            return price, "Yahoo Finance (previousClose)"

        # Priority 4: Try to fetch from history
        hist = stock.history(period="1d")
        if not hist.empty and "Close" in hist.columns:
            price = safe_get_float(hist["Close"].iloc[-1])
            if price > 0:
                return price, "Yahoo Finance (history)"

        return 0.0, "Not found"

    except Exception as e:
        logger.error(f"Error fetching price for {ticker}: {e}")
        return 0.0, f"Error: {str(e)}"


def validate_dcf_inputs(
    base_fcf: float,
    wacc: float,
    terminal_growth: float,
    shares: int,
    cash: float,
    debt: float,
    sector: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate all DCF inputs before calculation.

    Args:
        base_fcf: Base year FCF
        wacc: Weighted average cost of capital
        terminal_growth: Terminal growth rate
        shares: Shares outstanding
        cash: Cash
        debt: Total debt
        sector: Company sector (to handle special cases like financials)

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    warnings = []

    # Financial companies (banks, insurance, REITs) use different metrics
    # DCF with FCF doesn't apply well - should use DDM or P/B instead
    financial_sectors = [
        "financial services",
        "banks",
        "insurance",
        "real estate",
        "reit",
        "capital markets",
    ]

    is_financial = False
    if sector:
        sector_lower = sector.lower()
        is_financial = any(fs in sector_lower for fs in financial_sectors)

    # Validate base FCF
    if base_fcf == 0:
        if is_financial:
            warnings.append(
                "⚠️  Empresa financiera: FCF tradicional no aplica bien. Considera usar DDM o P/B"
            )
        else:
            errors.append("No se pudo obtener FCF - los datos pueden estar incompletos")
    elif base_fcf < 0:
        if is_financial:
            # For financial companies, negative FCF is often normal
            warnings.append(
                f"⚠️  FCF negativo (${base_fcf/1e9:.2f}B) es normal para empresas financieras. "
                "El modelo DCF tradicional no es ideal para bancos/aseguradoras. "
                "Recomendación: usar Dividend Discount Model (DDM) o Price-to-Book"
            )
        else:
            errors.append(
                f"FCF negativo (${base_fcf/1e9:.2f}B) - la empresa está quemando efectivo"
            )

    # Validate WACC
    if wacc <= 0:
        errors.append(f"WACC must be positive (current: {wacc:.2%})")
    elif wacc > 0.5:
        errors.append(f"WACC seems unreasonably high ({wacc:.2%}) - please verify")

    # Validate terminal growth
    if terminal_growth >= wacc:
        errors.append(
            f"Terminal growth ({terminal_growth:.2%}) must be less than WACC ({wacc:.2%})"
        )
    elif terminal_growth < -0.05:
        errors.append(
            f"Terminal growth ({terminal_growth:.2%}) is very negative - is this correct?"
        )
    elif terminal_growth > 0.10:
        errors.append(
            f"Terminal growth ({terminal_growth:.2%}) is very high - perpetual growth >10% is unrealistic"
        )

    # Validate shares
    if shares <= 0:
        errors.append("Shares outstanding must be greater than zero")
    elif shares < 1000:
        errors.append(
            f"Shares outstanding ({shares:,}) seems too low - did you enter in millions/billions?"
        )

    # Validate cash (warning only)
    if cash < 0:
        warnings.append(f"Cash is negative (${cash/1e9:.2f}B) - please verify")

    # Validate debt (warning only)
    if debt < 0:
        warnings.append(f"Debt is negative (${debt/1e9:.2f}B) - please verify")

    # Combine errors and warnings
    all_messages = errors + warnings

    # Valid if no errors (warnings are OK)
    is_valid = len(errors) == 0

    return is_valid, all_messages
