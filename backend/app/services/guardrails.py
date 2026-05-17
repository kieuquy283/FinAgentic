from __future__ import annotations

from app.schemas import GuardrailResult, EvidenceItem

FORECAST_DISCLAIMER = "Thông tin này chỉ mang mục đích tham khảo, nên kiểm tra, rà soát lại. Không nên tin tưởng tuyệt đối."
ADVISORY_DISCLAIMER = (
    "Đây không phải khuyến nghị đầu tư cá nhân hóa. Bạn nên tự đánh giá khẩu vị rủi ro, "
    "kiểm tra lại dữ liệu và tham khảo chuyên gia tài chính trước khi ra quyết định."
)


def get_disclaimer_policy(intent: str, route: str, answer_type: str | None = None) -> str:
    if answer_type == "unknown":
        return ""
    if intent == "forecast_outlook":
        return FORECAST_DISCLAIMER
    if intent == "investment_advisory":
        return ADVISORY_DISCLAIMER
    return ""


def apply_guardrails(
    intent: str,
    route: str,
    answer: str,
    evidence: list[EvidenceItem],
    has_numeric: bool,
    answer_type: str | None = None,
    demo_fallback: bool = False,
    runtime_warnings: list[str] | None = None,
) -> GuardrailResult:
    warnings: list[str] = []
    passed = True

    if not evidence:
        warnings.append("Thiếu evidence cho câu trả lời.")
        passed = False

    if has_numeric and not any(e.source_type in ["db", "analytics"] for e in evidence):
        warnings.append("Số liệu định lượng không có nguồn DB/analytics.")
        passed = False

    if demo_fallback:
        warnings.append("Real data missing; using demo fallback data.")

    if "demo" not in answer.lower() and demo_fallback:
        warnings.append("Dữ liệu đang ở chế độ demo/mock.")
    if runtime_warnings:
        warnings.extend(runtime_warnings)

    disclaimer = get_disclaimer_policy(intent=intent, route=route, answer_type=answer_type)
    return GuardrailResult(passed=passed, warnings=warnings, disclaimer=disclaimer)
