# -*- coding: utf-8 -*-
"""VISUAL_TRACE_ADAPTER: SemanticTrace → dãy khung (frame timeline) mà timeline frontend tua theo.

Mỗi bước trace thành MỘT khung (bất biến #31 `frame k ⇔ trace[k]`), mang thuyết minh hai tầng: Tier 1 (sự kiện
của bước) + Tier 2 (`pedagogical_intent`, chỉ ở khung đầu).

(/13) Khung không còn đối tượng 2D. Container/con trỏ/hộp giá trị (`array_strip`, `stack_view`, `graph_view`, …) là
đường lên màn hình của miền Tin học và đã gỡ cùng `visual_bindings`; hình học đi bằng `scene3d`, không qua đây.
`objects` vẫn có mặt (rỗng) vì đó là hình dạng khung mà frontend và `pacer` đọc.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec
from .interpreter import SemanticExecutionResult, SemanticTraceStep


class VisualFrame(BaseModel):
    step_index: int
    narration: str
    tier1_fact: str
    tier2_intent: Optional[str] = None
    objects: list[dict[str, Any]]
    highlighted_object_ids: list[str] = Field(default_factory=list)


class VisualTraceAdapter:
    def __init__(self, spec: SemanticProgramSpec):
        self.spec = spec

    def adapt(self, exec_result: SemanticExecutionResult) -> list[VisualFrame]:
        return [self._adapt_single_step(step) for step in exec_result.trace]

    def _adapt_single_step(self, step: SemanticTraceStep) -> VisualFrame:
        tier1 = step.tier1_narration
        tier2 = self.spec.pedagogical_intent
        narration = f"{tier2} | {tier1}" if step.step_index == 0 and tier2 else f"{tier1}"
        return VisualFrame(
            step_index=step.step_index,
            narration=narration,
            tier1_fact=tier1,
            tier2_intent=tier2,
            objects=[],
            highlighted_object_ids=[],
        )
