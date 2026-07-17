"""M14 Task 10 — TRANSCRIPT PARITY: evaluate_item (mới, qua run_pipeline) vs
_evaluate_item_legacy (cũ, tái dựng stage) trên CÙNG kịch bản mock.

Khác biệt HỢP LỆ DUY NHẤT: case gate-refusal (mới chấm ĐÚNG là từ chối, cũ bỏ
qua gate) — liệt kê tường minh. Sau khi test này xanh, _simulate_with_metrics +
_evaluate_item_legacy được RETIRE (test này giữ lại làm bằng chứng lịch sử; nó
tự bỏ qua nếu legacy đã xóa)."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.ai import pipeline
from app.evaluation import harness
from app.evaluation.dataset import EvalItem

pytestmark = pytest.mark.skipif(
    not hasattr(harness, "_evaluate_item_legacy"),
    reason="legacy đã retire — parity đã chứng minh (xem git history + test_eval_metrics_snapshot)",
)

XOR_OK = {
    "dsl_version": "1.0", "title": "XOR",
    "objects": [{"id": "a", "type": "switch", "value": 0}, {"id": "b", "type": "switch", "value": 0}, {"id": "y", "type": "lamp"}],
    "rules": [{"type": "boolean", "op": "xor", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
    "processes": [],
}
XOR_WRONG = {**XOR_OK, "rules": [{"type": "boolean", "op": "or", "inputs": ["a", "b"], "target": "y"}]}
BAD = {"dsl_version": "1.0", "title": "x", "objects": [{"id": "a", "type": "hologram"}]}
FINDMAX = {"problem": {"summary": "Tìm max", "input": "i", "output": "o"}, "data": {"array": [3, 1, 2]}}


def _analysis(oid, ownership="rule_derivable"):
    return json.dumps({
        "objects": [], "data": [], "relations": [], "processes": [], "constraints": [],
        "goal": oid, "input_description": "i", "output_description": "o",
        "result_ownership": ownership,
    })


def _mock(items, plans):
    st = {"idx": -1, "att": 0}

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        if "DANH MỤC MÔ PHỎNG" in user_text:
            return json.dumps(plans[items[st["idx"]].id]["classification"])
        if "simulation_id đã chọn" in user_text:
            sims = plans[items[st["idx"]].id]["simulate"]
            r = sims[min(st["att"], len(sims) - 1)]
            st["att"] += 1
            return r
        st["idx"] += 1
        st["att"] = 0
        own = plans[items[st["idx"]].id].get("ownership", "rule_derivable")
        return _analysis(items[st["idx"]].id, own)

    return fake


# Kịch bản KHÔNG dính gate (result_ownership=rule_derivable, không unsupported role)
_ITEMS = [
    EvalItem("p-spec", "tìm max", "specialized", "algorithm.find_max"),
    EvalItem("p-xor", "cổng xor", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    EvalItem("p-semwrong", "xor sai", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    EvalItem("p-retry", "xor retry", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    EvalItem("p-unsup", "hóa học", "unsupported"),
]
_PLANS = {
    "p-spec": {"classification": {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None}, "simulate": [json.dumps(FINDMAX)]},
    "p-xor": {"classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}, "simulate": [json.dumps(XOR_OK)]},
    "p-semwrong": {"classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}, "simulate": [json.dumps(XOR_WRONG)]},
    "p-retry": {"classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None}, "simulate": [json.dumps(BAD), json.dumps(XOR_OK)]},
    "p-unsup": {"classification": {"status": "unsupported", "simulation_id": None, "reason": "hóa học"}, "simulate": []},
}

_COMPARE_FIELDS = ("classified_ok", "spec_valid", "retry_count", "semantic_ok", "failure")


def test_parity_non_gate_cases(monkeypatch):
    monkeypatch.setattr(pipeline, "call_gemini", _mock(list(_ITEMS), _PLANS))
    new = asyncio.run(_run_all(harness.evaluate_item))
    monkeypatch.setattr(pipeline, "call_gemini", _mock(list(_ITEMS), _PLANS))
    old = asyncio.run(_run_all(harness._evaluate_item_legacy))

    new_by = {r.id: r for r in new}
    old_by = {r.id: r for r in old}
    for iid in old_by:
        for f in _COMPARE_FIELDS:
            assert getattr(new_by[iid], f) == getattr(old_by[iid], f), (
                f"parity lệch ở {iid}.{f}: new={getattr(new_by[iid], f)} old={getattr(old_by[iid], f)}"
            )


async def _run_all(fn):
    return [await fn(it, "k") for it in _ITEMS]


def test_gate_refusal_la_khac_biet_hop_le(monkeypatch):
    # Case gate-refusal: đề unsupported bị classify NHẦM về generic + ownership
    # algorithmic → gate chặn. MỚI: từ chối đúng. CŨ: bỏ qua gate → chấm sai.
    items = [EvalItem("g-misroute", "thuật toán tự nghĩ", "unsupported")]
    plans = {"g-misroute": {
        "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
        "simulate": [json.dumps(XOR_OK)], "ownership": "algorithmic",
    }}

    monkeypatch.setattr(pipeline, "call_gemini", _mock(list(items), plans))
    new = asyncio.run(harness.evaluate_item(items[0], "k"))
    monkeypatch.setattr(pipeline, "call_gemini", _mock(list(items), plans))
    old = asyncio.run(harness._evaluate_item_legacy(items[0], "k"))

    # MỚI: gate chặn → không ra envelope → nhóm unsupported = từ chối ĐÚNG
    assert new.classified_ok is True and new.computation_gate_fired is True
    # CŨ: bỏ qua gate → simulate generic thành công → chấm SAI (unsupported_as_generic)
    assert old.classified_ok is False and old.failure == "unsupported_as_generic"
    # → khác biệt hợp lệ, có chủ đích (mới nghiêm hơn cũ)
