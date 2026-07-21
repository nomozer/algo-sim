# -*- coding: utf-8 -*-
"""M17-RC1 §C2 — CỔNG ĐỦ DỮ KIỆN DÙNG CHUNG (một cổng, mọi target).

Luồng: target đã chọn → đọc `required_grounded_inputs` từ hợp đồng → chuẩn hoá
bằng chứng trong analyze → PASS hoặc TỪ CHỐI SỚM AN TOÀN → **chỉ sau PASS mới
được dựng spec/simulation**.

Nguyên tắc cấu trúc (điều kiện §C2):
- normalizer đăng ký theo **NHÓM DỮ KIỆN** (`InputKind`), KHÔNG theo target ⇒
  không có `sort_sufficiency_gate.py` / `graph_sufficiency_gate.py`…;
- deterministic given analyze — KHÔNG đọc text đề, KHÔNG keyword;
- `generated_default` KHÔNG thoả required input (hợp đồng phải công khai cho
  phép thì mới được, và hiện chỉ áp cho target NOT_APPLICABLE).

PHÒNG THỦ NHIỀU LỚP (đã thống nhất từ W2A): classify tự từ chối sớm **hoặc**
cổng này từ chối đều hợp lệ — miễn là executor không chạy, simulation không
được tạo, generic không nhận, và dữ kiện không bị bịa.

Thiên lệch có chủ đích: normalizer đặt ngưỡng **thấp** (chỉ cần bằng chứng yếu
là cho qua). Chặn oan một đề THẬT tệ hơn nhiều so với lọt một đề mơ hồ — đề mơ
hồ vẫn còn validator và các cổng khác phía sau. Vì vậy cổng này chỉ bắt trường
hợp đề gần như KHÔNG cho gì.
"""

from __future__ import annotations

import re

from app.simulation.error_codes import ErrorCode
from app.simulation.input_requirements import (
    InputKind,
    InputRequirements,
    requirements_for,
)
from app.simulation.structure_gate import linked_node_items

_NUM_RE = re.compile(r"-?\d+(?:[.,]\d+)?")


# ── đọc analyze thành mảnh dùng chung ────────────────────────────
def _data_items(analysis: dict) -> list[dict]:
    items = analysis.get("data") if isinstance(analysis, dict) else None
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def _str_list(analysis: dict, key: str) -> list[str]:
    items = analysis.get(key) if isinstance(analysis, dict) else None
    if not isinstance(items, list):
        return []
    out = []
    for it in items:
        if isinstance(it, str) and it.strip():
            out.append(it)
        elif isinstance(it, dict):
            joined = " ".join(v for v in it.values() if isinstance(v, str))
            if joined.strip():
                out.append(joined)
    return out


def _numeric_tokens(analysis: dict) -> list[str]:
    """Số CỤ THỂ xuất hiện Ở BẤT KỲ ĐÂU trong analyze.

    Cố tình quét TOÀN BỘ payload (đệ quy) chứ không bám một field: chưa có bằng
    chứng ghi lại về việc analyze thật có luôn điền `data[].values` hay không
    (live artifact W1/W2A không lưu analysis, và §C2 không được chạy live). Bám
    một field mà field đó trống ở đời thực ⇒ CHẶN OAN hàng loạt. Quét rộng thì
    chỉ bỏ lọt đề mơ hồ — vốn còn validator và các cổng khác phía sau."""
    toks: list[str] = []

    def walk(node: object) -> None:
        if isinstance(node, str):
            toks.extend(_NUM_RE.findall(node))
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            toks.append(str(node))
        elif isinstance(node, dict):
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(analysis if isinstance(analysis, dict) else {})
    return toks


# ── normalizer theo NHÓM DỮ KIỆN ─────────────────────────────────
def _has_finite_sequence(analysis: dict) -> tuple[bool, dict]:
    """Dãy hữu hạn: `data.values`/`data.labels` ≥2 phần tử, HOẶC ≥2 con số cụ
    thể ở bất kỳ đâu trong analyze, HOẶC ≥2 nhãn phần tử. Một con số lẻ KHÔNG
    phải dãy (đó là NUMERIC_VALUE)."""
    for item in _data_items(analysis):
        for key in ("values", "labels"):
            v = item.get(key)
            if isinstance(v, list) and len(v) >= 2:
                return True, {"source": f"data.{key}", "size": len(v)}
    toks = _numeric_tokens(analysis)
    if len(toks) >= 2:
        return True, {"source": "analysis.numeric_tokens", "size": len(toks),
                      "found": toks[:5]}
    return False, {"source": None, "numeric_tokens": len(toks)}


def _has_numeric_value(analysis: dict) -> tuple[bool, dict]:
    toks = _numeric_tokens(analysis)
    return bool(toks), {"source": "numeric_tokens", "found": toks[:5]}


def _has_tree_structure(analysis: dict) -> tuple[bool, dict]:
    """Tái dùng NGUYÊN luật đã chứng minh ở live W2A: ≥1 item nêu quan hệ giữa
    ≥2 nút CÓ TÊN. Không nới, không siết."""
    linked = linked_node_items(analysis)
    return bool(linked), {"source": "relations.named_pair", "linked_items": len(linked)}


def _has_graph_structure(analysis: dict) -> tuple[bool, dict]:
    """Đồ thị: hoặc có quan hệ giữa hai nút CÓ TÊN (như cây), hoặc nêu ≥2 đối
    tượng KÈM ≥1 quan hệ. Nới hơn cây vì tên đỉnh đời thực thường dài ("Trạm
    Bản Giốc") nên luật định-danh-ngắn của cây sẽ chặn oan."""
    linked = linked_node_items(analysis)
    if linked:
        return True, {"source": "relations.named_pair", "linked_items": len(linked)}
    objects = _str_list(analysis, "objects")
    relations = _str_list(analysis, "relations")
    if len(objects) >= 2 and len(relations) >= 1:
        return True, {"source": "objects+relations", "objects": len(objects),
                      "relations": len(relations)}
    return False, {"source": None, "objects": len(objects), "relations": len(relations)}


def _has_boolean_expression(analysis: dict) -> tuple[bool, dict]:
    """Mạch logic: đề phải nêu ≥2 thành phần (đầu vào/cổng). Một đề chỉ nói
    "vẽ mạch logic" không nêu gì thì objects rỗng hoặc 1."""
    objects = _str_list(analysis, "objects")
    return len(objects) >= 2, {"source": "objects", "objects": len(objects)}


def _has_conversion_parameters(analysis: dict) -> tuple[bool, dict]:
    """Đổi cơ số: tối thiểu phải có SỐ cần đổi (cơ số có thể nằm ở goal/
    constraints và được validator kiểm sau)."""
    return _has_numeric_value(analysis)


def _has_representation_objects(analysis: dict) -> tuple[bool, dict]:
    objects = _str_list(analysis, "objects")
    return bool(objects), {"source": "objects", "objects": len(objects)}


def _has_packet_or_layer(analysis: dict) -> tuple[bool, dict]:
    # Không target nào khai BẮT BUỘC nhóm này (engine sở hữu 9 bước PDU); giữ
    # normalizer để hợp đồng đóng — mọi InputKind đều có normalizer.
    return True, {"source": "engine_owned"}


EVIDENCE_NORMALIZERS = {
    InputKind.FINITE_SEQUENCE: _has_finite_sequence,
    InputKind.NUMERIC_VALUE: _has_numeric_value,
    InputKind.GRAPH_STRUCTURE: _has_graph_structure,
    InputKind.TREE_STRUCTURE: _has_tree_structure,
    InputKind.BOOLEAN_EXPRESSION: _has_boolean_expression,
    InputKind.CONVERSION_PARAMETERS: _has_conversion_parameters,
    InputKind.PACKET_OR_LAYER_DESCRIPTION: _has_packet_or_layer,
    InputKind.REPRESENTATION_OBJECTS: _has_representation_objects,
}


def sufficiency_evidence(analysis: dict, target_id: str) -> dict:
    """Bằng chứng máy-đọc (artifact/audit). Không đổi phán quyết."""
    req = requirements_for(target_id)
    if req is None:
        return {"target_id": target_id, "declared": False, "required": [], "missing": []}
    found, missing = _evaluate(analysis, req)
    return {
        "target_id": target_id,
        "declared": True,
        "applicability": req.applicability,
        "required": [k.value for k in req.required_grounded_inputs],
        "satisfied": {k: v for k, v in found.items()},
        "missing": missing,
        "generated_defaults_allowed": req.generated_defaults_allowed,
    }


def _evaluate(analysis: dict, req: InputRequirements) -> tuple[dict, list[str]]:
    found: dict[str, dict] = {}
    missing: list[str] = []
    for kind in req.required_grounded_inputs:
        normalizer = EVIDENCE_NORMALIZERS[kind]  # KeyError = InputKind thiếu normalizer
        ok, detail = normalizer(analysis if isinstance(analysis, dict) else {})
        if ok:
            found[kind.value] = detail
        else:
            missing.append(kind.value)
    return found, missing


def check_input_sufficiency(
    analysis: dict, target_id: str
) -> tuple[ErrorCode, str, dict] | None:
    """Trả (code, message học-sinh, evidence) khi THIẾU dữ kiện; None khi đủ.

    Gọi SAU khi route đã chốt và TRƯỚC khi dựng spec — chỉ sau PASS mới được
    tạo simulation."""
    req = requirements_for(target_id)
    if req is None or not req.required_grounded_inputs:
        return None
    found, missing = _evaluate(analysis, req)
    if not missing:
        return None
    return (
        req.insufficiency_error_code,
        req.learner_prompt_template,
        {
            "target_id": target_id,
            "required_grounded_inputs": [k.value for k in req.required_grounded_inputs],
            "missing_inputs": missing,
            "satisfied_inputs": sorted(found),
            "generated_defaults_allowed": req.generated_defaults_allowed,
        },
    )


def check_input_sufficiency_for_targets(
    analysis: dict, target_ids: list[str]
) -> tuple[ErrorCode, str, dict] | None:
    """Cho nhánh SELECTOR: route mới là token, target cụ thể chỉ biết sau khi
    resolve — nhưng dữ kiện phải kiểm TRƯỚC simulate.

    Dùng GIAO của các nhóm bắt buộc trên mọi variant (không phải hợp): chỉ đòi
    thứ mà biến thể NÀO cũng cần, nên không bao giờ đòi thừa → không chặn oan.
    Ví dụ sorting: cả bubble/insertion/selection đều cần `finite_sequence`."""
    reqs = [requirements_for(t) for t in target_ids]
    declared = [r for r in reqs if r is not None]
    if not declared or len(declared) != len(target_ids):
        return None  # có variant chưa khai hợp đồng → không suy đoán
    common = set(declared[0].required_grounded_inputs)
    for r in declared[1:]:
        common &= set(r.required_grounded_inputs)
    if not common:
        return None
    ref = declared[0]
    missing = [
        k.value for k in sorted(common, key=lambda x: x.value)
        if not EVIDENCE_NORMALIZERS[k](analysis if isinstance(analysis, dict) else {})[0]
    ]
    if not missing:
        return None
    return (
        ref.insufficiency_error_code,
        ref.learner_prompt_template,
        {
            "target_id": None,
            "selector_variants": sorted(target_ids),
            "required_grounded_inputs": sorted(k.value for k in common),
            "missing_inputs": missing,
            "satisfied_inputs": [],
            "generated_defaults_allowed": ref.generated_defaults_allowed,
        },
    )


__all__ = [
    "EVIDENCE_NORMALIZERS",
    "check_input_sufficiency",
    "check_input_sufficiency_for_targets",
    "sufficiency_evidence",
]
