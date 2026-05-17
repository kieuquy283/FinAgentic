from __future__ import annotations

import time

from app.llm.prompts import build_user_prompt
from app.llm.qwen_client import QwenClient
from app.runtime_diagnostics import get_request_diagnostics
from app.schemas import AnalyticalContext


class AdvisoryService:
    def __init__(self) -> None:
        self.qwen = QwenClient()

    def synthesize(self, ctx: AnalyticalContext) -> str:
        prompt = build_user_prompt(ctx)
        t0 = time.perf_counter()
        out = self.qwen.synthesize(prompt)
        diag = get_request_diagnostics()
        if diag is not None:
            diag.llm_ms = (time.perf_counter() - t0) * 1000
            diag.timeout_used = diag.timeout_used or self.qwen.last_timeout_used
        return out
