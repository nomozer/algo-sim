# -*- coding: utf-8 -*-
"""M17 W2A — routing/near-miss BOUNDARY cho tree.traversal qua production
run_pipeline (offline scripted). Kiểm PLUMBING pipeline (không kiểm chất lượng
classify của LLM — đó là việc LIVE): given quyết định classify, pipeline route/
validate/fail-closed đúng.

Ranh giới cross-family (tree DFS vs graph DFS) + near-miss (BST/AVL/heap/
expression-tree/n-ary/Dijkstra) verify: KHÔNG rơi vào tree.traversal khi
classify từ chối/route khác; tree spec HỎNG → fail-closed (không false ok).
"""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.simulation.descriptor import FamilyId
from app.simulation.mechanisms import FAMILY_MECHANISMS


def _fake_gemini(responses):
    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn số response scripted"
        return responses.pop(0)
    return fake


def _analysis(ownership="provided", roles=None, structured=True):
    # structured=True: analyze THẤY cấu trúc cây (nút + quan hệ) → qua structure
    # gate. structured=False: đề trống → gate chặn (insufficient).
    a = {
        "objects": ["A", "B", "C"] if structured else ["cây"],
        "data": [{"description": "cây"}],
        "relations": [{"type": "left_child", "from": "A", "to": "B"}] if structured else [],
        "processes": [], "constraints": [], "goal": "Duyệt cây",
        "input_description": "Cây nhị phân", "output_description": "Thứ tự duyệt",
        "domain_scope": "THPT_INFORMATICS", "simulatability": "MEANINGFUL_TRACE", "result_ownership": ownership,
    }
    if roles:
        a.update(roles)
    return json.dumps(a)


def _classify(sim_id, status="ok", reason=None):
    return json.dumps({"status": status, "simulation_id": sim_id, "reason": reason})


def _tree_spec(variant="preorder", root="A", nodes=None):
    nodes = nodes or [
        {"id": "A", "label": "A", "left": "B", "right": "C"},
        {"id": "B", "label": "B", "left": None, "right": None},
        {"id": "C", "label": "C", "left": None, "right": None},
    ]
    return json.dumps({"specVersion": "tree-1.0", "variant": variant, "rootId": root, "nodes": nodes})


def _run(monkeypatch, responses):
    monkeypatch.setattr(pipeline, "call_gemini", _fake_gemini(list(responses)))
    return asyncio.run(pipeline.run_pipeline("đề duyệt cây", "k"))


# ── plumbing: tree prompt → tree.traversal ok ──
def test_tree_route_ok(monkeypatch):
    env = _run(monkeypatch, [_analysis(), _classify("tree.traversal"), _tree_spec()])
    assert env["status"] == "ok" and env["simulation_id"] == "tree.traversal"
    assert env["config"]["variant"] == "preorder"
    # config KHÔNG chứa thứ tự duyệt / kết quả (engine FE tính)
    assert "visitedOrder" not in env["config"] and "steps" not in env["config"]


# ── fail-closed: tree spec HỎNG (multi-parent) → retry → không false ok ──
def test_tree_spec_hong_fail_closed(monkeypatch):
    bad = json.dumps({
        "specVersion": "tree-1.0", "variant": "preorder", "rootId": "A",
        "nodes": [
            {"id": "A", "left": "B", "right": "C"},
            {"id": "B", "left": "D"}, {"id": "C", "left": "D"}, {"id": "D"},  # D multi-parent
        ],
    })
    monkeypatch.setattr(pipeline, "call_gemini",
                        _fake_gemini([_analysis(), _classify("tree.traversal"), bad, bad, bad]))
    try:
        env = asyncio.run(pipeline.run_pipeline("đề duyệt cây", "k"))
        # nếu không raise thì PHẢI unsupported (không bao giờ ok với spec hỏng)
        assert env["status"] != "ok"
    except RuntimeError:
        pass  # 3 retry fail → RuntimeError (fail-closed) — chấp nhận


# ── structure gate: tree route + analyze KHÔNG cấu trúc → insufficient ──
def test_insufficient_structure_gate_chan_khong_bia_cay(monkeypatch):
    # LLM route tree.traversal (như live) nhưng analyze thiếu cấu trúc → gate
    # chặn TRƯỚC simulate → KHÔNG bịa cây (false-positive simulation).
    env = _run(monkeypatch, [_analysis(structured=False), _classify("tree.traversal")])
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
    assert env["error_code"] == "structure_insufficient"
    assert env.get("simulation_id") is None  # KHÔNG dựng cây


# ── FORCED-ROUTE REGRESSION (M17 W2A, pha A): dùng ĐÚNG analyze evidence THẬT
# của case insufficient live run 3. Live đó classify tự từ chối TRƯỚC nên gate
# NOT_RUN (early safe refusal). Test này ÉP route sang tree.traversal để chứng
# minh: nếu classify CÓ route tree thì structure gate v2 SẼ chặn đúng mã —
# tức tầng phòng thủ 2 thật sự hoạt động, không chỉ "không cần chạy".
def test_forced_route_insufficient_gate_fail_voi_analyze_live_that(monkeypatch):
    live_analysis = json.dumps({
        "objects": ["các nút của cây"],          # analyze THẬT (live pha A)
        "data": [],
        "relations": ["quan hệ cha-con giữa các nút"],
        "processes": [], "constraints": [], "goal": "Mô phỏng duyệt cây preorder",
        "input_description": "không nêu cấu trúc cây",
        "output_description": "thứ tự duyệt",
        "domain_scope": "THPT_INFORMATICS", "simulatability": "MEANINGFUL_TRACE", "result_ownership": "provided",
        "prescribed_procedure": "tree_traversal.preorder",
    })
    env = _run(monkeypatch, [live_analysis, _classify("tree.traversal")])
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "insufficient_specification"
    assert env["error_code"] == "structure_insufficient"
    assert env.get("simulation_id") is None      # không dựng cây
    assert env.get("config") is None             # không simulation envelope


# ── consistency gate (M17 W2A): analyze nói cơ chế CÂY nhưng classify lạc
# generic → recovery M15 (mechanism + ownership, KHÔNG keyword) ──
def test_classify_lac_generic_duoc_reclassify_ve_tree(monkeypatch):
    # analyze prescribed tree_traversal.inorder, classify lượt 1 = generic →
    # mismatch họ → ĐÚNG 1 reclassify → tree.traversal → ok.
    env = _run(monkeypatch, [
        _analysis(roles={"prescribed_procedure": "tree_traversal.inorder"}),
        _classify("generic.rule_scene"),
        _classify("tree.traversal"),
        _tree_spec(variant="inorder"),
    ])
    assert env["status"] == "ok" and env["simulation_id"] == "tree.traversal"


def test_classify_van_generic_sau_reclassify_thi_fail_closed(monkeypatch):
    # reclassify VẪN generic → fail-closed capability_gap, KHÔNG tạo generic sim
    env = _run(monkeypatch, [
        _analysis(roles={"prescribed_procedure": "tree_traversal.preorder"}),
        _classify("generic.rule_scene"),
        _classify("generic.rule_scene"),
    ])
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "route_mechanism_family_mismatch"
    assert env.get("simulation_id") is None  # KHÔNG generic simulation


def test_graph_dfs_khong_bi_keo_ve_tree(monkeypatch):
    # analyze KHÔNG đặt cơ chế cây cho đồ thị chung → không mismatch, giữ graph
    graph_cfg = json.dumps({
        "nodes": [{"id": "A"}, {"id": "B"}], "edges": [["A", "B"]],
        "start": "A", "variant": "dfs", "directed": False,
    })
    env = _run(monkeypatch, [
        _analysis(), _classify("network.graph_traversal"), graph_cfg,
    ])
    assert env["status"] == "ok" and env["simulation_id"] == "network.graph_traversal"


# ── cross-family: graph DFS → network.graph_traversal (KHÔNG tree) ──
def test_graph_dfs_route_graph_khong_tree(monkeypatch):
    graph_cfg = json.dumps({
        "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
        "edges": [["A", "B"], ["B", "C"]], "start": "A", "variant": "dfs", "directed": False,
    })
    env = _run(monkeypatch, [
        _analysis(roles={"process_roles": ["temporal"]}),
        _classify("network.graph_traversal"), graph_cfg,
    ])
    assert env["status"] == "ok" and env["simulation_id"] == "network.graph_traversal"


# ── near-miss: BST/AVL/heap/... → classify unsupported → KHÔNG rơi tree/generic ──
@pytest.mark.parametrize("prompt_kind", ["BST insert", "AVL balance", "heapify", "expression tree", "n-ary tree"])
def test_near_miss_unsupported_khong_leak(monkeypatch, prompt_kind):
    env = _run(monkeypatch, [
        _analysis(ownership="algorithmic"),
        _classify(None, status="unsupported",
                  reason=f"{prompt_kind} — cơ chế cây ngoài phạm vi duyệt cây nhị phân."),
    ])
    assert env["status"] == "unsupported"
    assert env.get("simulation_id") is None  # KHÔNG tree.traversal, KHÔNG generic


# ── taxonomy: cơ chế tree KHÔNG giao cơ chế graph (ranh giới family) ──
def test_tree_va_graph_mechanism_tach_bach():
    tree = set(FAMILY_MECHANISMS[FamilyId.TREE_TRAVERSAL])
    graph = set(FAMILY_MECHANISMS[FamilyId.GRAPH_TRAVERSAL])
    assert not (tree & graph)
    assert all(m.startswith("tree_traversal.") for m in tree)
    assert all(m.startswith("graph_traversal.") for m in graph)
