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
    #: Đối sánh HAI CHIỀU với enum `VisualContainerBinding.primitive` — bất biến
    #: #33. Thêm primitive vào contract mà quên nhánh ở `_adapt_single_step` thì
    #: LLM khai nó sẽ ra object rỗng, lỗi CÂM (đã xảy ra với `bar_chart`).
    HANDLED_PRIMITIVES: frozenset[str] = frozenset(
        {
            "array_strip",
            "queue_view",
            "stack_view",
            "table_grid",
            "tree_element",
            "bit_register",
            "bar_chart",
            "graph_view",
            "map_view",
        }
    )

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
                obj_dict["items"] = list(val) if isinstance(val, (list, tuple, set)) else []
            elif cb.primitive == "stack_view":
                obj_dict["items"] = list(val) if isinstance(val, (list, tuple, set)) else []
                obj_dict["capacity"] = max(8, len(obj_dict["items"]) + 2)
            elif cb.primitive == "table_grid":
                obj_dict["items"] = val if isinstance(val, list) else []
            elif cb.primitive == "graph_view":
                # Topology đọc THẲNG từ bộ nhớ: {đỉnh: [đỉnh kề, …]}.
                adj = val if isinstance(val, dict) else {}
                obj_dict["nodes"] = sorted(str(k) for k in adj)
                obj_dict["edges"] = sorted(
                    {
                        tuple(sorted((str(u), str(v))))
                        for u, ke in adj.items()
                        for v in (ke or [])
                    }
                )
                obj_dict["edges"] = [list(e) for e in obj_dict["edges"]]
                # Trạng thái đỉnh do CHƯƠNG TRÌNH khai biến nào mang nó; adapter
                # chỉ đọc. Không có khai báo ⇒ không tô, KHÔNG tự chạy lại BFS.
                if cb.visited_ref:
                    v = snap.get(cb.visited_ref)
                    obj_dict["visited"] = sorted(
                        str(x) for x in v
                    ) if isinstance(v, (list, tuple, set)) else []
                if cb.current_ref:
                    cur = snap.get(cb.current_ref)
                    obj_dict["current"] = None if cur is None else str(cur)
            elif cb.primitive == "bar_chart":
                # Cột = phần tử của container. Renderer chỉ ĐỌC chiều cao từ đây,
                # KHÔNG tự tính lại từ biểu thức nào khác (bất biến #31).
                obj_dict["items"] = list(val) if isinstance(val, (list, tuple)) else []
            elif cb.primitive == "map_view":
                # Cặp khoá→giá trị theo THỨ TỰ KHOÁ ĐÃ SẮP, không theo thứ tự
                # chèn: thứ tự chèn phụ thuộc lượt chạy nên hai lần chụp cùng
                # một bài cho hình khác nhau, và ảnh chụp hết so được với nhau.
                # Cùng lý do `graph_view` sắp `nodes`/`edges`.
                d = val if isinstance(val, dict) else {}
                obj_dict["entries"] = [[str(k), d[k]] for k in sorted(d, key=str)]
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
