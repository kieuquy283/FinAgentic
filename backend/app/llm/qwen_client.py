from __future__ import annotations

import os
import time

from app.llm.prompts import SYSTEM_PROMPT


class QwenClient:
    def __init__(self) -> None:
        self.api_key = os.getenv("QWEN_API_KEY", "").strip()
        self.base_url = os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1").strip()
        self.model = os.getenv("QWEN_MODEL", "qwen-plus").strip()

    def enabled(self) -> bool:
        return bool(self.api_key)

    def synthesize(self, user_prompt: str) -> str:
        if not self.enabled():
            return self._mock_fallback()
        try:
            return self._call_qwen(user_prompt)
        except Exception as exc:  # noqa: BLE001
            if self._is_transient(exc):
                time.sleep(0.6)
                try:
                    return self._call_qwen(user_prompt)
                except Exception:  # noqa: BLE001
                    return self._mock_fallback()
            return self._mock_fallback()

    def _call_qwen(self, user_prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=20.0)
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
            "Status: theo doi.\n"
            "Evidence summary: du lieu tong hop tu AnalyticalContext.\n"
            "Risks: bien dong ngan han, thay doi tin tuc, rui ro nganh.\n"
            "Confidence: low.\n"
            "Disclaimer: Thong tin chi de tham khao, khong phai khuyen nghi dau tu ca nhan."
        )

