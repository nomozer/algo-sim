# -*- coding: utf-8 -*-
"""Kiểm thử tích hợp production route cho lăng trụ (PRISM_P01).

Red-Before verification:
Chứng minh rằng trước khi sửa, pipeline._semantic_route_attempt bỏ qua
quyet_dinh_dinh_tuyen, gọi thẳng stage_semantic_program và vấp lỗi LLM call.
Sau khi sửa, với GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST, compiler được gọi
tất định, trả về envelope chứa scene3d lăng trụ (6 đỉnh, 5 mặt, 9 cạnh, đáp số 30)
mà 0 lượt gọi Gemini.
"""
from __future__ import annotations

import asyncio
import os
import pytest
from app.ai import pipeline as PL
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.obligations import Obligation
from app.simulation.semantic_program.request_contract import InputFact, RequestContract
from app.simulation.semantic_program.scale_normalization import SourceInvariant
from app.simulation.semantic_program.structured_relations import GeometricRelation


def _prism_p01_contract():
    text = (
        "Cho hình lăng trụ đứng ABC.DEF có đáy ABC là tam giác vuông tại A, "
        "AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF."
    )
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": ["5"]},
        ],
        "geometric_relations": [
            {
                "kind": "perpendicular_lines",
                "line": ["A", "B"],
                "other_line": ["A", "C"],
                "source_fact_id": "fact_perp_base",
                "model_assumption": False,
            },
            {
                "kind": "perpendicular_line_plane",
                "line": ["A", "D"],
                "plane": ["A", "B", "C"],
                "source_fact_id": "fact_perp_lateral",
                "model_assumption": False,
            },
        ],
        "obligations": [
            {
                "kind": "volume",
                "container": "solid_ABCDEF",
                "witness": "the_tich_lang_tru",
            }
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        },
    }
    return text, build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def _pyramid_control_contract():
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, "
        "AB = 3, AC = 4. Cạnh bên SA vuông góc với đáy, SA = 5. "
        "Tính thể tích khối chóp S.ABC."
    )
    contract = RequestContract(
        source_invariants=(
            SourceInvariant(points=("A", "B"), expected="3", source_fact_id="f_ab", scale_symbol="", source_text=""),
            SourceInvariant(points=("A", "C"), expected="4", source_fact_id="f_ac", scale_symbol="", source_text=""),
            SourceInvariant(points=("A", "S"), expected="5", source_fact_id="f_sa", scale_symbol="", source_text=""),
        ),
        input_facts=(
            InputFact(fact_id="f_vuong_day", label="đáy vuông", values=("tam giác ABC vuông tại A",)),
            InputFact(fact_id="f_vuong_canh_ben", label="cạnh bên vuông đáy", values=("SA ⊥ (ABC)",)),
        ),
        geometric_relations=(
            GeometricRelation(kind="perpendicular_lines", line=("A", "B"), other_line=("A", "C"), source_fact_id="f_vuong_day"),
            GeometricRelation(kind="perpendicular_line_plane", line=("S", "A"), plane=("A", "B", "C"), source_fact_id="f_vuong_canh_ben"),
        ),
        obligations=(
            Obligation(kind="volume", container="khoi_chop", params={"witness": "the_tich_khoi"}),
        ),
    )
    return text, contract


def test_prism_production_route_deterministic_compiler_success(monkeypatch):
    """PRISM_P01 qua production pipeline tạo đúng Scene3D và answer 30 mà không gọi LLM."""
    text, contract = _prism_p01_contract()

    # Mock duy nhất tầng analyze boundary bằng canonical contract
    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    # Chặn tuyệt đối Gemini call ở tầng synthesis
    async def no_gemini(*args, **kwargs):
        raise AssertionError("Production route đã gọi Gemini thay vì dùng compiler!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)

    # Kích hoạt compiler opt-in
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))

    assert env.get("status") == "ok", f"Pipeline thất bại: {env}"
    assert env.get("domain") == "geometry"
    assert env.get("source") == "semantic_program"

    scene = env.get("scene3d")
    assert scene is not None, "Envelope thiếu scene3d"

    objects = scene.get("objects", [])
    # 6 vertices A, B, C, D, E, F
    points = [o for o in objects if o.get("type") == "point3"]
    ids = {p.get("id") for p in points}
    assert ids == {"A", "B", "C", "D", "E", "F"}
    labels = {p.get("label") for p in points}
    assert labels == {"Điểm A", "Điểm B", "Điểm C", "Điểm D", "Điểm E", "Điểm F"}

    # 1 solid lăng trụ
    solids = [o for o in objects if o.get("type") == "solid"]
    assert len(solids) == 1, f"Kỳ vọng 1 solid, nhận {len(solids)}"
    solid = solids[0]
    assert len(solid.get("vertices", [])) == 6
    assert len(solid.get("faces", [])) == 5

    # Đếm số cạnh duy nhất từ các mặt
    edges = {
        tuple(sorted((face[i], face[(i + 1) % len(face)])))
        for face in solid.get("faces", [])
        for i in range(len(face))
    }
    assert len(edges) == 9, f"Kỳ vọng 9 cạnh, nhận {len(edges)}"

    # Kiểm tra đáp số = 30 trong readout
    readouts = [o for o in objects if o.get("type") == "quantity"]
    vol_readouts = [r for r in readouts if r.get("id") == "the_tich_lang_tru" or "30" in str(r.get("value"))]
    assert len(vol_readouts) >= 1, f"Không tìm thấy readout đáp số 30: {readouts}"
    assert str(vol_readouts[0].get("value")) == "30"


def test_pyramid_control_parity(monkeypatch):
    """Pyramid control qua production pipeline cũng dùng compiler và cho ra scene hợp lệ."""
    text, contract = _pyramid_control_contract()

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    async def no_gemini(*args, **kwargs):
        raise AssertionError("Pyramid control đã gọi Gemini thay vì dùng compiler!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))
    assert env.get("status") == "ok", f"Pipeline thất bại: {env}"
    scene = env.get("scene3d")
    assert scene is not None

    objects = scene.get("objects", [])
    points = [o for o in objects if o.get("type") == "point3"]
    assert len(points) == 4
    solids = [o for o in objects if o.get("type") == "solid"]
    assert len(solids) == 1
    assert len(solids[0].get("vertices", [])) == 4
    assert len(solids[0].get("faces", [])) == 4


def test_default_mode_bypasses_compiler(monkeypatch):
    """Khi không bật DETERMINISTIC_FIRST (mặc định LLM_ONLY), pipeline không tự kích hoạt compiler."""
    text, contract = _prism_p01_contract()

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    called = {"gemini": False}

    async def mock_gemini(*args, **kwargs):
        called["gemini"] = True
        raise RuntimeError("LLM_CALLED_AS_EXPECTED")

    monkeypatch.setattr(PL, "call_gemini", mock_gemini)
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)

    with pytest.raises(RuntimeError, match="LLM_CALLED_AS_EXPECTED"):
        asyncio.run(PL.run_pipeline(text, "fake_key"))

    assert called["gemini"] is True


def test_contradictory_facts_refusal_fail_closed(monkeypatch):
    """Khi đề có dữ kiện mâu thuẫn, compiler từ chối và pipeline trả unsupported fail-closed."""
    text = (
        "Cho hình lăng trụ đứng ABC.DEF có đáy ABC vuông tại A và vuông tại B, "
        "AB = 3, AC = 4. Cạnh bên AD = 5. Tính thể tích khối lăng trụ ABC.DEF."
    )
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AC", "kind": "float", "label": "AC", "value": ["4"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": ["5"]},
        ],
        "geometric_relations": [
            {"kind": "perpendicular_lines", "line": ["A", "B"], "other_line": ["A", "C"], "source_fact_id": "fact_perp_base_a", "model_assumption": False},
            {"kind": "perpendicular_lines", "line": ["B", "A"], "other_line": ["B", "C"], "source_fact_id": "fact_perp_base_b", "model_assumption": False},
            {"kind": "perpendicular_line_plane", "line": ["A", "D"], "plane": ["A", "B", "C"], "source_fact_id": "fact_perp_lateral", "model_assumption": False},
        ],
        "obligations": [
            {"kind": "volume", "container": "solid_ABCDEF", "witness": "the_tich_lang_tru"}
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C"],
            "top_cycle": ["D", "E", "F"],
            "correspondence": [["A", "D"], ["B", "E"], ["C", "F"]],
        },
    }
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    async def no_gemini(*args, **kwargs):
        raise AssertionError("Compiler refuse không được phép lùi về Gemini!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))
    assert env.get("status") == "unsupported"
    assert env.get("failure_category") == "geometry_generation_failed"
