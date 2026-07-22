# -*- coding: utf-8 -*-
"""M17-RC1 §C1.1 — lock SEMANTIC OPERATION CANONICALIZATION.

Nguyên nhân gốc: §C1 định danh yêu cầu bằng `(target_id, variant)`, tức TRỘN
"người dùng muốn làm gì" với "executor nào làm". Live L1-V4 cho thấy analyze
dao động giữa hai target ANH EM trong cùng family cho CÙNG một đề — và hệ từ
chối oan.

Nguyên tắc: **route được quyền chọn implementation target, KHÔNG được quyền
viết lại hay xoá yêu cầu semantic của người dùng.**

Ranh giới gộp — cái này quan trọng hơn cả bản sửa:
- ĐƯỢC gộp khi danh tính semantic TRÙNG HOÀN TOÀN, hoặc khi một yêu cầu kém
  cụ thể bị hấp thụ bởi yêu cầu cùng operation có variant;
- KHÔNG BAO GIỜ gộp max/min, BFS/DFS, bubble/insertion, preorder/inorder.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from app.ai import pipeline
from app.evaluation.authenticity_fixtures import _analysis, _booldag_cfg, _classify
from app.simulation.operations import (
    OPERATIONS,
    SEMANTIC_OPERATION_MAP,
    SemanticRequirement,
    canonical_requirements,
    satisfies_semantic_operations,
)

_LIVE = (Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17"
         / "rc1" / "live_analyze_sufficiency.json")


# ── hợp đồng registry ────────────────────────────────────────────
def test_moi_operation_deu_khai_semantic():
    """Target id KHÔNG được tự động trở thành operation id."""
    for op in OPERATIONS():
        assert op in SEMANTIC_OPERATION_MAP, f"{op}: thiếu semantic_operation_id"


def test_target_khai_duoc_no_satisfy_semantic_nao():
    assert satisfies_semantic_operations("logic.boolean_dag") == [
        SemanticRequirement("boolean.evaluate_expression")]
    assert satisfies_semantic_operations("tree.traversal", "preorder") == [
        SemanticRequirement("tree.traverse", "preorder")]
    # không truyền variant → target khai TẤT CẢ variant nó làm được
    assert len(satisfies_semantic_operations("tree.traversal")) == 4


# ── A–D: KHÔNG được gộp ──────────────────────────────────────────
@pytest.mark.parametrize("ops,n,ten", [
    (["single_pass_scan:find_max", "single_pass_scan:find_min"], 2, "A max+min"),
    (["graph_traversal:bfs", "graph_traversal:dfs"], 2, "B BFS+DFS"),
    (["comparison_sort:bubble", "comparison_sort:insertion"], 2, "C hai thuật toán sắp xếp"),
    (["tree_traversal:preorder", "tree_traversal:inorder",
      "tree_traversal:postorder", "tree_traversal:level_order"], 4, "D bốn kiểu duyệt cây"),
])
def test_khong_duoc_gop_yeu_cau_doc_lap(ops, n, ten):
    reqs = canonical_requirements(ops)
    assert len(reqs) == n, f"{ten}: gộp mất yêu cầu — còn {[r.label_key() for r in reqs]}"


def test_max_min_khong_gop_du_CHUNG_mechanism():
    """Ca kinh điển: cùng `track_extreme` nhưng là HAI mục tiêu."""
    mx = SEMANTIC_OPERATION_MAP["single_pass_scan:find_max"]
    mn = SEMANTIC_OPERATION_MAP["single_pass_scan:find_min"]
    assert mx.operation_id != mn.operation_id
    assert OPERATIONS()["single_pass_scan:find_max"].mechanism == \
        OPERATIONS()["single_pass_scan:find_min"].mechanism


# ── E: ĐƯỢC gộp (đúng chỗ và chỉ đúng chỗ) ───────────────────────
def test_target_anh_em_cung_bieu_dat_mot_yeu_cau_thi_gop():
    reqs = canonical_requirements(
        ["boolean_composition:rule_scene", "boolean_composition:boolean_dag",
         "boolean_composition:and_gate"])
    assert reqs == [SemanticRequirement("boolean.evaluate_expression")]


def test_yeu_cau_kem_cu_the_bi_hap_thu_boi_yeu_cau_co_variant():
    """"đổi cơ số" (chưa nêu cặp) + "đổi 10→2" = MỘT việc, không phải hai."""
    reqs = canonical_requirements(
        ["positional_representation:base_conversion",
         "positional_representation:decimal_to_binary"])
    assert reqs == [SemanticRequirement("number.convert_base", "10->2")]


# ── V4 regression: dùng ĐÚNG raw payload live, 0 HTTP ────────────
def _fake(responses):
    async def f(api_key, system_prompt, user_text, response_schema=None,
                temperature=0.2, image=None):
        assert responses, "gọi nhiều hơn scripted"
        return responses.pop(0)
    return f


_BOOL_CFG = _booldag_cfg(
    [{"id": "A", "value": 1}, {"id": "B", "value": 0}, {"id": "C", "value": 1}],
    [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
     {"id": "g2", "op": "NOT", "inputs": ["C"]},
     {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
    "g3",
)


@pytest.mark.skipif(not _LIVE.exists(), reason="chưa có artifact live L1")
@pytest.mark.parametrize("repeat", [1, 2])
def test_V4_regression_tu_raw_payload_live(monkeypatch, repeat):
    """Hai lượt live V4 gợi ý HAI target khác nhau (`rule_scene` vs
    `boolean_dag`) cho CÙNG một đề. Sau §C1.1 cả hai phải cho CÙNG phán quyết
    completeness — không lượt nào bị từ chối oan.

    Dùng nguyên payload analyze đã lưu: không gọi thêm HTTP, không sửa expected
    output để che lỗi."""
    live = json.loads(_LIVE.read_text(encoding="utf-8"))
    row = next(r for r in live["runs"]
               if r["case_id"] == "L1-V4-boolean-expression" and r["repeat"] == repeat)
    analysis = json.loads(row["raw_analyze_response"])

    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(analysis, ensure_ascii=False),
        json.dumps(_classify("logic.boolean_dag")),
        _BOOL_CFG,
    ]))
    env = asyncio.run(pipeline.run_pipeline(row["prompt"], "khoa-gia"))
    assert env["status"] == "ok", (
        f"lượt {repeat} từ chối oan: {env.get('error_code')} · "
        f"dropped={(env.get('completeness') or {}).get('dropped_operations')}")
    assert env["simulation_id"] == "logic.boolean_dag"
    assert env.get("completeness") is None  # ok ⟹ không còn yêu cầu bị bỏ sót


@pytest.mark.skipif(not _LIVE.exists(), reason="chưa có artifact live L1")
def test_hai_luot_V4_cho_cung_canonical_requirement():
    """Gợi ý target thô khác nhau ⇒ vẫn CÙNG yêu cầu semantic."""
    live = json.loads(_LIVE.read_text(encoding="utf-8"))
    rows = [r for r in live["runs"] if r["case_id"] == "L1-V4-boolean-expression"]
    canon = {tuple(canonical_requirements(r["requested_operations"])) for r in rows}
    assert len(canon) == 1, f"hai lượt cho canonical khác nhau: {canon}"


# ── F: canonicalization KHÔNG được vô hiệu hoá ownership gate ────
def test_canonicalization_khong_lam_vo_hieu_ownership_gate(monkeypatch):
    """Đề đòi cơ chế mà target KHÔNG sở hữu vẫn phải fail-closed. Gộp semantic
    chỉ được nới chỗ "target anh em cùng đáp ứng", tuyệt đối không nới quyền
    sở hữu cơ chế/route."""
    analysis = {
        **_analysis(goal="Sắp xếp bằng quick sort", prescribed="partition_recursive"),
        "requested_operations": [],
    }
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(analysis, ensure_ascii=False),
        json.dumps(_classify("algorithm.comparison_sort")),
    ]))
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp dãy 5 2 9 bằng quick sort", "khoa-gia"))
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env.get("simulation_id") is None


def test_target_khong_satisfy_van_bi_pha2_chan(monkeypatch):
    """Đề hỏi duyệt GIỮA, spec dựng duyệt TRƯỚC → vẫn chặn (gộp semantic không
    được nuốt khác biệt variant)."""
    from app.evaluation.authenticity_fixtures import _tree_cfg

    rel = [{"type": "left_child", "from": "A", "to": "B"}]
    analysis = {
        **_analysis(goal="Duyệt cây thứ tự giữa", objects=["nút A", "nút B"], relations=rel),
        "requested_operations": ["tree_traversal:inorder"],
    }
    monkeypatch.setattr(pipeline, "call_gemini", _fake([
        json.dumps(analysis, ensure_ascii=False),
        json.dumps(_classify("tree.traversal")),
        _tree_cfg("preorder", "A", [("A", "B", None), ("B", None, None)]),
    ]))
    env = asyncio.run(pipeline.run_pipeline("Duyệt cây gốc A theo thứ tự giữa", "khoa-gia"))
    assert env["status"] == "unsupported"
    assert env["error_code"] == "semantic_incomplete"
    assert env["completeness"]["dropped_operations"] == ["tree.traverse/inorder"]
