"""Disallowed Pairwise Collision Verifier (Python Backend Mirror).

Kiểm tra va chạm vùng cấm server-side để thẩm định chất lượng hình học của
mô phỏng trước khi phát hành (Gate 8).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any


@dataclass
class Rect:
    id: str
    type: str
    label: str | None
    x1: float
    y1: float
    x2: float
    y2: float


def compute_aabb(obj: dict[str, Any], cx: float, cy: float) -> Rect:
    otype = obj.get("type", "")
    hw = 10.0
    hh = 8.0

    if otype == "array_strip":
        count = len(obj.get("items") or [1])
        hw = min(40.0, max(12.0, count * 3.5))
        hh = 9.0
    elif otype == "bar_chart":
        count = len(obj.get("bars") or [1])
        hw = min(40.0, max(15.0, count * 4.0))
        hh = 16.0
    elif otype == "table_grid":
        cols = len(obj.get("headers") or [1, 2])
        hw = min(42.0, max(16.0, cols * 7.0))
        hh = 18.0
    elif otype == "stack_view":
        hw = 11.0
        hh = 18.0
    elif otype == "queue_view":
        hw = 18.0
        hh = 10.0
    elif otype == "value_box":
        hw = 9.0
        hh = 8.0
    elif otype == "slider":
        hw = 14.0
        hh = 8.0

    return Rect(
        id=obj["id"],
        type=otype,
        label=obj.get("label"),
        x1=cx - hw,
        y1=cy - hh,
        x2=cx + hw,
        y2=cy + hh,
    )


def intersects(r1: Rect, r2: Rect, tolerance: float = 1.0) -> bool:
    return not (
        r1.x2 - tolerance < r2.x1
        or r1.x1 + tolerance > r2.x2
        or r1.y2 - tolerance < r2.y1
        or r1.y1 + tolerance > r2.y2
    )


def compute_semantic_layout_py(spec: dict[str, Any]) -> dict[str, dict[str, float]]:
    """Python port của computeSemanticLayout."""
    pos: dict[str, dict[str, float]] = {}
    objects = spec.get("objects", [])
    structural = {"container", "group", "heading", "paragraph", "text", "pointer", "edge"}
    active = [o for o in objects if isinstance(o, dict) and o.get("type") not in structural]

    input_objs = []
    state_objs = []
    struct_objs = []
    output_objs = []
    other_objs = []

    for o in active:
        oid = o["id"]
        otype = o.get("type")
        if isinstance(o.get("x"), (int, float)) and isinstance(o.get("y"), (int, float)):
            pos[oid] = {"x": float(o["x"]), "y": float(o["y"])}
            continue

        if otype in ("array_strip", "bar_chart", "table_grid"):
            input_objs.append(o)
        elif otype in ("stack_view", "queue_view", "tree_element"):
            struct_objs.append(o)
        elif otype == "value_box" and any(
            k in (o.get("label") or "").lower() or k in oid.lower()
            for k in ("kết quả", "result", "kết luận", "thành tích", "tổng", "đếm", "res", "count")
        ):
            output_objs.append(o)
        elif otype in ("value_box", "switch", "slider", "lamp"):
            state_objs.append(o)
        else:
            other_objs.append(o)

    has_struct = len(struct_objs) > 0
    for idx, o in enumerate(input_objs):
        if o["id"] not in pos:
            pos[o["id"]] = {"x": 34.0 if has_struct else 50.0, "y": 18.0 + idx * 28.0 if has_struct else 22.0 + idx * 30.0}

    for idx, o in enumerate(struct_objs):
        if o["id"] not in pos:
            pos[o["id"]] = {"x": 78.0 + idx * 22.0, "y": 35.0}

    start_y = (50.0 if has_struct else 62.0) if input_objs else 25.0
    for idx, o in enumerate(state_objs):
        if o["id"] not in pos:
            col = idx % 2
            row = idx // 2
            base_x = 22.0 + col * 26.0 if has_struct else 30.0 + col * 38.0
            pos[o["id"]] = {"x": base_x, "y": start_y + row * 24.0}

    start_out_y = min(84.0, 52.0 + ((len(state_objs) + 1) // 2) * 22.0) if state_objs else (65.0 if input_objs else 45.0)
    for idx, o in enumerate(output_objs):
        if o["id"] not in pos:
            col = idx % 2
            row = idx // 2
            base_x = 26.0 + col * 28.0 if has_struct else (50.0 if (col == 0 and len(output_objs) == 1) else 50.0 + (col * 34.0 - 17.0))
            pos[o["id"]] = {"x": base_x, "y": start_out_y + row * 20.0}

    for idx, o in enumerate(other_objs):
        if o["id"] not in pos:
            pos[o["id"]] = {"x": 20.0 + (idx % 3) * 30.0, "y": 70.0 + (idx // 3) * 22.0}

    return pos


def check_disallowed_collisions_py(
    spec: dict[str, Any],
    custom_pos: dict[str, dict[str, float]] | None = None,
) -> list[dict[str, Any]]:
    """Kiểm tra va chạm vùng cấm server-side."""
    pos = custom_pos if custom_pos is not None else compute_semantic_layout_py(spec)
    structural = {"container", "group", "heading", "paragraph", "text", "pointer", "edge", "label"}
    objects = spec.get("objects", [])
    active = [o for o in objects if isinstance(o, dict) and o.get("type") not in structural]

    violations: list[dict[str, Any]] = []
    boxes: list[Rect] = []

    for o in active:
        oid = o.get("id", "")
        p = pos.get(oid)
        if not p:
            continue
        cx, cy = p["x"], p["y"]
        if cx < 5 or cx > 95 or cy < 5 or cy > 95:
            violations.append({
                "kind": "CANVAS_OVERFLOW",
                "id1": oid,
                "message": f'Đối tượng "{oid}" ({o.get("type")}) nằm quá sát biên: ({cx}, {cy}).',
            })
        boxes.append(compute_aabb(o, cx, cy))

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            b1 = boxes[i]
            b2 = boxes[j]
            if intersects(b1, b2):
                violations.append({
                    "kind": "BOX_ON_BOX",
                    "id1": b1.id,
                    "id2": b2.id,
                    "message": f'Va chạm vùng cấm giữa "{b1.id}" ({b1.type}) và "{b2.id}" ({b2.type}).',
                })

    return violations
