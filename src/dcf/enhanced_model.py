"""Enhanced DCF model with realistic parameters and equity value calculation."""

from typing import List, Tuple, Optional, Dict
import numpy as np
from enum import Enum


class ScenarioType(Enum):
    """Scenario types for DCF analysis."""
    PESSIMISTIC = "pessimistic"
    BASE = "base"
    OPTIMISTIC = "optimistic"


class EnhancedDCFModel:
    """
    Enhanced DCF valuation model with:
    - Tiered growth rates based on historical volatility
    - Equity value calculation (EV + Cash - Debt)
    - Proper handling of diluted shares
    """

    def __init__(
        self,
        wacc: float = 0.08,  # 8% default WACC (reduced from 8.5%)
        terminal_growth: float = 0.035,  # 3.5% terminal growth (increased from 3%)
    ):
        """
        Initialize enhanced DCF model.

        Args:
            wacc: Weighted Average Cost of Capital (default 8%)
            terminal_growth: Terminal perpetual growth rate (default 3.5%)
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
            return [0.18, 0.15, 0.12, 0.10, 0.08][:years]

        # Calculate historical growth rates (year-over-year)
        hist_growth = []
        for i in range(1, len(historical_fcf)):
            prev_fcf = historical_fcf[i - 1]
            curr_fcf = historical_fcf[i]

            # Skip if either value is invalid
            if prev_fcf == 0 or np.isnan(prev_fcf) or np.isnan(curr_fcf):
                continue

            growth = (curr_fcf - prev_fcf) / abs(prev_fcf)

            # Filter out extreme outliers (> 200% or < -90%)
            # These are likely data errors or one-time events
            if -0.90 < growth < 2.00:
                hist_growth.append(growth)

        if not hist_growth:
            return [0.18, 0.15, 0.12, 0.10, 0.08][:years]

        # Remove NaN values if any
        hist_growth = [g for g in hist_growth if not np.isnan(g)]

        if not hist_growth:
            return [0.18, 0.15, 0.12, 0.10, 0.08][:years]

        # Use MEDIAN for robustness against outliers
        median_growth = np.median(hist_growth)

        # Also calculate trimmed mean (remove top and bottom 25% if we have enough data)
        if len(hist_growth) >= 4:
            sorted_growth = sorted(hist_growth)
            # Remove extreme 25% on each side
            trim_count = max(1, len(sorted_growth) // 4)
            trimmed_growth = sorted_growth[trim_count:-trim_count]
            avg_growth = np.mean(trimmed_growth)
        else:
            avg_growth = np.mean(hist_growth)

        # Use the AVERAGE of median and trimmed mean for balanced estimate
        conservative_growth = (median_growth + avg_growth) / 2

        # Cap growth between -10% and +40% (realistic for most companies)
        avg_growth = max(-0.10, min(0.40, conservative_growth))

        # Determine growth tiers based on historical performance and volatility
        # UPDATED: More realistic growth rates to avoid systematic undervaluation
        # Volatility tolerance increased - high volatility in high-growth is normal
        # High average growth = more optimistic

        if avg_growth > 0.50:
            # Exceptional growth (e.g., explosive tech) → Very Aggressive
            tier1 = [0.40, 0.35]  # Years 1-2: 35-40%
            tier2 = [0.28, 0.22]  # Years 3-4: 22-28%
            tier3 = [0.15]  # Year 5: 15%
        elif avg_growth > 0.30:
            # Very high growth → Very Aggressive
            tier1 = [0.35, 0.30]  # Years 1-2: 30-35%
            tier2 = [0.25, 0.20]  # Years 3-4: 20-25%
            tier3 = [0.14]  # Year 5: 14%
        elif avg_growth > 0.20:
            # High growth → Aggressive
            tier1 = [0.28, 0.25]  # Years 1-2: 25-28%
            tier2 = [0.20, 0.16]  # Years 3-4: 16-20%
            tier3 = [0.12]  # Year 5: 12%
        elif avg_growth > 0.12:
            # Good growth → Moderate-Optimistic
            tier1 = [0.22, 0.20]  # Years 1-2: 20-22%
            tier2 = [0.16, 0.13]  # Years 3-4: 13-16%
            tier3 = [0.10]  # Year 5: 10%
        elif avg_growth > 0.06:
            # Moderate growth → Moderate
            tier1 = [0.17, 0.15]  # Years 1-2: 15-17%
            tier2 = [0.12, 0.10]  # Years 3-4: 10-12%
            tier3 = [0.08]  # Year 5: 8%
        elif avg_growth > 0:
            # Low growth → Conservative
            tier1 = [0.13, 0.11]  # Years 1-2: 11-13%
            tier2 = [0.09, 0.07]  # Years 3-4: 7-9%
            tier3 = [0.06]  # Year 5: 6%
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

    def normalize_base_fcf(
        self, historical_fcf: List[float], method: str = "average"
    ) -> float:
        """
        Normalize base FCF for companies with volatile cash flows.

        Args:
            historical_fcf: List of historical FCF values (most recent first)
            method: Normalization method - "average", "median", "weighted_average", or "current"

        Returns:
            Normalized base FCF
        """
        if not historical_fcf or len(historical_fcf) == 0:
            return 0.0

        # Filter out NaN and zero values
        valid_fcf = [f for f in historical_fcf if not np.isnan(f) and f != 0]

        if not valid_fcf:
            return 0.0

        if method == "current":
            # Use most recent year (original behavior)
            return valid_fcf[0]

        elif method == "average":
            # Simple average of historical years
            return np.mean(valid_fcf)

        elif method == "median":
            # Median (robust to outliers)
            return np.median(valid_fcf)

        elif method == "weighted_average":
            # Weighted average (more weight to recent years)
            if len(valid_fcf) >= 3:
                # Use last 3 years with weights: 50%, 30%, 20%
                weights = [0.5, 0.3, 0.2]
                weighted_fcf = sum(
                    fcf * w
                    for fcf, w in zip(valid_fcf[:3], weights[: len(valid_fcf[:3])])
                )
                return weighted_fcf
            else:
                return np.mean(valid_fcf)

        else:
            # Default to average
            return np.mean(valid_fcf)

    def full_dcf_valuation(
        self,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        years: int = 5,
        custom_growth_rates: Optional[List[float]] = None,
        normalize_base: bool = True,
        normalization_method: str = "weighted_average",
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
            normalize_base: Whether to normalize the base FCF
            normalization_method: Method for normalization ("average", "median", "weighted_average", "current")

        Returns:
            Dictionary with complete valuation results
        """
        # Step 0: Normalize base FCF if requested
        if normalize_base and historical_fcf:
            normalized_fcf = self.normalize_base_fcf(
                historical_fcf, method=normalization_method
            )
            # Only use normalized if it's reasonable (within 50% of current)
            if abs(normalized_fcf - base_fcf) / base_fcf < 0.5:
                base_fcf_original = base_fcf
                base_fcf = normalized_fcf
            else:
                base_fcf_original = base_fcf
        else:
            base_fcf_original = base_fcf

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
            "base_fcf_original": base_fcf_original,
            "normalized": normalize_base,
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


class ScenarioAnalyzer:
    """
    Scenario analysis for DCF valuation.

    Generates three scenarios (Pessimistic, Base, Optimistic) with different
    growth assumptions and calculates probability-weighted valuations.
    """

    def __init__(
        self,
        base_model: EnhancedDCFModel,
        pessimistic_probability: float = 0.25,
        base_probability: float = 0.50,
        optimistic_probability: float = 0.25,
    ):
        """
        Initialize scenario analyzer.

        Args:
            base_model: Base EnhancedDCFModel to use for calculations
            pessimistic_probability: Probability weight for pessimistic scenario (default 25%)
            base_probability: Probability weight for base scenario (default 50%)
            optimistic_probability: Probability weight for optimistic scenario (default 25%)

        Raises:
            ValueError: If probabilities don't sum to 1.0
        """
        if not np.isclose(pessimistic_probability + base_probability + optimistic_probability, 1.0):
            raise ValueError(
                f"Probabilities must sum to 1.0. Got: {pessimistic_probability + base_probability + optimistic_probability:.2f}"
            )

        self.base_model = base_model
        self.probabilities = {
            ScenarioType.PESSIMISTIC: pessimistic_probability,
            ScenarioType.BASE: base_probability,
            ScenarioType.OPTIMISTIC: optimistic_probability,
        }

    def _adjust_growth_rates(
        self,
        base_growth_rates: List[float],
        scenario: ScenarioType,
    ) -> List[float]:
        """
        Adjust growth rates based on scenario type.

        Args:
            base_growth_rates: Base case growth rates
            scenario: Scenario type

        Returns:
            Adjusted growth rates for the scenario
        """
        if scenario == ScenarioType.BASE:
            return base_growth_rates

        elif scenario == ScenarioType.PESSIMISTIC:
            # Reduce growth rates by 40% (more conservative)
            # Minimum 2% growth (avoid negative growth in normal conditions)
            adjusted = [max(0.02, rate * 0.60) for rate in base_growth_rates]
            return adjusted

        elif scenario == ScenarioType.OPTIMISTIC:
            # Increase growth rates by 40% (more aggressive)
            # Cap at 50% to avoid unrealistic projections
            adjusted = [min(0.50, rate * 1.40) for rate in base_growth_rates]
            return adjusted

        else:
            raise ValueError(f"Unknown scenario type: {scenario}")

    def _adjust_wacc(
        self,
        base_wacc: float,
        scenario: ScenarioType,
    ) -> float:
        """
        Adjust WACC based on scenario (risk adjustment).

        Args:
            base_wacc: Base case WACC
            scenario: Scenario type

        Returns:
            Adjusted WACC for the scenario
        """
        if scenario == ScenarioType.BASE:
            return base_wacc

        elif scenario == ScenarioType.PESSIMISTIC:
            # Increase WACC by 2% (higher risk)
            # Cap at 20%
            adjusted = min(0.20, base_wacc + 0.02)
            return adjusted

        elif scenario == ScenarioType.OPTIMISTIC:
            # Decrease WACC by 1% (lower risk)
            # Minimum 3%
            adjusted = max(0.03, base_wacc - 0.01)
            return adjusted

        else:
            raise ValueError(f"Unknown scenario type: {scenario}")

    def _adjust_terminal_growth(
        self,
        base_terminal_growth: float,
        scenario: ScenarioType,
    ) -> float:
        """
        Adjust terminal growth rate based on scenario.

        Args:
            base_terminal_growth: Base case terminal growth
            scenario: Scenario type

        Returns:
            Adjusted terminal growth for the scenario
        """
        if scenario == ScenarioType.BASE:
            return base_terminal_growth

        elif scenario == ScenarioType.PESSIMISTIC:
            # Reduce terminal growth by 1%
            # Minimum 1.5%
            adjusted = max(0.015, base_terminal_growth - 0.01)
            return adjusted

        elif scenario == ScenarioType.OPTIMISTIC:
            # Increase terminal growth by 0.5%
            # Cap at 5%
            adjusted = min(0.05, base_terminal_growth + 0.005)
            return adjusted

        else:
            raise ValueError(f"Unknown scenario type: {scenario}")

    def calculate_scenario(
        self,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        scenario: ScenarioType,
        base_growth_rates: Optional[List[float]] = None,
        years: int = 5,
    ) -> Dict:
        """
        Calculate DCF valuation for a specific scenario.

        Args:
            base_fcf: Base year FCF
            historical_fcf: Historical FCF for growth calculation
            cash: Cash and equivalents
            debt: Total debt
            diluted_shares: Diluted shares outstanding
            scenario: Scenario type
            base_growth_rates: Optional base growth rates (will be calculated if not provided)
            years: Number of projection years

        Returns:
            Dictionary with scenario valuation results

        Raises:
            ValueError: If inputs are invalid
        """
        try:
            # Validate inputs
            if diluted_shares <= 0:
                raise ValueError(f"Diluted shares must be positive. Got: {diluted_shares}")

            if base_fcf == 0:
                raise ValueError("Base FCF cannot be zero")

            if base_fcf < 0:
                raise ValueError(f"Base FCF cannot be negative. Got: {base_fcf:.2e}. DCF valuation requires positive cash flows.")

            # Calculate base growth rates if not provided
            if base_growth_rates is None:
                base_growth_rates = self.base_model.calculate_tiered_growth_rates(
                    historical_fcf, years
                )

            # Adjust parameters based on scenario
            adjusted_growth_rates = self._adjust_growth_rates(base_growth_rates, scenario)
            adjusted_wacc = self._adjust_wacc(self.base_model.wacc, scenario)
            adjusted_terminal_growth = self._adjust_terminal_growth(
                self.base_model.terminal_growth, scenario
            )

            # Create temporary model with adjusted parameters
            scenario_model = EnhancedDCFModel(
                wacc=adjusted_wacc,
                terminal_growth=adjusted_terminal_growth,
            )

            # Calculate valuation
            valuation = scenario_model.full_dcf_valuation(
                base_fcf=base_fcf,
                historical_fcf=historical_fcf,
                cash=cash,
                debt=debt,
                diluted_shares=diluted_shares,
                years=years,
                custom_growth_rates=adjusted_growth_rates,
                normalize_base=False,  # Already normalized in base case
            )

            # Add scenario metadata
            valuation["scenario_type"] = scenario.value
            valuation["probability"] = self.probabilities[scenario]
            valuation["scenario_label"] = scenario.name.capitalize()

            return valuation

        except Exception as e:
            raise ValueError(f"Error calculating {scenario.value} scenario: {str(e)}")

    def calculate_all_scenarios(
        self,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        years: int = 5,
        base_growth_rates: Optional[List[float]] = None,
    ) -> Dict[ScenarioType, Dict]:
        """
        Calculate all three scenarios (Pessimistic, Base, Optimistic).

        Args:
            base_fcf: Base year FCF
            historical_fcf: Historical FCF for growth calculation
            cash: Cash and equivalents
            debt: Total debt
            diluted_shares: Diluted shares outstanding
            years: Number of projection years
            base_growth_rates: Optional base growth rates

        Returns:
            Dictionary mapping scenario types to valuation results

        Raises:
            ValueError: If any scenario calculation fails
        """
        scenarios = {}
        errors = []

        for scenario_type in [ScenarioType.PESSIMISTIC, ScenarioType.BASE, ScenarioType.OPTIMISTIC]:
            try:
                scenarios[scenario_type] = self.calculate_scenario(
                    base_fcf=base_fcf,
                    historical_fcf=historical_fcf,
                    cash=cash,
                    debt=debt,
                    diluted_shares=diluted_shares,
                    scenario=scenario_type,
                    base_growth_rates=base_growth_rates,
                    years=years,
                )
            except Exception as e:
                errors.append(f"{scenario_type.name}: {str(e)}")

        if errors:
            raise ValueError(f"Failed to calculate scenarios: {'; '.join(errors)}")

        return scenarios

    def calculate_probability_weighted_value(
        self,
        scenarios: Dict[ScenarioType, Dict],
    ) -> float:
        """
        Calculate probability-weighted fair value per share.

        Args:
            scenarios: Dictionary of scenario results

        Returns:
            Probability-weighted fair value per share
        """
        weighted_value = 0.0

        for scenario_type, valuation in scenarios.items():
            probability = self.probabilities[scenario_type]
            fair_value = valuation["fair_value_per_share"]
            weighted_value += fair_value * probability

        return weighted_value

    def generate_risk_adjusted_recommendation(
        self,
        scenarios: Dict[ScenarioType, Dict],
        current_price: float,
        weighted_fair_value: float,
    ) -> Dict:
        """
        Generate risk-adjusted recommendation based on scenario analysis.

        Args:
            scenarios: Dictionary of scenario results
            current_price: Current market price
            weighted_fair_value: Probability-weighted fair value

        Returns:
            Dictionary with recommendation details
        """
        try:
            # Calculate upside/downside for each scenario
            pessimistic_fv = scenarios[ScenarioType.PESSIMISTIC]["fair_value_per_share"]
            base_fv = scenarios[ScenarioType.BASE]["fair_value_per_share"]
            optimistic_fv = scenarios[ScenarioType.OPTIMISTIC]["fair_value_per_share"]

            pessimistic_upside = ((pessimistic_fv - current_price) / current_price) * 100
            base_upside = ((base_fv - current_price) / current_price) * 100
            optimistic_upside = ((optimistic_fv - current_price) / current_price) * 100
            weighted_upside = ((weighted_fair_value - current_price) / current_price) * 100

            # Calculate range and risk metrics
            value_range = optimistic_fv - pessimistic_fv
            range_percentage = (value_range / base_fv) * 100
            downside_risk = ((current_price - pessimistic_fv) / current_price) * 100
            upside_potential = ((optimistic_fv - current_price) / current_price) * 100

            # Risk-adjusted recommendation logic
            if weighted_upside > 25 and pessimistic_upside > 0:
                recommendation = "STRONG BUY"
                confidence = "Alta"
                reasoning = (
                    f"Todos los escenarios muestran upside positivo. "
                    f"Incluso en el escenario pesimista hay {pessimistic_upside:.1f}% de potencial. "
                    f"El valor ponderado sugiere {weighted_upside:.1f}% de upside."
                )
                color = "#00CC00"

            elif weighted_upside > 15 and pessimistic_upside > -10:
                recommendation = "BUY"
                confidence = "Media-Alta"
                reasoning = (
                    f"El valor ponderado sugiere {weighted_upside:.1f}% de upside. "
                    f"El riesgo a la baja es limitado ({abs(pessimistic_upside):.1f}% en escenario pesimista). "
                    f"Relación riesgo/retorno favorable."
                )
                color = "#66CC66"

            elif weighted_upside > 5:
                recommendation = "HOLD"
                confidence = "Media"
                reasoning = (
                    f"Potencial moderado de {weighted_upside:.1f}%. "
                    f"El escenario pesimista muestra {pessimistic_upside:.1f}% de cambio. "
                    f"Relación riesgo/retorno equilibrada."
                )
                color = "#FFB366"

            elif weighted_upside > -5:
                recommendation = "HOLD"
                confidence = "Baja"
                reasoning = (
                    f"Valor cercano al precio actual ({weighted_upside:+.1f}%). "
                    f"Alta incertidumbre con rango de {range_percentage:.1f}% entre escenarios. "
                    f"Se recomienda esperar más claridad."
                )
                color = "#FF9933"

            elif pessimistic_upside < -15:
                recommendation = "STRONG SELL"
                confidence = "Alta"
                reasoning = (
                    f"Riesgo significativo a la baja. "
                    f"El escenario pesimista muestra {pessimistic_upside:.1f}% de caída potencial. "
                    f"El valor ponderado está {abs(weighted_upside):.1f}% por debajo del precio actual."
                )
                color = "#CC0000"

            else:
                recommendation = "SELL"
                confidence = "Media"
                reasoning = (
                    f"Sobrevaloración de {abs(weighted_upside):.1f}% según valor ponderado. "
                    f"El riesgo supera el potencial de retorno. "
                    f"Se recomienda reducir exposición."
                )
                color = "#FF3333"

            return {
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": reasoning,
                "color": color,
                "weighted_upside": weighted_upside,
                "pessimistic_upside": pessimistic_upside,
                "base_upside": base_upside,
                "optimistic_upside": optimistic_upside,
                "downside_risk": downside_risk,
                "upside_potential": upside_potential,
                "value_range": value_range,
                "range_percentage": range_percentage,
                "risk_reward_ratio": abs(upside_potential / downside_risk) if downside_risk != 0 else float('inf'),
            }

        except Exception as e:
            # Return conservative recommendation on error
            return {
                "recommendation": "HOLD",
                "confidence": "Indeterminada",
                "reasoning": f"No se pudo calcular recomendación: {str(e)}",
                "color": "#999999",
                "weighted_upside": 0.0,
                "error": str(e),
            }
