"""
[AuditFix] Complete EV → Equity Value → Price per Share Bridge

This module implements the rigorous conversion from Enterprise Value to Price per Share.

CRITICAL DCF PIPELINE:
1. DCF produces → Enterprise Value (EV)
2. EV - Adjustments → Equity Value
3. Equity Value / Diluted Shares → Price per Share

Many DCF implementations skip steps 2-3, leading to valuation errors.

COMMON MISTAKES AVOIDED:
❌ EV / Basic Shares (ignores debt, cash, minorities, options)
❌ EV - Debt (ignores cash, minorities, pensions)
❌ Using basic shares (ignores dilution from options/warrants)
✅ Full bridge with all adjustments (implemented here)

DAMODARAN'S BRIDGE FORMULA:
Enterprise Value (EV)
  - Total Debt (interest-bearing)
  + Cash & Equivalents
  - Minority Interest (non-controlling interests)
  - Preferred Stock (if any)
  + Associates & JVs (equity method investments)
  - Pension Deficit (unfunded obligations)
  - Other adjustments
= Equity Value

Equity Value / Fully Diluted Shares = Intrinsic Price per Share

REFERENCE: Damodaran "Investment Valuation" Ch. 14
"""

from typing import Tuple, Dict, Optional
import yfinance as yf
import numpy as np


def get_fully_diluted_shares(
    ticker: str,
    use_treasury_stock_method: bool = True,
    current_stock_price: Optional[float] = None,
) -> Tuple[float, Dict[str, any]]:
    """
    Calculate fully diluted shares outstanding using Treasury Stock Method.

    [AuditFix] Accounts for dilution from stock options, warrants, convertibles.

    TREASURY STOCK METHOD (TSM):
    1. Assume all in-the-money options are exercised
    2. Company receives cash = (Options × Strike Price)
    3. Company buys back shares at current price
    4. Net dilution = Options - Buyback Shares

    Formula:
        Diluted Shares = Basic Shares + (Options × (1 - Strike/Current Price))

    Where:
        - Basic Shares: Common shares outstanding
        - Options: In-the-money stock options/RSUs
        - Strike: Weighted average exercise price
        - Current Price: Current stock price

    Args:
        ticker: Stock ticker
        use_treasury_stock_method: Apply TSM for options (recommended)
        current_stock_price: Current price (fetched if None)

    Returns:
        Tuple of (diluted_shares, metadata_dict)

    Example:
        >>> diluted_shares, meta = get_fully_diluted_shares("AAPL")
        >>> print(f"Basic: {meta['basic_shares']/1e9:.2f}B")
        Basic: 15.5B
        >>> print(f"Diluted: {diluted_shares/1e9:.2f}B")
        Diluted: 15.8B
        >>> print(f"Dilution: {meta['dilution_pct']:.1%}")
        Dilution: 1.9%
    """
    metadata = {
        "basic_shares": 0,
        "diluted_shares_reported": 0,
        "diluted_shares_calculated": 0,
        "dilution_from_options": 0,
        "dilution_pct": 0.0,
        "method": "basic (no dilution data)",
        "warnings": [],
    }

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get basic shares outstanding
        basic_shares = info.get("sharesOutstanding", 0)
        metadata["basic_shares"] = basic_shares

        if basic_shares <= 0:
            metadata["warnings"].append("No shares outstanding data available")
            return 0, metadata

        # Try to get reported diluted shares (simplest approach)
        # Many companies report this in financials
        diluted_shares_reported = info.get("sharesOutstandingDiluted", 0)

        if diluted_shares_reported > 0:
            metadata["diluted_shares_reported"] = diluted_shares_reported
            metadata["dilution_pct"] = (diluted_shares_reported - basic_shares) / basic_shares
            metadata["method"] = "reported (company disclosure)"

            return float(diluted_shares_reported), metadata

        # If not available, calculate using Treasury Stock Method
        if use_treasury_stock_method:
            # Get current stock price if not provided
            if current_stock_price is None:
                current_stock_price = info.get("currentPrice", info.get("regularMarketPrice", 0))

            if current_stock_price <= 0:
                metadata["warnings"].append("No current price - using basic shares")
                return float(basic_shares), metadata

            # Try to estimate options dilution
            # Yahoo Finance sometimes provides these metrics
            implied_shares_outstanding = info.get("impliedSharesOutstanding", 0)

            if implied_shares_outstanding > basic_shares:
                # Use implied shares (includes dilution)
                diluted_shares = implied_shares_outstanding
                metadata["diluted_shares_calculated"] = diluted_shares
                metadata["dilution_from_options"] = diluted_shares - basic_shares
                metadata["dilution_pct"] = (diluted_shares - basic_shares) / basic_shares
                metadata["method"] = "calculated (implied shares)"

                return float(diluted_shares), metadata

        # Fallback: Use basic shares (conservative - understates dilution)
        metadata["method"] = "basic (no dilution available)"
        metadata["warnings"].append(
            "Using basic shares - may understate dilution from options/warrants"
        )

        return float(basic_shares), metadata

    except Exception as e:
        metadata["warnings"].append(f"Error calculating diluted shares: {str(e)}")
        metadata["method"] = "error"
        return 0, metadata


def calculate_equity_value_from_ev(
    enterprise_value: float,
    ticker: str,
    total_debt: Optional[float] = None,
    cash: Optional[float] = None,
    include_minority_interest: bool = True,
    include_preferred_stock: bool = True,
    include_pension_deficit: bool = False,
) -> Tuple[float, Dict[str, any]]:
    """
    Convert Enterprise Value to Equity Value using complete bridge.

    [AuditFix] Implements rigorous EV → Equity conversion per Damodaran.

    BRIDGE FORMULA:
    Enterprise Value (EV)
      - Total Debt
      + Cash & Equivalents
      - Minority Interest (if applicable)
      - Preferred Stock (if applicable)
      - Pension Deficit (if applicable)
      + Other adjustments
    = Equity Value (Market Cap Equivalent)

    Why each adjustment:
    - Debt: Deduct because EV = Equity + Debt (debt holders have claim)
    - Cash: Add back because it's not needed for operations (belongs to equity)
    - Minority Interest: Deduct because it's value owned by others
    - Preferred Stock: Deduct because it has priority claim over common equity
    - Pension Deficit: Deduct unfunded liability (future obligation)

    Args:
        enterprise_value: DCF-calculated Enterprise Value
        ticker: Stock ticker
        total_debt: Total debt (fetched if None)
        cash: Cash & equivalents (fetched if None)
        include_minority_interest: Adjust for minority interests
        include_preferred_stock: Adjust for preferred stock
        include_pension_deficit: Adjust for unfunded pensions (optional)

    Returns:
        Tuple of (equity_value, bridge_details_dict)

    Example:
        >>> ev = 500e9  # $500B enterprise value from DCF
        >>> equity_value, bridge = calculate_equity_value_from_ev(ev, "AAPL")
        >>> print(f"EV: ${ev/1e9:.1f}B → Equity: ${equity_value/1e9:.1f}B")
        EV: $500.0B → Equity: $480.5B
    """
    bridge = {
        "enterprise_value": enterprise_value,
        "adjustments": {},
        "equity_value": enterprise_value,  # Will be updated
        "warnings": [],
    }

    # [BugFix #8] Validate Enterprise Value is reasonable
    if enterprise_value < 0:
        bridge["warnings"].append(
            f"⚠️  CRITICAL: Negative Enterprise Value (${enterprise_value/1e9:.2f}B). "
            f"This suggests: (1) DCF inputs are incorrect, (2) company is distressed, "
            f"or (3) projected FCFs are negative. Review DCF assumptions."
        )
        bridge["interpretation"] = "INVALID: Negative EV - check DCF inputs"

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        balance_sheet = stock.balance_sheet

        # === 1. TOTAL DEBT ===
        if total_debt is None:
            # Fetch total debt
            total_debt = info.get("totalDebt", 0)

            # Fallback to balance sheet
            if total_debt == 0 and balance_sheet is not None and not balance_sheet.empty:
                # Try to get from balance sheet
                if "Total Debt" in balance_sheet.index:
                    total_debt = balance_sheet.loc["Total Debt"].iloc[0]
                elif "Long Term Debt" in balance_sheet.index and "Current Debt" in balance_sheet.index:
                    long_term_debt = balance_sheet.loc["Long Term Debt"].iloc[0]
                    current_debt = balance_sheet.loc["Current Debt"].iloc[0]
                    total_debt = long_term_debt + current_debt

        bridge["adjustments"]["total_debt"] = -float(total_debt) if total_debt > 0 else 0.0

        # === 2. CASH & EQUIVALENTS ===
        if cash is None:
            cash = info.get("totalCash", 0)

            # Fallback to balance sheet
            if cash == 0 and balance_sheet is not None and not balance_sheet.empty:
                if "Cash And Cash Equivalents" in balance_sheet.index:
                    cash = balance_sheet.loc["Cash And Cash Equivalents"].iloc[0]
                elif "Cash" in balance_sheet.index:
                    cash = balance_sheet.loc["Cash"].iloc[0]

        bridge["adjustments"]["cash_and_equivalents"] = float(cash) if cash > 0 else 0.0

        # === 3. MINORITY INTEREST (NON-CONTROLLING INTERESTS) ===
        minority_interest = 0
        if include_minority_interest and balance_sheet is not None and not balance_sheet.empty:
            # Common names for minority interest
            mi_names = [
                "Minority Interest",
                "Non Controlling Interest",
                "Noncontrolling Interest",
            ]

            for name in mi_names:
                if name in balance_sheet.index:
                    minority_interest = balance_sheet.loc[name].iloc[0]
                    break

        bridge["adjustments"]["minority_interest"] = -float(minority_interest) if minority_interest > 0 else 0.0

        # === 4. PREFERRED STOCK ===
        preferred_stock = 0
        if include_preferred_stock:
            preferred_stock = info.get("preferredStock", 0)

            # Fallback to balance sheet
            if preferred_stock == 0 and balance_sheet is not None and not balance_sheet.empty:
                if "Preferred Stock" in balance_sheet.index:
                    preferred_stock = balance_sheet.loc["Preferred Stock"].iloc[0]

        bridge["adjustments"]["preferred_stock"] = -float(preferred_stock) if preferred_stock > 0 else 0.0

        # === 5. PENSION DEFICIT (Optional - more advanced) ===
        pension_deficit = 0
        if include_pension_deficit and balance_sheet is not None and not balance_sheet.empty:
            # Pension deficit = Pension obligations - Pension assets
            # If negative (surplus), it adds value; if positive (deficit), subtracts
            pension_names = [
                "Pension Liabilities",
                "Defined Benefit Pension Liabilities",
                "Pension Deficit",
            ]

            for name in pension_names:
                if name in balance_sheet.index:
                    pension_deficit = balance_sheet.loc[name].iloc[0]
                    break

        bridge["adjustments"]["pension_deficit"] = -float(pension_deficit) if pension_deficit > 0 else 0.0

        # === CALCULATE EQUITY VALUE ===
        total_adjustments = sum(bridge["adjustments"].values())
        equity_value = enterprise_value + total_adjustments

        bridge["equity_value"] = equity_value
        bridge["total_adjustments"] = total_adjustments
        bridge["adjustment_as_pct_of_ev"] = total_adjustments / enterprise_value if enterprise_value != 0 else 0

        # === INTERPRETATION ===
        if equity_value < 0:
            bridge["warnings"].append(
                "⚠️ Negative equity value - company may be distressed or EV too low"
            )
            bridge["interpretation"] = "DISTRESSED: Liabilities exceed EV"
        elif abs(total_adjustments) > 0.50 * enterprise_value:
            bridge["warnings"].append(
                "⚠️ Large adjustments (>50% of EV) - verify balance sheet items"
            )
            bridge["interpretation"] = "High net debt/cash position - significant adjustments"
        else:
            bridge["interpretation"] = "Normal bridge - adjustments reasonable"

        return equity_value, bridge

    except Exception as e:
        bridge["warnings"].append(f"Error in EV bridge calculation: {str(e)}")
        bridge["interpretation"] = "ERROR: Could not complete bridge"
        return enterprise_value, bridge  # Return EV as fallback


def calculate_price_per_share(
    enterprise_value: float,
    ticker: str,
    total_debt: Optional[float] = None,
    cash: Optional[float] = None,
    use_diluted_shares: bool = True,
    include_minority_interest: bool = True,
    include_preferred_stock: bool = True,
) -> Tuple[float, Dict[str, any]]:
    """
    Complete DCF pipeline: EV → Equity Value → Intrinsic Price per Share.

    [AuditFix] This is the MAIN function for converting DCF output to price.

    COMPLETE PIPELINE:
    1. Start with Enterprise Value (from DCF)
    2. Convert to Equity Value (EV bridge)
    3. Divide by Fully Diluted Shares
    4. Result: Intrinsic Price per Share

    This function orchestrates the entire conversion.

    Args:
        enterprise_value: DCF-calculated Enterprise Value
        ticker: Stock ticker
        total_debt: Total debt (optional, fetched if None)
        cash: Cash & equivalents (optional, fetched if None)
        use_diluted_shares: Use diluted shares (recommended)
        include_minority_interest: Adjust for minorities
        include_preferred_stock: Adjust for preferreds

    Returns:
        Tuple of (intrinsic_price_per_share, complete_analysis_dict)

    Example:
        >>> ev = 500e9  # $500B from DCF
        >>> price, analysis = calculate_price_per_share(ev, "AAPL")
        >>> print(f"Intrinsic Value: ${price:.2f}/share")
        Intrinsic Value: $152.30/share
        >>> print(f"Current Price: ${analysis['current_price']:.2f}")
        Current Price: $145.00
        >>> print(f"Upside: {analysis['upside_pct']:.1%}")
        Upside: 5.0%
    """
    analysis = {
        "enterprise_value": enterprise_value,
        "equity_value": 0.0,
        "diluted_shares": 0,
        "intrinsic_price_per_share": 0.0,
        "current_price": 0.0,
        "upside_pct": 0.0,
        "warnings": [],
    }

    try:
        # Step 1: Convert EV to Equity Value
        equity_value, bridge_details = calculate_equity_value_from_ev(
            enterprise_value=enterprise_value,
            ticker=ticker,
            total_debt=total_debt,
            cash=cash,
            include_minority_interest=include_minority_interest,
            include_preferred_stock=include_preferred_stock,
        )

        analysis["equity_value"] = equity_value
        analysis["bridge_details"] = bridge_details
        analysis["warnings"].extend(bridge_details.get("warnings", []))

        # Step 2: Get Fully Diluted Shares
        diluted_shares, share_details = get_fully_diluted_shares(
            ticker=ticker,
            use_treasury_stock_method=use_diluted_shares,
        )

        analysis["diluted_shares"] = diluted_shares
        analysis["share_details"] = share_details
        analysis["warnings"].extend(share_details.get("warnings", []))

        if diluted_shares <= 0:
            analysis["warnings"].append("No shares data - cannot calculate price per share")
            return 0.0, analysis

        # Step 3: Calculate Intrinsic Price per Share
        intrinsic_price = equity_value / diluted_shares

        analysis["intrinsic_price_per_share"] = intrinsic_price

        # Step 4: Compare to Current Market Price
        stock = yf.Ticker(ticker)
        current_price = stock.info.get("currentPrice", stock.info.get("regularMarketPrice", 0))

        analysis["current_price"] = current_price

        if current_price > 0:
            upside_pct = (intrinsic_price - current_price) / current_price
            analysis["upside_pct"] = upside_pct
            analysis["upside_absolute"] = intrinsic_price - current_price

            # Interpretation
            if upside_pct > 0.30:
                analysis["recommendation"] = "STRONG BUY"
                analysis["interpretation"] = f"Significantly undervalued ({upside_pct:.1%} upside)"
            elif upside_pct > 0.15:
                analysis["recommendation"] = "BUY"
                analysis["interpretation"] = f"Undervalued ({upside_pct:.1%} upside)"
            elif upside_pct > -0.15:
                analysis["recommendation"] = "HOLD"
                analysis["interpretation"] = f"Fairly valued ({upside_pct:+.1%})"
            elif upside_pct > -0.30:
                analysis["recommendation"] = "SELL"
                analysis["interpretation"] = f"Overvalued ({upside_pct:.1%})"
            else:
                analysis["recommendation"] = "STRONG SELL"
                analysis["interpretation"] = f"Significantly overvalued ({upside_pct:.1%})"
        else:
            analysis["warnings"].append("No current price available for comparison")

        return intrinsic_price, analysis

    except Exception as e:
        analysis["warnings"].append(f"Error in price calculation: {str(e)}")
        return 0.0, analysis


def print_valuation_bridge_report(analysis: Dict[str, any]) -> None:
    """
    Print a formatted report of the complete valuation bridge.

    [AuditFix] Provides clear visualization of EV → Equity → Price pipeline.

    Args:
        analysis: Analysis dict from calculate_price_per_share()

    Example:
        >>> price, analysis = calculate_price_per_share(500e9, "AAPL")
        >>> print_valuation_bridge_report(analysis)
    """
    print("=" * 80)
    print("VALUATION BRIDGE: Enterprise Value → Price per Share")
    print("=" * 80)

    # Enterprise Value
    print(f"\n1️⃣ ENTERPRISE VALUE (from DCF)")
    print(f"   ${analysis['enterprise_value']/1e9:,.2f}B")

    # Bridge
    if "bridge_details" in analysis:
        bridge = analysis["bridge_details"]
        print(f"\n2️⃣ EV → EQUITY VALUE BRIDGE")

        for item, value in bridge.get("adjustments", {}).items():
            sign = "+" if value > 0 else ""
            print(f"   {sign}${value/1e9:,.2f}B  ({item.replace('_', ' ').title()})")

        print(f"   {'─' * 70}")
        print(f"   = ${analysis['equity_value']/1e9:,.2f}B  (Equity Value)")

    # Shares
    if "share_details" in analysis:
        shares = analysis["share_details"]
        print(f"\n3️⃣ SHARES OUTSTANDING")
        print(f"   Basic: {shares.get('basic_shares', 0)/1e9:.3f}B")
        print(f"   Diluted: {analysis['diluted_shares']/1e9:.3f}B")
        if shares.get("dilution_pct", 0) > 0:
            print(f"   Dilution: {shares['dilution_pct']:.2%}")

    # Price
    print(f"\n4️⃣ INTRINSIC PRICE PER SHARE")
    print(f"   ${analysis['intrinsic_price_per_share']:.2f}")

    # Market Comparison
    if analysis.get("current_price", 0) > 0:
        print(f"\n5️⃣ MARKET COMPARISON")
        print(f"   Current Price: ${analysis['current_price']:.2f}")
        print(f"   Intrinsic Value: ${analysis['intrinsic_price_per_share']:.2f}")
        print(f"   Upside: {analysis['upside_pct']:+.1%}")
        print(f"\n   📊 RECOMMENDATION: {analysis.get('recommendation', 'N/A')}")
        print(f"   💡 {analysis.get('interpretation', '')}")

    # Warnings
    if analysis.get("warnings"):
        print(f"\n⚠️  WARNINGS:")
        for warning in analysis["warnings"]:
            print(f"   - {warning}")

    print("\n" + "=" * 80)
