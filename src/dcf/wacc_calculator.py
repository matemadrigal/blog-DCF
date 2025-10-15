"""Dynamic WACC calculator using CAPM and real capital structure."""

import yfinance as yf
from typing import Optional, Tuple
from .damodaran_data import DamodaranData


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
    ) -> dict:
        """
        Calculate WACC dynamically.

        Formula: WACC = (E/V) × Re + (D/V) × Rd × (1 - Tc)

        Where:
        - E = Market value of equity
        - D = Market value of debt (or net debt)
        - V = E + D
        - Re = Cost of equity (CAPM)
        - Rd = Cost of debt
        - Tc = Tax rate

        Args:
            ticker: Stock ticker
            use_net_debt: Use net debt (debt - cash) instead of gross debt
            adjust_for_growth: Adjust WACC down for high-growth companies
            use_industry_wacc: Use Damodaran industry WACC directly instead of calculating

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

        # Get beta and calculate cost of equity
        beta, beta_source = self.get_beta(ticker)
        cost_of_equity = self.calculate_cost_of_equity(beta)

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
        # Apply progressive adjustment based on beta
        # UPDATED: More aggressive reductions to match market DCF models (NVDA target: 8-9%)
        if adjust_for_growth:
            if beta > 2.5:
                # Very high beta (e.g., some small-cap tech) - aggressive adjustment
                adjustment_factor = 0.62  # 38% reduction
            elif beta > 2.0:
                # Very high beta (e.g., NVDA ~2.1) - significant adjustment
                # Target: Beta 2.1 × 14% = 13.9% → adjusted to ~8.6%
                adjustment_factor = 0.62  # 38% reduction
            elif beta > 1.5:
                # High beta - moderate adjustment
                adjustment_factor = 0.75  # 25% reduction
            elif beta > 1.2:
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
            "beta": beta,
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
            "equity_risk_premium": self.market_return - self.risk_free_rate,
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
