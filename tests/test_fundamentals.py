import pytest

from src.dcf.fundamentals import (
    FundamentalNormalizationError,
    FundamentalSnapshot,
    MINIMUM_FUNDAMENTALS,
    normalize_fundamentals,
)


def test_normalize_fundamentals_accepts_aliases_and_computes_margins():
    raw = {
        "TotalRevenue": 2000,
        "OperatingIncome": 400,
        "NetIncome": "300",
        "FreeCashFlow": 250,
    }

    snapshot = normalize_fundamentals(raw)

    assert isinstance(snapshot, FundamentalSnapshot)
    assert snapshot.revenue == 2000
    assert snapshot.operating_margin == pytest.approx(0.2)
    assert snapshot.net_margin == pytest.approx(0.15)
    assert snapshot.fcf_margin == pytest.approx(0.125)


@pytest.mark.parametrize("missing_key", MINIMUM_FUNDAMENTALS)
def test_normalize_fundamentals_requires_all_minimum_metrics(missing_key):
    raw = {
        "revenue": 100,
        "operating_income": 10,
        "net_income": 8,
        "free_cash_flow": 7,
    }
    raw.pop(missing_key)

    with pytest.raises(FundamentalNormalizationError):
        normalize_fundamentals(raw)


def test_normalize_fundamentals_fails_on_non_positive_revenue():
    raw = {
        "totalRevenue": 0,
        "operatingIncome": 10,
        "netIncome": 8,
        "freeCashFlow": 7,
    }

    with pytest.raises(FundamentalNormalizationError):
        normalize_fundamentals(raw)
