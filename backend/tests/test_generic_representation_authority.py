# -*- coding: utf-8 -*-
"""M15 Task 15 (W5) — generic representation authority proof.

Khóa 13 phần proof cuối: repr membership owned CỦA generic.rule_scene DẪN XUẤT
từ manifest `process_types()` (một nguồn, không viết tay); hai membership của
CÙNG một target mang result_authority KHÁC nhau (computation vs representation,
§C1); FORMALIZED_FAMILIES đủ 8/8 family → K1 lock ("owned ≠ ()" khi đã
formalize, test_capability_descriptors.test_formalized_families_owned_khong_rong)
kích hoạt ĐẦY ĐỦ trên toàn CATALOG; và representation KHÔNG bao giờ trở thành
lối tắt trả lời một bài đòi computation (bất biến #21) — pin bằng run_pipeline
thật (mock LLM), không đọc text đề, chỉ đọc tín hiệu analyze có cấu trúc.
"""
from __future__ import annotations

import asyncio
import json

from app.ai import pipeline


def test_repr_owned_dan_xuat_tu_manifest_process_types():
    from app.simulation.catalog import CATALOG
    from app.simulation.dsl.manifest import process_types

    mems = [
        m
        for m in CATALOG["generic.rule_scene"].family_memberships
        if m.family_id.value == "structural_progressive_representation"
    ]
    assert len(mems) == 1
    assert set(mems[0].owned_mechanisms) == {
        f"structural_progressive_representation.{p}" for p in process_types()
    }  # một nguồn — manifest, không viết tay


def test_hai_membership_generic_authority_khac_nhau():
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import ResultAuthority

    auths = {
        m.family_id.value: m.result_authority
        for m in CATALOG["generic.rule_scene"].family_memberships
    }
    assert auths["boolean_composition"] == ResultAuthority.COMPUTATION
    assert auths["structural_progressive_representation"] == ResultAuthority.REPRESENTATION


def test_formalized_families_du_8():
    from app.simulation.descriptor import FamilyId
    from app.simulation.mechanisms import FORMALIZED_FAMILIES

    assert FORMALIZED_FAMILIES == frozenset(FamilyId)  # K1 đầy đủ — kích hoạt lock 14/14


# ── bất biến #21: representation KHÔNG trả lời bài đòi computation ─────────
# Mock call_gemini dispatch theo skill (marker trong user_text), giống pattern
# test_pipeline_mechanism_consistency.py / test_m13_routing.py: analyze trả
# result_ownership="algorithmic" (thuật toán không engine nào sở hữu),
# prescribed_procedure=None (KHÔNG mismatch family nên route-recovery không
# chen ngang), classify chọn thẳng generic.rule_scene → computation gate
# (M13) fire trên FINAL route → envelope unsupported/capability_gap, KHÔNG
# simulate nào chạy, KHÔNG config nào được sinh. Đây chính là target thứ hai
# của generic (structural_progressive_representation) không được phép "gánh
# hộ" một yêu cầu computation chỉ vì cùng một runtime target sở hữu cả hai
# membership.
def _analysis_json(ownership: str) -> str:
    return json.dumps(
        {
            "objects": ["dãy"],
            "data": [{"description": "dãy"}],
            "relations": [],
            "processes": ["x"],
            "constraints": [],
            "goal": "Tính kết quả bằng thuật toán",
            "input_description": "in",
            "output_description": "out",
            "result_ownership": ownership,
            "prescribed_procedure": None,
        }
    )


def _classify_json(sim_id: str) -> str:
    return json.dumps({"status": "ok", "simulation_id": sim_id, "reason": None})


def test_representation_khong_tra_loi_bai_computation():
    counts = {"analyze": 0, "classify": 0, "simulate": 0}

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        if "DANH MỤC MÔ PHỎNG" in user_text:
            counts["classify"] += 1
            return _classify_json("generic.rule_scene")
        if "simulation_id đã chọn" in user_text:
            counts["simulate"] += 1
            return "{}"
        counts["analyze"] += 1
        return _analysis_json("algorithmic")

    async def _run():
        return await pipeline.run_pipeline("Đề bất kỳ.", "k")

    # gọi hai lần: bản thân hàm phải deterministic (không phụ thuộc thứ tự gọi)
    import unittest.mock as mock

    with mock.patch.object(pipeline, "call_gemini", fake):
        env = asyncio.run(_run())

    assert env["status"] == "unsupported"
    assert env["failure_category"] == "capability_gap"
    assert env.get("simulation_id") is None
    assert "config" not in env
    assert counts["simulate"] == 0  # gate chặn TRƯỚC stage_simulate — không config nào sinh
    # reason/error KHÔNG đổi — pin nội dung message của computation_gate (F8 lock)
    from app.simulation.computation_gate import check_computation_ownership
    from app.simulation.representation import build_representation_plan

    analysis = json.loads(_analysis_json("algorithmic"))
    plan = build_representation_plan(analysis)
    expected_reason = check_computation_ownership(analysis, plan)
    assert expected_reason is not None
    assert env["reason"] == expected_reason
