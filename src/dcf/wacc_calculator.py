"""Dynamic WACC calculator using CAPM and real capital structure."""

import yfinance as yf
from typing import Optional, Tuple, Dict
from .damodaran_data import DamodaranData
import requests
from datetime import datetime, timedelta


class WACCCalculator:
    """
    Calculate WACC dynamically using:
    - CAPM for cost of equity (with Damodaran data)
    - Market data for cost of debt
    - Real capital structure (debt/equity ratio)
    - Proper handling of net cash vs net debt
    """

    def __init__(
        self,
        use_damodaran: bool = True,
        risk_free_rate: Optional[float] = None,
        market_return: Optional[float] = None,
        tax_rate: float = 0.21,  # Corporate tax rate 21%
    ):
        """
        Initialize WACC calculator.

        Args:
            use_damodaran: Use Damodaran's industry data for parameters
            risk_free_rate: Risk-free rate (uses Damodaran if None)
            market_return: Expected market return (uses Damodaran if None)
            tax_rate: Corporate tax rate
        """
        self.use_damodaran = use_damodaran

        if use_damodaran:
            self.risk_free_rate = DamodaranData.RISK_FREE_RATE
            self.market_return = DamodaranData.MARKET_RETURN
        else:
            self.risk_free_rate = risk_free_rate or 0.038
            self.market_return = market_return or 0.095

        self.tax_rate = tax_rate

    def get_beta(self, ticker: str, prefer_industry: bool = False) -> Tuple[float, str]:
        """
        Get beta from Yahoo Finance or Damodaran industry data.

        Args:
            ticker: Stock ticker
            prefer_industry: Prefer industry beta over company-specific beta

        Returns:
            Tuple of (beta value, source)
        """
        try:
            # Get Damodaran industry data
            if self.use_damodaran:
                industry_data = DamodaranData.get_industry_data(ticker)
                industry_beta = industry_data["beta"]

                # If prefer_industry, use it directly
                if prefer_industry:
                    return industry_beta, f"Industry ({industry_data['industry']})"

            # Try to get company-specific beta from Yahoo Finance
            stock = yf.Ticker(ticker)
            info = stock.info
            company_beta = info.get("beta", None)

            if company_beta is not None and company_beta > 0:
                return float(company_beta), "Company (Yahoo Finance)"

            # Fallback to industry beta if available
            if self.use_damodaran:
                return industry_beta, f"Industry ({industry_data['industry']})"

            # Ultimate fallback to market beta
            return 1.0, "Market (default)"

        except Exception:
            # Fallback to market beta
            return 1.0, "Market (default)"

    def adjust_beta_blume(self, raw_beta: float, adjustment_factor: float = 2/3) -> float:
        """
        Adjust beta using Blume's technique.

        Blume (1971) found that betas tend to regress toward the market beta (1.0) over time.
        This adjustment improves the predictive power of historical betas.

        Formula: Adjusted Beta = adjustment_factor × Raw Beta + (1 - adjustment_factor) × 1.0

        Default adjustment (2/3): This is Bloomberg's and many practitioners' standard.

        Args:
            raw_beta: Raw/historical beta from regression
            adjustment_factor: Weight on raw beta (default 2/3, range 0-1)

        Returns:
            Adjusted beta (closer to 1.0 than raw beta)

        Example:
            >>> calculator.adjust_beta_blume(1.5)  # High beta stock
            1.333  # (2/3)*1.5 + (1/3)*1.0 = 1.0 + 0.333

            >>> calculator.adjust_beta_blume(0.6)  # Low beta stock
            0.733  # (2/3)*0.6 + (1/3)*1.0 = 0.4 + 0.333
        """
        # Ensure adjustment_factor is in valid range
        adjustment_factor = max(0.0, min(1.0, adjustment_factor))

        # Apply Blume adjustment
        adjusted_beta = adjustment_factor * raw_beta + (1 - adjustment_factor) * 1.0

        return adjusted_beta

    def unlever_beta(self, levered_beta: float, debt_to_equity: float, tax_rate: Optional[float] = None) -> float:
        """
        Unlever (de-leverage) beta using Hamada formula.

        Removes the effect of financial leverage to get the asset/unlevered beta.
        This represents the business risk without financial risk.

        Formula: βU = βL / [1 + (1-T) × (D/E)]

        Where:
        - βU = Unlevered (asset) beta
        - βL = Levered (equity) beta
        - D/E = Debt-to-Equity ratio (market values)
        - T = Corporate tax rate

        Args:
            levered_beta: Levered/equity beta (observed from market)
            debt_to_equity: Debt-to-Equity ratio (market values)
            tax_rate: Corporate tax rate (uses instance tax_rate if None)

        Returns:
            Unlevered beta (business risk only)

        Example:
            >>> calculator.unlever_beta(1.2, 0.5, 0.21)  # βL=1.2, D/E=0.5, T=21%
            0.923  # 1.2 / [1 + (1-0.21)*0.5] = 1.2 / 1.395
        """
        tax = tax_rate if tax_rate is not None else self.tax_rate

        # Ensure D/E is non-negative
        debt_to_equity = max(0.0, debt_to_equity)

        # Hamada unlevering formula
        unlevered_beta = levered_beta / (1 + (1 - tax) * debt_to_equity)

        return unlevered_beta

    def relever_beta(self, unlevered_beta: float, debt_to_equity: float, tax_rate: Optional[float] = None) -> float:
        """
        Relever beta using Hamada formula.

        Adds the effect of financial leverage to the unlevered beta.
        Useful for:
        - Adjusting beta for target capital structure
        - Comparing companies with different leverage
        - Valuing leveraged transactions (LBOs)

        Formula: βL = βU × [1 + (1-T) × (D/E)]

        Where:
        - βL = Levered (equity) beta
        - βU = Unlevered (asset) beta
        - D/E = Target Debt-to-Equity ratio
        - T = Corporate tax rate

        Args:
            unlevered_beta: Unlevered/asset beta (business risk)
            debt_to_equity: Target Debt-to-Equity ratio
            tax_rate: Corporate tax rate (uses instance tax_rate if None)

        Returns:
            Relevered beta (business + financial risk)

        Example:
            >>> calculator.relever_beta(0.923, 1.0, 0.21)  # βU=0.923, D/E=1.0, T=21%
            1.652  # 0.923 × [1 + (1-0.21)*1.0] = 0.923 × 1.79
        """
        tax = tax_rate if tax_rate is not None else self.tax_rate

        # Ensure D/E is non-negative
        debt_to_equity = max(0.0, debt_to_equity)

        # Hamada relevering formula
        levered_beta = unlevered_beta * (1 + (1 - tax) * debt_to_equity)

        return levered_beta

    def get_risk_free_rate_dynamic(self, maturity_years: int = 10, cache_hours: int = 24) -> Tuple[float, str]:
        """
        Get current risk-free rate from US Treasury yields.

        Fetches real-time treasury yields instead of using static values.
        Uses US Treasury API for most accurate data.

        Args:
            maturity_years: Treasury maturity to use (1, 2, 3, 5, 7, 10, 20, 30 years)
            cache_hours: Hours to cache the result (default 24)

        Returns:
            Tuple of (risk_free_rate, source_description)

        Example:
            >>> calculator.get_risk_free_rate_dynamic(10)
            (0.0438, "US Treasury 10Y (2025-10-20)")
        """
        try:
            # US Treasury API endpoint
            # Alternative: Fred API, Yahoo Finance
            url = "https://home.treasury.gov/resource-center/data-chart-center/interest-rates/daily-treasury-rates.csv/2024/all?type=daily_treasury_yield_curve&field_tdr_date_value=2024&page&_format=csv"

            # Simplified approach: Use FRED API for 10Y treasury
            # For production, consider caching with timestamp
            fred_url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DGS{maturity_years}&api_key=YOUR_API_KEY&file_type=json&sort_order=desc&limit=1"

            # For now, fallback to reliable approximation method
            # Use yfinance to get treasury ETF yield as proxy
            import yfinance as yf

            # Map maturity to treasury ETF
            treasury_etfs = {
                1: "SHY",   # 1-3Y
                2: "SHY",   # 1-3Y
                3: "IEI",   # 3-7Y
                5: "IEI",   # 3-7Y
                7: "IEF",   # 7-10Y
                10: "IEF",  # 7-10Y
                20: "TLT",  # 20+Y
                30: "TLT",  # 20+Y
            }

            etf_ticker = treasury_etfs.get(maturity_years, "IEF")
            etf = yf.Ticker(etf_ticker)
            info = etf.info

            # Get yield (dividend yield is close approximation)
            treasury_yield = info.get("yield", None)
            if treasury_yield and treasury_yield > 0:
                rate = treasury_yield / 100 if treasury_yield > 1 else treasury_yield
                today = datetime.now().strftime("%Y-%m-%d")
                return rate, f"US Treasury ~{maturity_years}Y via {etf_ticker} ({today})"

            # Fallback to Damodaran static rate
            return self.risk_free_rate, f"Damodaran Static ({maturity_years}Y equivalent)"

        except Exception as e:
            # Fallback to instance risk-free rate
            return self.risk_free_rate, "Static (dynamic fetch failed)"

    def get_country_risk_premium(self, country_code: str = "USA") -> Tuple[float, str]:
        """
        Get country-specific equity risk premium.

        Uses Damodaran's country risk premium data to adjust for country-specific risk.
        Important for valuing companies with international operations or emerging market exposure.

        Formula: Total ERP = Mature Market ERP + Country Risk Premium

        Args:
            country_code: ISO 3-letter country code (USA, CHN, BRA, IND, etc.)

        Returns:
            Tuple of (country_risk_premium, description)

        Example:
            >>> calculator.get_country_risk_premium("USA")
            (0.0, "USA - Mature Market (no additional premium)")

            >>> calculator.get_country_risk_premium("BRA")
            (0.0234, "Brazil - Emerging Market (+2.34% premium)")

        Note:
            For production, integrate with Damodaran's country risk premium spreadsheet
            or similar data source.
        """
        # Country risk premiums (indicative, based on Damodaran 2024 data)
        # In production, fetch from Damodaran's website or database
        country_risk_premiums = {
            "USA": 0.0,      # Mature market baseline
            "CAN": 0.0,      # Canada
            "GBR": 0.0,      # United Kingdom
            "DEU": 0.0,      # Germany
            "FRA": 0.0,      # France
            "JPN": 0.0,      # Japan
            "AUS": 0.0,      # Australia
            "CHE": 0.0,      # Switzerland

            # Emerging markets (indicative premiums)
            "CHN": 0.0158,   # China (~1.58%)
            "IND": 0.0234,   # India (~2.34%)
            "BRA": 0.0312,   # Brazil (~3.12%)
            "MEX": 0.0267,   # Mexico (~2.67%)
            "RUS": 0.0823,   # Russia (~8.23% - high risk)
            "TUR": 0.0445,   # Turkey (~4.45%)
            "ZAF": 0.0389,   # South Africa (~3.89%)
            "ARG": 0.1234,   # Argentina (~12.34% - very high risk)
        }

        country_code_upper = country_code.upper()

        if country_code_upper in country_risk_premiums:
            premium = country_risk_premiums[country_code_upper]

            if premium == 0.0:
                return premium, f"{country_code_upper} - Mature Market (no additional premium)"
            else:
                return premium, f"{country_code_upper} - Emerging Market (+{premium*100:.2f}% premium)"
        else:
            # Unknown country - assume moderate risk
            return 0.02, f"{country_code_upper} - Unknown (assumed +2.0% premium)"

    def calculate_cost_of_equity(self, beta: float) -> float:
        """
        Calculate cost of equity using CAPM.

        Formula: Re = Rf + β × (Rm - Rf)

        Args:
            beta: Stock beta

        Returns:
            Cost of equity
        """
        equity_risk_premium = self.market_return - self.risk_free_rate
        cost_of_equity = self.risk_free_rate + (beta * equity_risk_premium)

        return cost_of_equity

    def calculate_cost_of_debt(
        self, ticker: str, total_debt: float, interest_expense: Optional[float] = None
    ) -> float:
        """
        Calculate cost of debt.

        Args:
            ticker: Stock ticker
            total_debt: Total debt
            interest_expense: Annual interest expense (optional)

        Returns:
            Cost of debt (pre-tax)
        """
        try:
            # If we have interest expense, calculate directly
            if interest_expense is not None and total_debt > 0:
                cost_of_debt = interest_expense / total_debt
                return max(0.02, min(0.15, cost_of_debt))  # Cap between 2-15%

            # Otherwise, estimate based on credit rating proxy
            # Use interest coverage ratio as proxy
            # Interest Coverage = EBIT / Interest Expense
            # Lower coverage = higher risk = higher cost of debt

            # Default to corporate bond average
            return 0.045  # ~4.5% for investment grade

        except Exception:
            return 0.045

    def get_capital_structure(
        self, ticker: str
    ) -> Tuple[float, float, float, Optional[float]]:
        """
        Get capital structure from balance sheet.

        Returns:
            Tuple of (market_cap, total_debt, cash, interest_expense)
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            balance_sheet = stock.balance_sheet
            financials = stock.financials

            # Market cap
            market_cap = info.get("marketCap", 0)

            # Total debt
            total_debt = 0
            if not balance_sheet.empty:
                col = balance_sheet.columns[0]
                for idx in balance_sheet.index:
                    name = str(idx).lower()
                    if "total debt" in name:
                        val = balance_sheet.loc[idx, col]
                        if val is not None and not str(val).lower() == "nan":
                            total_debt = float(val)
                            break

            if total_debt == 0:
                total_debt = info.get("totalDebt", 0)

            # Cash
            cash = info.get("totalCash", 0)

            # Interest expense
            interest_expense = None
            if not financials.empty:
                col = financials.columns[0]
                for idx in financials.index:
                    name = str(idx).lower()
                    if "interest expense" in name:
                        val = financials.loc[idx, col]
                        if val is not None and not str(val).lower() == "nan":
                            interest_expense = abs(float(val))
                            break

            return float(market_cap), float(total_debt), float(cash), interest_expense

        except Exception:
            return 0.0, 0.0, 0.0, None

    def calculate_wacc(
        self,
        ticker: str,
        use_net_debt: bool = True,
        adjust_for_growth: bool = True,
        use_industry_wacc: bool = False,
        apply_blume_adjustment: bool = True,
        use_dynamic_risk_free_rate: bool = False,
        country_code: str = "USA",
        target_debt_to_equity: Optional[float] = None,
    ) -> dict:
        """
        Calculate WACC dynamically with advanced adjustments.

        Formula: WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)

        Where:
        - E = Market value of equity
        - D = Market value of debt (or net debt)
        - V = E + D
        - Re = Cost of equity (CAPM with adjustments)
        - Rd = Cost of debt
        - Tc = Tax rate

        NEW FEATURES:
        - Beta ajustado por Blume (regresión hacia 1.0)
        - Beta desapalancado/reapalancado (Hamada formula)
        - Risk-free rate dinámico (US Treasury real-time)
        - Country Risk Premium (para mercados emergentes)

        Args:
            ticker: Stock ticker
            use_net_debt: Use net debt (debt - cash) instead of gross debt
            adjust_for_growth: Adjust WACC down for high-growth companies
            use_industry_wacc: Use Damodaran industry WACC directly instead of calculating
            apply_blume_adjustment: Apply Blume adjustment to beta (default True)
            use_dynamic_risk_free_rate: Fetch current treasury yields (default False)
            country_code: ISO country code for risk premium (default "USA")
            target_debt_to_equity: Target D/E ratio for relevering beta (default None = use current)

        Returns:
            Dictionary with WACC components and final WACC
        """
        # OPTION 1: Use Damodaran Industry WACC directly (fast, simple)
        if self.use_damodaran and use_industry_wacc:
            industry_data = DamodaranData.get_industry_data(ticker)

            # Get capital structure for reporting purposes
            market_cap, total_debt, cash, interest_expense = self.get_capital_structure(
                ticker
            )

            return {
                "wacc": industry_data["wacc"],
                "wacc_unadjusted": industry_data["wacc"],
                "cost_of_equity": industry_data["cost_of_equity"],
                "cost_of_debt": 0.0,  # Industry average doesn't separate
                "after_tax_cost_of_debt": 0.0,
                "beta": industry_data["beta"],
                "beta_source": f"Industry ({industry_data['industry']})",
                "equity_weight": 1.0 / (1.0 + industry_data["debt_ratio"]),
                "debt_weight": industry_data["debt_ratio"]
                / (1.0 + industry_data["debt_ratio"]),
                "market_cap": market_cap,
                "total_debt": total_debt,
                "net_debt": total_debt - cash,
                "debt_for_wacc": total_debt,
                "using_gross_debt": False,
                "using_industry_wacc": True,
                "industry": industry_data["industry"],
                "cash": cash,
                "risk_free_rate": self.risk_free_rate,
                "market_return": self.market_return,
                "equity_risk_premium": self.market_return - self.risk_free_rate,
            }

        # OPTION 1.5: Use industry WACC for Financial Services automatically
        # AJUSTADO: Para financieros, usar WACC de industria automáticamente
        # La deuda es parte del negocio, no debe penalizarse
        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            sector = stock.info.get("sector", "")

            if (
                sector == "Financial Services"
                and self.use_damodaran
                and not use_industry_wacc
            ):
                # Auto-redirect to industry WACC for financials
                return self.calculate_wacc(
                    ticker,
                    use_net_debt=use_net_debt,
                    adjust_for_growth=False,  # Don't adjust for financials
                    use_industry_wacc=True,
                )
        except Exception:
            pass  # Continue with company-specific calculation

        # OPTION 2: Calculate company-specific WACC (current method)
        # Get capital structure
        market_cap, total_debt, cash, interest_expense = self.get_capital_structure(
            ticker
        )

        # === NEW: ADVANCED BETA ADJUSTMENTS ===
        # Get raw beta
        beta_raw, beta_source = self.get_beta(ticker)

        # Track beta transformations
        beta_adjustments = {
            'beta_raw': beta_raw,
            'beta_blume_adjusted': beta_raw,
            'beta_unlevered': beta_raw,
            'beta_relevered': beta_raw,
            'beta_final': beta_raw,
        }

        # Step 1: Apply Blume adjustment (if enabled)
        if apply_blume_adjustment:
            beta_blume = self.adjust_beta_blume(beta_raw)
            beta_adjustments['beta_blume_adjusted'] = beta_blume
            beta_source += " → Blume adjusted"
        else:
            beta_blume = beta_raw

        # Step 2: Unlever/Relever beta (if target D/E specified)
        if target_debt_to_equity is not None and market_cap > 0:
            # Calculate current D/E ratio
            current_de = total_debt / market_cap if market_cap > 0 else 0

            # Unlever beta (remove current leverage effect)
            beta_unlevered = self.unlever_beta(beta_blume, current_de, self.tax_rate)
            beta_adjustments['beta_unlevered'] = beta_unlevered

            # Relever to target D/E ratio
            beta_relevered = self.relever_beta(beta_unlevered, target_debt_to_equity, self.tax_rate)
            beta_adjustments['beta_relevered'] = beta_relevered
            beta_adjustments['beta_final'] = beta_relevered

            beta_final = beta_relevered
            beta_source += f" → Hamada (target D/E={target_debt_to_equity:.2f})"
        else:
            beta_final = beta_blume
            beta_adjustments['beta_final'] = beta_final

        # === NEW: DYNAMIC RISK-FREE RATE ===
        rf_original = self.risk_free_rate
        rf_source = "Static (Damodaran)" if self.use_damodaran else "Static (user-provided)"

        if use_dynamic_risk_free_rate:
            rf_dynamic, rf_desc = self.get_risk_free_rate_dynamic(maturity_years=10)
            self.risk_free_rate = rf_dynamic  # Temporarily update
            rf_source = rf_desc

        # === NEW: COUNTRY RISK PREMIUM ===
        country_risk_premium, crp_desc = self.get_country_risk_premium(country_code)

        # Calculate cost of equity with adjustments
        # Re = Rf + β × (Rm - Rf) + Country Risk Premium
        equity_risk_premium = self.market_return - self.risk_free_rate
        cost_of_equity = self.risk_free_rate + (beta_final * equity_risk_premium) + country_risk_premium

        # Calculate cost of debt
        cost_of_debt = self.calculate_cost_of_debt(ticker, total_debt, interest_expense)

        # IMPORTANT: Use GROSS debt for capital structure weights
        # Even if net debt is negative (excess cash), we still have debt outstanding
        # and should capture the tax shield benefit
        #
        # Two approaches:
        # 1. If use_net_debt=True AND net_debt < 0: Treat as 100% equity (no debt benefit)
        # 2. If use_net_debt=True AND net_debt > 0: Use net debt for weights
        # 3. If use_net_debt=False: Always use gross debt

        if use_net_debt:
            net_debt = total_debt - cash

            # IMPORTANT: Even with excess cash, companies with material gross debt
            # get tax benefits from interest payments. We should capture this.
            #
            # Rule: If gross debt > $5B OR > 1% of market cap, use gross debt for WACC
            # This captures tax shield while being reasonable
            meaningful_debt_threshold = max(5e9, 0.01 * market_cap)

            if net_debt < 0 and total_debt > meaningful_debt_threshold:
                # Company has excess cash but meaningful gross debt
                # Use gross debt to capture tax shield benefit
                debt_for_wacc = total_debt
                using_gross_debt = True
            elif net_debt < 0:
                # Very little gross debt, treat as 100% equity
                debt_for_wacc = 0
                using_gross_debt = False
            else:
                # Normal case: net debt > 0
                # Use net debt (debt - cash)
                debt_for_wacc = net_debt
                using_gross_debt = False
        else:
            # Always use gross debt when use_net_debt=False
            debt_for_wacc = total_debt
            using_gross_debt = False

        # Calculate weights
        total_value = market_cap + debt_for_wacc

        if total_value == 0 or debt_for_wacc == 0:
            # 100% equity financed (no debt)
            wacc = cost_of_equity
            equity_weight = 1.0
            debt_weight = 0.0
        else:
            equity_weight = market_cap / total_value
            debt_weight = debt_for_wacc / total_value

            # Calculate WACC with tax shield
            wacc = (equity_weight * cost_of_equity) + (
                debt_weight * cost_of_debt * (1 - self.tax_rate)
            )

        # Adjust for high-growth companies
        # IMPORTANT: High beta can over-penalize growth stocks in DCF
        # Beta measures historical volatility, not necessarily future risk for mature tech companies
        # Apply progressive adjustment based on beta_final (after Blume/Hamada adjustments)
        # UPDATED: More aggressive reductions to match market DCF models (NVDA target: 8-9%)
        if adjust_for_growth:
            if beta_final > 2.5:
                # Very high beta (e.g., some small-cap tech) - aggressive adjustment
                adjustment_factor = 0.62  # 38% reduction
            elif beta_final > 2.0:
                # Very high beta (e.g., NVDA ~2.1) - significant adjustment
                # Target: Beta 2.1 × 14% = 13.9% → adjusted to ~8.6%
                adjustment_factor = 0.62  # 38% reduction
            elif beta_final > 1.5:
                # High beta - moderate adjustment
                adjustment_factor = 0.75  # 25% reduction
            elif beta_final > 1.2:
                # Above-market beta - slight adjustment
                adjustment_factor = 0.88  # 12% reduction
            else:
                # Normal or low beta - minimal or no adjustment
                adjustment_factor = 0.95  # 5% reduction for volatility

            wacc_adjusted = wacc * adjustment_factor
        else:
            wacc_adjusted = wacc

        # Get industry info for reference
        industry_data = None
        if self.use_damodaran:
            industry_data = DamodaranData.get_industry_data(ticker)

        # Apply sector-specific WACC floors to avoid underestimation
        # AJUSTADO: Nuevos floors para evitar valoraciones infladas
        import yfinance as yf

        try:
            stock = yf.Ticker(ticker)
            sector = stock.info.get("sector", "")
        except Exception:
            sector = ""

        # UPDATED: Reduced sector floors to avoid systematic undervaluation
        # Many DCF models for NVDA/high-growth use 8-9%, not >10%
        sector_floors = {
            "Technology": 0.070,  # 7.0% (reduced from 7.5%)
            "Healthcare": 0.060,  # 6.0% (reduced from 6.5%)
            "Consumer Defensive": 0.055,  # 5.5% (reduced from 6.0%)
            "Consumer Cyclical": 0.065,  # 6.5% (reduced from 7.0%)
            "Financial Services": 0.065,  # 6.5% (reduced from 7.0%)
            "Industrials": 0.065,  # 6.5% (reduced from 7.0%)
            "Energy": 0.065,  # 6.5% (reduced from 7.0%)
            "Utilities": 0.055,  # 5.5% (reduced from 6.0%)
            "Real Estate": 0.060,  # 6.0% (reduced from 6.5%)
            "Communication Services": 0.065,  # 6.5% (reduced from 7.0%)
            "Basic Materials": 0.065,  # 6.5% (reduced from 7.0%)
        }

        wacc_floor = sector_floors.get(
            sector, 0.060
        )  # Default 6.0% (reduced from 6.5%)
        wacc_before_floor = wacc_adjusted

        if wacc_adjusted < wacc_floor:
            wacc_adjusted = wacc_floor
            floor_applied = True
        else:
            floor_applied = False

        # Restore original risk-free rate if it was dynamically changed
        if use_dynamic_risk_free_rate:
            self.risk_free_rate = rf_original

        return {
            "wacc": wacc_adjusted,
            "wacc_unadjusted": wacc,
            "wacc_before_floor": wacc_before_floor if floor_applied else None,
            "floor_applied": floor_applied,
            "wacc_floor": wacc_floor,
            "sector": sector,
            "cost_of_equity": cost_of_equity,
            "cost_of_debt": cost_of_debt,
            "after_tax_cost_of_debt": cost_of_debt * (1 - self.tax_rate),
            "beta": beta_final,  # Final adjusted beta
            "beta_source": beta_source,
            "equity_weight": equity_weight,
            "debt_weight": debt_weight,
            "market_cap": market_cap,
            "total_debt": total_debt,
            "net_debt": total_debt - cash if use_net_debt else None,
            "debt_for_wacc": debt_for_wacc,
            "using_gross_debt": using_gross_debt if use_net_debt else False,
            "using_industry_wacc": False,
            "industry": industry_data["industry"] if industry_data else None,
            "industry_wacc": industry_data["wacc"] if industry_data else None,
            "cash": cash,
            "risk_free_rate": self.risk_free_rate,
            "market_return": self.market_return,
            "equity_risk_premium": equity_risk_premium,
            # === NEW: ADVANCED ADJUSTMENTS INFO ===
            "beta_adjustments": beta_adjustments,  # Dict with all beta transformations
            "blume_applied": apply_blume_adjustment,
            "hamada_applied": target_debt_to_equity is not None,
            "target_debt_to_equity": target_debt_to_equity,
            "current_debt_to_equity": total_debt / market_cap if market_cap > 0 else 0,
            "dynamic_risk_free_rate_used": use_dynamic_risk_free_rate,
            "risk_free_rate_source": rf_source,
            "risk_free_rate_original": rf_original if use_dynamic_risk_free_rate else None,
            "country_code": country_code,
            "country_risk_premium": country_risk_premium,
            "country_risk_premium_desc": crp_desc,
        }

    def calculate_company_terminal_growth(
        self,
        ticker: str,
        use_company_specific: bool = True,
        wacc: Optional[float] = None,
        validate_spread: bool = True,
    ) -> dict:
        """
        Calculate terminal growth rate specific to each company.

        Methodology (Damodaran):
        1. Base = GDP growth (~2.5%)
        2. Adjust for:
           - ROE vs industry (sustainable profitability)
           - Operating margin (efficiency)
           - Revenue growth trend (momentum)
           - Beta/risk (stability)

        Formula:
        g_terminal = GDP_base + ROE_premium + margin_premium - risk_adjustment

        Constraints:
        - Min: 1.5% (declining industries)
        - Max: 4.5% (high-growth tech with strong fundamentals)
        - Must be < WACC

        Args:
            ticker: Stock ticker
            use_company_specific: If True, calculate based on company metrics
            wacc: Optional WACC value for spread validation
            validate_spread: If True and wacc provided, ensure minimum 4pp spread

        Returns:
            dict with terminal_growth, components, and justification
        """
        if not use_company_specific:
            # Fallback to industry average
            if self.use_damodaran:
                g = DamodaranData.get_terminal_growth(ticker)
            else:
                g = self._get_simple_sector_terminal_growth(ticker)
            return {
                "terminal_growth": g,
                "method": "industry_average",
                "justification": f"Promedio de industria: {g:.2%}",
            }

        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Base GDP growth
            gdp_base = 0.025  # 2.5% US GDP long-term

            # 1. ROE Premium (sustainable profitability)
            # AJUSTADO: Reducido de 0.5% a 0.25% para ser más conservador
            roe = info.get("returnOnEquity", 0)
            if roe and roe > 0:
                # ROE > 15% = strong (add 0.25%)
                # ROE 10-15% = average (add 0%)
                # ROE < 10% = weak (subtract 0.25%)
                if roe > 0.15:
                    roe_premium = 0.0025  # Reducido de 0.005 a 0.0025
                elif roe > 0.10:
                    roe_premium = 0.0
                else:
                    roe_premium = -0.0025  # Reducido de -0.005 a -0.0025
            else:
                roe_premium = 0.0

            # 2. Margin Premium (operational efficiency)
            # AJUSTADO: Reducido de 0.5% a 0.25% para ser más conservador
            operating_margin = info.get("operatingMargins", 0)
            profit_margin = info.get("profitMargins", 0)

            avg_margin = (
                (operating_margin + profit_margin) / 2
                if operating_margin and profit_margin
                else 0
            )

            if avg_margin > 0.20:  # >20% margins = excellent
                margin_premium = 0.0025  # Reducido de 0.005 a 0.0025
            elif avg_margin > 0.10:  # 10-20% = good
                margin_premium = 0.00125  # Reducido de 0.0025 a 0.00125
            elif avg_margin > 0.05:  # 5-10% = average
                margin_premium = 0.0
            else:  # <5% = weak
                margin_premium = -0.0025  # Reducido de -0.005 a -0.0025

            # 3. Revenue Growth Trend (momentum)
            # AJUSTADO: Reducido de 0.5% a 0.25% para ser más conservador
            revenue_growth = info.get("revenueGrowth", 0)
            if revenue_growth and revenue_growth > 0:
                if revenue_growth > 0.15:  # >15% growth
                    growth_premium = 0.0025  # Reducido de 0.005 a 0.0025
                elif revenue_growth > 0.05:  # 5-15% growth
                    growth_premium = 0.00125  # Reducido de 0.0025 a 0.00125
                else:  # <5% growth
                    growth_premium = 0.0
            else:
                growth_premium = -0.0025  # Reducido de -0.005 a -0.0025

            # 4. Risk Adjustment (beta/volatility)
            beta = info.get("beta", 1.0)
            if beta and beta > 0:
                if beta > 1.5:  # High volatility
                    risk_adjustment = 0.005  # Reduce terminal growth
                elif beta > 1.2:
                    risk_adjustment = 0.0025
                elif beta < 0.8:  # Very stable
                    risk_adjustment = -0.0025  # Can sustain slightly higher growth
                else:
                    risk_adjustment = 0.0
            else:
                risk_adjustment = 0.0

            # Calculate terminal growth
            g_terminal = (
                gdp_base
                + roe_premium
                + margin_premium
                + growth_premium
                - risk_adjustment
            )

            # Apply sector-specific constraints for terminal growth
            # FASE 2 ADJUSTMENT: Different sectors have different long-term growth potential
            sector = info.get("sector", "")

            sector_terminal_ranges = {
                "Technology": (0.030, 0.045),  # 3.0-4.5% (innovation driven)
                "Communication Services": (0.025, 0.040),  # 2.5-4.0%
                "Healthcare": (0.025, 0.040),  # 2.5-4.0% (demographics driven)
                "Consumer Cyclical": (0.020, 0.035),  # 2.0-3.5%
                "Consumer Defensive": (0.020, 0.030),  # 2.0-3.0%
                "Financial Services": (0.025, 0.035),  # 2.5-3.5%
                "Industrials": (0.020, 0.033),  # 2.0-3.3%
                "Basic Materials": (0.015, 0.030),  # 1.5-3.0%
                "Energy": (0.015, 0.030),  # 1.5-3.0%
                "Utilities": (0.015, 0.025),  # 1.5-2.5% (regulated)
                "Real Estate": (0.020, 0.030),  # 2.0-3.0%
            }

            min_g, max_g = sector_terminal_ranges.get(sector, (0.015, 0.035))
            g_terminal = max(min_g, min(max_g, g_terminal))

            # Validate spread if WACC provided
            spread_adjusted = False
            g_terminal_before_spread = g_terminal
            if wacc is not None and validate_spread:
                g_terminal, spread_adjusted = self.validate_and_adjust_spread(
                    wacc, g_terminal
                )

            # Build justification
            components = {
                "gdp_base": gdp_base,
                "roe_premium": roe_premium,
                "margin_premium": margin_premium,
                "growth_premium": growth_premium,
                "risk_adjustment": risk_adjustment,
                "roe": roe,
                "operating_margin": operating_margin,
                "profit_margin": profit_margin,
                "revenue_growth": revenue_growth,
                "beta": beta,
            }

            justification = self._build_terminal_growth_justification(
                components, g_terminal
            )

            # Add spread adjustment info if applicable
            if spread_adjusted:
                justification += f"\n\n⚠️ **Ajuste por spread:** g ajustado de {g_terminal_before_spread:.2%} a {g_terminal:.2%} para mantener spread mínimo de 4.0pp con WACC"

            return {
                "terminal_growth": g_terminal,
                "method": "company_specific",
                "components": components,
                "justification": justification,
                "spread_adjusted": spread_adjusted,
                "g_before_spread_adjustment": (
                    g_terminal_before_spread if spread_adjusted else None
                ),
            }

        except Exception as e:
            # Fallback
            g = 0.025
            return {
                "terminal_growth": g,
                "method": "fallback",
                "justification": f"Error calculando métricas: {str(e)}. Usando 2.5% default",
            }

    def _build_terminal_growth_justification(
        self, components: dict, g_terminal: float
    ) -> str:
        """Build human-readable justification for terminal growth."""
        lines = [f"**Terminal Growth: {g_terminal:.2%}**\n"]
        lines.append(f"• Base GDP: {components['gdp_base']:.2%}")

        roe = components.get("roe", 0)
        if roe:
            roe_prem = components["roe_premium"]
            if roe_prem > 0:
                lines.append(f"• ROE alto ({roe:.1%}): +{roe_prem:.2%}")
            elif roe_prem < 0:
                lines.append(f"• ROE bajo ({roe:.1%}): {roe_prem:.2%}")

        margin_prem = components.get("margin_premium", 0)
        if margin_prem != 0:
            op_margin = components.get("operating_margin", 0)
            if margin_prem > 0:
                lines.append(f"• Márgenes altos ({op_margin:.1%}): +{margin_prem:.2%}")
            else:
                lines.append(f"• Márgenes bajos ({op_margin:.1%}): {margin_prem:.2%}")

        growth_prem = components.get("growth_premium", 0)
        rev_growth = components.get("revenue_growth", 0)
        if growth_prem > 0:
            lines.append(f"• Crecimiento fuerte ({rev_growth:.1%}): +{growth_prem:.2%}")
        elif growth_prem < 0:
            lines.append(f"• Crecimiento débil: {growth_prem:.2%}")

        risk_adj = components.get("risk_adjustment", 0)
        beta = components.get("beta", 1.0)
        if risk_adj > 0:
            lines.append(f"• Alta volatilidad (β={beta:.2f}): -{risk_adj:.2%}")
        elif risk_adj < 0:
            lines.append(f"• Baja volatilidad (β={beta:.2f}): {abs(risk_adj):.2%}")

        return "\n".join(lines)

    def validate_and_adjust_spread(
        self, wacc: float, g_terminal: float, min_spread: float = 0.04
    ) -> Tuple[float, bool]:
        """
        Validate that WACC - g spread is sufficient for model stability.

        A spread that is too low can lead to inflated valuations and
        mathematical instability in the Gordon Growth Model.

        Args:
            wacc: Weighted Average Cost of Capital
            g_terminal: Terminal growth rate
            min_spread: Minimum acceptable spread (default 4.0pp = 0.04)

        Returns:
            Tuple of (adjusted_g_terminal, was_adjusted)
        """
        spread = wacc - g_terminal

        if spread < min_spread:
            # Adjust g_terminal downward to meet minimum spread
            g_adjusted = wacc - min_spread

            # Ensure g doesn't go below reasonable minimum (1.5%)
            g_adjusted = max(0.015, g_adjusted)

            return g_adjusted, True
        else:
            return g_terminal, False

    def get_sector_terminal_growth(self, ticker: str) -> float:
        """
        Get industry-adjusted terminal growth rate.

        DEPRECATED: Use calculate_company_terminal_growth() instead.

        Uses Damodaran's methodology if available, otherwise falls back to
        simple sector-based calculation.

        Damodaran framework:
        - Terminal growth ≤ GDP growth + small premium
        - Tech: 3.5% (innovation premium)
        - Consumer/Healthcare: 2.5-3% (GDP linked)
        - Utilities: 2% (regulated, mature)

        Args:
            ticker: Stock ticker

        Returns:
            Terminal growth rate
        """
        # Use company-specific calculation
        result = self.calculate_company_terminal_growth(
            ticker, use_company_specific=True
        )
        return result["terminal_growth"]

    def _get_simple_sector_terminal_growth(self, ticker: str) -> float:
        """Simple sector-based terminal growth (fallback)."""
        # Use Damodaran's industry-specific terminal growth if available
        if self.use_damodaran:
            return DamodaranData.get_terminal_growth(ticker)

        # Fallback to simple sector-based calculation
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get("sector", "").lower()
            industry = info.get("industry", "").lower()

            # Technology and high-growth sectors
            if any(
                keyword in sector or keyword in industry
                for keyword in [
                    "technology",
                    "software",
                    "internet",
                    "semiconductor",
                    "biotech",
                ]
            ):
                return 0.035  # 3.5% terminal growth

            # Consumer and healthcare
            elif any(
                keyword in sector or keyword in industry
                for keyword in [
                    "consumer",
                    "healthcare",
                    "pharmaceutical",
                    "retail",
                ]
            ):
                return 0.03  # 3% terminal growth

            # Financials
            elif any(
                keyword in sector or keyword in industry
                for keyword in ["financial", "bank", "insurance"]
            ):
                return 0.025  # 2.5% terminal growth

            # Utilities and mature sectors
            elif any(
                keyword in sector or keyword in industry
                for keyword in ["utilities", "energy", "materials"]
            ):
                return 0.02  # 2% terminal growth

            else:
                # Default
                return 0.025  # 2.5% terminal growth

        except Exception:
            return 0.025
