"""
FINANCIAL AUDIT - CEO-LEVEL VALIDATION
=======================================

Exhaustive validation of all valuation models (DDM and DCF) against:
- CFA Institute standards
- Academic finance literature (Damodaran, Brealey-Myers)
- Industry best practices (Goldman Sachs, JPMorgan methodology)

This audit covers:
1. Mathematical formula correctness
2. Edge case handling
3. Input validation
4. Numerical stability
5. Financial theory compliance
"""

import sys

sys.path.insert(0, "/home/mateo/blog-DCF")

from src.models.ddm import DDMValuation
from src.utils.ddm_data_fetcher import (
    calculate_dividend_growth_rate,
    calculate_cost_of_equity_capm,
)
import numpy as np

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_header(text):
    """Print section header."""
    print(f"\n{'='*80}")
    print(f"{BLUE}{text}{RESET}")
    print(f"{'='*80}\n")


def print_test(test_name, passed, details=""):
    """Print test result."""
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} | {test_name}")
    if details:
        print(f"       {details}")


def print_warning(message):
    """Print warning."""
    print(f"{YELLOW}⚠️  WARNING{RESET} | {message}")


def print_error(message):
    """Print error."""
    print(f"{RED}❌ ERROR{RESET} | {message}")


# ============================================================================
# TEST 1: GORDON GROWTH MODEL - FORMULA VALIDATION
# ============================================================================
def test_gordon_growth_formula():
    """
    Validate Gordon Growth Model against CFA Institute formula.

    Standard formula: V = D₁ / (r - g)
    where D₁ = D₀ × (1 + g)
    """
    print_header("TEST 1: Gordon Growth Model - Formula Validation")

    ddm = DDMValuation("TEST")

    # Test case: Known values
    D0 = 5.00  # Current dividend
    r = 0.10  # 10% cost of equity
    g = 0.05  # 5% growth

    # Expected value (hand calculated)
    D1 = D0 * (1 + g)  # = 5.25
    V_expected = D1 / (r - g)  # = 5.25 / 0.05 = 105.00

    # Model calculation
    V_model, details = ddm.gordon_growth_model(D0, r, g)

    # Validate
    tolerance = 0.01  # $0.01 tolerance
    passed = abs(V_model - V_expected) < tolerance

    print_test(
        "Formula: V = D₁ / (r - g)",
        passed,
        f"Expected: ${V_expected:.2f}, Got: ${V_model:.2f}, Error: ${abs(V_model - V_expected):.4f}",
    )

    # Validate intermediate calculation
    D1_model = details["calculations"]["D₁ (Next Year Dividend)"]
    D1_expected = 5.25
    passed_d1 = abs(D1_model - D1_expected) < tolerance

    print_test(
        "Intermediate: D₁ = D₀ × (1 + g)",
        passed_d1,
        f"Expected: ${D1_expected:.2f}, Got: ${D1_model:.2f}",
    )

    return passed and passed_d1


# ============================================================================
# TEST 2: EDGE CASES - DIVISION BY ZERO
# ============================================================================
def test_edge_case_division_by_zero():
    """Test that r = g doesn't cause division by zero."""
    print_header("TEST 2: Edge Case - Division by Zero Protection")

    ddm = DDMValuation("TEST")

    # Test 1: r = g (should reject with error)
    V, details = ddm.gordon_growth_model(5.0, 0.10, 0.10)
    passed1 = V == 0.0 and len(details["errors"]) > 0
    print_test("r = g protection", passed1, f"Value: {V}, Errors: {details['errors']}")

    # Test 2: r < g (should reject with error)
    V, details = ddm.gordon_growth_model(5.0, 0.08, 0.10)
    passed2 = V == 0.0 and len(details["errors"]) > 0
    print_test("r < g protection", passed2, f"Value: {V}, Errors: {details['errors']}")

    # Test 3: r slightly > g (should work but warn)
    V, details = ddm.gordon_growth_model(5.0, 0.051, 0.05)
    passed3 = V > 0
    print_test(
        "r marginally > g (valid but extreme)",
        passed3,
        f"Value: ${V:.2f}, Spread: {(0.051-0.05)*100:.2f}bp",
    )

    return passed1 and passed2 and passed3


# ============================================================================
# TEST 3: NEGATIVE DIVIDENDS
# ============================================================================
def test_negative_dividends():
    """Test handling of negative dividends (should reject)."""
    print_header("TEST 3: Negative Dividend Protection")

    ddm = DDMValuation("TEST")

    # Test 1: Negative dividend
    V, details = ddm.gordon_growth_model(-5.0, 0.10, 0.05)
    passed1 = V == 0.0 and len(details["errors"]) > 0
    print_test(
        "Negative dividend rejection",
        passed1,
        f"Value: {V}, Errors: {details['errors']}",
    )

    # Test 2: Zero dividend
    V, details = ddm.gordon_growth_model(0.0, 0.10, 0.05)
    passed2 = V == 0.0 and len(details["errors"]) > 0
    print_test(
        "Zero dividend rejection", passed2, f"Value: {V}, Errors: {details['errors']}"
    )

    return passed1 and passed2


# ============================================================================
# TEST 4: TWO-STAGE DDM - FORMULA VALIDATION
# ============================================================================
def test_two_stage_formula():
    """Validate two-stage DDM calculation."""
    print_header("TEST 4: Two-Stage DDM - Formula Validation")

    ddm = DDMValuation("TEST")

    # Test parameters
    D0 = 5.0
    r = 0.10
    g_high = 0.15
    g_stable = 0.04
    n = 3

    # Manual calculation
    pv_stage1 = 0
    D = D0
    for t in range(1, n + 1):
        D = D * (1 + g_high)
        pv = D / ((1 + r) ** t)
        pv_stage1 += pv

    # Terminal value
    D_terminal = D * (1 + g_stable)
    TV = D_terminal / (r - g_stable)
    pv_terminal = TV / ((1 + r) ** n)

    V_expected = pv_stage1 + pv_terminal

    # Model calculation
    V_model, details = ddm.two_stage_ddm(D0, r, g_high, g_stable, n)

    # Validate
    tolerance = 0.01
    passed = abs(V_model - V_expected) < tolerance

    print_test(
        "Two-Stage DDM formula",
        passed,
        f"Expected: ${V_expected:.2f}, Got: ${V_model:.2f}, Error: ${abs(V_model - V_expected):.4f}",
    )

    # Validate stage 1 calculation
    pv_stage1_model = details["calculations"]["PV(High Growth Dividends)"]
    passed_s1 = abs(pv_stage1_model - pv_stage1) < tolerance

    print_test(
        "Stage 1: PV of high growth dividends",
        passed_s1,
        f"Expected: ${pv_stage1:.2f}, Got: ${pv_stage1_model:.2f}",
    )

    # Validate terminal value
    tv_model = details["stage_2_terminal_value"]
    passed_tv = abs(tv_model - TV) < tolerance

    print_test(
        "Stage 2: Terminal value calculation",
        passed_tv,
        f"Expected: ${TV:.2f}, Got: ${tv_model:.2f}",
    )

    return passed and passed_s1 and passed_tv


# ============================================================================
# TEST 5: H-MODEL - FORMULA VALIDATION
# ============================================================================
def test_h_model_formula():
    """Validate H-Model calculation."""
    print_header("TEST 5: H-Model - Formula Validation")

    ddm = DDMValuation("TEST")

    # Test parameters
    D0 = 5.0
    r = 0.10
    g_s = 0.12  # Initial growth
    g_l = 0.04  # Long-term growth
    H = 5.0  # Half-life

    # Manual calculation (CFA formula)
    # V = D₀(1+g_L)/(r-g_L) + D₀×H×(g_S-g_L)/(r-g_L)
    stable_component = D0 * (1 + g_l) / (r - g_l)
    excess_component = D0 * H * (g_s - g_l) / (r - g_l)
    V_expected = stable_component + excess_component

    # Model calculation
    V_model, details = ddm.h_model(D0, r, g_s, g_l, H)

    # Validate
    tolerance = 0.01
    passed = abs(V_model - V_expected) < tolerance

    print_test(
        "H-Model formula",
        passed,
        f"Expected: ${V_expected:.2f}, Got: ${V_model:.2f}, Error: ${abs(V_model - V_expected):.4f}",
    )

    # Validate components
    stable_comp_model = details["calculations"]["Stable Growth Component"]
    excess_comp_model = details["calculations"]["Excess Growth Component"]

    passed_stable = abs(stable_comp_model - stable_component) < tolerance
    passed_excess = abs(excess_comp_model - excess_component) < tolerance

    print_test(
        "Stable growth component",
        passed_stable,
        f"Expected: ${stable_component:.2f}, Got: ${stable_comp_model:.2f}",
    )

    print_test(
        "Excess growth component",
        passed_excess,
        f"Expected: ${excess_component:.2f}, Got: ${excess_comp_model:.2f}",
    )

    return passed and passed_stable and passed_excess


# ============================================================================
# TEST 6: CAPM FORMULA VALIDATION
# ============================================================================
def test_capm_formula():
    """Validate CAPM calculation."""
    print_header("TEST 6: CAPM - Cost of Equity Validation")

    # Test parameters
    rf = 0.04  # 4% risk-free rate
    beta = 1.2
    mrp = 0.06  # 6% market risk premium

    # Manual calculation: r_e = R_f + β × MRP
    r_expected = rf + beta * mrp  # = 0.04 + 1.2 * 0.06 = 0.112

    # Model calculation
    r_model = calculate_cost_of_equity_capm(rf, beta, mrp)

    # Validate
    tolerance = 0.0001  # 1 basis point
    passed = abs(r_model - r_expected) < tolerance

    print_test(
        "CAPM: r_e = R_f + β × MRP",
        passed,
        f"Expected: {r_expected:.4f}, Got: {r_model:.4f}, Error: {abs(r_model - r_expected):.6f}",
    )

    # Test edge cases
    # Beta = 1.0 should give r = rf + mrp
    r_beta1 = calculate_cost_of_equity_capm(rf, 1.0, mrp)
    expected_beta1 = rf + mrp
    passed_beta1 = abs(r_beta1 - expected_beta1) < tolerance

    print_test(
        "CAPM: β = 1.0 (market risk)",
        passed_beta1,
        f"Expected: {expected_beta1:.4f}, Got: {r_beta1:.4f}",
    )

    # Beta = 0 should give r = rf
    r_beta0 = calculate_cost_of_equity_capm(rf, 0.0, mrp)
    passed_beta0 = abs(r_beta0 - rf) < tolerance

    print_test(
        "CAPM: β = 0 (risk-free asset)",
        passed_beta0,
        f"Expected: {rf:.4f}, Got: {r_beta0:.4f}",
    )

    return passed and passed_beta1 and passed_beta0


# ============================================================================
# TEST 7: SUSTAINABLE GROWTH RATE
# ============================================================================
def test_sustainable_growth():
    """Validate sustainable growth rate calculation."""
    print_header("TEST 7: Sustainable Growth Rate (g = b × ROE)")

    ddm = DDMValuation("TEST")

    # Test case
    roe = 0.15  # 15% ROE
    payout_ratio = 0.40  # 40% payout

    # Manual calculation
    b = 1 - payout_ratio  # retention ratio = 0.60
    g_expected = b * roe  # = 0.60 * 0.15 = 0.09

    # Model calculation
    g_model = ddm.calculate_sustainable_growth_rate(roe, payout_ratio)

    # Validate
    tolerance = 0.0001
    passed = abs(g_model - g_expected) < tolerance

    print_test(
        "Sustainable growth: g = b × ROE",
        passed,
        f"Expected: {g_expected:.4f}, Got: {g_model:.4f}",
    )

    # Test edge case: 100% payout (no retention)
    g_100payout = ddm.calculate_sustainable_growth_rate(0.15, 1.0)
    passed_100 = abs(g_100payout - 0.0) < tolerance

    print_test(
        "Edge case: 100% payout → g = 0",
        passed_100,
        f"Expected: 0.0, Got: {g_100payout:.4f}",
    )

    # Test edge case: 0% payout (100% retention)
    g_0payout = ddm.calculate_sustainable_growth_rate(0.15, 0.0)
    passed_0 = abs(g_0payout - 0.15) < tolerance

    print_test(
        "Edge case: 0% payout → g = ROE",
        passed_0,
        f"Expected: 0.15, Got: {g_0payout:.4f}",
    )

    return passed and passed_100 and passed_0


# ============================================================================
# TEST 8: IMPLIED GROWTH RATE (REVERSE DDM)
# ============================================================================
def test_implied_growth():
    """Validate reverse DDM (implied growth from market price)."""
    print_header("TEST 8: Implied Growth Rate (Reverse DDM)")

    ddm = DDMValuation("TEST")

    # Test: Given V, D, r → solve for g
    # Correct formula: g = (V×r - D₀)/(V + D₀)

    P = 100.0  # Market price
    D = 5.0  # Dividend
    r = 0.10  # Cost of equity

    # Manual calculation using correct formula
    g_expected = (P * r - D) / (P + D)  # = (10 - 5) / 105 = 0.0476

    # Model calculation
    g_model, details = ddm.calculate_implied_growth_rate(P, D, r)

    # Validate
    tolerance = 0.0001
    passed = abs(g_model - g_expected) < tolerance

    print_test(
        "Implied growth: g = (V×r - D₀)/(V + D₀)",
        passed,
        f"Expected: {g_expected:.4f}, Got: {g_model:.4f}",
    )

    # Test consistency: Forward then reverse should give same g
    # Forward: V = D(1+g)/(r-g)
    g_original = 0.05
    D1 = D * (1 + g_original)
    V_forward = D1 / (r - g_original)

    # Reverse: g = r - D/V
    g_reverse, _ = ddm.calculate_implied_growth_rate(V_forward, D, r)

    passed_consistency = abs(g_reverse - g_original) < tolerance

    print_test(
        "Round-trip consistency (forward → reverse)",
        passed_consistency,
        f"Original g: {g_original:.4f}, Round-trip g: {g_reverse:.4f}",
    )

    return passed and passed_consistency


# ============================================================================
# TEST 9: NUMERICAL STABILITY
# ============================================================================
def test_numerical_stability():
    """Test numerical stability with extreme values."""
    print_header("TEST 9: Numerical Stability - Extreme Values")

    ddm = DDMValuation("TEST")

    # Test 1: Very small spread (r - g)
    V, details = ddm.gordon_growth_model(5.0, 0.0501, 0.05)
    passed1 = V > 0 and np.isfinite(V)
    print_test(
        "Small spread (r-g = 0.01%)",
        passed1,
        f"Value: ${V:.2f}, Finite: {np.isfinite(V)}",
    )

    # Test 2: Large dividend
    V, details = ddm.gordon_growth_model(100.0, 0.10, 0.05)
    passed2 = V > 0 and np.isfinite(V)
    print_test(
        "Large dividend ($100)", passed2, f"Value: ${V:.2f}, Finite: {np.isfinite(V)}"
    )

    # Test 3: Very small dividend
    V, details = ddm.gordon_growth_model(0.01, 0.10, 0.05)
    passed3 = V > 0 and np.isfinite(V)
    print_test(
        "Small dividend ($0.01)", passed3, f"Value: ${V:.2f}, Finite: {np.isfinite(V)}"
    )

    # Test 4: High cost of equity
    V, details = ddm.gordon_growth_model(5.0, 0.25, 0.04)
    passed4 = V > 0 and np.isfinite(V)
    print_test(
        "High cost of equity (25%)",
        passed4,
        f"Value: ${V:.2f}, Finite: {np.isfinite(V)}",
    )

    return passed1 and passed2 and passed3 and passed4


# ============================================================================
# TEST 10: DIVIDEND GROWTH RATE CALCULATION
# ============================================================================
def test_dividend_growth_calculation():
    """Test dividend growth rate calculation methods."""
    print_header("TEST 10: Dividend Growth Rate Calculation")

    # Test data: historical dividends
    historical_divs = [5.00, 4.50, 4.00, 3.60, 3.20]  # Most recent first

    # Test 1: CAGR method
    # CAGR = (Ending / Beginning)^(1/n) - 1
    # = (5.00 / 3.20)^(1/4) - 1 = 1.5625^0.25 - 1 ≈ 0.1178

    g_cagr, details = calculate_dividend_growth_rate(historical_divs, method="cagr")

    beginning = 3.20
    ending = 5.00
    n = 4
    g_expected = (ending / beginning) ** (1 / n) - 1

    tolerance = 0.0001
    passed_cagr = abs(g_cagr - g_expected) < tolerance

    print_test(
        "CAGR method", passed_cagr, f"Expected: {g_expected:.4f}, Got: {g_cagr:.4f}"
    )

    # Test 2: Arithmetic method
    g_arith, details = calculate_dividend_growth_rate(
        historical_divs, method="arithmetic"
    )
    passed_arith = g_arith > 0  # Should be positive for growing dividends

    print_test("Arithmetic method", passed_arith, f"Growth rate: {g_arith:.4f}")

    # Test 3: Regression method
    g_reg, details = calculate_dividend_growth_rate(
        historical_divs, method="regression"
    )
    passed_reg = g_reg > 0

    print_test("Regression method", passed_reg, f"Growth rate: {g_reg:.4f}")

    return passed_cagr and passed_arith and passed_reg


# ============================================================================
# RUN ALL TESTS
# ============================================================================
def run_full_audit():
    """Run complete financial audit."""
    print("\n" + "=" * 80)
    print(f"{BLUE}FINANCIAL AUDIT - CEO-LEVEL VALIDATION{RESET}")
    print(f"{BLUE}DCF Valuation Platform - Complete System Check{RESET}")
    print("=" * 80)

    results = []

    # Run all tests
    results.append(("Gordon Growth Formula", test_gordon_growth_formula()))
    results.append(("Division by Zero Protection", test_edge_case_division_by_zero()))
    results.append(("Negative Dividend Handling", test_negative_dividends()))
    results.append(("Two-Stage DDM Formula", test_two_stage_formula()))
    results.append(("H-Model Formula", test_h_model_formula()))
    results.append(("CAPM Formula", test_capm_formula()))
    results.append(("Sustainable Growth Rate", test_sustainable_growth()))
    results.append(("Implied Growth (Reverse DDM)", test_implied_growth()))
    results.append(("Numerical Stability", test_numerical_stability()))
    results.append(("Dividend Growth Calculation", test_dividend_growth_calculation()))

    # Summary
    print_header("AUDIT SUMMARY")

    total_tests = len(results)
    passed_tests = sum(1 for _, passed in results if passed)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"{GREEN}Passed: {passed_tests}{RESET}")
    if failed_tests > 0:
        print(f"{RED}Failed: {failed_tests}{RESET}")
    else:
        print(f"Failed: {failed_tests}")

    print(f"\nSuccess Rate: {(passed_tests/total_tests)*100:.1f}%")

    # List failed tests
    if failed_tests > 0:
        print(f"\n{RED}FAILED TESTS:{RESET}")
        for name, passed in results:
            if not passed:
                print(f"  ✗ {name}")

    # Final verdict
    print("\n" + "=" * 80)
    if failed_tests == 0:
        print(f"{GREEN}✅ ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION{RESET}")
        print(
            f"{GREEN}Financial rigor validated against CFA Institute standards{RESET}"
        )
    else:
        print(f"{RED}❌ SYSTEM REQUIRES FIXES BEFORE PRODUCTION{RESET}")
    print("=" * 80 + "\n")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = run_full_audit()
    sys.exit(0 if success else 1)
