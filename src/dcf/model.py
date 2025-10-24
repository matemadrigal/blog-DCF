from typing import Iterable
import warnings


def dcf_value(
    cash_flows: Iterable[float],
    discount_rate: float,
    perpetuity_growth: float = 0.02,
    use_mid_year_convention: bool = True,
    min_spread_bps: float = 0.02,
) -> float:
    """
    Estimate the DCF present value given a sequence of forecasted free cash flows.

    Args:
        cash_flows: Iterable of forecasted free cash flows for discrete forecast years (year 1..N).
        discount_rate: Annual discount rate as decimal (e.g., 0.08 for 8%).
        perpetuity_growth: Terminal perpetual growth rate used to compute the terminal value.
        use_mid_year_convention: If True, apply mid-year discounting (default True).
                                 Assumes cash flows occur mid-year rather than year-end.
        min_spread_bps: Minimum spread (r - g) in decimal (default 0.02 = 200 bps).
                        Prevents valuation explosion when r ≈ g.

    Returns:
        Present value (float) of the cash flows including terminal value.

    Notes:
        - Uses a Gordon Growth Model for terminal value at year N: TV = FCF_N * (1 + g) / (r - g)
        - [AuditFix] Added mid-year discounting convention (industry standard)
        - [AuditFix] Added numerical stability check for (r - g) spread
        - Mid-year convention: Discount factor = (1 + r)^(t - 0.5) instead of (1 + r)^t
    """
    # [AuditFix] Validate spread to prevent valuation explosion
    spread = discount_rate - perpetuity_growth

    if spread <= 0:
        raise ValueError(
            f"discount_rate ({discount_rate:.2%}) must be greater than "
            f"perpetuity_growth ({perpetuity_growth:.2%}). "
            f"Current spread: {spread:.4f}"
        )

    # [AuditFix] Warn if spread is too narrow (< min_spread_bps)
    if spread < min_spread_bps:
        warnings.warn(
            f"⚠️  Narrow spread detected: (r - g) = {spread:.4f} ({spread*10000:.0f} bps). "
            f"This may lead to inflated valuations. Minimum recommended: {min_spread_bps:.4f} "
            f"({min_spread_bps*10000:.0f} bps). Consider reducing perpetuity_growth or "
            f"increasing discount_rate.",
            UserWarning,
            stacklevel=2
        )

    cf_list = list(cash_flows)
    if len(cf_list) == 0:
        return 0.0

    # [AuditFix] Apply mid-year discounting convention
    # Standard practice: cash flows occur mid-year, not end-of-year
    # Discount factor: (1 + r)^(t - 0.5) vs (1 + r)^t
    pv = 0.0
    for i, cf in enumerate(cf_list, start=1):
        if use_mid_year_convention:
            # Mid-year: discount to t - 0.5
            discount_factor = (1 + discount_rate) ** (i - 0.5)
        else:
            # End-of-year: discount to t
            discount_factor = (1 + discount_rate) ** i

        pv += cf / discount_factor

    # Terminal value based on last cash flow
    # TV = FCF_N * (1 + g) / (r - g)
    last_cf = cf_list[-1]

    # [BugFix #2] Handle negative terminal FCF
    # A company with perpetually negative FCF has no terminal value
    # DCF valuation may not be appropriate for such companies
    if last_cf <= 0:
        warnings.warn(
            f"⚠️  Terminal FCF is non-positive ({last_cf:,.0f}). "
            f"Setting Terminal Value to 0. DCF may not be appropriate for this company. "
            f"Consider using alternative valuation methods or projecting to profitability.",
            UserWarning,
            stacklevel=2
        )
        terminal_value = 0.0
    else:
        terminal_value = last_cf * (1 + perpetuity_growth) / spread

    # [AuditFix] Apply mid-year discounting to terminal value
    # Terminal value occurs at end of explicit forecast period
    # With mid-year convention, discount from year N (not N - 0.5)
    n = len(cf_list)
    if use_mid_year_convention:
        # Terminal value occurs at end of year N
        # But since explicit FCFs use mid-year, we discount TV from N - 0.5
        # to maintain consistency (TV starts generating from mid-year N)
        tv_discount_factor = (1 + discount_rate) ** (n - 0.5)
    else:
        tv_discount_factor = (1 + discount_rate) ** n

    pv += terminal_value / tv_discount_factor

    return pv
