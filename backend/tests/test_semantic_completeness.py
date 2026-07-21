# -*- coding: utf-8 -*-
"""M17-RC1 §D — lock SEMANTIC COMPLETENESS GATE.

Bất biến: **status=ok ⟹ dropped_requirements rỗng.** Đề hỏi nhiều thao tác mà
family chỉ dựng được một → từ chối trung thực, KHÔNG âm thầm chọn một cái.

Phủ đủ 6 ca §D: 4 kiểu duyệt cây · BFS+DFS · 2 thuật toán sắp xếp · encode+
decode (mức contract) · single-operation KHÔNG bị chặn oan · pipeline hợp lệ
KHÔNG bị hiểu nhầm là xung đột.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from app.ai import pipeline
from app.simulation.completeness_gate import (
    check_represented_coverage,
    check_requested_combination,
    completeness_report,
    normalized_requested,
    represented_mechanisms,
)
from app.simulation.descriptor import FamilyId
from app.simulation.error_codes import ErrorCode
from app.simulation.operation_policy import (
    FAMILY_OPERATION_POLICY,
    MULTIPLE,
    PIPELINE,
    SINGLE,
    policy_for_family,
)

TREE = FamilyId.TREE_TRAVERSAL.value
GRAPH = FamilyId.GRAPH_TRAVERSAL.value
SORT = FamilyId.COMPARISON_SORT.value
PDU = FamilyId.LAYERED_PDU_TRANSFORM.value
BOOL = FamilyId.BOOLEAN_COMPOSITION.value

FOUR_TRAVERSALS = [
    "tree_traversal.preorder", "tree_traversal.inorder",
    "tree_traversal.postorder", "tree_traversal.level_order",
]


def _an(requested=None, prescribed=None, **extra):
    a = {
        "objects": ["A", "B"], "data": [], "relations": ["B là con trái của A"],
        "processes": [], "constraints": [], "goal": "Duyệt cây",
        "input_description": "cây", "output_description": "thứ tự",
        "result_ownership": "provided",
    }
    if requested is not None:
        a["requested_mechanisms"] = requested
    if prescribed is not None:
        a["prescribed_procedure"] = prescribed
    a.update(extra)
    return a


# ── chuẩn hoá yêu cầu ──
def test_chuan_hoa_gop_prescribed_va_bo_trung():
    a = _an(requested=["tree_traversal.preorder", "tree_traversal.preorder"],
            prescribed="tree_traversal.inorder")
    assert normalized_requested(a) == ["tree_traversal.inorder", "tree_traversal.preorder"]


def test_chuan_hoa_alias_legacy_sorting():
    """Giá trị legacy bare của sorting phải quy về canonical (một boundary)."""
    a = _an(requested=["adjacent_compare_swap", "shift_into_sorted_prefix"])
    assert normalized_requested(a) == [
        "comparison_sort.adjacent_compare_swap",
        "comparison_sort.shift_into_sorted_prefix",
    ]


# ── CA A: 4 kiểu duyệt cây → chặn (PHA 1) ──
def test_ca_A_bon_kieu_duyet_cay_bi_chan():
    v = check_requested_combination(_an(requested=FOUR_TRAVERSALS), {TREE})
    assert v is not None
    code, msg, ev = v
    assert code is ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED
    assert ev["operation_cardinality"] == SINGLE
    assert sorted(ev["requested_in_family"]) == sorted(FOUR_TRAVERSALS)
    assert ev["unsupported_combinations"]
    assert "tách" in msg  # thông điệp CHỈ ĐƯỜNG cho học sinh


# ── CA C: hai thuật toán sắp xếp → chặn ──
def test_ca_C_hai_thuat_toan_sort_bi_chan():
    a = _an(requested=["comparison_sort.adjacent_compare_swap",
                       "comparison_sort.shift_into_sorted_prefix"])
    v = check_requested_combination(a, {SORT})
    assert v is not None and v[0] is ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED


# ── CA D: BFS + DFS → chặn ──
def test_ca_D_bfs_va_dfs_bi_chan():
    a = _an(requested=["graph_traversal.breadth_first", "graph_traversal.depth_first"])
    v = check_requested_combination(a, {GRAPH})
    assert v is not None and v[0] is ErrorCode.MULTIPLE_OPERATIONS_NOT_SUPPORTED


# ── CA "không chặn oan": một thao tác ──
@pytest.mark.parametrize("mech,fams", [
    ("tree_traversal.preorder", {TREE}),
    ("graph_traversal.depth_first", {GRAPH}),
    ("comparison_sort.adjacent_compare_swap", {SORT}),
])
def test_single_operation_khong_bi_chan_oan(mech, fams):
    assert check_requested_combination(_an(requested=[mech]), fams) is None
    assert check_requested_combination(_an(), fams) is None  # không nêu gì → bỏ qua


# ── CA B/E: family pipeline / multiple KHÔNG bị coi là xung đột ──
def test_pipeline_nhieu_thao_tac_van_hop_le():
    assert policy_for_family(PDU).cardinality == PIPELINE
    a = _an(requested=["layered_pdu_transform.encapsulate_decapsulate_4layer"])
    assert check_requested_combination(a, {PDU}) is None


def test_family_multiple_nhieu_co_che_van_hop_le():
    assert policy_for_family(BOOL).cardinality == MULTIPLE
    a = _an(requested=["boolean_composition.single_gate_truth_table",
                       "boolean_composition.bounded_gate_dag"])
    assert check_requested_combination(a, {BOOL}) is None


# ── PHA 2: spec dựng ra bỏ sót yêu cầu ──
def test_pha2_spec_mot_variant_bo_sot_ba_yeu_cau():
    a = _an(requested=FOUR_TRAVERSALS)
    cfg = {"specVersion": "tree-1.0", "variant": "preorder", "rootId": "A", "nodes": []}
    v = check_represented_coverage(a, {TREE}, set(FOUR_TRAVERSALS), cfg)
    assert v is not None and v[0] is ErrorCode.SEMANTIC_INCOMPLETE
    assert sorted(v[2]["dropped_requirements"]) == sorted(FOUR_TRAVERSALS[1:])


def test_pha2_spec_dung_variant_thi_qua():
    a = _an(requested=["tree_traversal.inorder"])
    cfg = {"variant": "inorder"}
    assert check_represented_coverage(a, {TREE}, set(FOUR_TRAVERSALS), cfg) is None


def test_represented_suy_tu_variant_la_du_lieu_khong_doan_chu():
    assert represented_mechanisms({}, {GRAPH}, set(), {"variant": "dfs"}) == [
        "graph_traversal.depth_first"]
    assert represented_mechanisms({}, {SORT}, set(), {"variant": "selection"}) == [
        "comparison_sort.select_extreme_repeated"]


# ── chính sách khai đủ cho MỌI family (thêm family mới không lọt) ──
def test_moi_family_deu_co_chinh_sach():
    for fid in FamilyId:
        assert fid in FAMILY_OPERATION_POLICY, f"{fid.value} thiếu operation policy"


def test_bao_cao_du_truong_bat_buoc():
    rep = completeness_report(_an(requested=FOUR_TRAVERSALS), {TREE},
                             set(FOUR_TRAVERSALS), {"variant": "preorder"}, "BLOCKED")
    for field in ("requested_requirements", "normalized_requested_requirements",
                  "represented_requirements", "dropped_requirements",
                  "unsupported_combinations", "operation_cardinality",
                  "completeness_decision"):
        assert field in rep, field
    assert len(rep["dropped_requirements"]) == 3


# ── end-to-end qua production run_pipeline (scripted, 0 network) ──
def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


def _classify(sim_id, status="ok"):
    return json.dumps({"status": status, "simulation_id": sim_id, "reason": None})


def _tree_cfg(variant="preorder"):
    return json.dumps({
        "specVersion": "tree-1.0", "variant": variant, "rootId": "A",
        "nodes": [{"id": "A", "label": "A", "left": "B", "right": None},
                  {"id": "B", "label": "B", "left": None, "right": None}],
    })


def test_e2e_de_hoi_bon_kieu_duyet_khong_tao_simulation(monkeypatch):
    """Đúng ca đề đời thực: hỏi cả 4 quy trình → KHÔNG ok, KHÔNG generic,
    KHÔNG chạy simulate (chặn ở PHA 1 nên chỉ tốn analyze+classify)."""
    calls = [json.dumps(_an(requested=FOUR_TRAVERSALS)), _classify("tree.traversal")]
    monkeypatch.setattr(pipeline, "call_gemini", _fake(calls))
    env = asyncio.run(pipeline.run_pipeline("đề bốn quy trình", "k"))
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "semantic_incomplete"
    assert env["error_code"] == "multiple_operations_not_supported"
    assert env.get("simulation_id") is None          # không simulation
    assert env.get("config") is None                  # không spec
    assert len(env["completeness"]["requested_in_family"]) == 4
    assert calls == []                                # KHÔNG gọi simulate


def test_e2e_de_hoi_mot_kieu_duyet_van_chay_binh_thuong(monkeypatch):
    """Chống chặn oan: một thao tác → vẫn ok như trước."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_an(requested=["tree_traversal.inorder"])),
        _classify("tree.traversal"), _tree_cfg("inorder"),
    ]))
    env = asyncio.run(pipeline.run_pipeline("đề duyệt giữa", "k"))
    assert env["status"] == "ok" and env["simulation_id"] == "tree.traversal"


def test_e2e_status_ok_luon_co_dropped_rong(monkeypatch):
    """Bất biến trung tâm §D, kiểm trên envelope THẬT."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_an(requested=["tree_traversal.preorder"])),
        _classify("tree.traversal"), _tree_cfg("preorder"),
    ]))
    env = asyncio.run(pipeline.run_pipeline("đề duyệt trước", "k"))
    assert env["status"] == "ok"
    rep = completeness_report(env["analysis"], {TREE},
                              {"tree_traversal.preorder"}, env["config"], "PASS")
    assert rep["dropped_requirements"] == []


def _sort_spec(variant, array):
    return json.dumps({"family_version": "sort-fam-1", "variant": variant,
                       "array": list(array), "order": "asc"})


def test_nhanh_SELECTOR_cung_qua_gate_completeness(monkeypatch):
    """LỖ THẬT do RC1-C phát hiện: family comparison_sort route qua SELECTOR
    TOKEN và nhánh đó `return` TRƯỚC chỗ gate §D được cắm → đề "nổi bọt RỒI
    chèn" trả ok và bỏ im lặng một nửa. Đúng family có tín hiệu analyze giàu
    nhất lại là family lọt cổng. Test này khoá cả hai pha trên nhánh selector."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_an(requested=["adjacent_compare_swap", "shift_into_sorted_prefix"])),
        _classify("algorithm.comparison_sort"),
    ]))
    env = asyncio.run(pipeline.run_pipeline("sắp xếp bằng nổi bọt rồi bằng chèn", "k"))
    assert env["status"] == "unsupported"
    assert env["error_code"] == "multiple_operations_not_supported"
    assert env.get("simulation_id") is None
    assert len(env["completeness"]["requested_in_family"]) == 2


def test_nhanh_selector_mot_thuat_toan_khong_bi_chan_oan(monkeypatch):
    """Chống chặn oan trên chính nhánh vừa siết: một thuật toán → vẫn ok và
    envelope mang id CONCRETE (token không bao giờ leak)."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_an(requested=["adjacent_compare_swap"])),
        _classify("algorithm.comparison_sort"),
        _sort_spec("bubble", [5, 2, 9, 1]),
    ]))
    env = asyncio.run(pipeline.run_pipeline("sắp xếp dãy bằng nổi bọt", "k"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.bubble_sort"


def test_probe_artifact_khop_hanh_vi_gate_that():
    """Artifact §D không được TỰ NHẬN PASS: chạy lại đúng bộ probe sinh từ
    registry và bắt buộc 0 lệch / 0 chặn oan / 0 'ok mà còn sót'. Thêm family
    hay cơ chế mới → probe tự xuất hiện, đỏ ở đây nếu chính sách thiếu."""
    from semantic_completeness_report import BLOCKED, PASS, build_probes

    probes = build_probes()
    assert len(probes) >= len(FAMILY_OPERATION_POLICY), "thiếu probe cho family nào đó"
    assert [p["probe_id"] for p in probes if not p["match"]] == []
    assert [p["probe_id"] for p in probes
            if p["expected_decision"] == PASS and p["actual_decision"] == BLOCKED] == []
    assert [p["probe_id"] for p in probes
            if p["actual_decision"] == PASS and p["dropped_requirements"]] == []


def test_gate_moi_khong_lam_troi_artifact_M16_frozen():
    """M16 là ẢNH CHỤP LỊCH SỬ: record chỉ ghi cổng tồn tại thời M16. Gate thêm
    sau (structure/completeness) vẫn CHẠY và vẫn được audit M17 ghi, nhưng
    KHÔNG được lọt vào record M16 — nếu lọt, artifact frozen trôi dù không case
    nào đổi kết quả (đã suýt xảy ra ở RC1-D)."""
    from app.evaluation.m16_schema import M16_GATE_NAMES

    assert M16_GATE_NAMES == {"computation", "mechanism", "route_mechanism"}
    for new_gate in ("structure", "completeness_requested", "completeness_represented"):
        assert new_gate not in M16_GATE_NAMES


def test_e2e_spec_lech_variant_bi_pha2_chan(monkeypatch):
    """Đề hỏi inorder nhưng spec dựng preorder → PHA 2 chặn (không ok nửa vời)."""
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(_an(requested=["tree_traversal.inorder"])),
        _classify("tree.traversal"), _tree_cfg("preorder"),
    ]))
    env = asyncio.run(pipeline.run_pipeline("đề duyệt giữa", "k"))
    assert env["status"] == "unsupported"
    assert env["error_code"] == "semantic_incomplete"
    assert env["completeness"]["dropped_requirements"] == ["tree_traversal.inorder"]
