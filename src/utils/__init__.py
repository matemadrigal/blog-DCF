"""Utility functions for robust data fetching and validation."""

from .data_fetcher import (
    get_shares_outstanding,
    get_balance_sheet_data,
    get_fcf_data,
    get_current_price,
    validate_dcf_inputs,
    safe_get_float,
    safe_get_int,
)

__all__ = [
    "get_shares_outstanding",
    "get_balance_sheet_data",
    "get_fcf_data",
    "get_current_price",
    "validate_dcf_inputs",
    "safe_get_float",
    "safe_get_int",
]
