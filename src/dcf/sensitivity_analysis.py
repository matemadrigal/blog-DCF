"""Sensitivity Analysis Module for DCF Valuation.

Provides scenario-based analysis (pessimistic, base, optimistic) with proper
financial mathematics and Monte Carlo simulation capabilities.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class ScenarioResult:
    """Results for a specific scenario."""

    scenario_name: str
    fair_value_per_share: float
    enterprise_value: float
    equity_value: float
    wacc: float
    terminal_growth: float
    growth_rates: List[float]
    projected_fcf: List[float]
    probability: float = 0.0  # Probability weight for the scenario


class SensitivityAnalyzer:
    """
    Professional sensitivity analysis for DCF valuations.

    Implements:
    - Three-scenario analysis (pessimistic/base/optimistic)
    - Mathematically rigorous adjustments
    - Monte Carlo simulation support
    - Probability-weighted expected values
    """

    def __init__(self):
        """Initialize sensitivity analyzer."""
        pass

    def calculate_scenarios(
        self,
        enhanced_model,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        base_wacc: float,
        base_terminal_growth: float,
        years: int = 5,
        normalize_base: bool = True,
        normalization_method: str = "weighted_average",
        custom_growth_rates: Optional[List[float]] = None,
    ) -> Dict[str, ScenarioResult]:
        """
        Calculate pessimistic, base, and optimistic scenarios.

        Scenario adjustments (based on financial best practices):
        - Pessimistic: WACC +200bp, Terminal Growth -100bp, FCF growth -30%
        - Base: Current parameters
        - Optimistic: WACC -100bp, Terminal Growth +50bp, FCF growth +20%

        Args:
            enhanced_model: Instance of EnhancedDCFModel
            base_fcf: Base year free cash flow
            historical_fcf: Historical FCF data
            cash: Cash and equivalents
            debt: Total debt
            diluted_shares: Diluted shares outstanding
            base_wacc: Base case WACC
            base_terminal_growth: Base case terminal growth
            years: Projection years
            normalize_base: Whether to normalize FCF
            normalization_method: Normalization method

        Returns:
            Dictionary with 'pessimistic', 'base', 'optimistic' scenario results
        """
        scenarios = {}

        # === BASE SCENARIO ===
        enhanced_model.wacc = base_wacc
        enhanced_model.terminal_growth = base_terminal_growth

        # Use custom growth rates if provided by user, otherwise let model calculate
        base_result = enhanced_model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf,
            cash=cash,
            debt=debt,
            diluted_shares=diluted_shares,
            years=years,
            custom_growth_rates=custom_growth_rates,  # Use user's custom rates for base case
            normalize_base=normalize_base,
            normalization_method=normalization_method,
        )

        scenarios["base"] = ScenarioResult(
            scenario_name="Base Case",
            fair_value_per_share=base_result["fair_value_per_share"],
            enterprise_value=base_result["enterprise_value"],
            equity_value=base_result["equity_value"],
            wacc=base_result["wacc"],
            terminal_growth=base_result["terminal_growth"],
            growth_rates=base_result["growth_rates"],
            projected_fcf=base_result["projected_fcf"],
            probability=0.50,  # 50% probability for base case
        )

        # === PESSIMISTIC SCENARIO ===
        # Financial rationale:
        # - Higher discount rate (risk premium increases)
        # - Lower terminal growth (market deterioration)
        # - Conservative FCF growth (operational challenges)

        pessimistic_wacc = min(base_wacc + 0.02, 0.20)  # +200bp, capped at 20%
        pessimistic_terminal_growth = max(
            base_terminal_growth - 0.01, 0.015
        )  # -100bp, floor at 1.5%

        # Ensure WACC > terminal growth
        if pessimistic_wacc <= pessimistic_terminal_growth:
            pessimistic_wacc = pessimistic_terminal_growth + 0.02

        enhanced_model.wacc = pessimistic_wacc
        enhanced_model.terminal_growth = pessimistic_terminal_growth

        # Calculate growth rates with 30% haircut
        # If user provided custom rates, use those as base; otherwise calculate
        if custom_growth_rates:
            base_growth_rates = custom_growth_rates
        else:
            base_growth_rates = enhanced_model.calculate_tiered_growth_rates(
                historical_fcf, years
            )
        pessimistic_growth_rates = [max(g * 0.70, 0.0) for g in base_growth_rates]

        pessimistic_result = enhanced_model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf,
            cash=cash,
            debt=debt,
            diluted_shares=diluted_shares,
            years=years,
            custom_growth_rates=pessimistic_growth_rates,
            normalize_base=normalize_base,
            normalization_method=normalization_method,
        )

        scenarios["pessimistic"] = ScenarioResult(
            scenario_name="Pessimistic",
            fair_value_per_share=pessimistic_result["fair_value_per_share"],
            enterprise_value=pessimistic_result["enterprise_value"],
            equity_value=pessimistic_result["equity_value"],
            wacc=pessimistic_result["wacc"],
            terminal_growth=pessimistic_result["terminal_growth"],
            growth_rates=pessimistic_result["growth_rates"],
            projected_fcf=pessimistic_result["projected_fcf"],
            probability=0.25,  # 25% probability for pessimistic
        )

        # === OPTIMISTIC SCENARIO ===
        # Financial rationale:
        # - Lower discount rate (reduced risk, market confidence)
        # - Higher terminal growth (favorable long-term outlook)
        # - Enhanced FCF growth (operational excellence)

        optimistic_wacc = max(base_wacc - 0.01, 0.05)  # -100bp, floor at 5%
        optimistic_terminal_growth = min(
            base_terminal_growth + 0.005, 0.06
        )  # +50bp, capped at 6%

        # Ensure WACC > terminal growth
        if optimistic_wacc <= optimistic_terminal_growth:
            optimistic_wacc = optimistic_terminal_growth + 0.02

        enhanced_model.wacc = optimistic_wacc
        enhanced_model.terminal_growth = optimistic_terminal_growth

        # Calculate growth rates with 20% boost
        optimistic_growth_rates = [min(g * 1.20, 0.50) for g in base_growth_rates]

        optimistic_result = enhanced_model.full_dcf_valuation(
            base_fcf=base_fcf,
            historical_fcf=historical_fcf,
            cash=cash,
            debt=debt,
            diluted_shares=diluted_shares,
            years=years,
            custom_growth_rates=optimistic_growth_rates,
            normalize_base=normalize_base,
            normalization_method=normalization_method,
        )

        scenarios["optimistic"] = ScenarioResult(
            scenario_name="Optimistic",
            fair_value_per_share=optimistic_result["fair_value_per_share"],
            enterprise_value=optimistic_result["enterprise_value"],
            equity_value=optimistic_result["equity_value"],
            wacc=optimistic_result["wacc"],
            terminal_growth=optimistic_result["terminal_growth"],
            growth_rates=optimistic_result["growth_rates"],
            projected_fcf=optimistic_result["projected_fcf"],
            probability=0.25,  # 25% probability for optimistic
        )

        # Reset model to base case
        enhanced_model.wacc = base_wacc
        enhanced_model.terminal_growth = base_terminal_growth

        return scenarios

    def calculate_probability_weighted_value(
        self, scenarios: Dict[str, ScenarioResult]
    ) -> float:
        """
        Calculate probability-weighted expected fair value.

        Args:
            scenarios: Dictionary of scenario results

        Returns:
            Probability-weighted fair value per share
        """
        weighted_value = 0.0
        total_probability = 0.0

        for scenario in scenarios.values():
            weighted_value += scenario.fair_value_per_share * scenario.probability
            total_probability += scenario.probability

        # Normalize if probabilities don't sum to 1
        if total_probability > 0 and abs(total_probability - 1.0) > 0.01:
            weighted_value = weighted_value / total_probability

        return weighted_value

    def calculate_value_range(
        self, scenarios: Dict[str, ScenarioResult]
    ) -> Tuple[float, float, float]:
        """
        Calculate value range (min, median, max) from scenarios.

        Args:
            scenarios: Dictionary of scenario results

        Returns:
            Tuple of (min_value, median_value, max_value)
        """
        values = [s.fair_value_per_share for s in scenarios.values()]
        return min(values), np.median(values), max(values)

    def calculate_sensitivity_table(
        self,
        enhanced_model,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        base_wacc: float,
        base_terminal_growth: float,
        wacc_range: List[float] = None,
        terminal_growth_range: List[float] = None,
        years: int = 5,
        normalize_base: bool = True,
        normalization_method: str = "weighted_average",
    ) -> np.ndarray:
        """
        Generate 2D sensitivity table (WACC vs Terminal Growth).

        Args:
            enhanced_model: Instance of EnhancedDCFModel
            base_fcf: Base year FCF
            historical_fcf: Historical FCF
            cash: Cash
            debt: Debt
            diluted_shares: Shares outstanding
            base_wacc: Base WACC
            base_terminal_growth: Base terminal growth
            wacc_range: List of WACC values to test (default: ±2% in 0.5% steps)
            terminal_growth_range: List of terminal growth values (default: ±1% in 0.25% steps)
            years: Projection years
            normalize_base: Whether to normalize
            normalization_method: Normalization method

        Returns:
            2D numpy array with fair values per share
        """
        # Default ranges
        if wacc_range is None:
            wacc_range = [
                base_wacc - 0.02,
                base_wacc - 0.01,
                base_wacc,
                base_wacc + 0.01,
                base_wacc + 0.02,
            ]

        if terminal_growth_range is None:
            terminal_growth_range = [
                base_terminal_growth - 0.01,
                base_terminal_growth - 0.005,
                base_terminal_growth,
                base_terminal_growth + 0.005,
                base_terminal_growth + 0.01,
            ]

        # Initialize result matrix
        sensitivity_matrix = np.zeros((len(wacc_range), len(terminal_growth_range)))

        # Calculate fair value for each combination
        for i, wacc in enumerate(wacc_range):
            for j, tg in enumerate(terminal_growth_range):
                # Skip invalid combinations (WACC <= terminal growth)
                if wacc <= tg:
                    sensitivity_matrix[i, j] = np.nan
                    continue

                enhanced_model.wacc = wacc
                enhanced_model.terminal_growth = tg

                try:
                    result = enhanced_model.full_dcf_valuation(
                        base_fcf=base_fcf,
                        historical_fcf=historical_fcf,
                        cash=cash,
                        debt=debt,
                        diluted_shares=diluted_shares,
                        years=years,
                        normalize_base=normalize_base,
                        normalization_method=normalization_method,
                    )
                    sensitivity_matrix[i, j] = result["fair_value_per_share"]
                except Exception:
                    sensitivity_matrix[i, j] = np.nan

        # Reset model
        enhanced_model.wacc = base_wacc
        enhanced_model.terminal_growth = base_terminal_growth

        return sensitivity_matrix

    def monte_carlo_simulation(
        self,
        enhanced_model,
        base_fcf: float,
        historical_fcf: List[float],
        cash: float,
        debt: float,
        diluted_shares: float,
        base_wacc: float,
        base_terminal_growth: float,
        n_simulations: int = 10000,
        wacc_std: float = 0.01,
        terminal_growth_std: float = 0.005,
        years: int = 5,
        normalize_base: bool = True,
        normalization_method: str = "weighted_average",
    ) -> Dict[str, any]:
        """
        Run Monte Carlo simulation for DCF valuation.

        Args:
            enhanced_model: EnhancedDCFModel instance
            base_fcf: Base FCF
            historical_fcf: Historical FCF
            cash: Cash
            debt: Debt
            diluted_shares: Shares
            base_wacc: Mean WACC
            base_terminal_growth: Mean terminal growth
            n_simulations: Number of simulations
            wacc_std: Standard deviation for WACC
            terminal_growth_std: Standard deviation for terminal growth
            years: Projection years
            normalize_base: Normalize FCF
            normalization_method: Normalization method

        Returns:
            Dictionary with simulation results
        """
        results = []

        for _ in range(n_simulations):
            # Sample WACC from normal distribution
            wacc = np.random.normal(base_wacc, wacc_std)
            wacc = max(0.05, min(0.20, wacc))  # Bound between 5% and 20%

            # Sample terminal growth from normal distribution
            tg = np.random.normal(base_terminal_growth, terminal_growth_std)
            tg = max(0.015, min(0.06, tg))  # Bound between 1.5% and 6%

            # Ensure WACC > terminal growth
            if wacc <= tg:
                continue

            enhanced_model.wacc = wacc
            enhanced_model.terminal_growth = tg

            try:
                result = enhanced_model.full_dcf_valuation(
                    base_fcf=base_fcf,
                    historical_fcf=historical_fcf,
                    cash=cash,
                    debt=debt,
                    diluted_shares=diluted_shares,
                    years=years,
                    normalize_base=normalize_base,
                    normalization_method=normalization_method,
                )
                results.append(result["fair_value_per_share"])
            except Exception:
                continue

        # Reset model
        enhanced_model.wacc = base_wacc
        enhanced_model.terminal_growth = base_terminal_growth

        # Calculate statistics
        results = np.array(results)

        return {
            "mean": np.mean(results),
            "median": np.median(results),
            "std": np.std(results),
            "min": np.min(results),
            "max": np.max(results),
            "percentile_5": np.percentile(results, 5),
            "percentile_25": np.percentile(results, 25),
            "percentile_75": np.percentile(results, 75),
            "percentile_95": np.percentile(results, 95),
            "n_simulations": len(results),
            "distribution": results,
        }
