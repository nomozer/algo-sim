# -*- coding: utf-8 -*-
"""Regression & fail-closed suite for campaign `student-ready-geometry-simulation-input-reliability`.

Covers:
1. Local-first extraction -> `TypedFactNext /2` -> `Planner /26` -> `Exact Kernel /24` -> `Adapter /4` -> `Scene3D`
   on promoted VMMU cases (`vmmu_r254`, `vmmu_r277`, `vmmu_r488`), singular named `point_reflection`,
   and unnamed `@id` projection target in premise.
2. Fail-closed negatives: non-coplanar 4-gon sub-pyramid base, apex lying on base plane, disjoint second solid,
   degenerate `point == center` reflection, `@id` in forbidden `PlaneConstraintSpec` / multi-point premise slot,
   `vmmu_r491` (`FREE_POINT_UNDERDETERMINED`), `vmmu_r266` (`EXACT_DOMAIN_EXCEEDED`), `vmmu_r513` (`MISSING_DIMENSION`).
3. Invariance of all 4 locked Gemini extraction surfaces and `144:route-d -> 145:route-d` SQLite cache invalidation.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app import main as M
from app.ai import fact_extraction, function_calling
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.ai.local_geometry_parser import (
    LOCAL_PARSE_COMPLETE,
    LOCAL_PARSE_PARTIAL,
    parse_geometry_problem_locally,
)
from app.ai.typed_fact_next_extraction import typed_fact_next_surface_fingerprint
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.typed_fact_next import (
    PlaneConstraintSpec,
    TypedFactNextValidationError,
)
from tests.route_client import sign_in

ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs"

LOCKED_SURFACE_HASHES = {
    "function_calling": "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25",
    "fact_extraction_flat": "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a",
    "fact_extraction_v3": "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f",
    "typed_fact_next": "33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14",
}

_FORBIDDEN_ANSWER_KEYS = ("answers", "answer", "exact_answers", "numeric_answers")


def _load_real27_map() -> dict[str, str]:
    p25 = RUNS_DIR / "controlled-vision-real-image-validation" / "new_in_scope_image_manifest.json"
    p2 = RUNS_DIR / "local-semantic-source-gate-reliability" / "fresh_external_manifest.json"
    items = json.loads(p25.read_text(encoding="utf-8"))["items"] + json.loads(
        p2.read_text(encoding="utf-8")
    )["items"]
    return {it["case_id"]: it["statement"] for it in items}


def _assert_served_local_and_api(
    problem_text: str,
    expected_answers: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> dict:
    parsed = parse_geometry_problem_locally(problem_text)
    assert parsed.status == LOCAL_PARSE_COMPLETE, (parsed.status, parsed.fallback_reason)
    routed = run_typed_fact_next_v2_route(parsed.payload)
    assert routed.status == "SERVED", (routed.status, routed.code, routed.reason)
    assert routed.answers == expected_answers
    assert routed.scene3d and routed.scene3d.get("objects")
    assert validate_construction_continuity(routed.scene3d) == []

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HYBRID_LOCAL_FIRST", "1")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    with TestClient(M.app) as raw_client:
        client = sign_in(raw_client)
        res = client.post("/api/analyze", json={"input": {"type": "text", "content": problem_text}})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("schema_version") == "hybrid-route-d-simulation/4"
    env = body["envelope"]
    assert env["status"] == "ok", env
    sc = env.get("scene3d") or {}
    assert len(sc.get("objects") or []) > 0
    assert len((sc.get("formation") or {}).get("steps") or []) > 0
    assert validate_construction_continuity(sc) == []
    for k in _FORBIDDEN_ANSWER_KEYS:
        assert k not in body
        assert k not in env
    return body


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("vmmu_r254", {"q1": "9a³√13/2"}),
        ("vmmu_r277", {"q1": "8a³"}),
        ("vmmu_r488", {"q1": "a³/3"}),
    ],
)
def test_step3_real27_promotions_served_exact(case_id: str, expected: dict[str, str], monkeypatch):
    rmap = _load_real27_map()
    _assert_served_local_and_api(rmap[case_id], expected, monkeypatch)


def test_step3_singular_point_reflection_served(monkeypatch):
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a. "
        "Biết SA vuông góc với mặt phẳng (ABCD) và SA = 2a. "
        "Gọi D' là điểm đối xứng với D qua C. Tính thể tích khối chóp S.ABD'."
    )
    _assert_served_local_and_api(text, {"q1": "4a³/3"}, monkeypatch)


def test_step3_unnamed_at_id_projection_target_in_premise_served(monkeypatch):
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3a. "
        "Hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với trọng tâm của tam giác ABC. "
        "Biết SA = 2a. Tính thể tích khối chóp S.ABC."
    )
    _assert_served_local_and_api(text, {"q1": "3a³√3/4"}, monkeypatch)


def _base_v2_payload(
    problem_text: str,
    *,
    extra_premises: list[dict] | None = None,
    solids_extra: list[dict] | None = None,
    goals: list[dict] | None = None,
    described_points: list[dict] | None = None,
) -> dict:
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            },
            *(solids_extra or []),
        ],
        "premises": [
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "2a"},
                "quote": "đáy ABCD là hình vuông cạnh 2a",
                "solid_id": "s1",
            },
            {
                "kind": "perpendicular_line_plane",
                "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                "quote": "SA vuông góc với (ABCD)",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["S", "A"], "value": "2a"},
                "quote": "SA = 2a",
                "solid_id": "s1",
            },
            *(extra_premises or []),
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}
        ],
        "math_goals": goals
        or [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": "s1"},
                "solid_id": "s1",
                "quote": "Tính thể tích khối chóp S.ABCD.",
            }
        ],
    }
    if described_points is not None:
        payload["described_points"] = described_points
    return payload


def test_step3_negative_non_coplanar_sub_pyramid_base_refused():
    # M is midpoint of SD => A, B, M, D are non-coplanar for sub-pyramid C.ABMD
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a. "
        "SA vuông góc với (ABCD). SA = 2a. "
        "Gọi M là trung điểm của SD. Tính thể tích khối chóp C.ABMD."
    )
    parsed = parse_geometry_problem_locally(text)
    assert parsed.status == LOCAL_PARSE_COMPLETE, (parsed.status, parsed.fallback_reason)
    r = run_typed_fact_next_v2_route(parsed.payload)
    assert r.status != "SERVED"
    assert r.code in {"NON_COPLANAR_POINTS", "DEGENERATE_SOLID", "INCONSISTENT_FACTS"}

    # Explicit premise-declared solid C.ABMD must also hit Exact Kernel NON_COPLANAR_POINTS
    base_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 2a. "
        "Gọi M là trung điểm của SD. Xét khối chóp C.ABMD. Tính thể tích khối chóp C.ABMD."
    )
    payload = _base_v2_payload(
        base_text,
        extra_premises=[
            {
                "kind": "midpoint",
                "args": {"point": "M", "segment": ["S", "D"]},
                "quote": "Gọi M là trung điểm của SD",
                "solid_id": "s1",
            }
        ],
        solids_extra=[
            {"solid_id": "s2", "solid_type": "pyramid", "notation": "C.ABMD", "quote": "Xét khối chóp C.ABMD"}
        ],
        goals=[
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": "s2"},
                "solid_id": "s2",
                "quote": "Tính thể tích khối chóp C.ABMD",
            }
        ],
    )
    r_direct = run_typed_fact_next_v2_route(payload)
    assert r_direct.status != "SERVED"
    assert r_direct.code == "NON_COPLANAR_POINTS"


def test_step3_negative_apex_on_base_plane_refused():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 2a. "
        "Tính thể tích khối chóp A.BCD."
    )
    payload = _base_v2_payload(
        text,
        solids_extra=[
            {"solid_id": "s2", "solid_type": "pyramid", "notation": "A.BCD", "quote": "Tính thể tích khối chóp A.BCD."}
        ],
        goals=[
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": "s2"},
                "solid_id": "s2",
                "quote": "Tính thể tích khối chóp A.BCD.",
            }
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status != "SERVED"
    assert r.code in {"DEGENERATE_SOLID", "NON_COPLANAR_POINTS", "INCONSISTENT_FACTS", "BRIDGE_UNSUPPORTED_DERIVED_SOLID"}


def test_step3_negative_disjoint_second_solid_refused():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 2a. "
        "Cho hình chóp X.YZT. Tính thể tích khối chóp X.YZT."
    )
    payload = _base_v2_payload(
        text,
        solids_extra=[
            {"solid_id": "s2", "solid_type": "pyramid", "notation": "X.YZT", "quote": "Cho hình chóp X.YZT"}
        ],
        goals=[
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "volume",
                "target": {"solid_id": "s2"},
                "solid_id": "s2",
                "quote": "Tính thể tích khối chóp X.YZT.",
            }
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status != "SERVED"


def test_step3_negative_degenerate_point_reflection_same_point_and_center_refused():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 2a. "
        "Gọi D' là điểm đối xứng với D qua D. Tính thể tích khối chóp S.ABCD."
    )
    payload = _base_v2_payload(
        text,
        extra_premises=[
            {
                "kind": "point_reflection",
                "args": {"image": "D'", "point": "D", "center": "D"},
                "quote": "Gọi D' là điểm đối xứng với D qua D",
                "solid_id": "s1",
            }
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status != "SERVED"
    assert r.code in {
        "PRECONDITION_FAILED",
        "DEGENERATE_POINTS",
        "INCONSISTENT_FACTS",
        "INVALID_PREMISE_ARGS",
        "INVALID_TYPED_FACT_NEXT",
    }


def test_step3_negative_at_id_in_forbidden_plane_constraint_and_multi_point_premise_slot():
    with pytest.raises((ValidationError, TypedFactNextValidationError)):
        PlaneConstraintSpec(kind="parallel_to_line", operands=("@d1", "B"))

    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA vuông góc với (ABCD), SA = 2a. "
        "Gọi tâm tam giác ABC là G. Tính thể tích khối chóp S.ABCD."
    )
    payload = _base_v2_payload(
        text,
        described_points=[
            {"described_id": "d1", "kind": "centroid", "polygon": ["A", "B", "C"], "quote": "tâm tam giác ABC"}
        ],
        extra_premises=[
            {
                "kind": "perpendicular_lines",
                "args": {"line1": ["@d1", "B"], "line2": ["S", "A"]},
                "quote": "SA vuông góc với (ABCD)",
                "solid_id": "s1",
            }
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status != "SERVED"
    assert r.code in {"INVALID_QUALIFIED_REF", "INVALID_DESCRIBED_POINT", "INVALID_TYPED_FACT_NEXT", "INVALID_PREMISE_ARGS"}


def test_step3_vmmu_refusals_preserved(monkeypatch):
    rmap = _load_real27_map()

    p491 = parse_geometry_problem_locally(rmap["vmmu_r491"])
    assert p491.status == LOCAL_PARSE_PARTIAL
    assert p491.fallback_reason == "UNPARSED_FACT_CANDIDATE"

    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("HYBRID_LOCAL_FIRST", "1")
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "live")
    with TestClient(M.app) as raw_client:
        client = sign_in(raw_client)
        r491 = client.post("/api/analyze", json={"input": {"type": "text", "content": rmap["vmmu_r491"]}})
    assert r491.status_code == 503
    body491 = r491.json()
    assert body491["reason_code"] == "LIVE_AI_DISABLED"
    assert (body491.get("local_understanding") or {}).get("root_cause") == "FREE_POINT_UNDERDETERMINED"

    p266 = parse_geometry_problem_locally(rmap["vmmu_r266"])
    assert p266.status == LOCAL_PARSE_COMPLETE
    r266 = run_typed_fact_next_v2_route(p266.payload)
    assert r266.status == "REFUSED" and r266.code == "EXACT_DOMAIN_EXCEEDED"

    p513 = parse_geometry_problem_locally(rmap["vmmu_r513"])
    assert p513.status == LOCAL_PARSE_COMPLETE
    r513 = run_typed_fact_next_v2_route(p513.payload)
    assert r513.status == "REFUSED" and r513.code == "MISSING_DIMENSION"


def test_locked_gemini_extraction_surfaces_invariant():
    assert function_calling.surface_fingerprint() == LOCKED_SURFACE_HASHES["function_calling"]
    assert fact_extraction.surface_fingerprint("flat") == LOCKED_SURFACE_HASHES["fact_extraction_flat"]
    assert fact_extraction.surface_fingerprint("v3") == LOCKED_SURFACE_HASHES["fact_extraction_v3"]
    assert typed_fact_next_surface_fingerprint() == LOCKED_SURFACE_HASHES["typed_fact_next"]


def test_stale_144_route_d_cache_invalidated_and_recomputed_under_145(monkeypatch):
    assert M.CACHE_VERSION == "145"
    assert M.ROUTE_D_CACHE_POLICY == "145:route-d"

    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a. "
        "Biết SA vuông góc với mặt phẳng (ABCD) và SA = 2a. "
        "Gọi D' là điểm đối xứng với D qua C. Tính thể tích khối chóp S.ABD'."
    )
    key = prepare_local_first_hybrid(text, model=resolve_hybrid_gemini_model()).cache_key
    stale_env = {
        "schema_version": next(iter(M.SUPPORTED_VERSIONS)),
        "envelope": {
            "status": "ok",
            "simulation_id": "generic.semantic_program",
            "domain": "solid_geometry",
            "visual_mode": "3d",
            "scene3d": {"objects": [{"id": "STALE_144_MARKER", "type": "point3"}], "events": []},
        },
        "route_d": {"status": "SERVED", "planner": {"calls": []}},
    }
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text=text,
                simulation_id="generic.semantic_program",
                envelope_json=json.dumps(stale_env, ensure_ascii=False),
                dsl_version=next(iter(M.SUPPORTED_VERSIONS)),
                policy_version="144:route-d",
            )
        )
        s.commit()

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    try:
        with TestClient(M.app) as client:
            sign_in(client)
            res = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
        assert res.status_code == 200
        env = res.json()["envelope"]
        assert env["status"] == "ok"
        obj_ids = {o["id"] for o in env["scene3d"]["objects"]}
        assert "STALE_144_MARKER" not in obj_ids
        with SessionLocal() as s:
            row = s.query(SimulationCache).filter_by(key=key).first()
            assert row is not None
            assert row.policy_version == "145:route-d"
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
