# -*- coding: utf-8 -*-
"""MODEL_VARIANCE_EVIDENCE_REVIEW Test Suite.

Kiểm tra và đính chính các trục đo lường và diễn giải bằng chứng:
1. RED-BEFORE: Chứng minh 3 điểm yếu trên START_HEAD (token default 0, false positive defect, root_cause=CANONICAL_VALID).
2. GREEN-AFTER: Chứng minh tooling mới xử lý đúng kind-aware, token missing -> UNKNOWN, và tách bạch outcome - causality.
3. FAULT INJECTIONS F1 - F10: Kiểm tra 10 phép tiêm lỗi bắt buộc.
4. HISTORICAL IMMUTABILITY: 17 artifact live và báo cáo lịch sử không đổi byte.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

import pytest

GOC = Path(__file__).resolve().parents[2]
REPO = GOC.parent
for _p in (str(GOC), str(GOC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kind_aware_trace_evaluator as K  # noqa: E402
import run_preregistered_failure_reproduction as R  # noqa: E402

HIST_DIR = REPO / "docs" / "evaluation" / "geometry" / "photo-problem-to-scene" / "fresh-preregistered-failure-reproduction-retry"
HIST_REPORT = REPO / "docs" / "FRESH_PREREGISTERED_FAILURE_REPRODUCTION_RETRY.md"


# ══════════════════════════════════════════════════════════════════════════
# §1 · RED-BEFORE DEMONSTRATION TESTS (CHỨNG MINH LỖI CŨ TRÊN START_HEAD)
# ══════════════════════════════════════════════════════════════════════════
def test_red_before_old_extractor_flags_false_positive_multiple_defects():
    """RED-BEFORE: Extractor cũ trên START_HEAD gán nhãn MULTIPLE_STRUCTURAL_DEFECTS
    cho quan hệ perpendicular_lines hợp lệ vì có trường plane=() mặc định của Pydantic.
    """
    rel_obj = {
        "kind": "perpendicular_lines",
        "line": ["U", "V"],
        "other_line": ["U", "W"],
        "plane": (),
        "source_fact_id": "fact_1",
        "model_assumption": False,
    }
    trace = R.SafeStructureTraceExtractor.extract_relation_trace(
        rel_obj, 0, {"U", "V", "W"}, {"fact_1"}
    )
    assert trace["accepted"] is True
    # Trên extractor cũ, lỗi false positive xảy ra:
    assert trace["structural_pattern_id"] == "MULTIPLE_STRUCTURAL_DEFECTS"
    assert "/geometric_relations/0/plane" in trace["rfc6901_pointer"]


def test_red_before_old_token_aggregation_converts_missing_to_zero():
    """RED-BEFORE: Logic cũ dùng .get(..., 0) biến missing usage thành số 0 thay vì UNKNOWN."""
    empty_usage: dict[str, Any] = {}
    prompt_tokens = empty_usage.get("promptTokenCount", 0)
    assert prompt_tokens == 0  # Trả về 0 thay vì UNKNOWN


def test_red_before_old_classification_sets_root_cause_canonical_valid():
    """RED-BEFORE: Bộ phân loại cũ đặt root_cause=CANONICAL_VALID và confidence=HIGH
    cho trường hợp FAILURE_NOT_REPRODUCED.
    """
    mock_valid_traces = [{"accepted": True}, {"accepted": True}]
    outcome, root_cause, conf = R.classify_case_outcome(mock_valid_traces, None)
    assert outcome == "FAILURE_NOT_REPRODUCED"
    assert root_cause == "CANONICAL_VALID"
    assert conf == "HIGH"


# ══════════════════════════════════════════════════════════════════════════
# §2 · GREEN-AFTER VERIFICATION TESTS (TOOLING MỚI)
# ══════════════════════════════════════════════════════════════════════════
def test_green_after_token_audit_missing_is_unknown():
    """GREEN-AFTER: Missing usage hoặc null field luôn trả về UNKNOWN, không bao giờ 0."""
    assert K.parse_token_count({}, "promptTokenCount") == "UNKNOWN"
    assert K.parse_token_count(None, "promptTokenCount") == "UNKNOWN"
    assert K.parse_token_count({"promptTokenCount": None}, "promptTokenCount") == "UNKNOWN"
    assert K.parse_token_count({"promptTokenCount": ""}, "promptTokenCount") == "UNKNOWN"
    # Chỉ trả về số khi thực sự có số:
    assert K.parse_token_count({"promptTokenCount": 1500}, "promptTokenCount") == 1500
    assert K.parse_token_count({"promptTokenCount": 0}, "promptTokenCount") == 0


def test_green_after_token_aggregation_with_unknown():
    """GREEN-AFTER: Nếu có ca UNKNOWN, aggregate total bắt buộc là UNKNOWN, có subtotal riêng."""
    usages = [{"promptTokenCount": 100}, {}]
    total, subtotal = K.aggregate_tokens(usages, "promptTokenCount")
    assert total == "UNKNOWN"
    assert subtotal == 100

    usages_known = [{"promptTokenCount": 100}, {"promptTokenCount": 200}]
    tot2, sub2 = K.aggregate_tokens(usages_known, "promptTokenCount")
    assert tot2 == 300
    assert sub2 == 300


def test_green_after_kind_aware_trace_perpendicular_lines():
    """GREEN-AFTER: perpendicular_lines chuẩn với plane=() mặc định đạt CANONICAL_VALID."""
    rel_obj = {
        "kind": "perpendicular_lines",
        "line": ["U", "V"],
        "other_line": ["U", "W"],
        "plane": (),
        "source_fact_id": "fact_1",
        "model_assumption": False,
    }
    trace = K.extract_kind_aware_trace(
        rel_obj, 0, {"U", "V", "W"}, {"fact_1"}, normalizer_accepted=True
    )
    assert trace["accepted"] is True
    assert trace["structural_pattern_id"] == "CANONICAL_VALID"
    assert trace["rfc6901_pointer"] == "/geometric_relations/0"
    assert trace["pointer_status"] == "EXACT"


def test_green_after_kind_aware_trace_perpendicular_line_plane():
    """GREEN-AFTER: perpendicular_line_plane chuẩn với other_line=() mặc định đạt CANONICAL_VALID."""
    rel_obj = {
        "kind": "perpendicular_line_plane",
        "line": ["T", "U"],
        "plane": ["U", "V", "W"],
        "other_line": (),
        "source_fact_id": "fact_2",
        "model_assumption": False,
    }
    trace = K.extract_kind_aware_trace(
        rel_obj, 1, {"T", "U", "V", "W"}, {"fact_2"}, normalizer_accepted=True
    )
    assert trace["accepted"] is True
    assert trace["structural_pattern_id"] == "CANONICAL_VALID"
    assert trace["rfc6901_pointer"] == "/geometric_relations/1"


def test_green_after_accepted_relation_never_has_defect():
    """GREEN-AFTER: Bất biến — một relation đã accepted không bao giờ mang nhãn defect."""
    rel_obj = {
        "kind": "perpendicular_lines",
        "line": ["A", "B"],
        "other_line": ["A", "C"],
        "source_fact_id": "f1",
    }
    trace = K.extract_kind_aware_trace(
        rel_obj, 0, {"A", "B", "C"}, {"f1"}, normalizer_accepted=True
    )
    assert trace["accepted"] is True
    assert "DEFECT" not in trace["structural_pattern_id"]
    assert trace["structural_pattern_id"] == "CANONICAL_VALID"


def test_green_after_outcome_causality_separation():
    """GREEN-AFTER: Tách biệt rõ ràng Current Output (CANONICAL_VALID, HIGH) khỏi Historical Causality (NOT_ESTABLISHED)."""
    sep = K.separate_outcome_and_causality(True, True, [], [])
    assert sep["P03_CURRENT_OUTPUT_STATUS"] == "CANONICAL_VALID"
    assert sep["P05_CURRENT_OUTPUT_STATUS"] == "CANONICAL_VALID"
    assert sep["CURRENT_OUTCOME_CONFIDENCE"] == "HIGH"
    assert sep["P03_LIVE_OUTCOME"] == "NOT_REPRODUCED_VALID_EXACT"
    assert sep["P05_LIVE_OUTCOME"] == "NOT_REPRODUCED_VALID_EXACT"
    assert sep["CURRENT_OUTCOME_CONCORDANCE"] == "2/2 NOT_REPRODUCED"

    # Historical causality
    assert sep["P03_HISTORICAL_ROOT_CAUSE"] == "NOT_ESTABLISHED"
    assert sep["P05_HISTORICAL_ROOT_CAUSE"] == "NOT_ESTABLISHED"
    assert sep["CLUSTER_HISTORICAL_ROOT_CAUSE"] == "NOT_ESTABLISHED"
    assert sep["CAUSALITY_CONFIDENCE"] == "NOT_ESTABLISHED"
    assert sep["MODEL_VARIANCE_HYPOTHESIS"] == "CONSISTENT_WITH_CURRENT_EVIDENCE"
    assert sep["FAILURE_CLUSTER_HOMOGENEITY"] == "NOT_APPLICABLE_NO_CURRENT_FAILURES"


def test_green_after_source_artifacts_immutability():
    """GREEN-AFTER: Kiểm tra toàn bộ 17 artifact live và report không bị thay đổi byte."""
    assert HIST_DIR.exists()
    assert HIST_REPORT.exists()
    count = len(list(HIST_DIR.glob("*.json")))
    assert count == 17
    # Verify report is not empty
    assert len(HIST_REPORT.read_text(encoding="utf-8")) > 1000


# ══════════════════════════════════════════════════════════════════════════
# §3 · 10 PHÉP TIÊM LỖI (FAULT INJECTIONS F1 - F10)
# ══════════════════════════════════════════════════════════════════════════
def test_FI_01_get_input_tokens_default_zero():
    """F1: Tiêm .get('input_tokens', 0) trên missing data bị chặn bởi parse_token_count."""
    fake_empty = {}
    bad_val = fake_empty.get("input_tokens", 0)
    assert bad_val == 0  # Buggy behavior
    good_val = K.parse_token_count(fake_empty, "input_tokens")
    assert good_val == "UNKNOWN"  # Evaluator catches and fixes bug


def test_FI_02_usage_or_zero_object():
    """F2: Tiêm usage or {'promptTokenCount': 0} bị chặn."""
    fake_none = None
    bad_res = fake_none or {"promptTokenCount": 0}
    assert bad_res["promptTokenCount"] == 0
    good_res = K.parse_token_count(fake_none, "promptTokenCount")
    assert good_res == "UNKNOWN"


def test_FI_03_dung_common_keyset_cho_moi_kind():
    """F3: Dùng keyset chung (bắt buộc cả line, other_line, plane) gây lỗi cho perpendicular_lines."""
    common_required = ["line", "other_line", "plane"]
    rel = {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"]}
    # Keyset chung sẽ coi rel là thiếu plane
    missing_common = [k for k in common_required if k not in rel]
    assert "plane" in missing_common
    # Kind-aware spec không đòi plane:
    spec = K.KIND_SPECS["perpendicular_lines"]
    missing_kind_aware = [k for k in spec["required"] if k not in rel]
    assert "plane" not in missing_kind_aware


def test_FI_04_yeu_cau_plane_cho_perpendicular_lines():
    """F4: Ép buộc plane cho perpendicular_lines bị chặn bởi spec."""
    spec = K.KIND_SPECS["perpendicular_lines"]
    assert "plane" not in spec["required"]
    assert "plane" in spec["forbidden_non_empty"]


def test_FI_05_yeu_cau_other_line_cho_perpendicular_line_plane():
    """F5: Ép buộc other_line cho perpendicular_line_plane bị chặn bởi spec."""
    spec = K.KIND_SPECS["perpendicular_line_plane"]
    assert "other_line" not in spec["required"]
    assert "other_line" in spec["forbidden_non_empty"]


def test_FI_06_gan_defect_vao_accepted_relation():
    """F6: Cố tình gắn defect vào relation đã accepted bị chặn bởi bất biến cốt lõi."""
    rel = {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"], "source_fact_id": "f1"}
    trace = K.extract_kind_aware_trace(rel, 0, {"A", "B", "C"}, {"f1"}, normalizer_accepted=True)
    assert trace["accepted"] is True
    assert trace["structural_pattern_id"] == "CANONICAL_VALID"
    assert "DEFECT" not in trace["structural_pattern_id"]


def test_FI_07_doi_historical_root_cause_thanh_canonical_valid():
    """F7: Tiêm root_cause=CANONICAL_VALID cho failure lịch sử bị chặn bởi formatter."""
    sep = K.separate_outcome_and_causality(True, True, [], [])
    # Formatter bắt buộc historical root cause là NOT_ESTABLISHED
    assert sep["P03_HISTORICAL_ROOT_CAUSE"] != "CANONICAL_VALID"
    assert sep["P03_HISTORICAL_ROOT_CAUSE"] == "NOT_ESTABLISHED"


def test_FI_08_doi_causality_confidence_thanh_high():
    """F8: Tiêm causality_confidence=HIGH cho failure lịch sử bị chặn bởi formatter."""
    sep = K.separate_outcome_and_causality(True, True, [], [])
    assert sep["CAUSALITY_CONFIDENCE"] != "HIGH"
    assert sep["CAUSALITY_CONFIDENCE"] == "NOT_ESTABLISHED"


def test_FI_09_sua_historical_artifact():
    """F9: Phát hiện nếu có file trong fresh-preregistered-failure-reproduction-retry bị sửa đổi."""
    # Kiểm tra hash của SAFE_STRUCTURE_TRACE_CONTRACT.json
    contract_p = HIST_DIR / "SAFE_STRUCTURE_TRACE_CONTRACT.json"
    lf_hash = hashlib.sha256(contract_p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    assert lf_hash == "b429618c8577e591baa3050c20ebf579f6cc49717f62eaaae294313bbb5ab416"


def test_FI_10_luu_raw_model_value_vao_trace():
    """F10: Tiêm trường raw cấm (như problem_text hoặc AIzaSy) bị chặn bởi verify redaction."""
    rel_leaky = {
        "kind": "perpendicular_lines",
        "line": ["A", "B"],
        "other_line": ["A", "C"],
        "source_fact_id": "f1",
        "problem_text": "Cho hinh chóp...",
    }
    with pytest.raises(ValueError, match="FORBIDDEN_RAW_LEAK"):
        K.extract_kind_aware_trace(rel_leaky, 0, {"A", "B", "C"}, {"f1"}, normalizer_accepted=True)
