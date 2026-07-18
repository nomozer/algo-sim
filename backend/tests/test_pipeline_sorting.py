"""M14 Task 8 — pipeline end-to-end (MOCK) cho family surface sorting (§E).

Chứng minh: classify chọn token comparison_sort → mechanism gate → FamilySpec →
adapter → envelope mang CONCRETE id; selection/quick → capability_gap (KHÔNG
generic, KHÔNG simulate); variant sai → retry. 0 network (mock call_gemini)."""

from __future__ import annotations

import asyncio
import json

from app.ai import pipeline


def _fake_gemini(responses: list[str]):
    calls: list[dict] = []

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2):
        calls.append({"user": user_text})
        if not responses:
            raise AssertionError("fake Gemini bị gọi nhiều hơn số response chuẩn bị")
        return responses.pop(0)

    return fake, calls


def _analysis(proc=None, goal="Sắp xếp dãy điểm", ownership="algorithmic"):
    a = {
        "objects": ["dãy số"],
        "data": [{"description": "dãy điểm"}],
        "relations": [],
        "processes": ["sắp xếp"],
        "constraints": [],
        "goal": goal,
        "input_description": "Dãy số",
        "output_description": "Dãy đã sắp xếp",
        "result_ownership": ownership,
    }
    if proc is not None:
        a["prescribed_procedure"] = proc
    return json.dumps(a)


def _classify(sim_id="algorithm.comparison_sort"):
    return json.dumps({"status": "ok", "simulation_id": sim_id, "reason": None})


def _spec(variant="bubble", order="asc", array=None):
    return json.dumps({
        "family_version": "sort-fam-1", "variant": variant,
        "array": array or [5, 2, 9], "order": order,
    })


def test_bubble_positive_envelope_concrete(monkeypatch):
    fake, calls = _fake_gemini([_analysis("adjacent_compare_swap"), _classify(), _spec("bubble")])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp nổi bọt dãy 5,2,9.", "k"))
    assert env["status"] == "ok"
    assert env["simulation_id"] == "algorithm.bubble_sort"
    assert env["simulation_id"] != "algorithm.comparison_sort"  # token KHÔNG là envelope id
    assert env["config"]["algorithm_id"] == "bubble_sort"
    assert env["source"] == "family_resolved"
    assert env["variant"] == "bubble"
    assert len(calls) == 3


def test_insertion_positive(monkeypatch):
    fake, calls = _fake_gemini([_analysis("shift_into_sorted_prefix"), _classify(), _spec("insertion")])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp chèn dãy.", "k"))
    assert env["simulation_id"] == "algorithm.insertion_sort"
    assert env["config"]["algorithm_id"] == "insertion_sort"


def test_plain_sort_none_permissive(monkeypatch):
    # đề "sắp xếp tăng dần" không ép cơ chế (none) → permissive → bubble mặc định
    fake, calls = _fake_gemini([_analysis("none"), _classify(), _spec("bubble")])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp dãy tăng dần.", "k"))
    assert env["status"] == "ok" and env["simulation_id"] == "algorithm.bubble_sort"


def test_selection_sort_capability_gap_khong_simulate(monkeypatch):
    # analyze phát select_extreme_repeated → mechanism gate tầng 1 → gap TRƯỚC simulate
    fake, calls = _fake_gemini([_analysis("select_extreme_repeated"), _classify()])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp chọn dãy.", "k"))
    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env["error_code"] == "gate_mechanism_ownership"
    assert env.get("simulation_id") is None
    assert len(calls) == 2  # KHÔNG gọi simulate


def test_quick_sort_capability_gap(monkeypatch):
    fake, calls = _fake_gemini([_analysis("partition_recursive"), _classify()])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp nhanh dãy.", "k"))
    assert env["status"] == "unsupported" and env["failure_category"] == "capability_gap"
    assert len(calls) == 2


def test_variant_mismatch_retry(monkeypatch):
    # đề đòi insertion (shift) nhưng LLM điền bubble lần đầu → mismatch → retry → insertion
    fake, calls = _fake_gemini([
        _analysis("shift_into_sorted_prefix"), _classify(),
        _spec("bubble"),      # bị tầng 2 từ chối
        _spec("insertion"),   # retry đúng
    ])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp chèn.", "k"))
    assert env["status"] == "ok" and env["simulation_id"] == "algorithm.insertion_sort"
    assert len(calls) == 4  # analyze + classify + 2 lần simulate (retry)


def test_selection_sort_misroute_generic_van_bi_gate_chan(monkeypatch):
    # phòng thủ 2: selection-sort (cơ chế KHÔNG sở hữu) bị misroute về generic.
    # M15 Task 6 (Global Constraint 15): prescribed thuộc họ comparison_sort ≠ họ
    # của generic → recovery reclassify ĐÚNG 1 lượt (→ comparison_sort) TRƯỚC mọi
    # route-dependent gate; trên FINAL route mechanism gate tầng 1 chặn
    # select_extreme (unowned) → capability_gap. KẾT QUẢ (unsupported +
    # capability_gap, KHÔNG dựng generic) GIỮ NGUYÊN — chỉ đường đi đổi
    # (recovery→tier-1 thay vì computation gate; cần thêm 1 response reclassify).
    fake, calls = _fake_gemini([
        _analysis("select_extreme_repeated", ownership="algorithmic"),
        _classify("generic.rule_scene"),
        _classify("algorithm.comparison_sort"),  # reclassify bounded 1 lượt
    ])
    monkeypatch.setattr(pipeline, "call_gemini", fake)
    env = asyncio.run(pipeline.run_pipeline("Sắp xếp chọn.", "k"))
    assert env["status"] == "unsupported" and env["failure_category"] == "capability_gap"
