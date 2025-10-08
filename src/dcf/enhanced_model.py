"""Enhanced DCF model with realistic parameters and equity value calculation."""

from typing import List, Tuple, Optional
import numpy as np


class EnhancedDCFModel:
    """
    Enhanced DCF valuation model with:
    - Tiered growth rates based on historical volatility
    - Equity value calculation (EV + Cash - Debt)
    - Proper handling of diluted shares
    """

    def __init__(
        self,
        wacc: float = 0.085,  # 8.5% default WACC
        terminal_growth: float = 0.03,  # 3% terminal growth
    ):
        """
        Initialize enhanced DCF model.

        Args:
            wacc: Weighted Average Cost of Capital (default 8.5%)
            terminal_growth: Terminal perpetual growth rate (default 3%)
        """
        self.wacc = wacc
        self.terminal_growth = terminal_growth

    def calculate_tiered_growth_rates(
        self, historical_fcf: List[float], years: int = 5
    ) -> List[float]:
        """
        Calculate tiered growth rates based on historical volatility.

        Structure:
        - Years 1-2: High growth (10-25% based on volatility)
        - Years 3-4: Medium growth (10-15% based on volatility)
        - Year 5: Stabilizing growth (3-8% based on volatility)

        Args:
            historical_fcf: List of historical FCF values
            years: Number of years to project (default 5)

        Returns:
            List of growth rates for each year
        """
        if len(historical_fcf) < 2:
            # Conservative default if no history
            return [0.15, 0.12, 0.10, 0.08, 0.05][:years]

        # Calculate historical growth rates
        hist_growth = []
        for i in range(1, len(historical_fcf)):
            if historical_fcf[i - 1] != 0:
                growth = (historical_fcf[i] - historical_fcf[i - 1]) / abs(
                    historical_fcf[i - 1]
                )
                hist_growth.append(growth)

        if not hist_growth:
            return [0.15, 0.12, 0.10, 0.08, 0.05][:years]

        # Calculate volatility (standard deviation of growth rates)
        volatility = np.std(hist_growth)
        avg_growth = np.mean(hist_growth)

        # Cap average growth between -10% and +50%
        avg_growth = max(-0.10, min(0.50, avg_growth))

        # Determine growth tiers based on historical performance and volatility
        # High volatility = more conservative
        # High average growth = more optimistic

        if avg_growth > 0.15 and volatility < 0.20:
            # High growth, low volatility → Aggressive
            tier1 = [0.22, 0.20]  # Years 1-2: 20-22%
            tier2 = [0.14, 0.12]  # Years 3-4: 12-14%
            tier3 = [0.07]  # Year 5: 7%
        elif avg_growth > 0.10 and volatility < 0.25:
            # Good growth, moderate volatility → Moderate-Optimistic
            tier1 = [0.18, 0.16]  # Years 1-2: 16-18%
            tier2 = [0.12, 0.10]  # Years 3-4: 10-12%
            tier3 = [0.06]  # Year 5: 6%
        elif avg_growth > 0.05:
            # Moderate growth → Moderate
            tier1 = [0.15, 0.13]  # Years 1-2: 13-15%
            tier2 = [0.10, 0.08]  # Years 3-4: 8-10%
            tier3 = [0.05]  # Year 5: 5%
        elif avg_growth > 0:
            # Low growth → Conservative
            tier1 = [0.12, 0.10]  # Years 1-2: 10-12%
            tier2 = [0.08, 0.06]  # Years 3-4: 6-8%
            tier3 = [0.04]  # Year 5: 4%
        else:
            # Negative or no growth → Very conservative
            tier1 = [0.08, 0.06]  # Years 1-2: 6-8%
            tier2 = [0.05, 0.04]  # Years 3-4: 4-5%
            tier3 = [0.03]  # Year 5: 3%

        # Combine tiers
        growth_rates = tier1 + tier2 + tier3

        # Extend or truncate to match requested years
        if len(growth_rates) < years:
            # Extend with terminal growth
            growth_rates.extend([self.terminal_growth] * (years - len(growth_rates)))
        else:
            growth_rates = growth_rates[:years]

        return growth_rates

    def project_fcf(self, base_fcf: float, growth_rates: List[float]) -> List[float]:
        """
        Project future FCF using tiered growth rates.

        Args:
            base_fcf: Base year FCF
            growth_rates: List of growth rates for each year

        Returns:
            List of projected FCF values
        """
        projections = []
        current_fcf = base_fcf

        for rate in growth_rates:
            current_fcf = current_fcf * (1 + rate)
            projections.append(current_fcf)

        return projections

    def calculate_terminal_value(self, final_fcf: float) -> float:
        """
        Calculate terminal value using Gordon Growth Model.

        Formula: TV = FCF_final × (1 + g) / (WACC - g)

        Args:
            final_fcf: Final year projected FCF

        Returns:
            Terminal value
        """
        if self.wacc <= self.terminal_growth:
            raise ValueError(
                f"WACC ({self.wacc:.2%}) must be greater than terminal growth ({self.terminal_growth:.2%})"
            )

        tv = (final_fcf * (1 + self.terminal_growth)) / (
            self.wacc - self.terminal_growth
        )
        return tv

    def calculate_enterprise_value(
        self, projected_fcf: List[float]
    ) -> Tuple[float, float, List[float]]:
        """
        Calculate enterprise value (present value of all cash flows).

        Args:
            projected_fcf: List of projected FCF values

        Returns:
            Tuple of (enterprise_value, pv_terminal_value, pv_fcf_list)
        """
        if not projected_fcf:
            return 0.0, 0.0, []

        # Discount projected FCF to present value
        pv_fcf = []
        for i, fcf in enumerate(projected_fcf, start=1):
            pv = fcf / ((1 + self.wacc) ** i)
            pv_fcf.append(pv)

        # Calculate terminal value
        terminal_value = self.calculate_terminal_value(projected_fcf[-1])

        # Discount terminal value to present
        pv_terminal = terminal_value / ((1 + self.wacc) ** len(projected_fcf))

        # Enterprise value = sum of all PVs
        enterprise_value = sum(pv_fcf) + pv_terminal

        return enterprise_value, pv_terminal, pv_fcf

    def calculate_equity_value(
        self,
        enterprise_value: float,
        cash: float = 0.0,
        debt: float = 0.0,
    ) -> float:
        """
        Calculate equity value from enterprise value.

        Formula: Equity Value = EV + Cash - Debt

        Args:
            enterprise_value: Enterprise value from DCF
            cash: Cash and cash equivalents
            debt: Total debt

        Returns:
            Equity value
        """
        equity_value = enterprise_value + cash - debt
        return equity_value

    def calculate_fair_value_per_share(
        self,
        equity_value: float,
        diluted_shares: float,
    ) -> float:
        """
        Calculate fair value per share.

        Args:
            equity_value: Total equity value
            diluted_shares: Number of diluted shares outstanding

        Returns:
            Fair value per share
        """
        if diluted_shares <= 0:
            raise ValueError("Diluted shares must be greater than 0")

        fair_value = equity_value / diluted_shares
        return fair_value

    def full_dcf_valuation(
        self,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        years: int = 5,
        custom_growth_rates: Optional[List[float]] = None,
    ) -> dict:
        """
        Perform complete DCF valuation.

        Args:
            base_fcf: Base year FCF (in absolute units, e.g., billions)
            historical_fcf: List of historical FCF for growth calculation
            cash: Cash and equivalents
            debt: Total debt
            diluted_shares: Diluted shares outstanding
            years: Number of projection years
            custom_growth_rates: Optional custom growth rates (overrides calculated)

        Returns:
            Dictionary with complete valuation results
        """
        # Step 1: Determine growth rates
        if custom_growth_rates:
            growth_rates = custom_growth_rates[:years]
        else:
            growth_rates = self.calculate_tiered_growth_rates(historical_fcf, years)

        # Step 2: Project FCF
        projected_fcf = self.project_fcf(base_fcf, growth_rates)

        # Step 3: Calculate enterprise value
        enterprise_value, pv_terminal, pv_fcf = self.calculate_enterprise_value(
            projected_fcf
        )

        # Step 4: Calculate equity value
        equity_value = self.calculate_equity_value(enterprise_value, cash, debt)

        # Step 5: Calculate fair value per share
        fair_value_per_share = self.calculate_fair_value_per_share(
            equity_value, diluted_shares
        )

        # Calculate terminal value (undiscounted)
        terminal_value = self.calculate_terminal_value(projected_fcf[-1])

        return {
            "base_fcf": base_fcf,
            "growth_rates": growth_rates,
            "projected_fcf": projected_fcf,
            "pv_fcf": pv_fcf,
            "terminal_value": terminal_value,
            "pv_terminal_value": pv_terminal,
            "enterprise_value": enterprise_value,
            "cash": cash,
            "debt": debt,
            "equity_value": equity_value,
            "diluted_shares": diluted_shares,
            "fair_value_per_share": fair_value_per_share,
            "wacc": self.wacc,
            "terminal_growth": self.terminal_growth,
        }
