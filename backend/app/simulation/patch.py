# -*- coding: utf-8 -*-
"""SimulationPatch v1 (M7.14A) — chỉnh sửa TĂNG DẦN spec generic hiện có.

Patch chỉ là con đường thứ ba sinh ra một SimulationSpec HỢP LỆ (sau compose
và pattern reuse): áp ops trên BẢN SAO → full validate_generic_config → guard
bảo toàn tiến trình → engine build smoke. Patch fail ở bất kỳ bước nào thì spec
hiện tại NGUYÊN VẸN — không mutate.

PatchResult.status (docs/CORRECTNESS.md §3 — TÁCH BẠCH với InteractionFeedback):
- "valid"                → có config mới đã validate.
- "structurally_invalid" → id trùng / tham chiếu treo / vượt limit / phá luật
                            DSL → hard reject.
- "unsupported_to_verify" → yêu cầu cần năng lực chưa có (do TẦNG EDIT quyết
                            bằng known_gap_roles — patch thuần cấu trúc không
                            tự sinh status này).
- "invalid_with_feedback" → RESERVED: patch hợp lệ cấu trúc nhưng vi phạm rule
                            NGỮ NGHĨA engine CÓ — chưa có producer ở M7.14
                            (chờ M7.15 geometry constraints).

V1 không có op cho rules/processes/interactions — không phá scene_mode bằng patch.
"""

from __future__ import annotations

import copy

from app.simulation.dsl.manifest import temporal_process_types
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.edit_policy import STRUCTURE_INVALID, check_ops_against_policy
from app.simulation.generic_engine import build_timeline, initial_base, values_of

PATCH_STATUSES = ("valid", "structurally_invalid", "unsupported_to_verify", "invalid_with_feedback")

MAX_OPS = 10
ALLOWED_OPS = ("add_object", "remove_object", "update_object", "connect", "disconnect")
# update_object chỉ đổi NỘI DUNG/VỊ TRÍ — đổi cấu trúc (type/id/from/to/parent)
# phải remove + add tường minh.
UPDATE_FIELDS = {"text", "label", "x", "y", "value"}
# Trường được nhận khi add_object (validator full vẫn là chốt chặn cuối).
ADD_FIELDS = {"id", "type", "x", "y", "label", "text", "parent", "value", "weight", "node_type", "from", "to"}


def _invalid(msg: str, reason_code: str = STRUCTURE_INVALID) -> dict:
    """Lỗi patch. M7.14D: kèm reason_code hai namespace —
    `structure.*` (vi phạm luật DSL) vs `policy.*` (không hợp năng lực cảnh)."""
    return {"status": "structurally_invalid", "reason_code": reason_code, "error": msg}


def _ids(work: dict) -> set[str]:
    return {o["id"] for o in work["objects"]}


def _semantic_dependents(work: dict, oid: str) -> str | None:
    """Object bị RULE/PROCESS/parent-con phụ thuộc → KHÔNG cascade mù, reject rõ."""
    for r in work.get("rules", []):
        if r.get("target") == oid or oid in (r.get("inputs") or []):
            return f'"{oid}" đang là target/input của một rule — hãy sửa rule trước khi xóa.'
    for p in work.get("processes", []):
        if p.get("entity") == oid:
            return f'"{oid}" đang là entity của một process — không thể xóa.'
        if oid in (p.get("path") or []):
            return f'"{oid}" đang nằm trong path của move_along_path — không thể xóa.'
    children = [o["id"] for o in work["objects"] if o.get("parent") == oid]
    if children:
        return (
            f'"{oid}" đang chứa các object con ({", ".join(children)}) — '
            "hãy xóa/di chuyển các object con trước."
        )
    return None


def _cascade_remove(work: dict, removed: set[str]) -> None:
    """Gỡ dependents THUẦN HÌNH của các id đã xóa: interactions trỏ tới chúng,
    reveal-step nhắc tới chúng (step rỗng thì bỏ; reveal rỗng thì bỏ process)."""
    work["interactions"] = [it for it in work.get("interactions", []) if it.get("target") not in removed]
    new_procs = []
    for p in work.get("processes", []):
        if p.get("type") != "reveal_sequence":
            new_procs.append(p)
            continue
        steps = []
        for st in p.get("steps", []):
            objs = [o for o in st.get("objects", []) if o not in removed]
            if objs:
                steps.append({**st, "objects": objs})
        if steps:
            new_procs.append({**p, "steps": steps})
        # reveal không còn step nào → bỏ process (guard temporal sẽ bắt nếu mất diễn biến)
    work["processes"] = new_procs


def _remove_object(work: dict, oid: str) -> str | None:
    if oid not in _ids(work):
        return f'remove_object: "{oid}" không tồn tại.'
    dep = _semantic_dependents(work, oid)
    if dep:
        return dep
    # cascade các edge chạm object (edge là dependent thuần hình)
    removed = {oid} | {
        o["id"] for o in work["objects"]
        if o.get("type") == "edge" and (o.get("from") == oid or o.get("to") == oid)
    }
    work["objects"] = [o for o in work["objects"] if o["id"] not in removed]
    _cascade_remove(work, removed)
    return None


def _apply_one(work: dict, op: dict) -> str | None:
    """Áp MỘT operation lên bản làm việc; trả thông báo lỗi hoặc None."""
    if not isinstance(op, dict) or op.get("op") not in ALLOWED_OPS:
        return f'Operation không hợp lệ: "{op.get("op") if isinstance(op, dict) else op}".'
    kind = op["op"]

    if kind == "add_object":
        obj = op.get("object")
        if not isinstance(obj, dict) or not isinstance(obj.get("id"), str) or not obj["id"]:
            return 'add_object cần "object" có "id" chuỗi.'
        if obj["id"] in _ids(work):
            return f'add_object: id "{obj["id"]}" đã tồn tại.'
        clean = {k: v for k, v in obj.items() if k in ADD_FIELDS and v is not None}
        work["objects"].append(clean)
        return None

    if kind == "remove_object":
        oid = op.get("id")
        if not isinstance(oid, str):
            return 'remove_object cần "id" chuỗi.'
        return _remove_object(work, oid)

    if kind == "update_object":
        oid = op.get("id")
        fields = op.get("fields")
        if not isinstance(oid, str) or oid not in _ids(work):
            return f'update_object: "{oid}" không tồn tại.'
        if not isinstance(fields, dict) or not fields:
            return 'update_object cần "fields" không rỗng.'
        bad = set(fields) - UPDATE_FIELDS
        if bad:
            return (
                f'update_object chỉ đổi được {"/".join(sorted(UPDATE_FIELDS))} — '
                f'trường "{sorted(bad)[0]}" là cấu trúc, hãy remove + add.'
            )
        for o in work["objects"]:
            if o["id"] == oid:
                for k, v in fields.items():
                    if v is None:
                        o.pop(k, None)
                    else:
                        o[k] = v
        return None

    if kind == "connect":
        frm, to, eid = op.get("from"), op.get("to"), op.get("edge_id")
        if not (isinstance(frm, str) and isinstance(to, str) and isinstance(eid, str) and eid):
            return 'connect cần "from"/"to"/"edge_id" chuỗi.'
        ids = _ids(work)
        if frm not in ids or to not in ids:
            return f'connect: hai đầu phải tồn tại ("{frm}" → "{to}").'
        if eid in ids:
            return f'connect: edge_id "{eid}" đã tồn tại.'
        edge = {"id": eid, "type": "edge", "from": frm, "to": to}
        if isinstance(op.get("label"), str) and op["label"]:
            edge["label"] = op["label"]
        work["objects"].append(edge)
        return None

    # disconnect
    eid = op.get("edge_id")
    if not isinstance(eid, str):
        return 'disconnect cần "edge_id" chuỗi.'
    target = next((o for o in work["objects"] if o["id"] == eid), None)
    if target is None or target.get("type") != "edge":
        return f'disconnect: "{eid}" không phải một edge đang tồn tại.'
    work["objects"] = [o for o in work["objects"] if o["id"] != eid]
    _cascade_remove(work, {eid})
    return None


def validate_and_apply_patch(spec: dict, patch: dict, enforce_policy: bool = True) -> dict:
    """Trả PatchResult. spec đầu vào KHÔNG BAO GIỜ bị mutate.

    M7.14D: kiểm EditPolicy TRƯỚC khi áp — thao tác/loại object không hợp với
    năng lực cảnh (thêm điểm vào cảnh văn bản, sửa topology của cảnh có
    move_along_path...) bị từ chối với reason_code `policy.*`.
    """
    if not isinstance(patch, dict):
        return _invalid("Patch không phải đối tượng JSON.")
    ops = patch.get("operations")
    if not isinstance(ops, list) or not (1 <= len(ops) <= MAX_OPS):
        return _invalid(f'Patch cần "operations" có 1–{MAX_OPS} thao tác.')

    if enforce_policy:
        violation = check_ops_against_policy(spec, [op for op in ops if isinstance(op, dict)])
        if violation:
            return _invalid(violation["error"], violation["reason_code"])

    work = copy.deepcopy(spec)
    # chuẩn hóa các section có thể vắng (spec đã validate luôn có, nhưng phòng hờ)
    for key in ("objects", "rules", "interactions", "processes"):
        work.setdefault(key, [])

    for op in ops:
        err = _apply_one(work, op)
        if err:
            return _invalid(err)

    # Chốt chặn cuối: TOÀN BỘ luật DSL qua validator nguồn chân lý
    config, verr = validate_generic_config(work)
    if config is None:
        return _invalid(verr or "Spec sau patch không hợp lệ.")

    # Bảo toàn tiến trình: spec đang có diễn biến thì patch không được làm mất
    # (suy từ chính spec — họ temporal từ manifest, không hard-code reveal)
    temporal = temporal_process_types()
    had = any(p.get("type") in temporal for p in spec.get("processes", []))
    has = any(p.get("type") in temporal for p in config.get("processes", []))
    if had and not has:
        return _invalid(
            "Patch làm mất toàn bộ tiến trình diễn biến của cảnh — "
            "hãy giữ lại ít nhất một bước hình thành hoặc xóa ít object hơn."
        )

    # Engine build smoke — reuse/patch không bypass engine success
    try:
        frames = build_timeline(config)
        values_of(config, initial_base(config))
        if not frames:
            return _invalid("Engine không dựng được timeline từ spec sau patch.")
    except Exception as exc:
        return _invalid(f"Engine lỗi với spec sau patch: {exc}")

    return {"status": "valid", "config": config, "applied_ops": len(ops)}
