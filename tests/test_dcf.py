from src.dcf.model import dcf_value


def test_empty_cash_flows():
    assert dcf_value([], 0.1) == 0.0


def test_simple_dcf():
    # two years of cash flow 100, 100, discount rate 10%, g=2%
    pv = dcf_value([100, 100], 0.1, 0.02)
    # calculate expected manually
    # PVs: 100/1.1 + 100/1.1^2 = 90.9090909 + 82.6446281 = 173.553719
    # terminal value at year 2: 100*(1.02)/(0.1-0.02)=100*1.02/0.08=1275
    # discounted TV: 1275/1.1^2 = 1056.198347
    expected = 100 / 1.1 + 100 / (1.1**2) + 1275 / (1.1**2)
    assert abs(pv - expected) < 1e-6


def test_invalid_rates():
    import pytest

    with pytest.raises(ValueError):
        dcf_value([100], 0.02, 0.03)
