"""
[AuditFix] IFRS 16 Lease Adjustments (Optional)

IFRS 16 (effective 2019) brought operating leases onto the balance sheet.
This module provides optional adjustments to separate lease liabilities from debt.

WHY THIS MATTERS:
- Pre-IFRS 16: Operating leases were off-balance-sheet (only rental expense shown)
- Post-IFRS 16: Operating leases appear as Right-of-Use (ROU) assets + Lease liabilities
- Problem: Lease liabilities are NOT financial debt (no credit/default risk)
- Impact: Inflates D/E ratios, distorts WACC, makes companies look more levered

WHEN TO USE THIS ADJUSTMENT:
1. Comparing pre-2019 vs post-2019 financials
2. Valuing asset-light businesses (retail, airlines, restaurants)
3. When lease liabilities > 20% of total debt
4. For cross-industry comparisons (some industries lease-heavy)

WHEN NOT TO USE:
1. Companies with minimal leases (tech, financials)
2. When you want to include leases as financial obligations (conservative approach)
3. Historical analysis pre-2019 (no IFRS 16 impact)

DAMODARAN'S APPROACH:
- Separate operating leases from financial debt
- Use lower discount rate for leases (reflects rental cost, not credit risk)
- Adjust WACC to reflect true financial leverage
"""

from typing import Tuple, Optional, Dict
import yfinance as yf


def estimate_operating_lease_liability(
    ticker: str,
    use_disclosed_value: bool = True,
) -> Tuple[float, Dict[str, any]]:
    """
    Estimate operating lease liability under IFRS 16.

    [AuditFix] Separates operating leases from financial debt for accurate leverage.

    Method 1 (use_disclosed_value=True, PREFERRED):
        Try to get disclosed operating lease liability from balance sheet
        Look for: "Operating Lease Liabilities" or similar line items

    Method 2 (use_disclosed_value=False, FALLBACK):
        Estimate from operating lease expense (if available)
        Capitalize using: PV = Annual Lease Expense / Discount Rate
        Discount rate typically 4-6% (cost of borrowing for leases)

    Args:
        ticker: Stock ticker
        use_disclosed_value: Try to get disclosed value first (recommended)

    Returns:
        Tuple of (operating_lease_liability, metadata_dict)

    Example:
        >>> lease_liability, details = estimate_operating_lease_liability("SBUX")
        >>> print(f"Starbucks operating leases: ${lease_liability/1e9:.2f}B")
        Starbucks operating leases: $9.2B
    """
    metadata = {
        "method": None,
        "source": None,
        "confidence": "unknown",
        "warnings": [],
    }

    try:
        stock = yf.Ticker(ticker)

        # Method 1: Try to get disclosed operating lease liability
        if use_disclosed_value:
            # Try balance sheet
            bs = stock.balance_sheet
            if bs is not None and not bs.empty:
                # Common line item names for operating lease liabilities
                lease_items = [
                    "Operating Lease Liabilities",
                    "Operating Lease Liability",
                    "Lease Liabilities",
                    "Operating Leases",
                ]

                for item in lease_items:
                    if item in bs.index:
                        lease_value = bs.loc[item].iloc[0]
                        if lease_value > 0:
                            metadata["method"] = "Disclosed (Balance Sheet)"
                            metadata["source"] = item
                            metadata["confidence"] = "high"
                            return float(lease_value), metadata

        # Method 2: Estimate from operating lease expense (fallback)
        # Try income statement for lease expense
        income_stmt = stock.income_stmt
        if income_stmt is not None and not income_stmt.empty:
            # Common line items for lease/rental expense
            expense_items = [
                "Operating Lease Expense",
                "Rent Expense",
                "Lease Expense",
            ]

            for item in expense_items:
                if item in income_stmt.index:
                    annual_lease_expense = income_stmt.loc[item].iloc[0]

                    # [BugFix #5] Use finite annuity formula, not perpetuity
                    # Leases are NOT perpetual - typically 3-10 years
                    # Formula: PV = PMT × [1 - (1+r)^-n] / r
                    discount_rate = 0.05
                    average_lease_term = 7  # Conservative average (retail/commercial leases)

                    # Annuity present value factor
                    pv_factor = (1 - (1 + discount_rate) ** -average_lease_term) / discount_rate

                    # Estimated liability using finite annuity
                    estimated_liability = annual_lease_expense * pv_factor

                    metadata["method"] = "Estimated (Finite Annuity)"
                    metadata["source"] = item
                    metadata["confidence"] = "medium"
                    metadata["annual_lease_expense"] = float(annual_lease_expense)
                    metadata["discount_rate_used"] = discount_rate
                    metadata["lease_term_assumed"] = average_lease_term
                    metadata["pv_factor"] = pv_factor
                    metadata["warnings"].append(
                        "Estimated from expense - less accurate than disclosed liability"
                    )

                    return float(estimated_liability), metadata

        # No lease data found
        metadata["method"] = "Not Available"
        metadata["confidence"] = "none"
        metadata["warnings"].append(
            "No operating lease data found - assuming zero or immaterial"
        )
        return 0.0, metadata

    except Exception as e:
        metadata["method"] = "Error"
        metadata["confidence"] = "none"
        metadata["warnings"].append(f"Error fetching data: {str(e)}")
        return 0.0, metadata


def adjust_debt_for_leases(
    total_debt: float,
    operating_lease_liability: float,
    adjustment_method: str = "subtract",
) -> Tuple[float, Dict[str, any]]:
    """
    Adjust reported debt to exclude operating lease liabilities.

    [AuditFix] Removes lease liabilities from financial debt for accurate WACC.

    Methods:
    1. "subtract" (RECOMMENDED): Debt_adjusted = Total Debt - Operating Leases
        - Treats leases as non-financial obligations
        - Results in lower D/E ratio, higher WACC
        - Conservative approach

    2. "proportional": Debt_adjusted = Total Debt × (1 - Lease Ratio)
        - Smooths adjustment based on lease intensity
        - Less aggressive

    3. "none": No adjustment
        - Treats leases as financial debt
        - Most conservative for valuation

    Args:
        total_debt: Total debt including lease liabilities
        operating_lease_liability: Estimated operating lease liability
        adjustment_method: "subtract", "proportional", or "none"

    Returns:
        Tuple of (adjusted_debt, metadata_dict)

    Example:
        >>> total_debt = 50e9  # $50B total debt
        >>> lease_liability = 10e9  # $10B leases
        >>> adj_debt, details = adjust_debt_for_leases(total_debt, lease_liability)
        >>> print(f"Financial debt: ${adj_debt/1e9:.1f}B (was ${total_debt/1e9:.1f}B)")
        Financial debt: $40.0B (was $50.0B)
    """
    metadata = {
        "method": adjustment_method,
        "total_debt_original": total_debt,
        "operating_lease_liability": operating_lease_liability,
        "lease_as_pct_of_debt": 0.0,
        "adjustment_amount": 0.0,
    }

    if operating_lease_liability <= 0 or total_debt <= 0:
        # No adjustment needed
        metadata["adjustment_amount"] = 0.0
        return total_debt, metadata

    lease_pct = operating_lease_liability / total_debt
    metadata["lease_as_pct_of_debt"] = lease_pct

    if adjustment_method == "subtract":
        # Direct subtraction (most common)
        adjusted_debt = max(0, total_debt - operating_lease_liability)
        metadata["adjustment_amount"] = total_debt - adjusted_debt

    elif adjustment_method == "proportional":
        # Proportional reduction
        adjusted_debt = total_debt * (1 - lease_pct)
        metadata["adjustment_amount"] = total_debt - adjusted_debt

    elif adjustment_method == "none":
        # No adjustment
        adjusted_debt = total_debt
        metadata["adjustment_amount"] = 0.0

    else:
        raise ValueError(f"Unknown adjustment method: {adjustment_method}")

    return adjusted_debt, metadata


def get_ifrs16_adjusted_capital_structure(
    ticker: str,
    total_debt: float,
    market_cap: float,
    apply_ifrs16_adjustment: bool = False,
) -> Tuple[float, float, Dict[str, any]]:
    """
    Get IFRS 16 adjusted capital structure for WACC calculation.

    [AuditFix] Optional adjustment to remove lease liabilities from D/E ratio.

    This is the main function to use when calculating WACC with IFRS 16 adjustment.

    Args:
        ticker: Stock ticker
        total_debt: Total debt (including leases if post-2019)
        market_cap: Market capitalization
        apply_ifrs16_adjustment: Whether to apply IFRS 16 adjustment

    Returns:
        Tuple of (adjusted_debt, adjusted_d_to_e_ratio, metadata)

    Example:
        >>> adj_debt, adj_de, meta = get_ifrs16_adjusted_capital_structure(
        ...     "SBUX", total_debt=50e9, market_cap=100e9, apply_ifrs16_adjustment=True
        ... )
        >>> print(f"D/E: {meta['debt_to_equity_original']:.2f} → {adj_de:.2f}")
        D/E: 0.50 → 0.40
    """
    metadata = {
        "ifrs16_adjustment_applied": apply_ifrs16_adjustment,
        "total_debt_original": total_debt,
        "market_cap": market_cap,
        "debt_to_equity_original": total_debt / market_cap if market_cap > 0 else 0,
    }

    if not apply_ifrs16_adjustment:
        # No adjustment
        metadata["operating_lease_liability"] = 0.0
        metadata["adjusted_debt"] = total_debt
        metadata["debt_to_equity_adjusted"] = metadata["debt_to_equity_original"]
        metadata["adjustment_impact"] = "None (adjustment disabled)"

        return total_debt, metadata["debt_to_equity_original"], metadata

    # Estimate operating lease liability
    lease_liability, lease_meta = estimate_operating_lease_liability(ticker)

    # Adjust debt
    adjusted_debt, adj_meta = adjust_debt_for_leases(
        total_debt, lease_liability, adjustment_method="subtract"
    )

    adjusted_de = adjusted_debt / market_cap if market_cap > 0 else 0

    # Combine metadata
    metadata.update({
        "operating_lease_liability": lease_liability,
        "lease_estimation_method": lease_meta["method"],
        "lease_confidence": lease_meta["confidence"],
        "adjusted_debt": adjusted_debt,
        "debt_to_equity_adjusted": adjusted_de,
        "lease_as_pct_of_original_debt": lease_liability / total_debt if total_debt > 0 else 0,
        "d_to_e_change": adjusted_de - metadata["debt_to_equity_original"],
        "adjustment_impact": f"D/E reduced by {abs(adjusted_de - metadata['debt_to_equity_original']):.2%}",
        "warnings": lease_meta.get("warnings", []),
    })

    # Add interpretation
    if lease_liability > 0.20 * total_debt:
        metadata["interpretation"] = (
            f"⚠️ Leases are {lease_liability/total_debt:.1%} of total debt - "
            "adjustment significantly impacts leverage metrics"
        )
    elif lease_liability > 0:
        metadata["interpretation"] = (
            f"Leases are {lease_liability/total_debt:.1%} of total debt - "
            "minor impact on leverage"
        )
    else:
        metadata["interpretation"] = "No lease liabilities found - no adjustment made"

    return adjusted_debt, adjusted_de, metadata
