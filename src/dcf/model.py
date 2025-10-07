from typing import Iterable


def dcf_value(
    cash_flows: Iterable[float], discount_rate: float, perpetuity_growth: float = 0.02
) -> float:
    """
    Estimate the DCF present value given a sequence of forecasted free cash flows.

    Args:
        cash_flows: Iterable of forecasted free cash flows for discrete forecast years (year 1..N).
        discount_rate: Annual discount rate as decimal (e.g., 0.08 for 8%).
        perpetuity_growth: Terminal perpetual growth rate used to compute the terminal value.

    Returns:
        Present value (float) of the cash flows including terminal value.

    Notes:
        - Uses a Gordon Growth Model for terminal value at year N: TV = FCF_N * (1 + g) / (r - g)
        - Discount each cash flow and the terminal value to present at the supplied discount_rate.
    """
    if discount_rate <= perpetuity_growth:
        raise ValueError("discount_rate must be greater than perpetuity_growth")

    cf_list = list(cash_flows)
    if len(cf_list) == 0:
        return 0.0

    pv = 0.0
    for i, cf in enumerate(cf_list, start=1):
        pv += cf / ((1 + discount_rate) ** i)

    # Terminal value based on last cash flow
    last_cf = cf_list[-1]
    terminal_value = (
        last_cf * (1 + perpetuity_growth) / (discount_rate - perpetuity_growth)
    )
    pv += terminal_value / ((1 + discount_rate) ** len(cf_list))
    return pv
