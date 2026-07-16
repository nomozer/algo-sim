# -*- coding: utf-8 -*-
"""M12 — port Python của scan-interpreter (mirror core/scan.ts).

Backend KHÔNG chạy mô phỏng cho học sinh (engine frontend sở hữu timeline);
port này tồn tại để (a) validator server-side chặn spec sai TRƯỚC khi trả
envelope, (b) harness chấm HÀNH VI spec do LLM sinh (bài học M11: probe cấu
trúc không đủ). Phải giữ CÙNG LUẬT với core/scan.ts.
"""

from app.simulation.scan_engine import run_scan, validate_scan_spec
from app.simulation.semantic import check_semantic

FIND_FIRST_ABOVE = {
    "scan_version": "1.0",
    "array": [32, 31, 36, 30, 37],
    "seed": {"from": "constant", "value": 35, "varName": "nguong"},
    "compare": {"kind": "to_constant", "op": ">", "value": 35},
    "update": {"kind": "none"},
    "marking": "match_highlight",
    "stop": "first_match",
}

FIND_MAX = {
    "scan_version": "1.0",
    "array": [3, 7, 2, 9, 4],
    "seed": {"from": "first_element", "varName": "max", "trackIndexVar": "vt"},
    "compare": {"kind": "to_accumulator", "op": ">"},
    "update": {"kind": "replace_with_current"},
    "marking": "running_winner",
    "stop": "end_of_array",
}

COUNT_IF = {
    "scan_version": "1.0",
    "array": [5, 9, 6, 8, 4, 10, 7],
    "seed": {"from": "constant", "value": 0, "varName": "dem"},
    "compare": {"kind": "to_constant", "op": ">=", "value": 8},
    "update": {"kind": "increment"},
    "marking": "match_highlight",
    "stop": "end_of_array",
}


# ── validator (mirror validateScanSpec) ───────────────────────

def test_validate_spec_hop_le():
    spec, err = validate_scan_spec(FIND_FIRST_ABOVE)
    assert err is None
    assert spec["stop"] == "first_match"


def test_validate_reject_khoa_la_va_enum_la():
    assert validate_scan_spec({**FIND_FIRST_ABOVE, "secret": 1})[0] is None
    assert validate_scan_spec({**FIND_FIRST_ABOVE, "stop": "forever"})[0] is None
    assert validate_scan_spec({**FIND_FIRST_ABOVE, "scan_version": "2.0"})[0] is None
    assert validate_scan_spec({**FIND_FIRST_ABOVE, "array": []})[0] is None
    assert (
        validate_scan_spec({**FIND_FIRST_ABOVE, "compare": {"kind": "to_constant", "op": "≈", "value": 1}})[0]
        is None
    )


def test_validate_reject_combo_coherence():
    # running_winner đòi replace; to_accumulator đòi replace — mirror luật TS
    bad1 = {**FIND_MAX, "update": {"kind": "increment"}}
    assert validate_scan_spec(bad1)[0] is None
    bad2 = {**FIND_MAX, "update": {"kind": "none"}}
    assert validate_scan_spec(bad2)[0] is None


# ── interpreter (hành vi khớp ngữ nghĩa đã chứng minh phía TS) ─

def test_run_scan_first_match_dung_som():
    out = run_scan(FIND_FIRST_ABOVE)
    assert out["found_index"] == 2  # 36 tại index 2 (0-based)
    assert out["final_marks"].get(2) == "found"
    assert 3 not in out["final_marks"]  # 30, 37 chưa bị xét
    assert out["decisions"] == ["no_match", "no_match", "match"]


def test_run_scan_find_max():
    out = run_scan(FIND_MAX)
    assert out["final_vars"]["max"] == 9
    assert out["final_vars"]["vt"] == 3
    assert out["final_marks"] == {3: "found"}


def test_run_scan_count_if():
    out = run_scan(COUNT_IF)
    assert out["final_vars"]["dem"] == 3  # 9, 8, 10
    assert out["found_index"] is None


def test_run_scan_tat_dinh():
    assert run_scan(FIND_MAX) == run_scan(FIND_MAX)


# ── semantic kind bounded_scan (harness chấm hành vi) ─────────

def test_semantic_bounded_scan_dung():
    ok, detail = check_semantic(
        FIND_FIRST_ABOVE, {"kind": "bounded_scan", "stop": "first_match", "found_pos": 3}
    )
    assert ok, detail


def test_semantic_bounded_scan_sai_vi_tri_thi_fail():
    ok, _ = check_semantic(
        FIND_FIRST_ABOVE, {"kind": "bounded_scan", "stop": "first_match", "found_pos": 5}
    )
    assert not ok


def test_semantic_bounded_scan_final_value():
    ok, detail = check_semantic(COUNT_IF, {"kind": "bounded_scan", "final_value": 3})
    assert ok, detail
    ok2, _ = check_semantic(COUNT_IF, {"kind": "bounded_scan", "final_value": 99})
    assert not ok2
