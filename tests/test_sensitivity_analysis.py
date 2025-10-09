"""Test suite for sensitivity analysis module.

Validates:
- Mathematical correctness of scenario calculations
- Financial formula accuracy
- Probability-weighted calculations
- Range validations
"""

import pytest
import numpy as np
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.sensitivity_analysis import SensitivityAnalyzer, ScenarioResult


class TestSensitivityAnalyzer:
    """Test sensitivity analysis functionality."""

    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return {
            "base_fcf": 10_000_000_000,  # $10B
            "historical_fcf": [
                10_000_000_000,
                9_000_000_000,
                8_500_000_000,
                8_000_000_000,
            ],
            "cash": 50_000_000_000,  # $50B
            "debt": 30_000_000_000,  # $30B
            "diluted_shares": 5_000_000_000,  # 5B shares
            "base_wacc": 0.08,
            "base_terminal_growth": 0.035,
            "years": 5,
        }

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance."""
        return SensitivityAnalyzer()

    @pytest.fixture
    def enhanced_model(self, sample_data):
        """Create enhanced model instance."""
        return EnhancedDCFModel(
            wacc=sample_data["base_wacc"],
            terminal_growth=sample_data["base_terminal_growth"],
        )

    def test_scenario_calculation(self, analyzer, enhanced_model, sample_data):
        """Test that scenarios are calculated correctly."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        # Check all scenarios exist
        assert "pessimistic" in scenarios
        assert "base" in scenarios
        assert "optimistic" in scenarios

        # Check scenarios are ScenarioResult instances
        for scenario in scenarios.values():
            assert isinstance(scenario, ScenarioResult)

        # Check fair values are positive
        for scenario in scenarios.values():
            assert scenario.fair_value_per_share > 0
            assert scenario.enterprise_value > 0
            assert scenario.equity_value > 0

    def test_scenario_ordering(self, analyzer, enhanced_model, sample_data):
        """Test that pessimistic < base < optimistic."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        pess_fv = scenarios["pessimistic"].fair_value_per_share
        base_fv = scenarios["base"].fair_value_per_share
        opt_fv = scenarios["optimistic"].fair_value_per_share

        # Pessimistic should be lower than base
        assert (
            pess_fv < base_fv
        ), f"Pessimistic ({pess_fv}) should be < base ({base_fv})"

        # Optimistic should be higher than base
        assert opt_fv > base_fv, f"Optimistic ({opt_fv}) should be > base ({base_fv})"

    def test_wacc_adjustments(self, analyzer, enhanced_model, sample_data):
        """Test WACC adjustments are correct."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        base_wacc = sample_data["base_wacc"]

        # Pessimistic: WACC should be higher (+200bp)
        pess_wacc = scenarios["pessimistic"].wacc
        assert pess_wacc > base_wacc, "Pessimistic WACC should be higher than base"
        assert np.isclose(pess_wacc, base_wacc + 0.02, atol=0.001)

        # Optimistic: WACC should be lower (-100bp)
        opt_wacc = scenarios["optimistic"].wacc
        assert opt_wacc < base_wacc, "Optimistic WACC should be lower than base"
        assert np.isclose(opt_wacc, base_wacc - 0.01, atol=0.001)

    def test_terminal_growth_adjustments(self, analyzer, enhanced_model, sample_data):
        """Test terminal growth adjustments are correct."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        base_tg = sample_data["base_terminal_growth"]

        # Pessimistic: terminal growth should be lower (-100bp)
        pess_tg = scenarios["pessimistic"].terminal_growth
        assert pess_tg < base_tg, "Pessimistic terminal growth should be lower"

        # Optimistic: terminal growth should be higher (+50bp)
        opt_tg = scenarios["optimistic"].terminal_growth
        assert opt_tg > base_tg, "Optimistic terminal growth should be higher"

    def test_wacc_greater_than_terminal_growth(
        self, analyzer, enhanced_model, sample_data
    ):
        """Test WACC > terminal growth for all scenarios (financial validity)."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        for scenario_name, scenario in scenarios.items():
            assert (
                scenario.wacc > scenario.terminal_growth
            ), f"{scenario_name}: WACC ({scenario.wacc}) must be > terminal growth ({scenario.terminal_growth})"

    def test_probability_weighted_value(self, analyzer, enhanced_model, sample_data):
        """Test probability-weighted expected value calculation."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        prob_weighted = analyzer.calculate_probability_weighted_value(scenarios)

        # Manual calculation
        expected_value = (
            scenarios["pessimistic"].fair_value_per_share * 0.25
            + scenarios["base"].fair_value_per_share * 0.50
            + scenarios["optimistic"].fair_value_per_share * 0.25
        )

        assert np.isclose(
            prob_weighted, expected_value, rtol=0.01
        ), f"Probability-weighted value {prob_weighted} != expected {expected_value}"

        # Weighted value should be between pessimistic and optimistic
        assert scenarios["pessimistic"].fair_value_per_share <= prob_weighted
        assert prob_weighted <= scenarios["optimistic"].fair_value_per_share

    def test_value_range(self, analyzer, enhanced_model, sample_data):
        """Test value range calculation."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        min_val, median_val, max_val = analyzer.calculate_value_range(scenarios)

        # Check ordering
        assert min_val <= median_val <= max_val

        # Min should be pessimistic
        assert min_val == scenarios["pessimistic"].fair_value_per_share

        # Max should be optimistic
        assert max_val == scenarios["optimistic"].fair_value_per_share

    def test_probabilities_sum_to_one(self, analyzer, enhanced_model, sample_data):
        """Test that scenario probabilities sum to 1.0."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        total_prob = sum(s.probability for s in scenarios.values())

        assert np.isclose(
            total_prob, 1.0, atol=0.001
        ), f"Probabilities sum to {total_prob}, expected 1.0"

    def test_equity_value_calculation(self, analyzer, enhanced_model, sample_data):
        """Test equity value = enterprise value + cash - debt."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        for scenario_name, scenario in scenarios.items():
            expected_equity = (
                scenario.enterprise_value + sample_data["cash"] - sample_data["debt"]
            )

            assert np.isclose(
                scenario.equity_value, expected_equity, rtol=0.01
            ), f"{scenario_name}: Equity value mismatch"

    def test_fair_value_per_share_calculation(
        self, analyzer, enhanced_model, sample_data
    ):
        """Test fair value per share = equity value / shares."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        for scenario_name, scenario in scenarios.items():
            expected_fv_per_share = (
                scenario.equity_value / sample_data["diluted_shares"]
            )

            assert np.isclose(
                scenario.fair_value_per_share, expected_fv_per_share, rtol=0.01
            ), f"{scenario_name}: Fair value per share mismatch"

    def test_growth_rate_adjustments(self, analyzer, enhanced_model, sample_data):
        """Test FCF growth rate adjustments for scenarios."""
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=sample_data["base_fcf"],
            historical_fcf=sample_data["historical_fcf"],
            cash=sample_data["cash"],
            debt=sample_data["debt"],
            diluted_shares=sample_data["diluted_shares"],
            base_wacc=sample_data["base_wacc"],
            base_terminal_growth=sample_data["base_terminal_growth"],
            years=sample_data["years"],
        )

        base_avg_growth = np.mean(scenarios["base"].growth_rates)
        pess_avg_growth = np.mean(scenarios["pessimistic"].growth_rates)
        opt_avg_growth = np.mean(scenarios["optimistic"].growth_rates)

        # Pessimistic should have lower average growth
        assert (
            pess_avg_growth < base_avg_growth
        ), "Pessimistic average growth should be lower"

        # Optimistic should have higher average growth
        assert (
            opt_avg_growth > base_avg_growth
        ), "Optimistic average growth should be higher"

    def test_scenario_with_edge_case_wacc(self, analyzer, enhanced_model):
        """Test scenarios with edge case WACC values."""
        # Very high WACC (near cap)
        scenarios_high = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=10_000_000_000,
            historical_fcf=[10_000_000_000],
            cash=50_000_000_000,
            debt=30_000_000_000,
            diluted_shares=5_000_000_000,
            base_wacc=0.18,  # 18% - very high
            base_terminal_growth=0.03,
            years=5,
        )

        # Should not exceed 20% cap
        assert scenarios_high["pessimistic"].wacc <= 0.20

        # Very low WACC (near floor)
        scenarios_low = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=10_000_000_000,
            historical_fcf=[10_000_000_000],
            cash=50_000_000_000,
            debt=30_000_000_000,
            diluted_shares=5_000_000_000,
            base_wacc=0.06,  # 6% - very low
            base_terminal_growth=0.025,
            years=5,
        )

        # Should not go below 5% floor
        assert scenarios_low["optimistic"].wacc >= 0.05

    def test_scenario_with_negative_fcf(self, analyzer, enhanced_model):
        """Test scenarios handle companies with negative FCF gracefully."""
        # Company with improving but negative FCF
        scenarios = analyzer.calculate_scenarios(
            enhanced_model=enhanced_model,
            base_fcf=-1_000_000_000,  # Negative $1B
            historical_fcf=[-1_000_000_000, -2_000_000_000, -3_000_000_000],
            cash=10_000_000_000,
            debt=5_000_000_000,
            diluted_shares=1_000_000_000,
            base_wacc=0.12,  # Higher WACC for riskier company
            base_terminal_growth=0.02,
            years=5,
        )

        # Should complete without errors
        assert "pessimistic" in scenarios
        assert "base" in scenarios
        assert "optimistic" in scenarios

        # Values may be negative or very low, but should be calculated
        for scenario in scenarios.values():
            assert scenario.fair_value_per_share is not None
            assert not np.isnan(scenario.fair_value_per_share)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
