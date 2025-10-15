"""
Data fetching utilities for Dividend Discount Model (DDM).

Fetches dividend history, payout ratios, ROE, and other metrics
needed for DDM valuation of financial institutions and dividend-paying companies.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import logging

logger = logging.getLogger(__name__)


def safe_get_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None:
        return default

    try:
        if hasattr(value, "item"):
            value = value.item()

        result = float(value)

        if pd.isna(result) or result == float("inf") or result == float("-inf"):
            return default

        return result
    except (ValueError, TypeError, OverflowError):
        return default


def get_dividend_data(
    ticker: str, max_years: int = 5
) -> Tuple[float, List[float], Dict[str, Any]]:
    """
    Get dividend per share data with historical values.

    Args:
        ticker: Stock ticker
        max_years: Maximum years of historical data

    Returns:
        Tuple of (current_dps, historical_dps_list, metadata)
    """
    metadata = {
        "success": False,
        "years_found": 0,
        "data_source": "None",
        "errors": [],
        "warnings": [],
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Method 1: Try to get from dividends history (most accurate)
        try:
            dividends = stock.dividends
            if not dividends.empty:
                # Get annual dividends by summing quarterly/monthly dividends per year
                dividends_df = pd.DataFrame({"dividends": dividends})
                dividends_df["year"] = dividends_df.index.year

                annual_dividends = (
                    dividends_df.groupby("year")["dividends"]
                    .sum()
                    .sort_index(ascending=False)
                )

                historical_dps = annual_dividends.head(max_years).tolist()

                if historical_dps:
                    current_dps = historical_dps[0]
                    metadata["success"] = True
                    metadata["years_found"] = len(historical_dps)
                    metadata["data_source"] = "Dividends History (Yahoo Finance)"
                    return current_dps, historical_dps, metadata

        except Exception as e:
            metadata["warnings"].append(f"Could not fetch dividend history: {e}")

        # Method 2: Try info dict
        trailing_annual_dividend = safe_get_float(
            info.get("trailingAnnualDividendRate")
        )
        if trailing_annual_dividend > 0:
            metadata["success"] = True
            metadata["years_found"] = 1
            metadata["data_source"] = "Yahoo Finance (trailingAnnualDividendRate)"
            return trailing_annual_dividend, [trailing_annual_dividend], metadata

        # Method 3: Calculate from dividend rate
        dividend_rate = safe_get_float(info.get("dividendRate"))
        if dividend_rate > 0:
            metadata["success"] = True
            metadata["years_found"] = 1
            metadata["data_source"] = "Yahoo Finance (dividendRate)"
            metadata["warnings"].append("Using dividendRate - may need annualization")
            return dividend_rate, [dividend_rate], metadata

        # No dividend data found
        metadata["errors"].append(
            "No dividend data available - company may not pay dividends"
        )
        return 0.0, [], metadata

    except Exception as e:
        logger.error(f"Error fetching dividends for {ticker}: {e}")
        metadata["errors"].append(f"Exception: {str(e)}")
        return 0.0, [], metadata


def calculate_dividend_growth_rate(
    historical_dividends: List[float], method: str = "cagr"
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate dividend growth rate from historical data.

    Methods:
        - cagr: Compound Annual Growth Rate (geometric mean)
        - arithmetic: Simple arithmetic average of year-over-year growth
        - regression: Linear regression on log(dividends)

    Args:
        historical_dividends: List of annual dividends (most recent first)
        method: Calculation method ('cagr', 'arithmetic', 'regression')

    Returns:
        Tuple of (growth_rate, calculation_details)
    """
    details = {
        "method": method,
        "years_of_data": len(historical_dividends),
        "warnings": [],
        "errors": [],
    }

    if len(historical_dividends) < 2:
        details["errors"].append("Need at least 2 years of data to calculate growth")
        return 0.0, details

    # Remove zeros and negatives (invalid for growth calculation)
    valid_dividends = [d for d in historical_dividends if d > 0]

    if len(valid_dividends) < 2:
        details["errors"].append(
            "Need at least 2 positive dividends to calculate growth"
        )
        return 0.0, details

    # Reverse to chronological order (oldest to newest)
    dividends_chronological = valid_dividends[::-1]

    try:
        if method == "cagr":
            # CAGR = (Ending Value / Beginning Value)^(1/n) - 1
            beginning_value = dividends_chronological[0]
            ending_value = dividends_chronological[-1]
            n_years = len(dividends_chronological) - 1

            if beginning_value <= 0:
                details["errors"].append("Beginning dividend must be positive for CAGR")
                return 0.0, details

            growth_rate = (ending_value / beginning_value) ** (1 / n_years) - 1

            details["calculation"] = {
                "beginning_dividend": beginning_value,
                "ending_dividend": ending_value,
                "years": n_years,
                "formula": f"({ending_value:.2f} / {beginning_value:.2f})^(1/{n_years}) - 1",
            }

        elif method == "arithmetic":
            # Calculate year-over-year growth rates and average them
            yoy_growth_rates = []

            for i in range(1, len(dividends_chronological)):
                prev_div = dividends_chronological[i - 1]
                curr_div = dividends_chronological[i]

                if prev_div > 0:
                    yoy_growth = (curr_div - prev_div) / prev_div
                    yoy_growth_rates.append(yoy_growth)

            if not yoy_growth_rates:
                details["errors"].append(
                    "Could not calculate any year-over-year growth rates"
                )
                return 0.0, details

            growth_rate = np.mean(yoy_growth_rates)

            details["calculation"] = {
                "yoy_growth_rates": yoy_growth_rates,
                "average": growth_rate,
            }

        elif method == "regression":
            # Linear regression on log(dividends)
            # log(D_t) = a + b*t => growth rate ≈ b
            years = np.arange(len(dividends_chronological))
            log_dividends = np.log(dividends_chronological)

            # Fit linear regression
            slope, intercept = np.polyfit(years, log_dividends, 1)
            growth_rate = np.exp(slope) - 1  # Convert log growth to percentage

            details["calculation"] = {
                "method": "Linear regression on log(dividends)",
                "slope": slope,
                "intercept": intercept,
            }

        else:
            details["errors"].append(f"Unknown method: {method}")
            return 0.0, details

        details["growth_rate"] = growth_rate

        # Add warnings for unusual growth rates
        if growth_rate > 0.20:
            details["warnings"].append(
                f"⚠️  Very high growth rate ({growth_rate:.2%}) - may not be sustainable"
            )
        elif growth_rate < -0.10:
            details["warnings"].append(
                f"⚠️  Large negative growth rate ({growth_rate:.2%}) - company may be cutting dividends"
            )

        return growth_rate, details

    except Exception as e:
        logger.error(f"Error calculating dividend growth: {e}")
        details["errors"].append(f"Exception: {str(e)}")
        return 0.0, details


def get_payout_ratio(ticker: str) -> Tuple[float, Dict[str, Any]]:
    """
    Get dividend payout ratio.

    Formula:
        Payout Ratio = Dividends / Net Income
        Or: Dividend per Share / Earnings per Share

    Args:
        ticker: Stock ticker

    Returns:
        Tuple of (payout_ratio, metadata)
    """
    metadata = {
        "success": False,
        "data_source": "None",
        "warnings": [],
        "errors": [],
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Method 1: Direct from info
        payout_ratio = safe_get_float(info.get("payoutRatio"))
        if payout_ratio > 0:
            metadata["success"] = True
            metadata["data_source"] = "Yahoo Finance (payoutRatio)"

            # Validate payout ratio
            if payout_ratio > 1.0:
                metadata["warnings"].append(
                    f"⚠️  Payout ratio ({payout_ratio:.2%}) > 100% - company paying more than it earns"
                )
            elif payout_ratio > 0.80:
                metadata["warnings"].append(
                    f"⚠️  High payout ratio ({payout_ratio:.2%}) - limited room for dividend growth"
                )

            return payout_ratio, metadata

        # Method 2: Calculate from DPS and EPS
        trailing_annual_dividend = safe_get_float(
            info.get("trailingAnnualDividendRate")
        )
        trailing_eps = safe_get_float(info.get("trailingEps"))

        if trailing_annual_dividend > 0 and trailing_eps > 0:
            payout_ratio = trailing_annual_dividend / trailing_eps
            metadata["success"] = True
            metadata["data_source"] = "Calculated (DPS / EPS)"

            if payout_ratio > 1.0:
                metadata["warnings"].append(
                    f"⚠️  Payout ratio ({payout_ratio:.2%}) > 100% - unsustainable"
                )

            return payout_ratio, metadata

        # Method 3: Try to get from financials
        try:
            # Get income statement
            financials = stock.financials

            if not financials.empty:
                col = financials.columns[0]  # Most recent year

                # Find Net Income
                net_income = None
                for idx in financials.index:
                    name = str(idx).lower()
                    if "net income" in name:
                        net_income = safe_get_float(financials.loc[idx, col])
                        break

                # Get dividends paid from cash flow statement
                cashflow = stock.cashflow
                if not cashflow.empty:
                    cf_col = cashflow.columns[0]
                    for idx in cashflow.index:
                        name = str(idx).lower()
                        if "dividends paid" in name or "cash dividends paid" in name:
                            dividends_paid = abs(
                                safe_get_float(cashflow.loc[idx, cf_col])
                            )

                            if net_income and net_income > 0 and dividends_paid > 0:
                                payout_ratio = dividends_paid / net_income
                                metadata["success"] = True
                                metadata["data_source"] = "Calculated from financials"

                                if payout_ratio > 1.0:
                                    metadata["warnings"].append(
                                        f"⚠️  Payout ratio ({payout_ratio:.2%}) > 100%"
                                    )

                                return payout_ratio, metadata

        except Exception as e:
            metadata["warnings"].append(f"Could not calculate from financials: {e}")

        # No payout ratio found - estimate conservatively
        metadata["errors"].append(
            "Could not determine payout ratio - company may not pay dividends"
        )
        return 0.0, metadata

    except Exception as e:
        logger.error(f"Error fetching payout ratio for {ticker}: {e}")
        metadata["errors"].append(f"Exception: {str(e)}")
        return 0.0, metadata


def get_roe(ticker: str) -> Tuple[float, Dict[str, Any]]:
    """
    Get Return on Equity (ROE).

    Formula:
        ROE = Net Income / Shareholders' Equity

    Args:
        ticker: Stock ticker

    Returns:
        Tuple of (roe, metadata)
    """
    metadata = {
        "success": False,
        "data_source": "None",
        "warnings": [],
        "errors": [],
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Method 1: Direct from info
        roe = safe_get_float(info.get("returnOnEquity"))
        if roe != 0:
            metadata["success"] = True
            metadata["data_source"] = "Yahoo Finance (returnOnEquity)"

            # Validate ROE
            if roe < 0:
                metadata["warnings"].append(
                    f"⚠️  Negative ROE ({roe:.2%}) - company may be unprofitable"
                )
            elif roe > 0.50:
                metadata["warnings"].append(
                    f"⚠️  Very high ROE ({roe:.2%}) - verify calculation or high leverage"
                )

            return roe, metadata

        # Method 2: Calculate from financials
        try:
            financials = stock.financials
            balance_sheet = stock.balance_sheet

            if not financials.empty and not balance_sheet.empty:
                fin_col = financials.columns[0]
                bs_col = balance_sheet.columns[0]

                # Get Net Income
                net_income = None
                for idx in financials.index:
                    name = str(idx).lower()
                    if "net income" in name:
                        net_income = safe_get_float(financials.loc[idx, fin_col])
                        break

                # Get Shareholders' Equity
                shareholders_equity = None
                for idx in balance_sheet.index:
                    name = str(idx).lower()
                    if (
                        "stockholders equity" in name
                        or "shareholders equity" in name
                        or "total equity" in name
                    ):
                        shareholders_equity = safe_get_float(
                            balance_sheet.loc[idx, bs_col]
                        )
                        break

                if (
                    net_income is not None
                    and shareholders_equity is not None
                    and shareholders_equity != 0
                ):
                    roe = net_income / shareholders_equity
                    metadata["success"] = True
                    metadata["data_source"] = "Calculated (Net Income / Equity)"

                    if roe < 0:
                        metadata["warnings"].append(f"⚠️  Negative ROE ({roe:.2%})")

                    return roe, metadata

        except Exception as e:
            metadata["warnings"].append(f"Could not calculate from financials: {e}")

        # No ROE found
        metadata["errors"].append("Could not determine ROE")
        return 0.0, metadata

    except Exception as e:
        logger.error(f"Error fetching ROE for {ticker}: {e}")
        metadata["errors"].append(f"Exception: {str(e)}")
        return 0.0, metadata


def calculate_cost_of_equity_capm(
    risk_free_rate: float, beta: float, market_risk_premium: float
) -> float:
    """
    Calculate cost of equity using CAPM.

    Formula (CFA Institute):
        r_e = R_f + β × (R_m - R_f)

        where:
            r_e = Cost of equity (required return)
            R_f = Risk-free rate (typically 10-year Treasury)
            β = Beta (systematic risk)
            (R_m - R_f) = Market risk premium (typically 5-7%)

    Args:
        risk_free_rate: Risk-free rate (as decimal, e.g., 0.04 for 4%)
        beta: Stock beta
        market_risk_premium: Market risk premium (as decimal, e.g., 0.06 for 6%)

    Returns:
        Cost of equity (as decimal)
    """
    return risk_free_rate + beta * market_risk_premium


def get_cost_of_equity(
    ticker: str,
    risk_free_rate: float = 0.04,
    market_risk_premium: float = 0.06,
) -> Tuple[float, Dict[str, Any]]:
    """
    Get cost of equity for a company using CAPM.

    FASE 2 ADJUSTMENT: For financial companies (banks), apply beta adjustment
    if company beta is significantly higher than industry average to avoid
    over-penalizing stable banks with temporarily elevated betas.

    Args:
        ticker: Stock ticker
        risk_free_rate: Risk-free rate (default: 4%)
        market_risk_premium: Market risk premium (default: 6%)

    Returns:
        Tuple of (cost_of_equity, metadata)
    """
    metadata = {
        "success": False,
        "method": "CAPM",
        "formula": "r_e = R_f + β × MRP",
        "inputs": {
            "risk_free_rate": risk_free_rate,
            "market_risk_premium": market_risk_premium,
        },
        "warnings": [],
        "errors": [],
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get beta
        beta = safe_get_float(info.get("beta"))
        original_beta = beta

        if beta == 0:
            metadata["errors"].append("Beta not available")
            # Use default beta of 1.0 (market risk)
            beta = 1.0
            metadata["warnings"].append("⚠️  Using default beta = 1.0")

        # FASE 2: Adjust beta for financial companies with high betas
        # Rationale: Bank betas can be temporarily elevated due to market stress,
        # but large banks are typically stable businesses with betas ~1.0-1.2
        sector = info.get("sector", "")
        industry = info.get("industry", "")

        is_financial = any(
            keyword in sector.lower() or keyword in industry.lower()
            for keyword in ["financial", "bank", "insurance", "capital markets"]
        )

        if is_financial and beta > 1.3:
            # Beta seems too high for a financial institution
            # Apply blended approach: 60% company beta + 40% industry average (1.1)
            industry_beta = 1.1  # Typical beta for banks/financials
            adjusted_beta = 0.60 * beta + 0.40 * industry_beta

            metadata["warnings"].append(
                f"⚠️  Beta ajustado para empresa financiera: {original_beta:.2f} → {adjusted_beta:.2f}"
            )
            metadata["warnings"].append(
                "💡 Aplicado blend 60/40 con beta de industria (1.1) para evitar sobre-penalización"
            )

            beta = adjusted_beta
            metadata["inputs"]["beta_original"] = original_beta
            metadata["inputs"]["beta_adjusted"] = True
            metadata["inputs"]["beta_industry"] = industry_beta

        metadata["inputs"]["beta"] = beta

        # Calculate cost of equity using CAPM
        cost_of_equity = calculate_cost_of_equity_capm(
            risk_free_rate, beta, market_risk_premium
        )

        metadata["success"] = True
        metadata["cost_of_equity"] = cost_of_equity

        # Validate
        if cost_of_equity < 0.05:
            metadata["warnings"].append(
                f"⚠️  Low cost of equity ({cost_of_equity:.2%}) - verify inputs"
            )
        elif cost_of_equity > 0.25:
            metadata["warnings"].append(
                f"⚠️  High cost of equity ({cost_of_equity:.2%}) - high risk company"
            )

        return cost_of_equity, metadata

    except Exception as e:
        logger.error(f"Error calculating cost of equity for {ticker}: {e}")
        metadata["errors"].append(f"Exception: {str(e)}")
        # Return reasonable default (10%)
        return 0.10, metadata
