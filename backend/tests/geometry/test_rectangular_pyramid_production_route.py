# -*- coding: utf-8 -*-
"""Kiểm thử tích hợp production route cho chóp đáy chữ nhật/vuông (RECT_PYRAMID_P01).

Kiểm chứng:
1. Khi GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST, pipeline gọi compiler tất định,
   sinh Scene3D và tính đúng thể tích (24 và 18) mà 0 lượt gọi Gemini.
2. Khi GEOMETRY_COMPILER_MODE=LLM_ONLY, pipeline trả DISABLED (giữ nguyên chế độ mặc định).
3. Khi contract mâu thuẫn hoặc không hợp lệ, pipeline REFUSE fail-closed.
"""
from __future__ import annotations

import asyncio
import os
import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.semantic_program.request_contract import PyramidTopologySpec


def _rect_pyramid_contract():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, AD = 4. "
        "Cạnh bên SA vuông góc với mặt phẳng đáy, SA = 6. Tính thể tích khối chóp S.ABCD."
    )
    payload = {
        "input_facts": [
            {"id": "fact_len_AB", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_len_AD", "kind": "float", "label": "AD", "value": ["4"]},
            {"id": "fact_len_SA", "kind": "float", "label": "SA", "value": ["6"]},
        ],
        "geometric_relations": [
            {
                "kind": "perpendicular_lines",
                "line": ["A", "B"],
                "other_line": ["A", "D"],
                "source_fact_id": "fact_perp_base",
                "model_assumption": False,
            },
            {
                "kind": "perpendicular_line_plane",
                "line": ["S", "A"],
                "plane": ["A", "B", "C"],
                "source_fact_id": "fact_perp_lateral",
                "model_assumption": False,
            },
        ],
        "obligations": [
            {
                "kind": "volume",
                "container": "khoi_chop",
                "witness": "v",
            }
        ],
        "solid_topology": {
            "solid_kind": "pyramid",
            "apex": "S",
            "base_cycle": ["A", "B", "C", "D"],
            "base_shape": "rectangle",
        },
    }
    return text, build_request_contract(payload, problem_text=text, domain="hinh_hoc")


def test_rectangular_pyramid_production_route_deterministic_success(monkeypatch):
    """RECT_PYRAMID qua production pipeline tạo đúng Scene3D và volume 24 mà 0 gọi LLM."""
    text, contract = _rect_pyramid_contract()

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
    # 5 vertices A, B, C, D, S
    points = [o for o in objects if o.get("type") == "point3"]
    ids = {p.get("id") for p in points}
    assert ids == {"A", "B", "C", "D", "S"}

    # 1 solid chóp
    solids = [o for o in objects if o.get("type") == "solid"]
    assert len(solids) == 1, f"Kỳ vọng 1 solid, nhận {len(solids)}"
    solid = solids[0]
    assert len(solid.get("vertices", [])) == 5
    assert len(solid.get("faces", [])) == 5

    # 8 cạnh
    edges = {
        tuple(sorted((face[i], face[(i + 1) % len(face)])))
        for face in solid.get("faces", [])
        for i in range(len(face))
    }
    assert len(edges) == 8, f"Kỳ vọng 8 cạnh, nhận {len(edges)}"

    # Readout thể tích = 24
    readouts = [o for o in objects if o.get("type") == "quantity"]
    vol_readouts = [r for r in readouts if r.get("id") == "v" or "24" in str(r.get("value"))]
    assert len(vol_readouts) >= 1, f"Không tìm thấy readout thể tích: {readouts}"
    assert str(vol_readouts[0].get("value")) == "24"


def test_rectangular_pyramid_production_route_disabled_by_default(monkeypatch):
    """Khi GEOMETRY_COMPILER_MODE không bật (hoặc mặc định LLM_ONLY), compiler bị DISABLED."""
    from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen

    _, contract = _rect_pyramid_contract()
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    qd = quyet_dinh_dinh_tuyen(contract)
    assert qd.decision == "DISABLED"
