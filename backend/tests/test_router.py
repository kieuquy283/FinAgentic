import pytest
from app.router import route_query


def test_demo_query_1_company_info():
    r = route_query("FPT niem yet o san nao?")
    assert r.intent == "company_info"
    assert r.route == "direct"


def test_demo_query_2_market_data():
    r = route_query("Gia FPT 3 thang gan day the nao?")
    assert r.intent == "market_data"
    assert r.route == "direct"


def test_demo_query_3_analytics():
    r = route_query("Tinh RSI14 va SMA20 cua FPT")
    assert r.intent == "technical_analysis"
    assert r.route == "analytics"


def test_demo_query_4_news():
    r = route_query("Tin tuc gan day ve HPG la tich cuc hay tieu cuc?")
    assert r.intent == "news_sentiment"
    assert r.route == "rag"


def test_demo_query_5_advisory():
    r = route_query("FPT co dang theo doi khong? Neu ly do va rui ro")
    assert r.intent == "investment_advisory"
    assert r.route == "advisory"
