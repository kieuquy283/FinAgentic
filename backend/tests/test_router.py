from app.router import route_query


def test_market_data_past_range():
    r = route_query("Thống kê dữ liệu giá lịch sử FPT trong 3 tháng gần đây")
    assert r.intent in ["market_data", "technical_analysis"]
    assert r.route in ["market_data_direct", "analytics_direct"]
    assert r.time_context == "past_range"


def test_forecast_future_horizon():
    r = route_query("Dự đoán FPT có tăng không trong 3 tháng tới")
    assert r.intent in ["forecast_outlook", "investment_advisory"]
    assert r.route == "advisory_llm"
    assert r.time_context == "future_horizon"


def test_short_ambiguous_query_planner_or_low_conf():
    r = route_query("FPT 3 tháng")
    assert r.route == "planner_fallback" or r.confidence == "low"


def test_technical_analysis_sma20():
    r = route_query("Tính SMA20 của FPT")
    assert r.intent == "technical_analysis"
    assert r.route == "analytics_direct"


def test_news_sentiment_route():
    r = route_query("Tin tức HPG gần đây tích cực hay tiêu cực?")
    assert r.intent == "news_sentiment"
    assert r.route == "rag_light"


def test_company_info_route():
    r = route_query("FPT niêm yết ở sàn nào?")
    assert r.intent == "company_info"
    assert r.route == "company_direct"
