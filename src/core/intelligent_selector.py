"""
Intelligent data selector - automatically chooses best data source and method.

Eliminates the need for user to choose between Manual/Autocompletar/Multi-fuente.
"""

from typing import Tuple, Dict, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataQuality:
    """Quality metrics for fetched data."""

    confidence: float  # 0.0 - 1.0
    completeness: float  # 0.0 - 1.0
    source: str  # Where data came from
    method: str  # How it was calculated
    fallback_used: bool  # Whether fallback was needed
    metadata: Dict[str, Any]  # Additional info


class IntelligentDataSelector:
    """
    Automatically selects best data source and calculation method.

    Philosophy:
    - User shouldn't need to choose between options
    - System always uses best available data
    - Transparent about what was used and why
    """

    def __init__(self, data_aggregator=None, cache_manager=None):
        """
        Initialize selector with dependencies.

        Args:
            data_aggregator: Multi-source data aggregator
            cache_manager: Cache manager for performance
        """
        self.aggregator = data_aggregator
        self.cache = cache_manager

    def get_best_fcf_data(
        self, ticker: str, years: int = 5
    ) -> Tuple[float, list, DataQuality]:
        """
        Intelligently fetch FCF data using best available method.

        Decision logic:
        1. Try multi-source aggregator (highest quality)
        2. If confidence < 80%, try Yahoo direct
        3. Use normalization if historical data available
        4. Never ask user to choose

        Args:
            ticker: Stock ticker
            years: Years of historical data needed

        Returns:
            Tuple of (base_fcf, historical_fcf, quality_metrics)
        """
        quality = DataQuality(
            confidence=0.0,
            completeness=0.0,
            source="None",
            method="None",
            fallback_used=False,
            metadata={},
        )

        # Strategy 1: Try multi-source aggregator (best quality)
        if self.aggregator:
            try:
                financial_data = self.aggregator.get_financial_data(
                    ticker, years, strategy="best_quality"
                )

                if financial_data and financial_data.confidence_score >= 0.8:
                    fcf_data = financial_data.calculate_fcf()
                    if fcf_data and len(fcf_data) >= 3:
                        base_fcf = fcf_data[0]
                        quality = DataQuality(
                            confidence=financial_data.confidence_score,
                            completeness=financial_data.data_completeness / 100,
                            source=financial_data.data_source,
                            method="Multi-source aggregation",
                            fallback_used=False,
                            metadata={
                                "years_found": len(fcf_data),
                                "sources_used": financial_data.data_source,
                            },
                        )

                        logger.info(
                            f"✅ {ticker}: Using multi-source data "
                            f"(confidence: {quality.confidence:.0%})"
                        )
                        return base_fcf, fcf_data, quality
            except Exception as e:
                logger.warning(f"Multi-source failed for {ticker}: {e}")

        # Strategy 2: Fallback to Yahoo Finance direct
        try:
            from src.utils.data_fetcher import get_fcf_data

            base_fcf, historical_fcf, metadata = get_fcf_data(ticker, max_years=years)

            if metadata["success"] and len(historical_fcf) >= 3:
                # Calculate confidence based on data quality
                confidence = self._calculate_fcf_confidence(historical_fcf, metadata)

                quality = DataQuality(
                    confidence=confidence,
                    completeness=metadata["years_found"] / years,
                    source="Yahoo Finance",
                    method="Operating CF - CAPEX",
                    fallback_used=True,
                    metadata=metadata,
                )

                logger.info(
                    f"⚠️ {ticker}: Using Yahoo fallback "
                    f"(confidence: {confidence:.0%})"
                )
                return base_fcf, historical_fcf, quality

        except Exception as e:
            logger.error(f"Yahoo Finance failed for {ticker}: {e}")

        # Strategy 3: Last resort - return empty with low confidence
        quality = DataQuality(
            confidence=0.0,
            completeness=0.0,
            source="None",
            method="No data available",
            fallback_used=True,
            metadata={"error": "All data sources failed"},
        )

        logger.error(f"❌ {ticker}: No FCF data available")
        return 0.0, [], quality

    def get_best_wacc_method(self, ticker: str, company_data: Dict) -> Tuple[str, Dict]:
        """
        Automatically choose best WACC calculation method.

        Logic:
        - If company has reliable beta and debt data → Company-specific CAPM
        - If company is in Damodaran dataset → Industry WACC available as reference
        - Always use company-specific if possible

        Args:
            ticker: Stock ticker
            company_data: Company financial data

        Returns:
            Tuple of (method_name, config_dict)
        """
        # Check if we have reliable data for company-specific CAPM
        has_beta = company_data.get("beta") is not None
        has_debt_data = (
            company_data.get("totalDebt") is not None
            or company_data.get("cash") is not None
        )
        has_market_cap = company_data.get("marketCap") is not None

        if has_beta and has_debt_data and has_market_cap:
            return "company_specific", {
                "use_damodaran": True,
                "use_industry_wacc": False,
                "reason": "Reliable company-specific data available",
            }

        # Fallback: Use industry WACC if in Damodaran dataset
        try:
            from src.dcf.damodaran_data import DamodaranData

            industry_data = DamodaranData.get_industry_data(ticker)
            if industry_data:
                return "industry_average", {
                    "use_damodaran": True,
                    "use_industry_wacc": True,
                    "industry": industry_data["industry"],
                    "reason": "Using industry average (Damodaran)",
                }
        except Exception:
            pass

        # Last resort: Conservative default
        return "conservative_default", {
            "use_damodaran": False,
            "use_industry_wacc": False,
            "wacc": 0.08,
            "reason": "Using conservative default (8%)",
        }

    def get_best_normalization_method(self, historical_fcf: list) -> str:
        """
        Automatically choose best FCF normalization method.

        Logic:
        - If FCF is volatile (high std dev) → Use median (robust to outliers)
        - If FCF is stable → Use weighted average (emphasizes recent)
        - If only 1-2 years → Use current (no history to normalize)

        Args:
            historical_fcf: List of historical FCF values

        Returns:
            Best normalization method name
        """
        if not historical_fcf or len(historical_fcf) < 2:
            return "current"

        if len(historical_fcf) < 3:
            return "current"

        # Calculate volatility
        import numpy as np

        volatility = np.std(historical_fcf) / np.mean(historical_fcf)

        if volatility > 0.3:  # High volatility
            return "median"  # Robust to outliers
        else:
            return "weighted_average"  # Emphasize recent data

    def should_normalize_fcf(self, historical_fcf: list) -> bool:
        """
        Decide if FCF should be normalized.

        Logic:
        - If recent FCF is outlier (>30% from average) → Normalize
        - If very volatile (std dev > 30% of mean) → Normalize
        - Otherwise → Use current year

        Args:
            historical_fcf: List of historical FCF values

        Returns:
            True if normalization is recommended
        """
        if not historical_fcf or len(historical_fcf) < 3:
            return False

        import numpy as np

        recent = historical_fcf[0]
        avg = np.mean(historical_fcf)
        std = np.std(historical_fcf)

        # Check if recent is outlier
        if abs(recent - avg) / avg > 0.3:
            return True

        # Check if very volatile
        if std / avg > 0.3:
            return True

        return False

    def _calculate_fcf_confidence(self, historical_fcf: list, metadata: Dict) -> float:
        """
        Calculate confidence score for FCF data.

        Factors:
        - Number of years (more = better)
        - Consistency (less volatility = better)
        - Data completeness (fewer errors = better)

        Args:
            historical_fcf: Historical FCF values
            metadata: Metadata from data fetch

        Returns:
            Confidence score 0.0 - 1.0
        """
        confidence = 0.5  # Base confidence

        # Factor 1: Number of years
        years_found = len(historical_fcf)
        if years_found >= 5:
            confidence += 0.2
        elif years_found >= 3:
            confidence += 0.1

        # Factor 2: Data completeness
        if not metadata.get("errors"):
            confidence += 0.2
        elif len(metadata.get("errors", [])) <= 1:
            confidence += 0.1

        # Factor 3: Consistency (low volatility)
        if years_found >= 3:
            import numpy as np

            volatility = np.std(historical_fcf) / np.mean(historical_fcf)
            if volatility < 0.2:  # Low volatility
                confidence += 0.1
            elif volatility > 0.5:  # High volatility
                confidence -= 0.1

        return min(1.0, max(0.0, confidence))

    def get_quality_badge(self, quality: DataQuality) -> str:
        """
        Get visual quality badge for UI display.

        Args:
            quality: Data quality metrics

        Returns:
            Emoji badge string
        """
        if quality.confidence >= 0.9:
            return "🟢 Excelente"
        elif quality.confidence >= 0.7:
            return "🟡 Buena"
        elif quality.confidence >= 0.5:
            return "🟠 Aceptable"
        else:
            return "🔴 Baja"

    def get_explanation(self, quality: DataQuality) -> str:
        """
        Get human-readable explanation of data selection.

        Args:
            quality: Data quality metrics

        Returns:
            Explanation string
        """
        lines = [
            f"**Fuente:** {quality.source}",
            f"**Método:** {quality.method}",
            f"**Confianza:** {quality.confidence:.0%}",
            f"**Completitud:** {quality.completeness:.0%}",
        ]

        if quality.fallback_used:
            lines.append(
                "⚠️ *Usando fuente de respaldo (fuente principal no disponible)*"
            )

        if quality.metadata:
            if "years_found" in quality.metadata:
                lines.append(f"**Años históricos:** {quality.metadata['years_found']}")

        return "\n".join(lines)
