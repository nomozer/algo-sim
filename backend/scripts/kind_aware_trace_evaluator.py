# -*- coding: utf-8 -*-
"""KIND_AWARE_TRACE_EVALUATOR (2026-09-22).

Evaluation Tooling phục vụ wave MODEL_VARIANCE_EVIDENCE_REVIEW:
1. Token Usage Audit: Phân biệt nghiêm ngặt missing/unobserved (UNKNOWN) với số 0 thực sự.
   Không bao giờ dùng .get(..., 0) trên dữ liệu thiếu.
2. Kind-Aware Structural Trace: Đánh giá cấu trúc theo đúng relation kind, loại bỏ
   hoàn toàn false-positive do default field rỗng từ Pydantic dump.
   Bất biến cốt lõi: Quan hệ đã accepted TUYỆT ĐỐI KHÔNG mang nhãn structural defect.
3. Tách biệt rành mạch:
   - Current Output Status (CANONICAL_VALID, HIGH)
   - Historical Root Cause (NOT_ESTABLISHED, NOT_ESTABLISHED)
   - Model Variance Hypothesis (CONSISTENT_WITH_CURRENT_EVIDENCE, NOT PROVEN)
   - Failure Cluster Homogeneity (NOT_APPLICABLE_NO_CURRENT_FAILURES)
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ALLOWLIST_KEYS = {
    "kind", "line", "other_line", "plane", "line1", "line2",
    "points", "source_fact_id", "model_assumption", "description",
}

FORBIDDEN_RAW_KEYS = {
    "raw_response", "raw_candidate", "raw_prompt", "problem_text",
    "point_labels", "endpoint_values", "plane_values", "source_fact_id_value",
    "unknown_key_names", "string_values", "numerical_values", "input",
    "input_value", "msg", "ctx", "traceback", "exception_message",
    "semantic_program", "api_key",
}

KIND_SPECS: dict[str, dict[str, Any]] = {
    "perpendicular_lines": {
        "required": ["kind", "line", "other_line", "source_fact_id"],
        "applicable_arities": {"line": 2, "other_line": 2},
        "forbidden_non_empty": ["plane"],
    },
    "perpendicular_line_plane": {
        "required": ["kind", "line", "plane", "source_fact_id"],
        "applicable_arities": {"line": 2, "plane": 3},
        "forbidden_non_empty": ["other_line"],
    },
    "parallel_lines": {
        "required": ["kind", "line", "other_line", "source_fact_id"],
        "applicable_arities": {"line": 2, "other_line": 2},
        "forbidden_non_empty": ["plane"],
    },
    "parallel_line_plane": {
        "required": ["kind", "line", "plane", "source_fact_id"],
        "applicable_arities": {"line": 2, "plane": 3},
        "forbidden_non_empty": ["other_line"],
    },
    "perpendicular_planes": {
        "required": ["kind", "plane", "other_plane", "source_fact_id"],
        "applicable_arities": {"plane": 3, "other_plane": 3},
        "forbidden_non_empty": ["line", "other_line"],
    },
    "parallel_planes": {
        "required": ["kind", "plane", "other_plane", "source_fact_id"],
        "applicable_arities": {"plane": 3, "other_plane": 3},
        "forbidden_non_empty": ["line", "other_line"],
    },
}


# ══════════════════════════════════════════════════════════════════════════
# §1 · TOKEN USAGE AUDIT
# ══════════════════════════════════════════════════════════════════════════
def parse_token_count(usage_dict: dict[str, Any] | None, field_name: str) -> int | str:
    """Chính sách token usage bắt buộc:
    - Thiếu dictionary hoặc dictionary rỗng => UNKNOWN.
    - Trường không có trong dictionary hoặc có giá trị None => UNKNOWN.
    - Chỉ ghi số nguyên >= 0 nếu trường thực sự tồn tại với giá trị số.
    - TUYỆT ĐỐI KHÔNG dùng .get(..., 0) để ngụy tạo missing data thành 0.
    """
    if not usage_dict or not isinstance(usage_dict, dict):
        return "UNKNOWN"
    if field_name not in usage_dict:
        return "UNKNOWN"
    val = usage_dict[field_name]
    if val is None or val == "":
        return "UNKNOWN"
    if isinstance(val, (int, float)):
        return int(val)
    return "UNKNOWN"


def aggregate_tokens(case_usages: list[dict[str, Any] | None], field_name: str) -> tuple[int | str, int]:
    """Tính tổng token cho một trường:
    - Nếu bất kỳ ca nào là UNKNOWN, tổng aggregate BẮT BUỘC là UNKNOWN.
    - Trả về đồng thời (aggregate_result, known_subtotal).
    """
    known_subtotal = 0
    has_unknown = False
    for u in case_usages:
        c = parse_token_count(u, field_name)
        if c == "UNKNOWN":
            has_unknown = True
        elif isinstance(c, int):
            known_subtotal += c
        else:
            has_unknown = True
    aggregate_val = "UNKNOWN" if has_unknown else known_subtotal
    return aggregate_val, known_subtotal


# ══════════════════════════════════════════════════════════════════════════
# §2 · KIND-AWARE RELATION STRUCTURAL TRACE
# ══════════════════════════════════════════════════════════════════════════
def extract_kind_aware_trace(
    rel_obj: Any,
    index: int,
    declared_points: set[str],
    declared_fact_ids: set[str],
    normalizer_accepted: bool = False,
    rule_id: str | None = None,
    pydantic_error_type: str | None = None,
) -> dict[str, Any]:
    """Trích xuất safe trace nhận biết loại quan hệ (kind-aware).
    Khắc phục false-positive của extractor cũ khi Pydantic model_dump sinh
    các trường rỗng mặc định (plane=() cho perpendicular_lines).
    """
    rec_type = type(rel_obj).__name__
    if not isinstance(rel_obj, dict):
        return {
            "relation_index": index,
            "received_json_type": rec_type,
            "recognized_kind": None,
            "valid_keys_present": [],
            "required_fields_present": {},
            "field_json_types": {},
            "array_lengths": {},
            "element_type_sequences": {},
            "pydantic_error_type": "type_error",
            "rfc6901_pointer": f"/geometric_relations/{index}",
            "pointer_status": "EXACT",
            "candidate_pointer_count": 1,
            "rule_id": "NOT_AN_OBJECT",
            "source_fact_resolved": False,
            "point_reference_valid": False,
            "unknown_key_count": 0,
            "structural_pattern_id": "WRONG_JSON_TYPE",
            "accepted": False,
        }

    raw_kind = rel_obj.get("kind")
    spec = KIND_SPECS.get(str(raw_kind))
    rec_kind = str(raw_kind) if spec is not None else None

    present_keys = list(rel_obj.keys())
    valid_keys = sorted([k for k in present_keys if k in ALLOWLIST_KEYS])
    unknown_keys = [k for k in present_keys if k not in ALLOWLIST_KEYS]
    unknown_key_count = len(unknown_keys)

    # Required fields check
    req_present: dict[str, bool] = {}
    if spec:
        for rf in spec["required"]:
            req_present[rf] = bool(rf in rel_obj and rel_obj[rf])
    else:
        req_present["kind"] = "kind" in rel_obj

    # Source fact resolution
    raw_sfid = rel_obj.get("source_fact_id")
    sf_resolved = bool(raw_sfid and str(raw_sfid) in declared_fact_ids)

    # Point references validation
    pt_refs_valid = True
    for fld in ("line", "other_line", "plane", "other_plane", "points", "line1", "line2"):
        val = rel_obj.get(fld)
        if isinstance(val, (list, tuple)):
            for p in val:
                if isinstance(p, str) and declared_points and p not in declared_points:
                    pt_refs_valid = False

    # Defect detection
    defects: list[str] = []
    ptr: str = f"/geometric_relations/{index}"
    ptr_status: str = "EXACT"

    if rec_kind is None:
        defects.append("UNRECOGNIZED_KIND")
    if unknown_key_count > 0:
        defects.append("UNKNOWN_KEY_PRESENT")
    if not all(req_present.values()):
        defects.append("MISSING_REQUIRED_FIELD")

    if spec:
        # Check only applicable arities
        for fld, exp_len in spec["applicable_arities"].items():
            if fld in rel_obj:
                val = rel_obj[fld]
                if not isinstance(val, (list, tuple)):
                    defects.append("WRONG_JSON_TYPE")
                    ptr = f"/geometric_relations/{index}/{fld}"
                elif any(isinstance(x, (list, tuple, dict)) for x in val):
                    defects.append("NESTING_SHAPE_MISMATCH")
                    ptr = f"/geometric_relations/{index}/{fld}"
                elif len(val) != exp_len:
                    defects.append("WRONG_ARRAY_ARITY")
                    ptr = f"/geometric_relations/{index}/{fld}"

        # Check only non-empty forbidden fields
        for fld in spec.get("forbidden_non_empty", []):
            val = rel_obj.get(fld)
            # Tuple/list rỗng do default dump của Pydantic KHÔNG PHẢI lỗi sai tầng!
            if val is not None and val != () and val != [] and val != "":
                defects.append("KNOWN_FIELD_PLACED_AT_WRONG_LEVEL")
                ptr = f"/geometric_relations/{index}/{fld}"

    if not pt_refs_valid:
        defects.append("REFERENCE_RESOLUTION_FAILURE")

    if rel_obj.get("model_assumption") is True and sf_resolved:
        defects.append("MODEL_ASSUMPTION_POLICY_FAILURE")

    unique_defects = sorted(set(defects))

    # BẤT BIẾN CỐT LÕI: Quan hệ đã accepted TUYỆT ĐỐI KHÔNG mang nhãn defect
    if normalizer_accepted and pydantic_error_type is None and rule_id is None and not unknown_keys and pt_refs_valid:
        pattern_id = "CANONICAL_VALID"
        accepted = True
        ptr = f"/geometric_relations/{index}"
    elif len(unique_defects) > 1:
        pattern_id = "MULTIPLE_STRUCTURAL_DEFECTS"
        accepted = False
    elif len(unique_defects) == 1:
        pattern_id = unique_defects[0]
        accepted = False
    else:
        pattern_id = "CANONICAL_VALID" if normalizer_accepted else "UNCLASSIFIED_SAFE_STRUCTURE"
        accepted = normalizer_accepted

    trace = {
        "relation_index": index,
        "received_json_type": rec_type,
        "recognized_kind": rec_kind,
        "valid_keys_present": valid_keys,
        "required_fields_present": req_present,
        "field_json_types": {k: type(v).__name__ for k, v in rel_obj.items() if k in ALLOWLIST_KEYS},
        "array_lengths": {k: len(v) for k, v in rel_obj.items() if isinstance(v, (list, tuple)) and k in ALLOWLIST_KEYS},
        "element_type_sequences": {},
        "pydantic_error_type": pydantic_error_type,
        "rfc6901_pointer": ptr,
        "pointer_status": ptr_status,
        "candidate_pointer_count": 1,
        "rule_id": rule_id,
        "source_fact_resolved": sf_resolved,
        "point_reference_valid": pt_refs_valid,
        "unknown_key_count": unknown_key_count,
        "structural_pattern_id": pattern_id,
        "accepted": accepted,
    }

    # Redaction verification
    # Check forbidden keys in rel_obj
    for bad in ("AIzaSy", "GEMINI_API_KEY", "msg", "ctx", "traceback", "problem_text", "input_value", "raw_response"):
        if bad in rel_obj or bad in str(rel_obj.get("description", "")):
            raise ValueError(f"FORBIDDEN_RAW_LEAK in relation object: {bad}")

    van = json.dumps(trace, ensure_ascii=False)
    for bad in ("AIzaSy", "GEMINI_API_KEY", "msg", "ctx", "traceback", "problem_text", "input_value"):
        if bad in ("AIzaSy", "GEMINI_API_KEY"):
            if bad in van:
                raise ValueError(f"SECRET_LEAK: {bad}")
        elif f'"{bad}"' in van or f'"{bad}":' in van:
            raise ValueError(f"FORBIDDEN_RAW_LEAK: {bad}")

    return trace


# ══════════════════════════════════════════════════════════════════════════
# §3 · TÁCH BẠCH OUTCOME VÀ CAUSALITY
# ══════════════════════════════════════════════════════════════════════════
def separate_outcome_and_causality(
    p03_accepted: bool,
    p05_accepted: bool,
    p03_traces: list[dict[str, Any]],
    p05_traces: list[dict[str, Any]],
) -> dict[str, Any]:
    """Tách biệt trạng thái quan sát hiện tại khỏi nguyên nhân thất bại lịch sử:
    - Current output: CANONICAL_VALID, HIGH, NOT_REPRODUCED_VALID_EXACT.
    - Historical failure root cause: NOT_ESTABLISHED (không được dùng CANONICAL_VALID!).
    - Causality confidence: NOT_ESTABLISHED (không được nâng lên HIGH!).
    - Model variance: CONSISTENT_WITH_CURRENT_EVIDENCE (không được kết luận PROVEN).
    - Failure cluster homogeneity: NOT_APPLICABLE_NO_CURRENT_FAILURES.
    """
    if p03_accepted and p05_accepted:
        p03_out = "NOT_REPRODUCED_VALID_EXACT"
        p05_out = "NOT_REPRODUCED_VALID_EXACT"
        cluster_rep = "NOT_REPRODUCED"
        cur_status = "CANONICAL_VALID"
        cur_conf = "HIGH"
        concordance = "2/2 NOT_REPRODUCED"
        cluster_homog = "NOT_APPLICABLE_NO_CURRENT_FAILURES"
    elif p03_accepted != p05_accepted:
        p03_out = "NOT_REPRODUCED_VALID_EXACT" if p03_accepted else "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"
        p05_out = "NOT_REPRODUCED_VALID_EXACT" if p05_accepted else "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"
        cluster_rep = "PARTIAL_REPRODUCTION"
        cur_status = "PARTIAL_CANONICAL_VALID"
        cur_conf = "MEDIUM"
        concordance = "1/2 NOT_REPRODUCED"
        cluster_homog = "NOT_APPLICABLE"
    else:
        p03_out = "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"
        p05_out = "FAILURE_REPRODUCED_WITH_SAFE_DIAGNOSTIC"
        cluster_rep = "BOTH_REPRODUCED"
        cur_status = "MALFORMED_RELATION_REPRODUCED"
        cur_conf = "HIGH"
        concordance = "0/2 NOT_REPRODUCED"
        cluster_homog = "SAME_OR_DIFFERENT_STRUCTURE"

    return {
        "P03_CURRENT_OUTPUT_STATUS": cur_status if p03_accepted else "MALFORMED",
        "P05_CURRENT_OUTPUT_STATUS": cur_status if p05_accepted else "MALFORMED",
        "P03_LIVE_OUTCOME": p03_out,
        "P05_LIVE_OUTCOME": p05_out,
        "CURRENT_OUTCOME_CONCORDANCE": concordance,
        "CURRENT_OUTPUT_STATUS": cur_status,
        "CURRENT_OUTCOME_CONFIDENCE": cur_conf,
        "P03_HISTORICAL_ROOT_CAUSE": "NOT_ESTABLISHED",
        "P05_HISTORICAL_ROOT_CAUSE": "NOT_ESTABLISHED",
        "CLUSTER_HISTORICAL_ROOT_CAUSE": "NOT_ESTABLISHED",
        "CAUSALITY_CONFIDENCE": "NOT_ESTABLISHED",
        "MODEL_VARIANCE_HYPOTHESIS": "CONSISTENT_WITH_CURRENT_EVIDENCE",
        "FAILURE_CLUSTER_HOMOGENEITY": cluster_homog,
        "CLUSTER_REPRODUCTION_RESULT": cluster_rep,
        "NEXT_ACTION": "DOCS_INFORMATION_ARCHITECTURE_AND_HANDOFF_HARDENING",
    }
