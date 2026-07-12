# -*- coding: utf-8 -*-
"""Test harness đánh giá OFFLINE (M7 §7) — mock Gemini, không cần mạng/key.

Kiểm chứng: harness chấm đúng classification, spec validity, retry, semantic,
phân loại lỗi, và tổng hợp metrics. Đây là "offline harness verified" (§8) —
KHÔNG phải bằng chứng AI thật (chỉ eval_live mới cho metric thật).
"""

import asyncio
import json

from app.ai import pipeline
from app.evaluation.dataset import DATASET, EvalItem
from app.evaluation.harness import classify_error, evaluate_item, run_eval

# ── Spec generic mẫu ──────────────────────────────────────────

XOR_OK = {
    "dsl_version": "1.0",
    "title": "XOR",
    "objects": [
        {"id": "a", "type": "switch", "value": 0},
        {"id": "b", "type": "switch", "value": 0},
        {"id": "y", "type": "lamp"},
    ],
    "rules": [{"type": "boolean", "op": "xor", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
    "processes": [],
}
XOR_WRONG_OP = {**XOR_OK, "rules": [{"type": "boolean", "op": "or", "inputs": ["a", "b"], "target": "y"}]}
BAD_TYPE = {"dsl_version": "1.0", "title": "x", "objects": [{"id": "a", "type": "hologram"}]}


def _analysis(item_id: str) -> dict:
    return {
        "objects": [], "data": [], "relations": [], "processes": [], "constraints": [],
        "goal": f"ITEM:{item_id}", "input_description": "i", "output_description": "o", "notes": None,
    }


def _make_mock(items: list[EvalItem], plans: dict):
    """Mock tuần tự: analyze mở item mới, classify/simulate theo item đó."""
    st = {"idx": -1, "sim_attempt": 0}

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        if "DANH MỤC MÔ PHỎNG" in user_text:
            return json.dumps(plans[items[st["idx"]].id]["classification"])
        if "simulation_id đã chọn" in user_text:
            plan = plans[items[st["idx"]].id]
            sims = plan["simulate"]
            r = sims[min(st["sim_attempt"], len(sims) - 1)]
            st["sim_attempt"] += 1
            return r
        # analyze → sang item mới
        st["idx"] += 1
        st["sim_attempt"] = 0
        return json.dumps(_analysis(items[st["idx"]].id))

    return fake


def test_classify_error_mapping():
    assert classify_error("Object type không hợp lệ") == "unknown_primitive"
    assert classify_error("Rule tham chiếu input không tồn tại") == "dangling_reference"
    assert classify_error("Rule có phụ thuộc vòng") == "cycle"
    assert classify_error("Tối đa 20 rule") == "over_limit"


def test_harness_cham_dung_va_tong_hop(monkeypatch):
    items = [
        EvalItem("t-spec", "tìm max", "specialized", "algorithm.find_max"),
        EvalItem("t-xor", "cổng xor", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
        EvalItem("t-semwrong", "cổng xor sai", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
        EvalItem("t-retry", "cổng xor lỗi rồi ok", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
        EvalItem("t-unsup", "phản ứng hóa học", "unsupported"),
        EvalItem("t-unsupbad", "bài vượt v1", "unsupported"),
    ]
    # config find_max hợp lệ để validator specialized chấp nhận
    findmax_cfg = {
        "problem": {"summary": "Tìm max", "input": "i", "output": "o"},
        "data": {"array": [3, 1, 2]},
    }
    plans = {
        "t-spec": {
            "classification": {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None},
            "simulate": [json.dumps(findmax_cfg)],
        },
        "t-xor": {
            "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
            "simulate": [json.dumps(XOR_OK)],
        },
        "t-semwrong": {
            "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
            "simulate": [json.dumps(XOR_WRONG_OP)],  # cú pháp đúng, hành vi sai
        },
        "t-retry": {
            "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
            "simulate": [json.dumps(BAD_TYPE), json.dumps(XOR_OK)],  # sai lần 1, đúng lần 2
        },
        "t-unsup": {
            "classification": {"status": "unsupported", "simulation_id": None, "reason": "hóa học"},
            "simulate": [],
        },
        "t-unsupbad": {
            "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
            "simulate": [json.dumps(XOR_OK)],  # bị gán generic dù đáng lẽ unsupported
        },
    }
    monkeypatch.setattr(pipeline, "call_gemini", _make_mock(items, plans))

    report = asyncio.run(run_eval(items, "khoa-gia"))
    by_id = {r.id: r for r in report.results}

    assert by_id["t-spec"].classified_ok and by_id["t-spec"].spec_valid
    assert by_id["t-xor"].semantic_ok is True and by_id["t-xor"].failure is None
    assert by_id["t-semwrong"].failure == "semantic_wrong"
    assert by_id["t-retry"].spec_valid and by_id["t-retry"].retry_count == 1
    assert by_id["t-unsup"].classified_ok and by_id["t-unsup"].failure is None
    assert by_id["t-unsupbad"].failure == "unsupported_as_generic"

    m = report.metrics()
    assert m["total"] == 6
    assert m["specialized_selection_accuracy"] == 1.0
    assert m["error_categories"]["semantic_wrong"] == 1
    assert m["error_categories"]["unsupported_as_generic"] == 1
    assert 0.0 <= m["semantic_pass_rate"] <= 1.0
    assert m["avg_retry_count"] >= 0


def test_dataset_du_24_de_3_nhom():
    assert len(DATASET) == 25
    groups = {}
    for it in DATASET:
        groups[it.group] = groups.get(it.group, 0) + 1
    # M7.6 §4: b-graphpkt generic→specialized; M7.7: +b-triangle progressive (generic)
    assert groups["specialized"] == 9
    assert groups["generic"] == 10
    assert groups["unsupported"] == 6


def test_evaluate_item_don_le(monkeypatch):
    item = EvalItem("solo", "cổng xor", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"})
    plans = {"solo": {"classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}, "simulate": [json.dumps(XOR_OK)]}}
    monkeypatch.setattr(pipeline, "call_gemini", _make_mock([item], plans))
    res = asyncio.run(evaluate_item(item, "khoa-gia"))
    assert res.classified_ok and res.spec_valid and res.semantic_ok
