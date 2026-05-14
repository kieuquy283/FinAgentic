from __future__ import annotations

from app.llm.prompts import build_user_prompt
from app.llm.qwen_client import QwenClient
from app.schemas import AnalyticalContext


class AdvisoryService:
    def __init__(self) -> None:
        self.qwen = QwenClient()

    def synthesize(self, ctx: AnalyticalContext) -> str:
        prompt = build_user_prompt(ctx)
        return self.qwen.synthesize(prompt)
