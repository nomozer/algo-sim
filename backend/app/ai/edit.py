# -*- coding: utf-8 -*-
"""Natural-language edit NHẸ (M7.14A) — sửa tăng dần spec generic hiện có.

KHÔNG chạy full analyze → classify → simulate. Một call LLM nhỏ (skill edit)
sinh {required_roles, operations}; sau đó MỌI PHÁN QUYẾT là tất định:

1. Server đối chiếu required_roles ∩ known_gap_roles → có giao ≠ ∅ là
   "unsupported_to_verify" — KHÔNG áp patch, không tin LLM tự quyết
   supported/unsupported (chỉnh sửa B, M7.14).
2. validate_and_apply_patch: áp trên bản sao + full validator + guard tiến
   trình + engine smoke; fail → retry 1 lần kèm lỗi; vẫn fail → lỗi,
   spec hiện tại nguyên vẹn.

LLM ở đây chỉ DỊCH yêu cầu thành patch + khai vai trò — không phán đúng/sai
(docs/CORRECTNESS.md §1.6).
"""

from __future__ import annotations

import json

from app.ai.gemini import call_gemini, load_skill
from app.simulation.dsl.manifest import (
    SEMANTIC_ROLES,
    known_gap_roles,
    limit,
    object_types,
)
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.patch import ALLOWED_OPS, MAX_OPS, UPDATE_FIELDS, validate_and_apply_patch

# ── Schema structured output — sinh từ manifest, không viết tay enum rời ──

EDIT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        # Vai trò ngữ nghĩa mà YÊU CẦU SỬA cần — cùng taxonomy với analyze;
        # server đối chiếu known_gap_roles một cách TẤT ĐỊNH.
        "required_roles": {
            "type": "ARRAY",
            "items": {"type": "STRING", "enum": list(SEMANTIC_ROLES)},
        },
        "operations": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "op": {"type": "STRING", "enum": list(ALLOWED_OPS)},
                    # add_object
                    "object": {
                        "type": "OBJECT",
                        "nullable": True,
                        "properties": {
                            "id": {"type": "STRING"},
                            "type": {"type": "STRING", "enum": sorted(object_types())},
                            "x": {"type": "NUMBER", "nullable": True},
                            "y": {"type": "NUMBER", "nullable": True},
                            "label": {"type": "STRING", "nullable": True},
                            "text": {"type": "STRING", "nullable": True},
                            "parent": {"type": "STRING", "nullable": True},
                            "value": {"type": "NUMBER", "nullable": True},
                        },
                        "required": ["id", "type"],
                    },
                    # remove_object / update_object
                    "id": {"type": "STRING", "nullable": True},
                    "fields": {
                        "type": "OBJECT",
                        "nullable": True,
                        "properties": {
                            "text": {"type": "STRING", "nullable": True},
                            "label": {"type": "STRING", "nullable": True},
                            "x": {"type": "NUMBER", "nullable": True},
                            "y": {"type": "NUMBER", "nullable": True},
                            "value": {"type": "NUMBER", "nullable": True},
                        },
                    },
                    # connect / disconnect
                    "from": {"type": "STRING", "nullable": True},
                    "to": {"type": "STRING", "nullable": True},
                    "edge_id": {"type": "STRING", "nullable": True},
                    "label": {"type": "STRING", "nullable": True},
                },
                "required": ["op"],
            },
        },
        "note": {"type": "STRING", "nullable": True},
    },
    "required": ["required_roles", "operations"],
}


def _objects_summary(spec: dict) -> str:
    """Danh sách object hiện tại — gọn, đủ để LLM tham chiếu id và tính vị trí
    tương đối ('phía trên AB' → từ tọa độ A, B). KHÔNG gửi manifest dài."""
    lines = []
    for o in spec.get("objects", []):
        parts = [f'id={o["id"]}', f'type={o["type"]}']
        for k in ("label", "parent", "from", "to"):
            if o.get(k):
                parts.append(f"{k}={o[k]}")
        if isinstance(o.get("text"), str):
            parts.append(f'text="{o["text"][:40]}"')
        if isinstance(o.get("x"), (int, float)) and isinstance(o.get("y"), (int, float)):
            parts.append(f'pos=({o["x"]},{o["y"]})')
        lines.append("- " + " ".join(parts))
    return "\n".join(lines) if lines else "(chưa có object nào)"


def _edit_contract(spec: dict) -> str:
    remain = limit("max_objects") - len(spec.get("objects", []))
    return (
        f"CÁC THAO TÁC CHO PHÉP ({'/'.join(ALLOWED_OPS)}), tối đa {MAX_OPS} thao tác:\n"
        '- add_object: {"op":"add_object","object":{"id","type",...}} — type thuộc '
        f"{', '.join(sorted(object_types()))}; tọa độ x,y trong 0–100 (có thể bỏ trống để hệ tự đặt); "
        "heading/paragraph/text cần \"text\"; con của container/group đặt \"parent\".\n"
        '- connect: {"op":"connect","from","to","edge_id","label?"} — nối hai object ĐÃ tồn tại.\n'
        '- disconnect: {"op":"disconnect","edge_id"}.\n'
        '- remove_object: {"op":"remove_object","id"} — cạnh chạm object sẽ bị gỡ theo.\n'
        f'- update_object: {{"op":"update_object","id","fields"}} — fields chỉ gồm '
        f"{'/'.join(sorted(UPDATE_FIELDS))}.\n"
        f"Còn được thêm tối đa {max(0, remain)} object (giới hạn {limit('max_objects')})."
    )


def _fill_missing_edge_ids(spec: dict, ops: list[dict]) -> None:
    """LLM hay bỏ trống edge_id trong connect (schema nullable) — chuẩn hóa
    TẤT ĐỊNH phía server thay vì retry cầu may: sinh "from_to" (đánh số nếu
    trùng), tính cả id do các op trước trong CÙNG patch tạo ra."""
    taken = {o["id"] for o in spec.get("objects", [])}
    for op in ops:
        if op.get("op") == "add_object" and isinstance(op.get("object"), dict):
            oid = op["object"].get("id")
            if isinstance(oid, str):
                taken.add(oid)
        if op.get("op") == "connect" and not op.get("edge_id"):
            base = f'{op.get("from", "")}_{op.get("to", "")}'
            eid, n = base, 1
            while eid in taken:
                n += 1
                eid = f"{base}{n}"
            op["edge_id"] = eid
        if op.get("op") == "connect" and isinstance(op.get("edge_id"), str):
            taken.add(op["edge_id"])


async def edit_simulation(config: dict, instruction: str, api_key: str) -> dict:
    """Trả PatchResult mở rộng:
    - {"status": "valid", "config", "patch", "note?"}
    - {"status": "unsupported_to_verify", "reason", "missing_roles"}
    - {"status": "structurally_invalid", "error"}
    """
    # Chỉ nhận spec generic HỢP LỆ làm điểm xuất phát
    spec, err = validate_generic_config(config)
    if spec is None:
        return {"status": "structurally_invalid", "error": f"Spec hiện tại không hợp lệ: {err}"}

    base = (
        f'Yêu cầu chỉnh sửa của người học:\n"""\n{instruction}\n"""\n\n'
        f"CẢNH HIỆN TẠI (title: {spec['title']}):\n{_objects_summary(spec)}\n\n"
        f"{_edit_contract(spec)}"
    )
    prompt = base
    last_error = "không rõ"

    for _attempt in range(2):  # 1 lần + 1 retry kèm lỗi
        raw = await call_gemini(api_key, load_skill("edit"), prompt, EDIT_SCHEMA, 0.1)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            last_error = "Kết quả không phải JSON hợp lệ."
            prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."
            continue

        # ── Phán quyết TẤT ĐỊNH #1: vai trò dẫn xuất → unsupported_to_verify ──
        roles = {r for r in parsed.get("required_roles", []) if r in SEMANTIC_ROLES}
        gaps = sorted(roles & known_gap_roles())
        if gaps:
            return {
                "status": "unsupported_to_verify",
                "reason": (
                    "Yêu cầu này cần năng lực hệ chưa có "
                    f"(vai trò: {', '.join(gaps)}) — hệ không thể đặt đối tượng đúng "
                    "bản chất toán học nên sẽ không thêm hình xấp xỉ. "
                    "Bạn vẫn có thể thêm/nối các đối tượng tường minh."
                ),
                "missing_roles": gaps,
            }

        # ── Phán quyết TẤT ĐỊNH #2: patch validate + apply trên bản sao ──
        ops = [op for op in parsed.get("operations", []) if isinstance(op, dict)]
        # dọn khóa null từ structured output để patch nhận đúng hình dạng
        cleaned = [{k: v for k, v in op.items() if v is not None} for op in ops]
        _fill_missing_edge_ids(spec, cleaned)
        result = validate_and_apply_patch(spec, {"operations": cleaned})
        if result["status"] == "valid":
            out = {"status": "valid", "config": result["config"], "patch": {"operations": cleaned}}
            if isinstance(parsed.get("note"), str) and parsed["note"]:
                out["note"] = parsed["note"]
            return out
        last_error = result.get("error", "không rõ")
        prompt = f"{base}\n\nLần trước bị từ chối vì: {last_error}\nHãy sửa lại."

    return {"status": "structurally_invalid", "error": last_error}
