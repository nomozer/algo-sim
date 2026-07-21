# -*- coding: utf-8 -*-
"""M17-RC1 §C — lock ma trận archetype.

Kiểm cái mà artifact KHÔNG tự chứng minh được: vốn từ đóng, mẫu số coverage
không nuốt NOT_APPLICABLE, NOT_APPLICABLE phải có lý do DẪN XUẤT, và mọi
target/slot đều được phân giải (thêm target thứ 20 không lặng lẽ biến mất).

Không chạy lại 77 case ở đây (script artifact làm việc đó) — test này soi
LUẬT phân giải trên bản ghi giả lập, nên nhanh và không phụ thuộc fixture.
"""

from __future__ import annotations

from app.evaluation.rc1c_matrix import (
    COVERAGE_GAP,
    COVERED_FAIL,
    COVERED_PASS,
    GAP_KINDS,
    NOT_APPLICABLE,
    SLOTS,
    SlotCaseRecord,
    ai_reachable_ids,
    analyze_expressible_families,
    build_target_records,
    coverage_gaps,
    coverage_metrics,
    leaked_result_fields,
    required_grounded_inputs,
)
from app.simulation.descriptor import FamilyId


def _rec(**kw) -> SlotCaseRecord:
    base = dict(
        case_id="c", slot="supported_canonical", target_id=None, family_id=None,
        expected_status="ok", expected_route=None, expected_error_code=None,
        actual_status="ok", route=None, variant=None, executor=None,
        simulation_created=True, generic_leak=False, false_positive_simulation=False,
        false_refusal=False, dropped_requirements=[], failure_category=None,
        error_code=None, leaked_result_fields=[], matched=True,
    )
    base.update(kw)
    return SlotCaseRecord(**base)


def test_von_tu_dong():
    assert len(SLOTS) == 8 and len(set(SLOTS)) == 8
    assert len(GAP_KINDS) == 8


def test_moi_target_duoc_phan_giai_du_8_slot():
    targets = build_target_records([])
    assert [t["target_id"] for t in targets] == ai_reachable_ids()
    for t in targets:
        assert set(t["archetype_slots"]) == set(SLOTS), t["target_id"]
        for slot, s in t["archetype_slots"].items():
            assert s["status"] in (COVERED_PASS, COVERED_FAIL, COVERAGE_GAP, NOT_APPLICABLE)
            if s["status"] == COVERAGE_GAP:
                assert s["gap_kind"] in GAP_KINDS, (t["target_id"], slot)
                assert s["reason"], f"{t['target_id']}/{slot}: gap thiếu lý do"


def test_khong_co_bang_chung_thi_la_GAP_chu_khong_phai_PASS():
    """Bản ghi rỗng ⟹ không slot nào được PASS. Đây là luật chống 'tự nhận
    coverage': PASS phải có case chạy thật đứng sau."""
    targets = build_target_records([])
    statuses = {s["status"] for t in targets for s in t["archetype_slots"].values()}
    assert COVERED_PASS not in statuses


def test_NOT_APPLICABLE_luon_kem_ly_do_dan_xuat():
    """NOT_APPLICABLE chỉ hợp lệ khi HỢP ĐỒNG chứng minh — không được dùng để
    che fixture thiếu. Kiểm: mọi N/A phải nêu căn cứ (required rỗng, hoặc
    family chỉ có ≤1 cơ chế)."""
    for t in build_target_records([]):
        for slot, s in t["archetype_slots"].items():
            if s["status"] != NOT_APPLICABLE:
                continue
            assert s["gap_kind"] is None, "N/A không phải gap"
            assert ("config_schema.required rỗng" in s["reason"]
                    or "cơ chế và cardinality=single" in s["reason"]), (
                f"{t['target_id']}/{slot}: N/A không có căn cứ dẫn xuất")


def test_mau_so_coverage_khong_chua_NOT_APPLICABLE():
    targets = build_target_records([])
    m = coverage_metrics(targets, [])
    assert m["coverage_denominator"] == m["covered_pass"] + m["covered_fail"] + m["coverage_gap"]
    assert m["total_archetype_slots"] == m["coverage_denominator"] + m["not_applicable"]
    assert m["not_applicable"] > 0  # có thật, và vẫn không lọt mẫu số


def test_required_grounded_inputs_dan_xuat_tu_config_schema():
    assert required_grounded_inputs("tree.traversal") == [
        "nodes", "rootId", "specVersion", "variant"]
    # encapsulation KHÔNG cần dữ kiện nào từ đề → slot insufficient là N/A
    assert required_grounded_inputs("network.protocol_encapsulation") == []


def test_ro_ri_ket_qua_bat_duoc_khi_config_chua_dap_an():
    """Oracle rò rỉ: config KHÔNG được mang sẵn field kết quả. Fault-injection
    để chứng minh oracle biết kêu (không phải luôn xanh)."""
    assert leaked_result_fields("tree.traversal", {"variant": "preorder", "nodes": []}) == []
    assert leaked_result_fields(
        "tree.traversal", {"variant": "preorder", "visitedOrder": ["A", "B"]}
    ) == ["visitedOrder"]
    # None = schema nullable bỏ trống, KHÔNG tính là rò
    assert leaked_result_fields("tree.traversal", {"visitedOrder": None}) == []


def test_case_that_bai_keo_slot_ve_COVERED_FAIL():
    """Fault-injection: một case lệch kỳ vọng phải làm slot đỏ, không được
    lặng lẽ vẫn PASS."""
    bad = _rec(case_id="x", target_id="tree.traversal", family_id="tree_traversal",
               slot="supported_canonical", matched=False, actual_status="unsupported")
    t = next(t for t in build_target_records([bad]) if t["target_id"] == "tree.traversal")
    assert t["archetype_slots"]["supported_canonical"]["status"] == COVERED_FAIL
    assert t["engine_authenticity"] == "BROKEN"


def test_generic_khong_bao_gio_duoc_nang_len_REAL():
    """generic.rule_scene mang dual authority → PARTIAL. Nâng lên REAL là
    overclaim (đề thuật toán sẽ được coi như có engine sở hữu kết quả)."""
    ok = _rec(target_id="generic.rule_scene", family_id="boolean_composition")
    t = next(t for t in build_target_records([ok]) if t["target_id"] == "generic.rule_scene")
    assert t["engine_authenticity"] == "PARTIAL"


def test_family_khong_bieu_dat_duoc_thi_semantic_completeness_la_GAP():
    """Ranh giới thật: analyze chỉ phơi cơ chế của 3 family. Family ngoài đó
    KHÔNG được tính COVERED chỉ vì probe cấp-gate xanh — gate không bao giờ
    nhận được dữ liệu ở đời thực."""
    expressible = analyze_expressible_families()
    assert expressible == {
        FamilyId.COMPARISON_SORT.value,
        FamilyId.POSITIONAL_REPRESENTATION.value,
        FamilyId.TREE_TRAVERSAL.value,
    }
    t = next(t for t in build_target_records([])
             if t["target_id"] == "network.graph_traversal")
    slot = t["archetype_slots"]["semantic_completeness"]
    assert slot["status"] == COVERAGE_GAP
    assert slot["gap_kind"] == "missing_audit_metadata"


def test_gap_luon_xuat_hien_trong_coverage_gaps():
    targets = build_target_records([])
    gaps = coverage_gaps(targets)
    n = sum(1 for t in targets for s in t["archetype_slots"].values()
            if s["status"] == COVERAGE_GAP)
    assert len(gaps) == n
    assert all(g["gap_kind"] in GAP_KINDS for g in gaps)
