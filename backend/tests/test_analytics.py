import pytest
from app.services.analytics_service import AnalyticsService


def test_sma_known_series():
    svc = AnalyticsService()
    prices = [float(i) for i in range(1, 41)]
    assert svc.calculate_sma(prices, 20) == 30.5


def test_rsi_is_bounded():
    svc = AnalyticsService()
    prices = [100 + (i % 5) for i in range(40)]
    v = svc.calculate_rsi(prices, 14)
    assert 0 <= v <= 100


def test_insufficient_data():
    svc = AnalyticsService()
    with pytest.raises(ValueError):
        svc.calculate_sma([1, 2, 3], 20)
    with pytest.raises(ValueError):
        svc.calculate_rsi([1, 2], 14)
