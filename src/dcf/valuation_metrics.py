"""
Módulo de métricas de valoración relativa para análisis comparativo.

Este módulo implementa cálculos precisos de métricas de valoración:
- EV/EBITDA (Enterprise Value to EBITDA)
- P/E (Price to Earnings Ratio)
- P/B (Price to Book Ratio)

Todas las fórmulas están contrastadas con estándares financieros académicos.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import yfinance as yf
from datetime import datetime


@dataclass
class ValuationMetrics:
    """
    Conjunto completo de métricas de valoración relativa.

    Attributes:
        ticker: Símbolo de la acción
        company_name: Nombre de la empresa

        # Componentes de Enterprise Value
        market_cap: Capitalización de mercado (shares × price)
        total_debt: Deuda total (corto + largo plazo)
        cash_and_equivalents: Efectivo y equivalentes
        enterprise_value: EV = Market Cap + Debt - Cash

        # Métricas del Income Statement
        ebitda: Earnings Before Interest, Taxes, Depreciation, and Amortization
        net_income: Beneficio neto (después de impuestos)
        eps: Earnings Per Share (diluted)

        # Métricas del Balance Sheet
        book_value: Valor en libros del equity
        book_value_per_share: Valor en libros por acción

        # Ratios de Valoración
        ev_ebitda: Enterprise Value / EBITDA
        pe_ratio: Price / Earnings (trailing)
        pb_ratio: Price / Book Value

        # Metadata
        current_price: Precio actual de la acción
        shares_outstanding: Acciones en circulación (diluted)
        data_source: Fuente de los datos
        calculation_date: Fecha del cálculo
    """

    ticker: str
    company_name: Optional[str] = None

    # Components
    market_cap: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None
    enterprise_value: Optional[float] = None

    # Income metrics
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    eps: Optional[float] = None

    # Balance metrics
    book_value: Optional[float] = None
    book_value_per_share: Optional[float] = None

    # Valuation ratios
    ev_ebitda: Optional[float] = None
    pe_ratio: Optional[float] = None
    pb_ratio: Optional[float] = None

    # Metadata
    current_price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    data_source: str = "Unknown"
    calculation_date: datetime = None

    def __post_init__(self):
        if self.calculation_date is None:
            self.calculation_date = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "ticker": self.ticker,
            "company_name": self.company_name,
            "market_cap": self.market_cap,
            "total_debt": self.total_debt,
            "cash_and_equivalents": self.cash_and_equivalents,
            "enterprise_value": self.enterprise_value,
            "ebitda": self.ebitda,
            "net_income": self.net_income,
            "eps": self.eps,
            "book_value": self.book_value,
            "book_value_per_share": self.book_value_per_share,
            "ev_ebitda": self.ev_ebitda,
            "pe_ratio": self.pe_ratio,
            "pb_ratio": self.pb_ratio,
            "current_price": self.current_price,
            "shares_outstanding": self.shares_outstanding,
            "data_source": self.data_source,
            "calculation_date": (
                self.calculation_date.isoformat() if self.calculation_date else None
            ),
        }


class ValuationMetricsCalculator:
    """
    Calculadora de métricas de valoración relativa.

    Implementa cálculos precisos basados en teoría financiera estándar:

    1. Enterprise Value (EV):
       EV = Market Cap + Total Debt - Cash & Equivalents

       Representa el valor total de la empresa incluyendo deuda.
       Se usa para comparar empresas con diferentes estructuras de capital.

    2. EV/EBITDA:
       EV/EBITDA = Enterprise Value / EBITDA

       Múltiplo de valoración que compara el valor de la empresa con su
       capacidad de generar flujo operativo antes de impuestos y depreciación.
       - Múltiplo < 10: Potencialmente subvaluada
       - Múltiplo 10-15: Valoración razonable
       - Múltiplo > 15: Potencialmente sobrevaluada

    3. P/E Ratio (Price to Earnings):
       P/E = Price per Share / Earnings per Share

       Indica cuánto pagan los inversores por cada dólar de beneficio.
       - P/E < 15: Potencialmente subvaluada
       - P/E 15-25: Valoración razonable
       - P/E > 25: Potencialmente sobrevaluada o crecimiento alto esperado

    4. P/B Ratio (Price to Book):
       P/B = Price per Share / Book Value per Share

       Compara el precio de mercado con el valor contable.
       - P/B < 1: Cotizando por debajo del valor en libros
       - P/B 1-3: Valoración normal
       - P/B > 3: Prima significativa sobre valor contable

    Referencias:
    - Damodaran, A. (2012). Investment Valuation (3rd ed.)
    - McKinsey & Company. (2015). Valuation: Measuring and Managing the Value of Companies
    - CFA Institute. (2020). Equity Valuation: A Survey of Professional Practice
    """

    def __init__(self):
        """Initialize the calculator."""
        pass

    def calculate_enterprise_value(
        self, market_cap: float, total_debt: float, cash: float
    ) -> float:
        """
        Calculate Enterprise Value.

        Formula: EV = Market Cap + Total Debt - Cash & Equivalents

        Args:
            market_cap: Market capitalization (shares × price)
            total_debt: Total debt (short-term + long-term)
            cash: Cash and cash equivalents

        Returns:
            Enterprise Value
        """
        return market_cap + total_debt - cash

    def calculate_ev_ebitda(
        self, enterprise_value: float, ebitda: float
    ) -> Optional[float]:
        """
        Calculate EV/EBITDA multiple.

        Formula: EV/EBITDA = Enterprise Value / EBITDA

        Args:
            enterprise_value: Enterprise Value
            ebitda: Earnings Before Interest, Taxes, Depreciation, and Amortization

        Returns:
            EV/EBITDA ratio or None if EBITDA <= 0

        Notes:
            - Returns None if EBITDA is negative or zero (ratio not meaningful)
            - Typical ranges: 8-12x for mature companies, 15-25x for growth companies
        """
        if ebitda is None or ebitda <= 0:
            return None
        return enterprise_value / ebitda

    def calculate_pe_ratio(self, price: float, eps: float) -> Optional[float]:
        """
        Calculate Price to Earnings ratio.

        Formula: P/E = Price per Share / Earnings per Share

        Args:
            price: Current stock price
            eps: Earnings per share (diluted, trailing 12 months)

        Returns:
            P/E ratio or None if EPS <= 0

        Notes:
            - Returns None if EPS is negative or zero (ratio not meaningful)
            - Uses diluted EPS for conservative calculation
            - Trailing P/E uses historical earnings, Forward P/E uses projected
        """
        if eps is None or eps <= 0:
            return None
        return price / eps

    def calculate_pb_ratio(
        self, price: float, book_value_per_share: float
    ) -> Optional[float]:
        """
        Calculate Price to Book ratio.

        Formula: P/B = Price per Share / Book Value per Share

        Args:
            price: Current stock price
            book_value_per_share: Book value of equity per share

        Returns:
            P/B ratio or None if book value <= 0

        Notes:
            - Returns None if book value is negative (negative equity)
            - Book value = Total Assets - Total Liabilities - Preferred Stock
        """
        if book_value_per_share is None or book_value_per_share <= 0:
            return None
        return price / book_value_per_share

    def calculate_all_metrics(
        self,
        ticker: str,
        use_data_provider: Optional[Any] = None,
    ) -> ValuationMetrics:
        """
        Calculate all valuation metrics for a given ticker.

        Args:
            ticker: Stock ticker symbol
            use_data_provider: Optional custom data provider (defaults to yfinance)

        Returns:
            ValuationMetrics object with all calculated ratios

        Raises:
            ValueError: If ticker data cannot be fetched
        """
        if use_data_provider:
            return self._calculate_from_provider(ticker, use_data_provider)
        else:
            return self._calculate_from_yahoo(ticker)

    def _calculate_from_yahoo(self, ticker: str) -> ValuationMetrics:
        """
        Calculate metrics using Yahoo Finance data.

        Args:
            ticker: Stock ticker symbol

        Returns:
            ValuationMetrics object
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            # Basic data
            company_name = info.get("longName") or info.get("shortName")
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            shares = info.get("sharesOutstanding")

            # Market cap
            market_cap = info.get("marketCap")
            if not market_cap and current_price and shares:
                market_cap = current_price * shares

            # Balance sheet items
            total_debt = info.get("totalDebt", 0.0)
            cash = info.get("totalCash", 0.0)

            # Calculate Enterprise Value
            enterprise_value = None
            if market_cap and total_debt is not None and cash is not None:
                enterprise_value = self.calculate_enterprise_value(
                    market_cap, total_debt, cash
                )

            # Income statement items
            ebitda = info.get("ebitda")
            net_income = info.get("netIncomeToCommon")
            eps = info.get("trailingEps")

            # Balance sheet - equity
            book_value = info.get("bookValue")  # Per share
            total_stockholder_equity = info.get("totalStockholderEquity")

            book_value_per_share = book_value
            if not book_value_per_share and total_stockholder_equity and shares:
                book_value_per_share = total_stockholder_equity / shares

            # Calculate ratios
            ev_ebitda = None
            if enterprise_value and ebitda:
                ev_ebitda = self.calculate_ev_ebitda(enterprise_value, ebitda)

            pe_ratio = None
            if current_price and eps:
                pe_ratio = self.calculate_pe_ratio(current_price, eps)

            pb_ratio = None
            if current_price and book_value_per_share:
                pb_ratio = self.calculate_pb_ratio(current_price, book_value_per_share)

            # Create metrics object
            metrics = ValuationMetrics(
                ticker=ticker.upper(),
                company_name=company_name,
                market_cap=market_cap,
                total_debt=total_debt,
                cash_and_equivalents=cash,
                enterprise_value=enterprise_value,
                ebitda=ebitda,
                net_income=net_income,
                eps=eps,
                book_value=total_stockholder_equity,
                book_value_per_share=book_value_per_share,
                ev_ebitda=ev_ebitda,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                current_price=current_price,
                shares_outstanding=shares,
                data_source="Yahoo Finance",
                calculation_date=datetime.now(),
            )

            return metrics

        except Exception as e:
            raise ValueError(f"Error calculating metrics for {ticker}: {str(e)}")

    def _calculate_from_provider(
        self, ticker: str, data_provider: Any
    ) -> ValuationMetrics:
        """
        Calculate metrics using custom data provider.

        Args:
            ticker: Stock ticker symbol
            data_provider: Custom data provider with get_financial_data method

        Returns:
            ValuationMetrics object
        """
        financial_data = data_provider.get_financial_data(ticker)

        if not financial_data:
            raise ValueError(f"No data available for {ticker}")

        # Extract data
        current_price = financial_data.current_price
        shares = financial_data.shares_outstanding

        # Calculate market cap
        market_cap = financial_data.market_cap
        if not market_cap and current_price and shares:
            market_cap = current_price * shares

        # Balance sheet
        total_debt = financial_data.total_debt or 0.0
        cash = financial_data.cash_and_equivalents or 0.0

        # Calculate EV
        enterprise_value = None
        if market_cap:
            enterprise_value = self.calculate_enterprise_value(
                market_cap, total_debt, cash
            )

        # Income statement - use most recent year
        ebitda = financial_data.ebitda[0] if financial_data.ebitda else None
        net_income = financial_data.net_income[0] if financial_data.net_income else None

        # Calculate EPS
        eps = None
        if net_income and shares:
            eps = net_income / shares

        # Book value (would need additional data)
        book_value_per_share = None

        # Calculate ratios
        ev_ebitda = None
        if enterprise_value and ebitda:
            ev_ebitda = self.calculate_ev_ebitda(enterprise_value, ebitda)

        pe_ratio = None
        if current_price and eps:
            pe_ratio = self.calculate_pe_ratio(current_price, eps)

        pb_ratio = None

        # Create metrics object
        metrics = ValuationMetrics(
            ticker=ticker.upper(),
            company_name=financial_data.company_name,
            market_cap=market_cap,
            total_debt=total_debt,
            cash_and_equivalents=cash,
            enterprise_value=enterprise_value,
            ebitda=ebitda,
            net_income=net_income,
            eps=eps,
            book_value=None,
            book_value_per_share=book_value_per_share,
            ev_ebitda=ev_ebitda,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            current_price=current_price,
            shares_outstanding=shares,
            data_source=financial_data.data_source,
            calculation_date=datetime.now(),
        )

        return metrics

    def get_valuation_interpretation(self, metrics: ValuationMetrics) -> Dict[str, str]:
        """
        Provide interpretation of valuation metrics.

        Args:
            metrics: ValuationMetrics object

        Returns:
            Dictionary with interpretation for each metric
        """
        interpretation = {}

        # EV/EBITDA interpretation
        if metrics.ev_ebitda:
            if metrics.ev_ebitda < 8:
                interpretation["ev_ebitda"] = "🟢 Potencialmente subvaluada"
            elif metrics.ev_ebitda < 12:
                interpretation["ev_ebitda"] = "🟡 Valoración moderada"
            elif metrics.ev_ebitda < 15:
                interpretation["ev_ebitda"] = "🟠 Valoración elevada"
            else:
                interpretation["ev_ebitda"] = (
                    "🔴 Valoración muy elevada o alta expectativa de crecimiento"
                )
        else:
            interpretation["ev_ebitda"] = (
                "⚪ No disponible (EBITDA negativo o sin datos)"
            )

        # P/E interpretation
        if metrics.pe_ratio:
            if metrics.pe_ratio < 15:
                interpretation["pe_ratio"] = "🟢 Potencialmente subvaluada"
            elif metrics.pe_ratio < 20:
                interpretation["pe_ratio"] = "🟡 Valoración razonable"
            elif metrics.pe_ratio < 25:
                interpretation["pe_ratio"] = "🟠 Valoración elevada"
            else:
                interpretation["pe_ratio"] = (
                    "🔴 Valoración muy elevada o alta expectativa de crecimiento"
                )
        else:
            interpretation["pe_ratio"] = (
                "⚪ No disponible (beneficios negativos o sin datos)"
            )

        # P/B interpretation
        if metrics.pb_ratio:
            if metrics.pb_ratio < 1:
                interpretation["pb_ratio"] = (
                    "🟢 Cotizando por debajo del valor en libros"
                )
            elif metrics.pb_ratio < 2:
                interpretation["pb_ratio"] = "🟡 Prima moderada sobre valor contable"
            elif metrics.pb_ratio < 3:
                interpretation["pb_ratio"] = "🟠 Prima significativa"
            else:
                interpretation["pb_ratio"] = (
                    "🔴 Prima muy elevada (negocio de alto valor intangible)"
                )
        else:
            interpretation["pb_ratio"] = "⚪ No disponible"

        return interpretation

    def compare_with_dcf(
        self,
        dcf_fair_value: float,
        current_price: float,
        metrics: ValuationMetrics,
    ) -> Dict[str, Any]:
        """
        Compare DCF valuation with relative valuation metrics.

        Args:
            dcf_fair_value: Fair value per share from DCF model
            current_price: Current market price
            metrics: ValuationMetrics object

        Returns:
            Dictionary with comparison analysis
        """
        comparison = {
            "dcf_fair_value": dcf_fair_value,
            "current_price": current_price,
            "dcf_upside": ((dcf_fair_value - current_price) / current_price) * 100,
        }

        # DCF signal
        if comparison["dcf_upside"] > 20:
            comparison["dcf_signal"] = "🟢 Fuertemente subvaluada (DCF)"
        elif comparison["dcf_upside"] > 10:
            comparison["dcf_signal"] = "🟢 Subvaluada (DCF)"
        elif comparison["dcf_upside"] > -10:
            comparison["dcf_signal"] = "🟡 Valoración justa (DCF)"
        else:
            comparison["dcf_signal"] = "🔴 Sobrevaluada (DCF)"

        # Relative valuation signals
        signals = []

        if metrics.ev_ebitda:
            if metrics.ev_ebitda < 10:
                signals.append("🟢 EV/EBITDA bajo")
            elif metrics.ev_ebitda > 15:
                signals.append("🔴 EV/EBITDA alto")

        if metrics.pe_ratio:
            if metrics.pe_ratio < 15:
                signals.append("🟢 P/E bajo")
            elif metrics.pe_ratio > 25:
                signals.append("🔴 P/E alto")

        comparison["relative_signals"] = (
            signals if signals else ["🟡 Métricas en rango normal"]
        )

        # Overall consensus
        dcf_bullish = comparison["dcf_upside"] > 10
        relative_bullish = any("🟢" in s for s in signals)
        relative_bearish = any("🔴" in s for s in signals)

        if dcf_bullish and relative_bullish:
            comparison["consensus"] = (
                "🟢 COMPRA FUERTE - DCF y métricas relativas confirman subvaluación"
            )
        elif dcf_bullish and not relative_bearish:
            comparison["consensus"] = "🟢 COMPRA - DCF sugiere valor"
        elif not dcf_bullish and relative_bullish:
            comparison["consensus"] = (
                "🟡 NEUTRAL - Señales mixtas entre DCF y métricas relativas"
            )
        elif not dcf_bullish and relative_bearish:
            comparison["consensus"] = (
                "🔴 EVITAR - DCF y métricas relativas sugieren sobrevaluación"
            )
        else:
            comparison["consensus"] = "🟡 NEUTRAL - Valoración en rango justo"

        return comparison
