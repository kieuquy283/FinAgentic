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


def test_forecast_query_fpt_one_month_routes_to_forecast():
    r = route_query("dự kiến tình hình của fpt trong 1 tháng tới")
    assert r.intent == "forecast_outlook"
    assert r.route == "advisory_llm"
    assert r.time_context == "future_horizon"
    assert r.date_range == "1M"


def test_forecast_query_sets_need_news_and_need_advice():
    r = route_query("dự kiến tình hình của fpt trong 1 tháng tới")
    assert r.need_news is True
    assert r.need_advice is True


def test_forecast_horizon_one_month():
    r = route_query("triển vọng FPT trong 30 ngày tới thế nào?")
    assert r.intent == "forecast_outlook"
    assert r.date_range == "1M"


def test_tinh_hinh_fpt_3_thang_gan_day_routes_to_market_data():
    r = route_query("tình hình FPT 3 tháng gần đây")
    assert r.intent == "market_data"
    assert r.route in ["market_data_direct", "analytics_direct"]
    assert r.date_range == "3M"


def test_dien_bien_gia_fpt_3_thang_qua_routes_to_market_data():
    r = route_query("diễn biến giá FPT 3 tháng qua")
    assert r.intent == "market_data"
    assert r.route in ["market_data_direct", "analytics_direct"]
    assert r.date_range == "3M"


def test_fpt_gan_day_the_nao_not_forecast():
    r = route_query("FPT gần đây thế nào?")
    assert r.intent != "forecast_outlook"


def test_du_kien_tinh_hinh_fpt_1_thang_toi_routes_to_forecast():
    r = route_query("dự kiến tình hình FPT trong 1 tháng tới")
    assert r.intent == "forecast_outlook"
    assert r.route == "advisory_llm"
    assert r.date_range == "1M"


def test_du_doan_gia_fpt_thang_toi_routes_to_forecast():
    r = route_query("dự đoán giá FPT tháng tới")
    assert r.intent == "forecast_outlook"
    assert r.route == "advisory_llm"
    assert r.date_range == "1M"


def test_tinh_hinh_alone_is_ambiguous_not_future_by_itself():
    r = route_query("tình hình")
    assert r.intent != "forecast_outlook"


def test_past_time_expression_overrides_ambiguous_tinh_hinh_keyword():
    r = route_query("tình hình FPT vừa qua")
    assert r.intent == "market_data"
