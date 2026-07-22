# -*- coding: utf-8 -*-
"""M17-RC1 §C1 — lock OPERATION INTENT EXPRESSIBILITY.

Điều phải chứng minh: mọi operation quan trọng **analyze nói được** (end-to-end
qua production pipeline), chứ không chỉ "gate xử đúng khi test tiêm sẵn".

Bài học đã trả giá: định danh yêu cầu bằng *mechanism* làm `find_max` và
`find_min` gộp thành một (chung `track_extreme`) → đề "tìm cả max lẫn min" trả
`ok` và bỏ im lặng một nửa. **Operation KHÔNG BAO GIỜ dedupe theo mechanism.**
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import (
    _algo_cfg,
    _analysis,
    _classify,
    _sort_spec,
    _traverse_cfg,
    _tree_cfg,
)
from app.simulation.catalog import CATALOG
from app.simulation.completeness_gate import normalized_requested_operations
from app.simulation.descriptor import FamilyId
from app.simulation.operations import (
    OPERATIONS,
    _sanity,
    analyze_exposed_operations,
    operation_family,
    operations_for_family,
    operations_of_target,
)

TREE_REL = [
    {"type": "left_child", "from": "A", "to": "B"},
    {"type": "right_child", "from": "A", "to": "C"},
]
TREE_NODES = [("A", "B", "C"), ("B", None, None), ("C", None, None)]


# ── registry ─────────────────────────────────────────────────────
def test_registry_khong_vi_pham_cau_truc():
    assert _sanity() == []


def test_moi_operation_deu_co_target_that():
    for op, s in OPERATIONS().items():
        assert s.target_id in CATALOG, f"{op}: target không có trong CATALOG"
        assert CATALOG[s.target_id].executor_id, f"{op}: target thiếu executor"


def test_max_va_min_la_HAI_operation_dung_chung_MOT_mechanism():
    """Trung tâm của §C1. Nếu test này đỏ thì lỗi §D đã quay lại."""
    reg = OPERATIONS()
    mx, mn = reg["single_pass_scan:find_max"], reg["single_pass_scan:find_min"]
    assert mx.operation_id != mn.operation_id
    assert mx.mechanism == mn.mechanism == "single_pass_scan.track_extreme"
    assert mx.target_id != mn.target_id


def test_moi_family_deu_phoi_operation_qua_analyze():
    """Khác `analyze_exposed_values()` (chỉ 3 family): operation phủ 9/9 nên
    gate completeness nhận được dữ liệu ở MỌI family."""
    exposed = set(analyze_exposed_operations())
    fams = {operation_family(o) for o in exposed}
    assert fams == {f.value for f in FamilyId}, f"family thiếu operation: {fams}"


def test_khong_dedupe_theo_mechanism():
    a = {"requested_operations": ["single_pass_scan:find_max", "single_pass_scan:find_min"]}
    assert len(normalized_requested_operations(a)) == 2


def test_gia_tri_la_bi_loai_khong_bia_operation():
    a = {"requested_operations": ["single_pass_scan:find_max", "khong_ton_tai:abc"]}
    assert normalized_requested_operations(a) == ["single_pass_scan:find_max"]


def test_operations_of_target_loc_theo_variant():
    assert operations_of_target("tree.traversal", "inorder") == ["tree_traversal:inorder"]
    assert len(operations_of_target("tree.traversal", None)) == 4


# ── end-to-end qua production run_pipeline ───────────────────────
def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


def _an(goal, ops, **kw):
    return json.dumps({**_analysis(goal=goal, **kw), "requested_operations": ops})


def _cls(sim_id):
    """`_classify` trả dict (CaseScript giữ dict); provider thật nhận JSON."""
    return json.dumps(_classify(sim_id))


def _run(monkeypatch, responses, text):
    monkeypatch.setattr(pipeline, "call_gemini", _fake(list(responses)))
    return asyncio.run(pipeline.run_pipeline(text, "khoa-gia"))


BLOCK_CASES = [
    pytest.param(
        [_an("Tìm cả max lẫn min", ["single_pass_scan:find_max", "single_pass_scan:find_min"]),
         _cls("algorithm.find_max")],
        "Tìm cả giá trị lớn nhất và nhỏ nhất của dãy 4 7 2 9 5",
        2, id="max+min"),
    pytest.param(
        [_an("Duyệt cây cả bốn cách",
             ["tree_traversal:preorder", "tree_traversal:inorder",
              "tree_traversal:postorder", "tree_traversal:level_order"],
             objects=["nút A", "nút B", "nút C"], relations=TREE_REL),
         _cls("tree.traversal")],
        "Duyệt cây gốc A theo cả bốn cách", 4, id="tree-4-variant"),
    pytest.param(
        [_an("Duyệt đồ thị cả BFS lẫn DFS", ["graph_traversal:bfs", "graph_traversal:dfs"],
             objects=["đỉnh A", "đỉnh B", "đỉnh C"], relations=["A nối B", "A nối C"]),
         _cls("network.graph_traversal")],
        "Duyệt đồ thị từ A bằng cả BFS lẫn DFS", 2, id="bfs+dfs"),
    pytest.param(
        [_an("Sắp xếp bằng hai thuật toán",
             ["comparison_sort:bubble", "comparison_sort:insertion"]),
         _cls("algorithm.comparison_sort")],
        "Sắp xếp dãy 5 2 9 1 bằng nổi bọt rồi bằng chèn", 2, id="2-sort-variant"),
]


@pytest.mark.parametrize("responses,text,n_ops", BLOCK_CASES)
def test_e2e_nhieu_operation_bi_tu_choi_TRUNG_THUC(monkeypatch, responses, text, n_ops):
    """Không simulation nửa vời: chặn TRƯỚC simulate, không leak generic,
    thông điệp học sinh dùng NHÃN TIẾNG VIỆT chứ không id kỹ thuật."""
    env = _run(monkeypatch, responses, text)
    assert env["status"] == "unsupported"
    assert env["error_code"] == "multiple_operations_not_supported"
    assert env["failure_category"] == "semantic_incomplete"
    assert env.get("simulation_id") is None      # simulation_created = False
    assert env.get("config") is None
    assert len(env["completeness"]["requested_operations"]) == n_ops
    msg = env["reason"]
    assert ":" not in msg and "_" not in msg, f"thông điệp lộ id kỹ thuật: {msg}"


OK_CASES = [
    pytest.param(
        [_an("Tìm giá trị lớn nhất", ["single_pass_scan:find_max"]),
         _cls("algorithm.find_max"), _algo_cfg([4, 7, 2], summary="Tìm max")],
        "Tìm giá trị lớn nhất của dãy 4 7 2", "algorithm.find_max", id="max-only"),
    pytest.param(
        [_an("Duyệt cây thứ tự giữa", ["tree_traversal:inorder"],
             objects=["nút A", "nút B", "nút C"], relations=TREE_REL),
         _cls("tree.traversal"), _tree_cfg("inorder", "A", TREE_NODES)],
        "Duyệt cây gốc A theo thứ tự giữa", "tree.traversal", id="tree-1-variant"),
    pytest.param(
        [_an("Duyệt đồ thị BFS", ["graph_traversal:bfs"],
             objects=["đỉnh A", "đỉnh B", "đỉnh C"], relations=["A nối B", "A nối C"]),
         _cls("network.graph_traversal"),
         _traverse_cfg(["A", "B", "C"], [["A", "B"], ["A", "C"]], "A", "bfs")],
        "Duyệt đồ thị từ A bằng BFS", "network.graph_traversal", id="bfs-only"),
    pytest.param(
        [_an("Sắp xếp nổi bọt", ["comparison_sort:bubble"]),
         _cls("algorithm.comparison_sort"), _sort_spec("bubble", [5, 2, 9, 1])],
        "Sắp xếp dãy 5 2 9 1 bằng nổi bọt", "algorithm.bubble_sort", id="1-sort-variant"),
]


@pytest.mark.parametrize("responses,text,route", OK_CASES)
def test_e2e_mot_operation_KHONG_bi_chan_oan(monkeypatch, responses, text, route):
    """Bất biến §C1: status=ok ⟹ dropped_operations = []."""
    env = _run(monkeypatch, responses, text)
    assert env["status"] == "ok", env.get("reason")
    assert env["simulation_id"] == route
    assert env.get("completeness") is None  # ok thì không có bản ghi thiếu sót


def test_e2e_variant_lech_yeu_cau_bi_pha2_chan(monkeypatch):
    """Đề hỏi inorder, spec dựng preorder → PHA 2 chặn (dropped_operations)."""
    env = _run(monkeypatch, [
        _an("Duyệt cây thứ tự giữa", ["tree_traversal:inorder"],
            objects=["nút A", "nút B", "nút C"], relations=TREE_REL),
        _cls("tree.traversal"), _tree_cfg("preorder", "A", TREE_NODES),
    ], "Duyệt cây gốc A theo thứ tự giữa")
    assert env["status"] == "unsupported"
    assert env["error_code"] == "semantic_incomplete"
    assert env["completeness"]["dropped_operations"] == ["tree_traversal:inorder"]


def test_e2e_nhanh_selector_pha2_dung_variant_da_resolve(monkeypatch):
    """Đề hỏi chèn, selector resolve ra nổi bọt → PHA 2 phải bắt trên nhánh
    selector (đường từng bỏ qua gate ở RC1-C)."""
    env = _run(monkeypatch, [
        _an("Sắp xếp bằng chèn", ["comparison_sort:insertion"]),
        _cls("algorithm.comparison_sort"), _sort_spec("bubble", [5, 2, 9, 1]),
    ], "Sắp xếp dãy 5 2 9 1 bằng thuật toán chèn")
    assert env["status"] == "unsupported"
    assert env["error_code"] == "semantic_incomplete"
    assert env["completeness"]["dropped_operations"] == ["comparison_sort:insertion"]


@pytest.mark.xfail(
    strict=True,
    reason=(
        "M17-RC1 §L1 phát hiện — DEFECT MỞ, chờ quyết định, KHÔNG tự vá. "
        "Live chạy cùng một đề mạch logic hai lần: lần 1 analyze khai "
        "`boolean_composition:rule_scene`, lần 2 khai `:boolean_dag`. Khi "
        "classify route ĐÚNG tới logic.boolean_dag mà analyze lỡ khai operation "
        "ANH EM cùng family (do target khác sở hữu), PHA 2 tính "
        "dropped_operations=[rule_scene] → semantic_incomplete: TỪ CHỐI OAN một "
        "đề hoàn toàn hợp lệ. Đã chứng minh bằng CHÍNH payload analyze thật của "
        "L1-V4 #1. Phơi ra ở mọi family có nhiều target sở hữu operation khác "
        "nhau: boolean_composition (3), single_pass_scan (6), graph_traversal "
        "(2), positional_representation (2). strict=True để khi vá xong test "
        "xanh thì pytest báo đỏ, buộc xoá marker."
    ),
)
def test_operation_anh_em_cung_family_khong_duoc_lam_tu_choi_oan(monkeypatch):
    """analyze khai operation anh em trong CÙNG family ⇏ đề bị từ chối."""
    from app.evaluation.authenticity_fixtures import _booldag_cfg

    env = _run(monkeypatch, [
        _an("Mô phỏng mạch (A AND B) OR NOT C", ["boolean_composition:rule_scene"],
            objects=["biến A", "biến B", "biến C", "phép AND", "phép OR"],
            relations=["A và B vào phép AND", "NOT C vào phép OR"]),
        _cls("logic.boolean_dag"),
        _booldag_cfg([{"id": "A", "value": 1}, {"id": "B", "value": 0},
                      {"id": "C", "value": 1}],
                     [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                      {"id": "g2", "op": "NOT", "inputs": ["C"]},
                      {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}], "g3"),
    ], "Mô phỏng biểu thức (A AND B) OR NOT C với A=true, B=false, C=true.")
    assert env["status"] == "ok", (
        f"từ chối oan: {env.get('error_code')} · "
        f"dropped={(env.get('completeness') or {}).get('dropped_operations')}")


# ── MỌI đường trả envelope ok phải qua PHA 2 ─────────────────────
def test_moi_duong_tra_ok_deu_qua_phase2():
    """Khoá cấu trúc: đếm call site `_completeness_phase2` phải BẰNG số đường
    phát envelope ok trong run_pipeline. Thêm một đường trả ok mới mà quên gate
    ⇒ test đỏ (đúng cách lỗ selector đã lọt ở RC1-D)."""
    src = Path(pipeline.__file__).read_text(encoding="utf-8")
    ok_emits = len(re.findall(r'_emit\(observer,\s*"envelope",\s*status="ok"', src))
    phase2_calls = len(re.findall(r"_completeness_phase2\(", src))
    # -1 vì có một lần là ĐỊNH NGHĨA hàm, không phải call site
    assert phase2_calls - 1 == ok_emits, (
        f"{ok_emits} đường trả ok nhưng chỉ {phase2_calls - 1} chỗ gọi PHA 2")


def test_moi_family_co_it_nhat_mot_operation():
    for f in FamilyId:
        assert operations_for_family(f.value), f"{f.value}: không có operation nào"
