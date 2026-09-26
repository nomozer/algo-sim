# -*- coding: utf-8 -*-
"""Kiểm thử tích hợp production route cho cuboid, cube và right square prism.

Kiểm chứng các yêu cầu Phase 6:
1. Tạo request bằng đúng production request builder (build_request_contract).
2. Parse qua đúng Pydantic production boundary.
3. Chạy với GEOMETRY_COMPILER_MODE=DETERMINISTIC_FIRST:
   - compiler được gọi;
   - 0 synthesis request sau common input;
   - Scene3D envelope hợp lệ;
   - Đáp số: 60 (CUBOID_P01), 64 (CUBE_P01), 63 (SQUARE_PRISM_CONTROL).
4. Chạy control với DEFAULT_MODE=LLM_ONLY để chứng minh mặc định chưa bị thay đổi (DISABLED).
5. Chứng minh payload không chứa expected answer, expected volume, grading labels.
"""
from __future__ import annotations

import asyncio
import os
import pytest

from app.ai import pipeline as PL
from app.simulation.semantic_program.analyze_contract import build_request_contract
from app.simulation.geometry_compiler.routing import quyet_dinh_dinh_tuyen


def _cuboid_p01_payload():
    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 3, AD = 4, AA' = 5. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    payload = {
        "input_facts": [
            {"id": "fact_ab", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_ad", "kind": "float", "label": "AD", "value": ["4"]},
            {"id": "fact_aa_prime", "kind": "float", "label": "AA'", "value": ["5"]},
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
                "line": ["A'", "A"],
                "plane": ["A", "B", "D"],
                "source_fact_id": "fact_perp_lat",
                "model_assumption": False,
            },
        ],
        "obligations": [
            {
                "kind": "volume",
                "container": "khoi_hop",
                "witness": "V",
            }
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "rectangle",
            "lateral_structure": "right",
            "solid_subkind": "cuboid",
            "source_grounding": "hình hộp chữ nhật",
        },
    }
    return text, payload


def _cube_p01_payload():
    text = (
        "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 4. "
        "Tính thể tích của hình lập phương đó."
    )
    payload = {
        "input_facts": [
            {"id": "fact_edge", "kind": "float", "label": "AB", "value": ["4"]},
        ],
        "geometric_relations": [
            {
                "kind": "perpendicular_lines",
                "line": ["A", "B"],
                "other_line": ["A", "D"],
                "source_fact_id": "fact_perp_base",
                "model_assumption": False,
            },
        ],
        "obligations": [
            {
                "kind": "volume",
                "container": "khoi_hop",
                "witness": "V",
            }
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "square",
            "lateral_structure": "right",
            "solid_subkind": "cube",
            "source_grounding": "hình lập phương",
        },
    }
    return text, payload


def _square_prism_control_payload():
    text = (
        "Cho hình lăng trụ đứng có đáy là hình vuông cạnh 3, chiều cao bằng 7. "
        "Tính thể tích khối lăng trụ đứng đó."
    )
    payload = {
        "input_facts": [
            {"id": "fact_base_edge", "kind": "float", "label": "AB", "value": ["3"]},
            {"id": "fact_height", "kind": "float", "label": "AA'", "value": ["7"]},
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
                "line": ["A'", "A"],
                "plane": ["A", "B", "D"],
                "source_fact_id": "fact_perp_lat",
                "model_assumption": False,
            },
        ],
        "obligations": [
            {
                "kind": "volume",
                "container": "khoi_lang_tru",
                "witness": "V",
            }
        ],
        "solid_topology": {
            "solid_kind": "prism",
            "base_cycle": ["A", "B", "C", "D"],
            "top_cycle": ["A'", "B'", "C'", "D'"],
            "correspondence": [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
            "base_shape": "square",
            "lateral_structure": "right",
            "solid_subkind": "right_square_prism",
            "source_grounding": "hình lăng trụ đứng có đáy là hình vuông",
        },
    }
    return text, payload


# ─── PRODUCTION ROUTE TESTS ────────────────────────────────────────────────

def test_cuboid_p01_production_route_deterministic_success(monkeypatch):
    """CUBOID_P01 (3x4x5 -> V=60) qua production pipeline tạo đúng Scene3D và V=60 với 0 LLM calls."""
    text, payload = _cuboid_p01_payload()
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    async def no_gemini(*args, **kwargs):
        raise AssertionError("Production route đã gọi Gemini thay vì dùng deterministic compiler!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))

    assert env.get("status") == "ok", f"Pipeline thất bại: {env}"
    assert env.get("domain") == "geometry"
    assert env.get("source") == "semantic_program"

    scene = env.get("scene3d")
    assert scene is not None, "Envelope thiếu scene3d"

    objects = scene.get("objects", [])
    # 8 đỉnh
    points = [o for o in objects if o.get("type") == "point3"]
    assert len(points) == 8
    p_ids = {p.get("id") for p in points}
    assert p_ids == {"A", "B", "C", "D", "A_prime", "B_prime", "C_prime", "D_prime"}

    # 1 solid
    solids = [o for o in objects if o.get("type") == "solid"]
    assert len(solids) == 1
    solid = solids[0]
    assert len(solid.get("vertices", [])) == 8
    assert len(solid.get("faces", [])) == 6

    # Euler characteristic: 8 - 12 + 6 = 2
    edges = {
        tuple(sorted((face[i], face[(i + 1) % len(face)])))
        for face in solid.get("faces", [])
        for i in range(len(face))
    }
    assert len(edges) == 12
    assert len(points) - len(edges) + len(solid.get("faces", [])) == 2

    # Readout thể tích = 60
    readouts = [o for o in objects if o.get("type") == "quantity"]
    vol_readouts = [r for r in readouts if r.get("id") == "V" or "60" in str(r.get("value"))]
    assert len(vol_readouts) >= 1, f"Không tìm thấy readout thể tích: {readouts}"
    assert str(vol_readouts[0].get("value")) == "60"


def test_cube_p01_production_route_deterministic_success(monkeypatch):
    """CUBE_P01 (edge=4 -> V=64) qua production pipeline tạo đúng Scene3D và V=64 với 0 LLM calls."""
    text, payload = _cube_p01_payload()
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    async def no_gemini(*args, **kwargs):
        raise AssertionError("Production route đã gọi Gemini thay vì dùng deterministic compiler!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))

    assert env.get("status") == "ok", f"Pipeline thất bại: {env}"
    scene = env.get("scene3d")
    assert scene is not None

    objects = scene.get("objects", [])
    readouts = [o for o in objects if o.get("type") == "quantity"]
    vol_readouts = [r for r in readouts if r.get("id") == "V" or "64" in str(r.get("value"))]
    assert len(vol_readouts) >= 1
    assert str(vol_readouts[0].get("value")) == "64"


def test_square_prism_control_production_route_deterministic_success(monkeypatch):
    """SQUARE_PRISM_CONTROL (base=3, h=7 -> V=63) qua production pipeline tạo đúng V=63 với 0 LLM calls."""
    text, payload = _square_prism_control_payload()
    contract = build_request_contract(payload, problem_text=text, domain="hinh_hoc")

    async def mock_analyze(*args, **kwargs):
        return contract, None

    monkeypatch.setattr(PL, "stage_semantic_analyze", mock_analyze)

    async def no_gemini(*args, **kwargs):
        raise AssertionError("Production route đã gọi Gemini thay vì dùng deterministic compiler!")

    monkeypatch.setattr(PL, "call_gemini", no_gemini)
    monkeypatch.setenv("GEOMETRY_COMPILER_MODE", "DETERMINISTIC_FIRST")

    env = asyncio.run(PL.run_pipeline(text, "fake_key"))

    assert env.get("status") == "ok", f"Pipeline thất bại: {env}"
    scene = env.get("scene3d")
    assert scene is not None

    objects = scene.get("objects", [])
    readouts = [o for o in objects if o.get("type") == "quantity"]
    vol_readouts = [r for r in readouts if r.get("id") == "V" or "63" in str(r.get("value"))]
    assert len(vol_readouts) >= 1
    assert str(vol_readouts[0].get("value")) == "63"


def test_cuboid_cube_production_route_disabled_by_default(monkeypatch):
    """Khi GEOMETRY_COMPILER_MODE không bật (hoặc mặc định LLM_ONLY), compiler bị DISABLED."""
    _, payload = _cuboid_p01_payload()
    contract = build_request_contract(payload, domain="hinh_hoc")

    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    qd = quyet_dinh_dinh_tuyen(contract)
    assert qd.decision == "DISABLED"


def test_payload_contains_no_answers_or_grading_labels():
    """Chứng minh payload không chứa expected answer, expected volume, hay grading labels."""
    for fn, forbidden in [
        (_cuboid_p01_payload, ["60", "expected_answer", "grading"]),
        (_cube_p01_payload, ["64", "expected_answer", "grading"]),
        (_square_prism_control_payload, ["63", "expected_answer", "grading"]),
    ]:
        _, payload = fn()
        import json
        dumped = json.dumps(payload)
        for term in forbidden:
            assert term not in dumped, f"Payload vi phạm: chứa {term}"
