# -*- coding: utf-8 -*-
"""VISUAL_TRACE_ADAPTER: Bộ tiếp hợp chuyển đổi SemanticTrace sang Visual Frame Timeline (DSL).

Nguyên tắc:
- 100% tất định (Deterministic mapping).
- Semantic Program không cần biết về MOVE_POINTER hay HIGHLIGHT.
- Adapter tự động suy luận:
  + Biến con trỏ đổi giá trị -> Di chuyển visual pointer.
  + Đọc/ghi/so sánh mảng -> Kích hoạt highlight ô tương ứng.
  + State biến cập nhật -> Đồng bộ giá trị trong value_box.
  + Thuyết minh 2 tầng: Tier 1 (Fact) + Tier 2 (Pedagogical Intent).
"""
from __future__ import annotations
import copy
from typing import Any, Optional
from pydantic import BaseModel, Field

from .contract import SemanticProgramSpec, VisualBindings
from .interpreter import SemanticExecutionResult, SemanticTraceStep


class VisualObject(BaseModel):
    id: str
    type: str
    label: Optional[str] = None
    items: Optional[list[Any]] = None
    value: Optional[Any] = None
    target: Optional[str] = None
    target_index: Optional[int] = None
    capacity: Optional[int] = None
    highlight_indices: Optional[list[int]] = None


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
        self.bindings: VisualBindings = spec.visual_bindings

    def adapt(self, exec_result: SemanticExecutionResult) -> list[VisualFrame]:
        frames: list[VisualFrame] = []

        for step in exec_result.trace:
            frame = self._adapt_single_step(step)
            frames.append(frame)

        return frames

    def _adapt_single_step(self, step: SemanticTraceStep) -> VisualFrame:
        snap = step.memory_snapshot
        visual_objects: list[dict[str, Any]] = []
        highlighted_ids: list[str] = []

        # 1. Dựng các container hiển thị
        for cb in self.bindings.containers:
            val = snap.get(cb.semantic_id, [])
            obj_dict: dict[str, Any] = {
                "id": cb.semantic_id,
                "type": cb.primitive,
                "label": cb.label,
            }

            if cb.primitive in ("array_strip", "queue_view"):
                obj_dict["items"] = list(val) if isinstance(val, (list, tuple)) else []
            elif cb.primitive == "stack_view":
                obj_dict["items"] = list(val) if isinstance(val, (list, tuple)) else []
                obj_dict["capacity"] = max(8, len(obj_dict["items"]) + 2)
            elif cb.primitive == "table_grid":
                obj_dict["items"] = val if isinstance(val, list) else []
            elif cb.primitive == "tree_element":
                obj_dict["value"] = val
            elif cb.primitive == "bit_register":
                obj_dict["value"] = val

            # Highlight logic nếu bước này tác động trực tiếp vào container
            if step.target == cb.semantic_id:
                highlighted_ids.append(cb.semantic_id)

            visual_objects.append(obj_dict)

        # 2. Dựng các con trỏ hiển thị (Pointers)
        for pb in self.bindings.pointers:
            idx_val = snap.get(pb.var_ref, None)
            if idx_val is not None and isinstance(idx_val, int):
                ptr_dict: dict[str, Any] = {
                    "id": pb.pointer_id,
                    "type": "pointer",
                    "label": pb.label,
                    "target": pb.target_container,
                    "target_index": idx_val,
                }
                visual_objects.append(ptr_dict)
                if step.target == pb.var_ref:
                    highlighted_ids.append(pb.pointer_id)

        # 3. Dựng các hộp giá trị (Value Boxes)
        for vb in self.bindings.value_boxes:
            v_val = snap.get(vb.var_ref, None)
            vb_dict: dict[str, Any] = {
                "id": vb.box_id,
                "type": "value_box",
                "label": vb.label,
                "value": v_val if v_val is not None else "",
            }
            if step.target == vb.var_ref:
                highlighted_ids.append(vb.box_id)
            visual_objects.append(vb_dict)

        # 4. Ghép thuyết minh 2 tầng
        tier1 = step.tier1_narration
        tier2 = self.spec.pedagogical_intent
        narration = f"{tier1}"
        if step.step_index == 0 and tier2:
            narration = f"{tier2} | {tier1}"

        return VisualFrame(
            step_index=step.step_index,
            narration=narration,
            tier1_fact=tier1,
            tier2_intent=tier2,
            objects=visual_objects,
            highlighted_object_ids=highlighted_ids,
        )
