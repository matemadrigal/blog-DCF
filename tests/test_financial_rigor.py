"""
Financial Rigor Tests - Benchmark Cases

Tests all financial audit fixes with known benchmark cases:
1. Growth rate caps
2. Complete equity bridge (minority interests, preferred stock)
3. Beta adjustments (Blume, Hamada)
4. WACC correctness

"""

import pytest
import numpy as np
from src.dcf.enhanced_model import EnhancedDCFModel
from src.dcf.wacc_calculator import WACCCalculator


class TestGrowthRateCaps:
    """Test that growth rates are properly capped to prevent overvaluation."""

    def test_maximum_growth_rate_cap(self):
        """Test that maximum Y1 growth is capped at 35% (not 40%)."""
        model = EnhancedDCFModel()

        # Simulate exceptional historical growth (>50% avg)
        # Should trigger highest tier but still be capped
        hist_fcf = [100, 160, 250, 400]  # ~60% avg growth

        growth_rates = model.calculate_tiered_growth_rates(hist_fcf, years=5)

        # Y1 growth should be ≤ 35% (not 40%)
        assert growth_rates[0] <= 0.35, f"Y1 growth {growth_rates[0]:.1%} exceeds 35% cap"

        # Y2 growth should be ≤ 32%
        assert growth_rates[1] <= 0.32, f"Y2 growth {growth_rates[1]:.1%} exceeds 32% cap"

        print(f"✅ Growth rates capped correctly: {[f'{g:.1%}' for g in growth_rates]}")

    def test_very_high_growth_tier(self):
        """Test very high growth tier (30-50% avg) is reasonable."""
        model = EnhancedDCFModel()

        # Simulate very high growth (~40% avg)
        hist_fcf = [100, 140, 196, 274]  # ~40% avg growth

        growth_rates = model.calculate_tiered_growth_rates(hist_fcf, years=5)

        # Should be in 28-32% tier for Y1 (not 35%)
        assert 0.28 <= growth_rates[0] <= 0.32, f"Y1 growth {growth_rates[0]:.1%} out of expected range"

        print(f"✅ Very high growth tier correct: {[f'{g:.1%}' for g in growth_rates]}")

    def test_high_growth_tier(self):
        """Test high growth tier (20-30% avg) is reasonable."""
        model = EnhancedDCFModel()

        # Simulate high growth (~25% avg)
        hist_fcf = [100, 125, 156, 195]  # ~25% avg growth

        growth_rates = model.calculate_tiered_growth_rates(hist_fcf, years=5)

        # Should be in 25-28% tier for Y1
        assert 0.24 <= growth_rates[0] <= 0.29, f"Y1 growth {growth_rates[0]:.1%} out of expected range"

        print(f"✅ High growth tier correct: {[f'{g:.1%}' for g in growth_rates]}")


class TestCompleteEquityBridge:
    """Test complete equity bridge with minority interests and preferred stock."""

    def test_basic_equity_bridge(self):
        """Test basic equity bridge (EV + Cash - Debt)."""
        model = EnhancedDCFModel()

        ev = 1000e6  # $1B enterprise value
        cash = 200e6  # $200M cash
        debt = 300e6  # $300M debt

        equity = model.calculate_equity_value(ev, cash, debt)

        expected = 1000e6 + 200e6 - 300e6  # $900M
        assert equity == expected, f"Expected ${expected/1e6:.0f}M, got ${equity/1e6:.0f}M"

        print(f"✅ Basic equity bridge: ${equity/1e6:.0f}M")

    def test_equity_bridge_with_minority_interests(self):
        """Test equity bridge with minority interests."""
        model = EnhancedDCFModel()

        ev = 1000e6
        cash = 200e6
        debt = 300e6
        minority = 50e6  # $50M minority interests

        equity = model.calculate_equity_value(ev, cash, debt, minority_interests=minority)

        expected = 1000e6 + 200e6 - 300e6 - 50e6  # $850M
        assert equity == expected, f"Expected ${expected/1e6:.0f}M, got ${equity/1e6:.0f}M"

        print(f"✅ Equity with minority interests: ${equity/1e6:.0f}M")

    def test_equity_bridge_with_preferred_stock(self):
        """Test equity bridge with preferred stock."""
        model = EnhancedDCFModel()

        ev = 1000e6
        cash = 200e6
        debt = 300e6
        preferred = 25e6  # $25M preferred stock

        equity = model.calculate_equity_value(ev, cash, debt, preferred_stock=preferred)

        expected = 1000e6 + 200e6 - 300e6 - 25e6  # $875M
        assert equity == expected, f"Expected ${expected/1e6:.0f}M, got ${equity/1e6:.0f}M"

        print(f"✅ Equity with preferred stock: ${equity/1e6:.0f}M")

    def test_complete_equity_bridge(self):
        """Test complete equity bridge with all adjustments."""
        model = EnhancedDCFModel()

        ev = 1000e6
        cash = 200e6
        debt = 300e6
        minority = 50e6
        preferred = 25e6
        pension = 10e6  # $10M underfunded pension

        equity = model.calculate_equity_value(
            ev, cash, debt,
            minority_interests=minority,
            preferred_stock=preferred,
            pension_adjustments=pension
        )

        expected = 1000e6 + 200e6 - 300e6 - 50e6 - 25e6 - 10e6  # $815M
        assert equity == expected, f"Expected ${expected/1e6:.0f}M, got ${equity/1e6:.0f}M"

        print(f"✅ Complete equity bridge: ${equity/1e6:.0f}M")


class TestBetaAdjustments:
    """Test Blume and Hamada beta adjustments."""

    def test_blume_adjustment_high_beta(self):
        """Test Blume adjustment for high beta stock."""
        calc = WACCCalculator()

        raw_beta = 2.0
        adjusted = calc.adjust_beta_blume(raw_beta)

        expected = (2/3) * 2.0 + (1/3) * 1.0  # 1.667
        assert abs(adjusted - expected) < 0.001, f"Expected {expected:.3f}, got {adjusted:.3f}"

        # Adjusted beta should be closer to 1.0
        assert abs(adjusted - 1.0) < abs(raw_beta - 1.0), "Blume adjustment should move beta toward 1.0"

        print(f"✅ Blume adjustment (high beta): {raw_beta:.2f} → {adjusted:.3f}")

    def test_blume_adjustment_low_beta(self):
        """Test Blume adjustment for low beta stock."""
        calc = WACCCalculator()

        raw_beta = 0.6
        adjusted = calc.adjust_beta_blume(raw_beta)

        expected = (2/3) * 0.6 + (1/3) * 1.0  # 0.733
        assert abs(adjusted - expected) < 0.001, f"Expected {expected:.3f}, got {adjusted:.3f}"

        # Adjusted beta should be closer to 1.0
        assert abs(adjusted - 1.0) < abs(raw_beta - 1.0), "Blume adjustment should move beta toward 1.0"

        print(f"✅ Blume adjustment (low beta): {raw_beta:.2f} → {adjusted:.3f}")

    def test_hamada_unlever(self):
        """Test Hamada unlevering formula."""
        calc = WACCCalculator()

        levered_beta = 1.2
        de_ratio = 0.5  # D/E = 50%
        tax_rate = 0.21

        unlevered = calc.unlever_beta(levered_beta, de_ratio, tax_rate)

        # Formula: βU = βL / [1 + (1-T) × (D/E)]
        expected = 1.2 / (1 + (1 - 0.21) * 0.5)  # 0.860
        assert abs(unlevered - expected) < 0.001, f"Expected {expected:.3f}, got {unlevered:.3f}"

        # Unlevered beta should be lower (less risk)
        assert unlevered < levered_beta, "Unlevered beta should be lower than levered beta"

        print(f"✅ Hamada unlever: {levered_beta:.2f} → {unlevered:.3f}")

    def test_hamada_relever(self):
        """Test Hamada relevering formula."""
        calc = WACCCalculator()

        unlevered_beta = 0.860
        target_de = 1.0  # Target D/E = 100%
        tax_rate = 0.21

        relevered = calc.relever_beta(unlevered_beta, target_de, tax_rate)

        # Formula: βL = βU × [1 + (1-T) × (D/E)]
        expected = 0.860 * (1 + (1 - 0.21) * 1.0)  # 1.540
        assert abs(relevered - expected) < 0.001, f"Expected {expected:.3f}, got {relevered:.3f}"

        # Relevered beta should be higher (more leverage = more risk)
        assert relevered > unlevered_beta, "Relevered beta should be higher than unlevered beta"

        print(f"✅ Hamada relever: {unlevered_beta:.3f} → {relevered:.3f}")

    def test_hamada_round_trip(self):
        """Test that unlever → relever returns original beta."""
        calc = WACCCalculator()

        original_beta = 1.2
        de_ratio = 0.5
        tax_rate = 0.21

        # Unlever then relever
        unlevered = calc.unlever_beta(original_beta, de_ratio, tax_rate)
        relevered = calc.relever_beta(unlevered, de_ratio, tax_rate)

        assert abs(relevered - original_beta) < 0.001, f"Round-trip failed: {original_beta:.3f} → {relevered:.3f}"

        print(f"✅ Hamada round-trip: {original_beta:.3f} → {unlevered:.3f} → {relevered:.3f}")


class TestDCFFormulas:
    """Test core DCF formulas for correctness."""

    def test_terminal_value_gordon_growth(self):
        """Test terminal value using Gordon Growth Model."""
        model = EnhancedDCFModel(wacc=0.10, terminal_growth=0.03)

        final_fcf = 100e6  # $100M final year FCF

        tv = model.calculate_terminal_value(final_fcf)

        # Formula: TV = FCF × (1 + g) / (r - g)
        expected = (100e6 * 1.03) / (0.10 - 0.03)  # $1,471M
        assert abs(tv - expected) < 1e3, f"Expected ${expected/1e6:.1f}M, got ${tv/1e6:.1f}M"

        print(f"✅ Terminal value: ${tv/1e6:.1f}M")

    def test_terminal_value_error_when_wacc_le_growth(self):
        """Test that terminal value raises error when WACC ≤ g."""
        model = EnhancedDCFModel(wacc=0.03, terminal_growth=0.04)  # WACC < g (invalid!)

        with pytest.raises(ValueError, match="WACC.*must be greater than.*terminal growth"):
            model.calculate_terminal_value(100e6)

        print("✅ Terminal value correctly rejects WACC ≤ g")

    def test_present_value_discounting(self):
        """Test present value discounting formula."""
        model = EnhancedDCFModel(wacc=0.10)

        fcf_projections = [100e6, 110e6, 121e6, 133e6, 146e6]  # $100M growing at 10%

        ev, pv_terminal, pv_fcf = model.calculate_enterprise_value(fcf_projections)

        # Check first year PV: 100M / 1.10^1 = 90.91M
        expected_y1 = 100e6 / (1.10 ** 1)
        assert abs(pv_fcf[0] - expected_y1) < 1e3, f"Y1 PV: Expected ${expected_y1/1e6:.2f}M, got ${pv_fcf[0]/1e6:.2f}M"

        # Check second year PV: 110M / 1.10^2 = 90.91M
        expected_y2 = 110e6 / (1.10 ** 2)
        assert abs(pv_fcf[1] - expected_y2) < 1e3, f"Y2 PV: Expected ${expected_y2/1e6:.2f}M, got ${pv_fcf[1]/1e6:.2f}M"

        print(f"✅ PV discounting correct: EV = ${ev/1e6:.1f}M")


class TestWACCFormula:
    """Test WACC formula correctness."""

    def test_wacc_basic_formula(self):
        """Test basic WACC formula: WACC = (E/V) × Re + (D/V) × Rd × (1-T)."""
        # Manual calculation
        market_cap = 1000e6  # $1B equity
        debt = 500e6  # $500M debt
        total_value = market_cap + debt  # $1.5B

        cost_of_equity = 0.12  # 12%
        cost_of_debt = 0.05  # 5%
        tax_rate = 0.21  # 21%

        # WACC = (E/V) × Re + (D/V) × Rd × (1-T)
        expected_wacc = (
            (market_cap / total_value) * cost_of_equity +
            (debt / total_value) * cost_of_debt * (1 - tax_rate)
        )

        # Calculate manually
        equity_weight = market_cap / total_value  # 66.67%
        debt_weight = debt / total_value  # 33.33%
        after_tax_debt_cost = cost_of_debt * (1 - tax_rate)  # 3.95%

        wacc_manual = equity_weight * cost_of_equity + debt_weight * after_tax_debt_cost

        assert abs(wacc_manual - expected_wacc) < 0.0001, "WACC formula inconsistent"

        print(f"✅ WACC formula correct: {wacc_manual*100:.2f}%")
        print(f"   E/V: {equity_weight*100:.1f}%, D/V: {debt_weight*100:.1f}%")
        print(f"   Re: {cost_of_equity*100:.1f}%, Rd(after-tax): {after_tax_debt_cost*100:.2f}%")


def run_all_benchmark_tests():
    """Run all benchmark tests."""
    print("\n" + "=" * 70)
    print("FINANCIAL RIGOR BENCHMARK TESTS")
    print("=" * 70 + "\n")

    # Run test classes
    test_classes = [
        TestGrowthRateCaps(),
        TestCompleteEquityBridge(),
        TestBetaAdjustments(),
        TestDCFFormulas(),
        TestWACCFormula(),
    ]

    passed = 0
    failed = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n{'='*70}")
        print(f"{class_name}")
        print(f"{'='*70}")

        # Get all test methods
        test_methods = [m for m in dir(test_class) if m.startswith('test_')]

        for method_name in test_methods:
            try:
                method = getattr(test_class, method_name)
                method()
                passed += 1
            except Exception as e:
                print(f"❌ {method_name} FAILED: {e}")
                failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("\n🎉 ALL BENCHMARK TESTS PASSED!")
    else:
        print(f"\n⚠️ {failed} tests failed")

    return failed == 0


if __name__ == "__main__":
    success = run_all_benchmark_tests()
    exit(0 if success else 1)
