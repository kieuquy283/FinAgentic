from __future__ import annotations

import os

from app.llm.prompts import SYSTEM_PROMPT


class QwenClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("QWEN_API_KEY", "").strip()
        self.base_url = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").strip()
        self.model = os.getenv("QWEN_MODEL", "qwen-plus").strip()
        self.timeout_seconds = float(os.getenv("QWEN_TIMEOUT_SECONDS", "5"))
        self.last_timeout_used = False

    def enabled(self) -> bool:
        return bool(self.api_key)

    def synthesize(self, user_prompt: str) -> str:
        self.last_timeout_used = False
        if not self.enabled():
            return self._mock_fallback()
        try:
            return self._call_qwen(user_prompt)
        except Exception as exc:  # noqa: BLE001
            if self._is_transient(exc):
                self.last_timeout_used = True
                return self._mock_fallback()
            return self._mock_fallback()

    def _call_qwen(self, user_prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=self.timeout_seconds)
        resp = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = (resp.choices[0].message.content or "").strip() if resp.choices else ""
        return content or self._mock_fallback()

    def _is_transient(self, exc: Exception) -> bool:
        name = exc.__class__.__name__.lower()
        return any(k in name for k in ["timeout", "connection", "rate", "apierror", "internal"])

    def _mock_fallback(self) -> str:
        return (
            "Status: theo dõi.\n"
            "Evidence summary: dữ liệu tổng hợp từ AnalyticalContext.\n"
            "Risks: biến động ngắn hạn, thay đổi tin tức, rủi ro ngành.\n"
            "Confidence: low.\n"
            "Disclaimer: Thông tin chỉ để tham khảo, không phải khuyến nghị đầu tư cá nhân."
        )
