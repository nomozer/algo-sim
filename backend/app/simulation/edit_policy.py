# -*- coding: utf-8 -*-
"""EditPolicy v1 (M7.14D) — affordance chỉnh sửa DẪN XUẤT TỪ NĂNG LỰC của cảnh.

Vấn đề đang sửa: mọi cảnh generic đều nhận CÙNG một bộ thao tác (Thêm điểm/Nối/
Xóa), kể cả cảnh văn bản (container/heading/paragraph) hay cảnh giá trị
(switch/lamp/value_box). Sai về ngữ nghĩa.

Nguyên tắc:
- Suy từ CHÍNH SPEC (object/rule/process types) — spec vẫn đúng SAU khi patch,
  khác với analysis của đề gốc (analysis không có ở sample offline, không cập
  nhật sau edit).
- TUYỆT ĐỐI không hard-code theo tên bài/môn/tiêu đề ("triangle", "web"...).
- Ẩn UI là KHÔNG đủ: policy được thực thi ở cả patch validation (file này được
  patch.py + edit.py gọi) lẫn affordance (mirror TS: generic/edit-policy.ts).

LƯU Ý PHẠM VI: `EditFamily` dưới đây là phân loại của EditPolicy **v1**, KHÔNG
phải taxonomy vĩnh viễn của hệ thống (taxonomy vĩnh viễn là SEMANTIC_ROLES trong
manifest). Cảnh LAI (vd vừa structural vừa node/edge) dùng precedence BẢO THỦ —
multi-family edit CHƯA được hỗ trợ, xem docs/ARCHITECTURE_MAP.md.
"""

from __future__ import annotations

from app.simulation.dsl.manifest import limit, temporal_process_types

# ── reason_code (M7.14D) — hai namespace ─────────────────────
# policy.*    : thao tác hợp lệ về cấu trúc nhưng KHÔNG hợp với năng lực cảnh này
# structure.* : vi phạm luật DSL (id trùng, tham chiếu treo, chu trình, quá giới hạn)
POLICY_OPERATION_NOT_ALLOWED = "policy.operation_not_allowed"
POLICY_OBJECT_TYPE_NOT_ALLOWED = "policy.object_type_not_allowed"
POLICY_PATH_TOPOLOGY_LOCKED = "policy.path_topology_locked"
POLICY_FAMILY_MISMATCH = "policy.family_mismatch"  # CHỈ dùng khi không có code cụ thể hơn

STRUCTURE_INVALID = "structure.invalid"  # mặc định cho lỗi DSL (validator quyết chi tiết)

# Họ object (mirror generic/model.ts)
STRUCTURAL_TYPES = {"container", "group", "heading", "paragraph", "text"}
TEXT_CONTENT_TYPES = {"heading", "paragraph", "text"}
CONTAINER_TYPES = {"container", "group"}
RELATIONAL_TYPES = {"node", "edge"}

ALL_OPS = ("add_object", "remove_object", "update_object", "connect", "disconnect")


class EditFamily:
    """Phân loại EditPolicy v1 (không phải taxonomy vĩnh viễn của hệ)."""

    SPATIAL = "spatial"            # điểm/nút + cạnh tường minh → thêm điểm/nối/xóa
    STRUCTURAL = "structural"      # khung chứa + nội dung chữ → thêm/sửa/xóa nội dung
    VALUE_ONLY = "value_only"      # switch/lamp/value_box + rule → chỉ tương tác, không sửa cấu trúc
    OBSERVATION = "observation"    # cảnh có tiến trình di chuyển → topology KHÓA


def _types_in(spec: dict) -> set[str]:
    return {o.get("type", "") for o in spec.get("objects", [])}


def _has_move_process(spec: dict) -> bool:
    """Process di chuyển ràng buộc topology (path/entity) → không cho sửa cấu trúc."""
    return any(p.get("type") == "move_along_path" for p in spec.get("processes", []))


def _max_depth(spec: dict) -> int:
    by_id = {o["id"]: o for o in spec.get("objects", [])}
    best = 0
    for o in spec.get("objects", []):
        depth, cur, seen = 0, o["id"], {o["id"]}
        while by_id.get(cur, {}).get("parent") is not None:
            cur = by_id[cur]["parent"]
            if cur in seen:
                break
            seen.add(cur)
            depth += 1
        best = max(best, depth)
    return best


def edit_policy_of(spec: dict) -> dict:
    """Suy EditPolicy từ spec. Precedence BẢO THỦ (cảnh lai → chọn hạn chế hơn):

        move_along_path  >  structural  >  spatial  >  value_only

    Trả: {family, allowed_ops, addable_types, ui_actions, note}
    """
    types = _types_in(spec)
    has_structural = bool(types & STRUCTURAL_TYPES)
    has_relational = bool(types & RELATIONAL_TYPES)

    # 1) Tiến trình di chuyển: thêm/xóa node đổi ngữ nghĩa path → KHÓA topology.
    if _has_move_process(spec):
        return {
            "family": EditFamily.OBSERVATION,
            "allowed_ops": ["update_object"],  # đổi nhãn/nội dung là vô hại
            "addable_types": [],
            "ui_actions": ["edit_text"],
            "note": "Cảnh có tiến trình di chuyển theo đường — cấu trúc topology bị khóa.",
        }

    # 2) Cảnh cấu trúc/nội dung: thêm mục nội dung, KHÔNG thêm điểm/nối.
    if has_structural:
        addable = sorted(TEXT_CONTENT_TYPES)
        # container/group chỉ thêm được khi còn dư độ sâu lồng nhau
        if _max_depth(spec) + 1 < limit("max_nesting_depth"):
            addable += sorted(CONTAINER_TYPES)
        return {
            "family": EditFamily.STRUCTURAL,
            "allowed_ops": ["add_object", "remove_object", "update_object"],
            "addable_types": addable,
            "ui_actions": ["add_content", "edit_text", "delete"],
            "note": "Cảnh nội dung có bố cục — thêm/sửa/xóa mục nội dung.",
        }

    # 3) Cảnh quan hệ điểm-cạnh tường minh: đây (và CHỈ đây) mới có Thêm điểm/Nối.
    if has_relational:
        return {
            "family": EditFamily.SPATIAL,
            "allowed_ops": list(ALL_OPS),
            "addable_types": ["node", "edge", "label"],
            "ui_actions": ["add_node", "connect", "delete", "edit_text"],
            "note": "Cảnh điểm–cạnh — thêm điểm, nối, xóa.",
        }

    # 4) Còn lại (switch/lamp/value_box + rule): tương tác giữ nguyên, KHÔNG sửa
    #    cấu trúc (thêm/xóa object sẽ làm rule sai nghĩa).
    return {
        "family": EditFamily.VALUE_ONLY,
        "allowed_ops": ["update_object"],
        "addable_types": [],
        "ui_actions": ["edit_text"],
        "note": "Cảnh giá trị/logic — dùng tương tác sẵn có (bật/tắt), không sửa cấu trúc.",
    }


def check_ops_against_policy(spec: dict, ops: list[dict]) -> dict | None:
    """Kiểm ops theo policy của spec. Trả None nếu hợp lệ, hoặc
    {"reason_code", "error"} nếu vi phạm — CODE CỤ THỂ được ưu tiên,
    family_mismatch chỉ là fallback."""
    policy = edit_policy_of(spec)
    allowed_ops = set(policy["allowed_ops"])
    addable = set(policy["addable_types"])
    locked = policy["family"] == EditFamily.OBSERVATION

    for op in ops:
        kind = op.get("op")
        if kind not in allowed_ops:
            if locked and kind in ("add_object", "remove_object", "connect", "disconnect"):
                return {
                    "reason_code": POLICY_PATH_TOPOLOGY_LOCKED,
                    "error": (
                        f'Không thể "{kind}" trong cảnh này: có tiến trình di chuyển theo đường, '
                        "thay đổi topology sẽ làm sai đường đi. " + policy["note"]
                    ),
                }
            return {
                "reason_code": POLICY_OPERATION_NOT_ALLOWED,
                "error": f'Thao tác "{kind}" không phù hợp với cảnh này. {policy["note"]}',
            }
        if kind == "add_object":
            obj_type = (op.get("object") or {}).get("type")
            if obj_type not in addable:
                return {
                    "reason_code": POLICY_OBJECT_TYPE_NOT_ALLOWED,
                    "error": (
                        f'Không thể thêm đối tượng loại "{obj_type}" vào cảnh này. '
                        + (f'Chỉ thêm được: {", ".join(sorted(addable))}.' if addable
                           else "Cảnh này không cho thêm đối tượng mới.")
                    ),
                }
    return None


def policy_contract_text(spec: dict) -> str:
    """Mô tả policy cho prompt edit — LLM chỉ thấy thao tác/loại HỢP LỆ với cảnh
    này (prompt nhỏ hơn, ít patch sai hơn). Server vẫn chặn tất định sau đó."""
    p = edit_policy_of(spec)
    if not p["allowed_ops"] or p["allowed_ops"] == ["update_object"]:
        return (
            f"PHẠM VI CHỈNH SỬA CỦA CẢNH NÀY: {p['note']}\n"
            'Chỉ được dùng: update_object (đổi "text"/"label" của đối tượng có sẵn). '
            "Mọi yêu cầu thêm/xóa/nối đối tượng đều KHÔNG hợp lệ với cảnh này — "
            "khi đó trả operations rỗng và nêu lý do trong note."
        )
    return (
        f"PHẠM VI CHỈNH SỬA CỦA CẢNH NÀY: {p['note']}\n"
        f"Thao tác được phép: {', '.join(p['allowed_ops'])}.\n"
        f"Loại đối tượng được phép thêm: {', '.join(p['addable_types']) or 'không có'}.\n"
        "Yêu cầu nằm ngoài phạm vi này KHÔNG hợp lệ — trả operations rỗng và nêu lý do trong note."
    )
