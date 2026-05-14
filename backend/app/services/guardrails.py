from __future__ import annotations

from app.schemas import GuardrailResult, EvidenceItem

DISCLAIMER = (
    "Thong tin nay chi phuc vu muc dich tham khao va demo he thong, khong phai khuyen nghi dau tu ca nhan hoa. "
    "Nguoi dung can tu danh gia rui ro hoac tham khao chuyen gia tai chinh truoc khi ra quyet dinh."
)


def apply_guardrails(
    intent: str,
    answer: str,
    evidence: list[EvidenceItem],
    has_numeric: bool,
    demo_fallback: bool = False,
) -> GuardrailResult:
    warnings: list[str] = []
    passed = True

    if not evidence:
        warnings.append("Thieu evidence cho cau tra loi.")
        passed = False

    if has_numeric and not any(e.source_type in ["db", "analytics"] for e in evidence):
        warnings.append("So lieu dinh luong khong co nguon DB/analytics.")
        passed = False

    if demo_fallback:
        warnings.append("Real data missing; using demo fallback data.")

    if "demo" not in answer.lower() and demo_fallback:
        warnings.append("Du lieu dang o che do demo/mock.")

    return GuardrailResult(passed=passed, warnings=warnings, disclaimer=DISCLAIMER)
