"""
Utilities to normalize fundamental data used by the DCF module.

The goal is to provide a consistent snapshot with the minimal metrics
required to apply the valuation pipeline and compare companies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, MutableMapping

MINIMUM_FUNDAMENTALS = (
    "revenue",
    "operating_income",
    "net_income",
    "free_cash_flow",
)

# Accepted aliases for each fundamental metric (lower-case keys).
_ALIASES: Mapping[str, tuple[str, ...]] = {
    "revenue": ("totalrevenue", "revenue", "sales"),
    "operating_income": (
        "operatingincome",
        "operating_income",
        "ebit",
        "operatingprofit",
    ),
    "net_income": ("netincome", "net_income", "earnings", "netprofit"),
    "free_cash_flow": ("freecashflow", "free_cash_flow", "fcf"),
}


@dataclass(frozen=True)
class FundamentalSnapshot:
    """
    Minimal set of normalized fundamentals that downstream components consume.

    The snapshot keeps the raw values alongside derived margin metrics so the
    UI layer can display both absolute and relative indicators.
    """

    revenue: float
    operating_income: float
    net_income: float
    free_cash_flow: float
    operating_margin: float
    net_margin: float
    fcf_margin: float

    def as_dict(self) -> MutableMapping[str, float]:
        """Return a shallow dict copy of the snapshot for serialization."""
        return {
            "revenue": self.revenue,
            "operating_income": self.operating_income,
            "net_income": self.net_income,
            "free_cash_flow": self.free_cash_flow,
            "operating_margin": self.operating_margin,
            "net_margin": self.net_margin,
            "fcf_margin": self.fcf_margin,
        }


class FundamentalNormalizationError(ValueError):
    """Raised when the provided data cannot be normalized."""


def normalize_fundamentals(data: Mapping[str, Any]) -> FundamentalSnapshot:
    """
    Normalize a mapping of raw fundamentals into a :class:`FundamentalSnapshot`.

    Args:
        data: Mapping with company fundamentals. Keys can be any of the accepted
            aliases defined in ``_ALIASES`` (case-insensitive).

    Returns:
        FundamentalSnapshot containing the minimal set of normalized metrics.

    Raises:
        FundamentalNormalizationError: When required values are missing or invalid.
    """
    if not isinstance(data, Mapping):
        raise FundamentalNormalizationError("data must be a mapping")

    if not data:
        raise FundamentalNormalizationError("data mapping is empty")

    normalized = _normalize_keys(data)
    values = {}
    for metric in MINIMUM_FUNDAMENTALS:
        aliases = _ALIASES.get(metric, ())
        value = _first_available_value(normalized, aliases)
        if value is None:
            raise FundamentalNormalizationError(f"Missing value for '{metric}'")
        try:
            values[metric] = float(value)
        except (TypeError, ValueError) as exc:
            raise FundamentalNormalizationError(
                f"Invalid numeric value for '{metric}': {value}"
            ) from exc

    revenue = values["revenue"]
    if revenue <= 0:
        raise FundamentalNormalizationError("revenue must be positive")

    operating_income = values["operating_income"]
    net_income = values["net_income"]
    free_cash_flow = values["free_cash_flow"]

    operating_margin = operating_income / revenue
    net_margin = net_income / revenue
    fcf_margin = free_cash_flow / revenue

    return FundamentalSnapshot(
        revenue=revenue,
        operating_income=operating_income,
        net_income=net_income,
        free_cash_flow=free_cash_flow,
        operating_margin=operating_margin,
        net_margin=net_margin,
        fcf_margin=fcf_margin,
    )


def _normalize_keys(data: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a copy of the mapping with lower-case stripped keys."""
    normalized: dict[str, Any] = {}
    for key, value in data.items():
        if not isinstance(key, str):
            continue
        normalized[key.replace(" ", "").lower()] = value
    return normalized


def _first_available_value(
    data: Mapping[str, Any], aliases: Iterable[str]
) -> Any | None:
    """Return the first non-null value found for the provided aliases."""
    for alias in aliases:
        if alias in data:
            value = data[alias]
            if value is not None:
                return value
    return None
