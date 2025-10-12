"""
FCF Quality Check Module

Provides validation and quality control for Free Cash Flow data.
Detects unit mismatches, unreasonable values, and data quality issues.
"""

import yfinance as yf
from typing import Tuple, Dict, List
import logging

logger = logging.getLogger(__name__)


class FCFQualityIssue:
    """Enum-like class for FCF quality issues."""

    UNIT_MISMATCH = "unit_mismatch"
    UNREASONABLY_HIGH = "unreasonably_high"
    UNREASONABLY_LOW = "unreasonably_low"
    NEGATIVE_FOR_NON_FINANCIAL = "negative_non_financial"
    HIGH_VOLATILITY = "high_volatility"
    MISSING_DATA = "missing_data"


def validate_fcf_quality(
    ticker: str, base_fcf: float, historical_fcf: List[float], metadata: Dict
) -> Tuple[bool, List[str], Dict[str, float]]:
    """
    Validate FCF data quality and detect potential issues.

    Args:
        ticker: Stock ticker
        base_fcf: Base year FCF
        historical_fcf: List of historical FCF values
        metadata: Metadata from FCF fetch

    Returns:
        Tuple of (is_valid, list_of_warnings, quality_metrics)
    """
    warnings = []
    metrics = {}

    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get key company metrics
        market_cap = info.get("marketCap", 0)
        total_revenue = info.get("totalRevenue", 0)
        sector = info.get("sector", "")

        metrics["market_cap"] = market_cap
        metrics["revenue"] = total_revenue
        metrics["sector"] = sector

        # === CHECK 1: Zero or missing FCF ===
        if base_fcf == 0:
            warnings.append(f"FCF base es cero para {ticker}")
            return False, warnings, metrics

        # === CHECK 2: FCF Yield (FCF / Market Cap) ===
        if market_cap > 0 and base_fcf > 0:
            fcf_yield = (base_fcf / market_cap) * 100
            metrics["fcf_yield"] = fcf_yield

            # Typical FCF yields: 1-15% for most companies
            if fcf_yield < 0.1:
                warnings.append(
                    f"⚠️ FCF Yield muy bajo ({fcf_yield:.3f}%) - "
                    f"posible error de unidades (millones vs billones)"
                )
            elif fcf_yield > 25:
                warnings.append(
                    f"⚠️ FCF Yield muy alto ({fcf_yield:.1f}%) - "
                    f"posible error de unidades o datos incorrectos"
                )

        # === CHECK 3: FCF Margin (FCF / Revenue) ===
        if total_revenue > 0 and base_fcf != 0:
            fcf_margin = (base_fcf / total_revenue) * 100
            metrics["fcf_margin"] = fcf_margin

            # Typical FCF margins: -10% to 30%
            if fcf_margin < -50:
                warnings.append(
                    f"⚠️ FCF Margin muy negativo ({fcf_margin:.1f}%) - "
                    f"empresa está quemando mucho cash"
                )
            elif fcf_margin > 60:
                warnings.append(
                    f"⚠️ FCF Margin muy alto ({fcf_margin:.1f}%) - "
                    f"posible error de datos"
                )

        # === CHECK 4: Negative FCF for non-financial companies ===
        if base_fcf < 0 and sector != "Financial Services":
            warnings.append(
                f"⚠️ FCF negativo (${base_fcf/1e9:.2f}B) para empresa no financiera - "
                f"empresa está quemando cash"
            )

        # === CHECK 5: High volatility in historical FCF ===
        if len(historical_fcf) >= 3:
            # Calculate coefficient of variation
            import numpy as np

            # Filter out zeros
            non_zero_fcf = [f for f in historical_fcf if f != 0]

            if len(non_zero_fcf) >= 3:
                fcf_std = np.std(non_zero_fcf)
                fcf_mean = np.mean(non_zero_fcf)

                if fcf_mean != 0:
                    cv = abs(fcf_std / fcf_mean)
                    metrics["fcf_volatility"] = cv

                    if cv > 1.0:
                        warnings.append(
                            f"⚠️ Alta volatilidad en FCF histórico (CV={cv:.2f}) - "
                            f"considerar normalización"
                        )

        # === CHECK 6: Sudden large changes ===
        if len(historical_fcf) >= 2:
            fcf_current = historical_fcf[0]
            fcf_previous = historical_fcf[1]

            if fcf_previous != 0 and fcf_current != 0:
                change_pct = abs((fcf_current - fcf_previous) / fcf_previous) * 100

                if change_pct > 200:
                    warnings.append(
                        f"⚠️ Cambio drástico en FCF año-a-año ({change_pct:.0f}%) - "
                        f"revisar datos"
                    )

        # === CHECK 7: Unit consistency check ===
        # If FCF is in single-digit millions but company has $100B+ market cap,
        # there's likely a unit issue
        if market_cap > 100e9 and 0 < base_fcf < 100e6:
            warnings.append(
                f"⚠️ CRÍTICO: Posible error de unidades - "
                f"FCF ${base_fcf/1e6:.1f}M para empresa con Market Cap ${market_cap/1e9:.1f}B"
            )

        # Determine if data is valid (no critical issues)
        critical_issues = [
            w for w in warnings if "CRÍTICO" in w or "FCF base es cero" in w
        ]
        is_valid = len(critical_issues) == 0

        return is_valid, warnings, metrics

    except Exception as e:
        logger.error(f"Error validating FCF quality for {ticker}: {e}")
        warnings.append(f"Error en validación: {str(e)}")
        return False, warnings, metrics


def get_quality_score(warnings: List[str], metrics: Dict) -> Tuple[float, str]:
    """
    Calculate a quality score (0-100) for FCF data.

    Args:
        warnings: List of warning messages
        metrics: Quality metrics dictionary

    Returns:
        Tuple of (score, grade_letter)
    """
    score = 100.0

    # Deduct points for each warning
    for warning in warnings:
        if "CRÍTICO" in warning:
            score -= 40
        elif "muy" in warning.lower():
            score -= 15
        else:
            score -= 10

    # Bonus for low volatility
    if metrics.get("fcf_volatility"):
        cv = metrics["fcf_volatility"]
        if cv < 0.3:
            score = min(100, score + 5)

    # Cap score
    score = max(0, min(100, score))

    # Assign grade
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return score, grade


def generate_quality_report(
    ticker: str, base_fcf: float, historical_fcf: List[float], metadata: Dict
) -> str:
    """
    Generate a human-readable quality report for FCF data.

    Args:
        ticker: Stock ticker
        base_fcf: Base year FCF
        historical_fcf: List of historical FCF values
        metadata: Metadata from FCF fetch

    Returns:
        Formatted report string
    """
    is_valid, warnings, metrics = validate_fcf_quality(
        ticker, base_fcf, historical_fcf, metadata
    )

    score, grade = get_quality_score(warnings, metrics)

    report_lines = []
    report_lines.append(f"=== FCF Quality Report: {ticker} ===")
    report_lines.append(f"Quality Score: {score:.0f}/100 (Grade: {grade})")
    report_lines.append("")

    # Base FCF info
    fcf_display = (
        f"${base_fcf/1e9:.2f}B" if abs(base_fcf) > 1e9 else f"${base_fcf/1e6:.2f}M"
    )
    report_lines.append(f"Base FCF: {fcf_display}")
    report_lines.append(f"Data Source: {metadata.get('data_source', 'Unknown')}")
    report_lines.append("")

    # Metrics
    if metrics:
        report_lines.append("Key Metrics:")
        if "fcf_yield" in metrics:
            report_lines.append(f"  FCF Yield: {metrics['fcf_yield']:.2f}%")
        if "fcf_margin" in metrics:
            report_lines.append(f"  FCF Margin: {metrics['fcf_margin']:.2f}%")
        if "fcf_volatility" in metrics:
            report_lines.append(
                f"  FCF Volatility (CV): {metrics['fcf_volatility']:.2f}"
            )
        report_lines.append("")

    # Warnings
    if warnings:
        report_lines.append("Warnings:")
        for warning in warnings:
            report_lines.append(f"  • {warning}")
    else:
        report_lines.append("✅ No issues detected")

    report_lines.append("")
    report_lines.append(f"Status: {'✅ VALID' if is_valid else '❌ NEEDS REVIEW'}")

    return "\n".join(report_lines)
