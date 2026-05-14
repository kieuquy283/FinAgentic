from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolResponse(BaseModel):
    source: str = "vnstock"
    fetched_at: str
    data_type: str
    data: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

