"""M14 Task 10 §F5 — eval KHÔNG để lại side effect: 0 row mới ở
simulation_cache / simulation_patterns / reuse_metrics; fault-injection chứng
minh gate-refusal được report là honest refusal (khóa bất biến #22)."""

from __future__ import annotations

import asyncio
import json

from app.ai import pipeline
from app.evaluation import harness
from app.evaluation.dataset import EvalItem
from app.persistence.db import SessionLocal, SimulationCache, SimulationPattern, ReuseMetric, init_db


def _analysis(oid, ownership="rule_derivable"):
    return json.dumps({
        "objects": [], "data": [], "relations": [], "processes": [], "constraints": [],
        "goal": oid, "input_description": "i", "output_description": "o", "result_ownership": ownership,
    })


XOR_OK = {
    "dsl_version": "1.0", "title": "XOR",
    "objects": [{"id": "a", "type": "switch", "value": 0}, {"id": "b", "type": "switch", "value": 0}, {"id": "y", "type": "lamp"}],
    "rules": [{"type": "boolean", "op": "xor", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}], "processes": [],
}


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
        return _analysis(items[st["idx"]].id, plans[items[st["idx"]].id].get("ownership", "rule_derivable"))

    return fake


def _counts():
    with SessionLocal() as s:
        return (
            s.query(SimulationCache).count(),
            s.query(SimulationPattern).count(),
            s.query(ReuseMetric).count(),
        )


def test_eval_khong_ghi_production_rows(monkeypatch):
    init_db()
    items = [
        EvalItem("s-spec", "tìm max", "specialized", "algorithm.find_max"),
        EvalItem("s-xor", "cổng xor", "generic", "generic.rule_scene", {"kind": "boolean_gate", "op": "xor"}),
    ]
    plans = {
        "s-spec": {"classification": {"status": "ok", "simulation_id": "algorithm.find_max", "reason": None},
                   "simulate": [json.dumps({"problem": {"summary": "x", "input": "i", "output": "o"}, "data": {"array": [3, 1, 2]}})]},
        "s-xor": {"classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
                  "simulate": [json.dumps(XOR_OK)]},
    }
    monkeypatch.setattr(pipeline, "call_gemini", _mock(items, plans))

    before = _counts()
    report = asyncio.run(harness.run_eval(items, "k"))
    after = _counts()

    assert [r for r in report.results if r.spec_valid]  # có case chạy tới cùng
    assert before == after, f"eval ghi side-effect: before={before} after={after}"


def test_fault_injection_classify_qua_nhung_gate_chan_van_honest_refusal(monkeypatch):
    # classify CHO QUA (generic ok) nhưng deterministic gate chặn (ownership
    # algorithmic) → report phải hiện TỪ CHỐI, không phải "chạy thành công".
    items = [EvalItem("f-gap", "thuật toán tự nghĩ", "unsupported")]
    plans = {"f-gap": {
        "classification": {"status": "ok", "simulation_id": "generic.rule_scene", "reason": None},
        "simulate": [json.dumps(XOR_OK)], "ownership": "algorithmic",
    }}
    monkeypatch.setattr(pipeline, "call_gemini", _mock(items, plans))

    res = asyncio.run(harness.evaluate_item(items[0], "k"))
    assert res.classified_ok is True           # từ chối đúng (nhóm unsupported)
    assert res.computation_gate_fired is True   # gate THẬT chạy trong eval
    assert res.spec_valid is None               # KHÔNG chạy tới envelope ok
    assert res.final_simulation_id is None
