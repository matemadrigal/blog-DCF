"""
Tests for report calculation logic.

Testing pure calculation functions separated from rendering.
This ensures business logic correctness independent of PDF generation.
"""

import pytest
from src.reports.report_calculations import (
    ReportCalculations,
    DCFReportData,
    DDMReportData,
    RecommendationType,
    RecommendationColor,
)


class TestReportCalculations:
    """Test suite for ReportCalculations static methods."""

    def test_calculate_upside_undervalued(self):
        """Test upside calculation when stock is undervalued."""
        # Fair value $120, market $100 = 20% upside
        upside = ReportCalculations.calculate_upside(120.0, 100.0)
        assert upside == pytest.approx(20.0, rel=1e-9)

    def test_calculate_upside_overvalued(self):
        """Test upside calculation when stock is overvalued."""
        # Fair value $80, market $100 = -20% (overvalued)
        upside = ReportCalculations.calculate_upside(80.0, 100.0)
        assert upside == pytest.approx(-20.0, rel=1e-9)

    def test_calculate_upside_fairly_valued(self):
        """Test upside calculation when stock is fairly valued."""
        # Fair value $100, market $100 = 0% upside
        upside = ReportCalculations.calculate_upside(100.0, 100.0)
        assert upside == pytest.approx(0.0, rel=1e-9)

    def test_calculate_upside_zero_market_price(self):
        """Test upside with zero market price (edge case)."""
        upside = ReportCalculations.calculate_upside(100.0, 0.0)
        assert upside == 0.0

    def test_calculate_upside_large_divergence(self):
        """Test upside with extreme divergence."""
        # Fair value $200, market $100 = 100% upside
        upside = ReportCalculations.calculate_upside(200.0, 100.0)
        assert upside == pytest.approx(100.0, rel=1e-9)

    def test_get_recommendation_strong_buy(self):
        """Test recommendation for strong buy (>30% upside)."""
        rec, color = ReportCalculations.get_recommendation(35.0)
        assert rec == RecommendationType.STRONG_BUY
        assert color == RecommendationColor.STRONG_BUY

    def test_get_recommendation_buy(self):
        """Test recommendation for buy (15-30% upside)."""
        rec, color = ReportCalculations.get_recommendation(20.0)
        assert rec == RecommendationType.BUY
        assert color == RecommendationColor.BUY

    def test_get_recommendation_hold(self):
        """Test recommendation for hold (-15% to 15%)."""
        rec, color = ReportCalculations.get_recommendation(5.0)
        assert rec == RecommendationType.HOLD
        assert color == RecommendationColor.HOLD

        rec, color = ReportCalculations.get_recommendation(-5.0)
        assert rec == RecommendationType.HOLD
        assert color == RecommendationColor.HOLD

    def test_get_recommendation_sell(self):
        """Test recommendation for sell (-30% to -15%)."""
        rec, color = ReportCalculations.get_recommendation(-20.0)
        assert rec == RecommendationType.SELL
        assert color == RecommendationColor.SELL

    def test_get_recommendation_strong_sell(self):
        """Test recommendation for strong sell (<-30%)."""
        rec, color = ReportCalculations.get_recommendation(-35.0)
        assert rec == RecommendationType.STRONG_SELL
        assert color == RecommendationColor.STRONG_SELL

    def test_format_currency_basic(self):
        """Test basic currency formatting."""
        result = ReportCalculations.format_currency(1234567.89)
        assert result == "$1,234,567.89"

    def test_format_currency_with_suffix(self):
        """Test currency formatting with suffix."""
        result = ReportCalculations.format_currency(1.23, decimals=2, suffix="B")
        assert result == "$1.23B"

    def test_format_currency_negative(self):
        """Test currency formatting with negative value."""
        result = ReportCalculations.format_currency(-1234.56)
        assert result == "$-1,234.56"

    def test_format_percentage_decimal_input(self):
        """Test percentage formatting with decimal input (0.15 = 15%)."""
        result = ReportCalculations.format_percentage(0.15, decimals=2)
        assert result == "15.00%"

    def test_format_percentage_percentage_input(self):
        """Test percentage formatting with percentage input (15 = 15%)."""
        result = ReportCalculations.format_percentage(15.0, decimals=1)
        assert result == "15.0%"

    def test_calculate_discount_rate_spread(self):
        """Test WACC vs terminal growth spread calculation."""
        spread = ReportCalculations.calculate_discount_rate_spread(0.10, 0.03)
        assert spread == pytest.approx(7.0, rel=1e-9)

    def test_calculate_implied_perpetuity_multiple(self):
        """Test implied EV/FCF multiple in perpetuity."""
        multiple = ReportCalculations.calculate_implied_perpetuity_multiple(0.10, 0.03)
        # 1 / (0.10 - 0.03) = 14.285...
        assert multiple == pytest.approx(14.285714, rel=1e-5)

    def test_calculate_implied_perpetuity_multiple_invalid(self):
        """Test perpetuity multiple when WACC <= growth (invalid)."""
        multiple = ReportCalculations.calculate_implied_perpetuity_multiple(0.03, 0.05)
        assert multiple == 0.0


class TestDCFReportData:
    """Test suite for DCFReportData dataclass."""

    def test_dcf_report_data_creation(self):
        """Test creating valid DCFReportData."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            fair_value_total=3_000_000_000_000,  # $3T
            shares_outstanding=15_000_000_000,  # 15B shares
            market_price=200.0,
            wacc=0.08,
            terminal_growth=0.03,
            base_fcf=100_000_000_000,  # $100B
        )

        assert data.ticker == "AAPL"
        assert data.fair_value_total == 3_000_000_000_000

    def test_dcf_fair_value_per_share(self):
        """Test fair value per share calculation."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.08,
            terminal_growth=0.03,
            base_fcf=100_000_000_000,
        )

        # $3T / 15B shares = $200/share
        assert data.fair_value_per_share == pytest.approx(200.0, rel=1e-9)

    def test_dcf_market_cap(self):
        """Test market cap calculation."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.08,
            terminal_growth=0.03,
            base_fcf=100_000_000_000,
        )

        # $200 × 15B shares = $3T
        assert data.market_cap == pytest.approx(3_000_000_000_000, rel=1e-9)

    def test_dcf_enterprise_value(self):
        """Test enterprise value calculation (equity + net debt)."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.08,
            terminal_growth=0.03,
            base_fcf=100_000_000_000,
            total_debt=100_000_000_000,  # $100B debt
            cash=50_000_000_000,  # $50B cash
        )

        # EV = Equity + Net Debt = $3T + ($100B - $50B) = $3.05T
        expected_ev = 3_000_000_000_000 + (100_000_000_000 - 50_000_000_000)
        assert data.enterprise_value == pytest.approx(expected_ev, rel=1e-9)

    def test_dcf_invalid_shares(self):
        """Test validation: shares_outstanding must be positive."""
        with pytest.raises(ValueError, match="shares_outstanding must be positive"):
            DCFReportData(
                ticker="AAPL",
                company_name="Apple Inc.",
                fair_value_total=3_000_000_000_000,
                shares_outstanding=0,  # Invalid
                market_price=200.0,
                wacc=0.08,
                terminal_growth=0.03,
                base_fcf=100_000_000_000,
            )

    def test_dcf_invalid_wacc(self):
        """Test validation: WACC must be between 0 and 1."""
        with pytest.raises(ValueError, match="wacc must be between 0 and 1"):
            DCFReportData(
                ticker="AAPL",
                company_name="Apple Inc.",
                fair_value_total=3_000_000_000_000,
                shares_outstanding=15_000_000_000,
                market_price=200.0,
                wacc=1.5,  # Invalid (150%)
                terminal_growth=0.03,
                base_fcf=100_000_000_000,
            )

    def test_dcf_invalid_terminal_growth(self):
        """Test validation: terminal growth must be reasonable."""
        with pytest.raises(
            ValueError, match="terminal_growth must be between -10% and 10%"
        ):
            DCFReportData(
                ticker="AAPL",
                company_name="Apple Inc.",
                fair_value_total=3_000_000_000_000,
                shares_outstanding=15_000_000_000,
                market_price=200.0,
                wacc=0.08,
                terminal_growth=0.15,  # Invalid (15%)
                base_fcf=100_000_000_000,
            )


class TestDDMReportData:
    """Test suite for DDMReportData dataclass."""

    def test_ddm_report_data_creation(self):
        """Test creating valid DDMReportData."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            sector="Financial Services",
            fair_value_per_share=150.0,
            shares_outstanding=3_000_000_000,
            market_price=140.0,
            cost_of_equity=0.10,
            dividend_growth_rate=0.05,
            current_dividend=4.0,
        )

        assert data.ticker == "JPM"
        assert data.fair_value_per_share == 150.0

    def test_ddm_fair_value_total(self):
        """Test total equity value calculation."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            fair_value_per_share=150.0,
            shares_outstanding=3_000_000_000,  # 3B shares
            market_price=140.0,
            cost_of_equity=0.10,
            dividend_growth_rate=0.05,
            current_dividend=4.0,
        )

        # $150 × 3B shares = $450B
        assert data.fair_value_total == pytest.approx(450_000_000_000, rel=1e-9)

    def test_ddm_dividend_yield(self):
        """Test dividend yield based on fair value."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            fair_value_per_share=100.0,
            shares_outstanding=3_000_000_000,
            market_price=90.0,
            cost_of_equity=0.10,
            dividend_growth_rate=0.05,
            current_dividend=4.0,
        )

        # $4 / $100 = 4.0%
        assert data.dividend_yield == pytest.approx(0.04, rel=1e-9)

    def test_ddm_market_dividend_yield(self):
        """Test current market dividend yield."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            fair_value_per_share=100.0,
            shares_outstanding=3_000_000_000,
            market_price=80.0,
            cost_of_equity=0.10,
            dividend_growth_rate=0.05,
            current_dividend=4.0,
        )

        # $4 / $80 = 5.0%
        assert data.market_dividend_yield == pytest.approx(0.05, rel=1e-9)

    def test_ddm_invalid_cost_of_equity(self):
        """Test validation: cost of equity must be between 0 and 1."""
        with pytest.raises(ValueError, match="cost_of_equity must be between 0 and 1"):
            DDMReportData(
                ticker="JPM",
                company_name="JPMorgan Chase",
                fair_value_per_share=150.0,
                shares_outstanding=3_000_000_000,
                market_price=140.0,
                cost_of_equity=1.5,  # Invalid (150%)
                dividend_growth_rate=0.05,
                current_dividend=4.0,
            )


class TestValidationFunctions:
    """Test suite for validation functions."""

    def test_validate_dcf_sanity_healthy_model(self):
        """Test DCF sanity check with healthy parameters."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.08,  # 8%
            terminal_growth=0.03,  # 3% (5pp spread)
            base_fcf=100_000_000_000,
        )

        warnings = ReportCalculations.validate_dcf_sanity(data)
        assert len(warnings) == 0  # No warnings for healthy model

    def test_validate_dcf_sanity_low_spread(self):
        """Test DCF sanity check with low WACC-growth spread."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.05,  # 5%
            terminal_growth=0.03,  # 3% (only 2pp spread - too low!)
            base_fcf=100_000_000_000,
        )

        warnings = ReportCalculations.validate_dcf_sanity(data)
        assert len(warnings) > 0
        assert any("spread muy bajo" in w for w in warnings)

    def test_validate_dcf_sanity_high_terminal_growth(self):
        """Test DCF sanity check with unreasonably high terminal growth."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            fair_value_total=3_000_000_000_000,
            shares_outstanding=15_000_000_000,
            market_price=200.0,
            wacc=0.12,
            terminal_growth=0.08,  # 8% - too high for perpetuity!
            base_fcf=100_000_000_000,
        )

        warnings = ReportCalculations.validate_dcf_sanity(data)
        assert len(warnings) > 0
        assert any("Terminal growth muy alto" in w for w in warnings)

    def test_validate_dcf_sanity_negative_fcf(self):
        """Test DCF sanity check with negative base FCF."""
        data = DCFReportData(
            ticker="UBER",
            company_name="Uber Technologies",
            fair_value_total=50_000_000_000,
            shares_outstanding=2_000_000_000,
            market_price=25.0,
            wacc=0.10,
            terminal_growth=0.03,
            base_fcf=-1_000_000_000,  # Negative FCF!
        )

        warnings = ReportCalculations.validate_dcf_sanity(data)
        assert len(warnings) > 0
        assert any("FCF base negativo" in w for w in warnings)

    def test_validate_ddm_sanity_healthy_model(self):
        """Test DDM sanity check with healthy parameters."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            fair_value_per_share=150.0,
            shares_outstanding=3_000_000_000,
            market_price=140.0,
            cost_of_equity=0.10,  # 10%
            dividend_growth_rate=0.05,  # 5% (5pp spread)
            current_dividend=4.0,
            payout_ratio=0.30,
        )

        warnings = ReportCalculations.validate_ddm_sanity(data)
        assert len(warnings) == 0

    def test_validate_ddm_sanity_high_payout_ratio(self):
        """Test DDM sanity check with unsustainable payout ratio."""
        data = DDMReportData(
            ticker="T",
            company_name="AT&T",
            fair_value_per_share=20.0,
            shares_outstanding=7_000_000_000,
            market_price=18.0,
            cost_of_equity=0.08,
            dividend_growth_rate=0.03,
            current_dividend=1.5,
            payout_ratio=0.95,  # 95% - unsustainable!
        )

        warnings = ReportCalculations.validate_ddm_sanity(data)
        assert len(warnings) > 0
        assert any("Payout ratio muy alto" in w for w in warnings)

    def test_validate_ddm_sanity_no_dividend(self):
        """Test DDM sanity check with zero dividend."""
        data = DDMReportData(
            ticker="BRK.B",
            company_name="Berkshire Hathaway",
            fair_value_per_share=350.0,
            shares_outstanding=1_300_000_000,
            market_price=340.0,
            cost_of_equity=0.08,
            dividend_growth_rate=0.0,
            current_dividend=0.0,  # No dividend!
        )

        warnings = ReportCalculations.validate_ddm_sanity(data)
        assert len(warnings) > 0
        assert any("no paga dividendos" in w for w in warnings)


class TestRealWorldScenarios:
    """Test with real-world valuation scenarios."""

    def test_apple_dcf_scenario(self):
        """Test realistic Apple DCF valuation."""
        data = DCFReportData(
            ticker="AAPL",
            company_name="Apple Inc.",
            sector="Technology",
            fair_value_total=3_750_000_000_000,  # $3.75T
            shares_outstanding=15_000_000_000,
            market_price=250.0,
            wacc=0.088,
            terminal_growth=0.031,
            base_fcf=108_810_000_000,
            total_debt=120_000_000_000,
            cash=60_000_000_000,
            revenue=383_000_000_000,
        )

        # Fair value per share
        fair_value_ps = data.fair_value_per_share
        assert fair_value_ps == pytest.approx(250.0, rel=0.01)

        # Upside calculation
        upside = ReportCalculations.calculate_upside(fair_value_ps, data.market_price)
        assert upside == pytest.approx(0.0, abs=0.1)  # Fairly valued

        # Recommendation
        rec, _ = ReportCalculations.get_recommendation(upside)
        assert rec == RecommendationType.HOLD

        # Validation
        warnings = ReportCalculations.validate_dcf_sanity(data)
        # Should be minimal warnings for a well-structured model
        assert len(warnings) <= 1

    def test_jpmorgan_ddm_scenario(self):
        """Test realistic JPMorgan DDM valuation."""
        data = DDMReportData(
            ticker="JPM",
            company_name="JPMorgan Chase",
            sector="Financial Services",
            fair_value_per_share=217.02,
            shares_outstanding=2_900_000_000,
            market_price=306.74,
            cost_of_equity=0.1076,
            dividend_growth_rate=0.08,
            model_type="Gordon Growth Model",
            current_dividend=5.55,
            payout_ratio=0.30,
            roe=0.15,
            beta=1.13,
        )

        # Upside calculation
        upside = ReportCalculations.calculate_upside(
            data.fair_value_per_share, data.market_price
        )
        # Fair value $217, market $307 = -29.3% (overvalued by model)
        assert upside == pytest.approx(-29.26, rel=0.01)

        # Recommendation
        rec, _ = ReportCalculations.get_recommendation(upside)
        assert rec == RecommendationType.SELL

        # Dividend yield
        div_yield = data.dividend_yield
        # $5.55 / $217.02 = 2.56%
        assert div_yield == pytest.approx(0.0256, rel=0.01)
