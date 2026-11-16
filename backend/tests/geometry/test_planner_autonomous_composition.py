# -*- coding: utf-8 -*-
"""Run `planner-autonomous-composition-and-search-efficiency`: tests for generalized autonomous
composition, within-goal & cross-rule intermediate reuse, precondition-first search pruning,
`ask_distance_lines`, `MG9` root-cause & fail-closed boundary, negative/cycle/tamper safety,
`output-policy/1` Mode A isolation, locked extraction fingerprints, and `141 -> 142` cache invalidation.
"""
from __future__ import annotations

import copy
import json
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai import fact_extraction, function_calling
from app.ai.adaptive_input_router import route_text_input
from app.ai.hybrid_offline import (
    hybrid_offline_policy,
    prepare_local_first_hybrid,
    resolve_hybrid_gemini_model,
    run_hybrid_offline,
)
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
from app.ai.typed_fact_next_extraction import ReplayExtractor, typed_fact_next_surface_fingerprint
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.simulation.geometry_functions import (
    engine,
    planner,
    typed_fact_next as TN,
    typed_fact_next_bridge as TB,
)
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS

_RM_TOOLS = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools"
)
if str(_RM_TOOLS) not in sys.path:
    sys.path.insert(0, str(_RM_TOOLS))
import reasoning_matrix as RM  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
RM_CASES = {c["id"]: c for c in RM.build_cases()}


# ── Shared Geometry Builders & Independent Exact Fraction Oracles ────────────────────────────────────────────────────

def _pyr_payload(
    txt: str,
    desc: list[dict],
    goals: list[dict],
    *,
    sa: str = "2",
    side: str = "2",
    secs: tuple[dict, ...] = (),
) -> dict:
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": txt,
        "length_unit": "1",
        "solids": [
            {"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}
        ],
        "premises": [
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": side},
                "quote": f"đáy ABCD là hình vuông cạnh {side}",
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
                "args": {"segment": ["S", "A"], "value": sa},
                "quote": f"SA = {sa}",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "derived_sections": list(secs),
        "described_points": desc,
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}
        ],
        "math_goals": goals,
    }


def _prism_payload(txt: str, desc: list[dict], goals: list[dict]) -> dict:
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": txt,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                "solid_id": "s1",
            },
            {
                "kind": "right_angle",
                "args": {"vertex": "A", "rays": ["B", "C"]},
                "quote": "đáy ABC là tam giác vuông tại A",
                "solid_id": "s1",
            },
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"}, "quote": "AA' = 2", "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "described_points": desc,
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "math_goals": goals,
    }


def _cube_payload(txt: str, desc: list[dict], goals: list[dict]) -> dict:
    q = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2"
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": txt,
        "length_unit": "1",
        "solids": [
            {"solid_id": "s1", "solid_type": "prism", "notation": "ABCD.A'B'C'D'", "quote": q}
        ],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, "quote": q, "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "2"}, "quote": q, "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"}, "quote": q, "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "described_points": desc,
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": q}],
        "math_goals": goals,
    }


def _tet_payload(txt: str, desc: list[dict], goals: list[dict]) -> dict:
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": txt,
        "length_unit": "1",
        "solids": [
            {"solid_id": "s1", "solid_type": "pyramid", "notation": "A.BCD", "quote": "Cho tứ diện đều ABCD"}
        ],
        "premises": [
            {"kind": "regular_pyramid", "args": {"apex": "A", "base": ["B", "C", "D"]}, "quote": "Cho tứ diện đều ABCD cạnh 2", "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["B", "C", "D"], "side": "2"}, "quote": "Cho tứ diện đều ABCD cạnh 2", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "Cho tứ diện đều ABCD cạnh 2", "solid_id": "s1"},
        ],
        "relations": [],
        "derived_sections": [],
        "described_points": desc,
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho tứ diện đều ABCD"}],
        "math_goals": goals,
    }


def _run_gold(text: str, payload: dict) -> tuple[dict, dict, dict[str, str]]:
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route, env = out.response["route_d"], out.response["envelope"]
    answers = {k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()} if route["status"] == "SERVED" else {}
    return route, env, answers


def _assert_oracle_and_continuity(
    text: str,
    payload: dict,
    expected: dict[str, tuple[str, Fraction]],
    *,
    expected_cls: str | None = None,
    check_nl: bool = False,
) -> tuple[dict, dict]:
    route, env, answers = _run_gold(text, payload)
    assert route["status"] == "SERVED", (env.get("reason_code"), env)
    assert env.get("result") is None, "output-policy/1 Mode A must hide exact answer in default envelope"
    for gid, (meas, want) in expected.items():
        got = Fraction(answers[gid]) if meas == "cos2" else RM.coef_square(answers[gid])
        assert got == want, (gid, answers[gid], want)
    assert validate_construction_continuity(env["scene3d"]) == []
    if expected_cls is not None:
        assert route["planner"]["search_telemetry"]["classification"] == expected_cls
    if check_nl:
        lp = parse_geometry_problem_locally(text)
        assert lp.status == LOCAL_PARSE_COMPLETE, (lp.status, lp.reason_code)
        nr = route_text_input(text, allow_live_ai=False)
        nrd, nenv = nr.response["route_d"], nr.response["envelope"]
        assert nrd["status"] == "SERVED", (nenv.get("reason_code"), nenv)
        assert nenv.get("result") is None
        nl_ans = {k: v["coef"] for k, v in (nrd.get("answer_exact") or {}).items()}
        assert nl_ans == answers
        assert validate_construction_continuity(nenv["scene3d"]) == []
    return route, env


def _sub(a: tuple[Fraction, ...], b: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return tuple(x - y for x, y in zip(a, b))


def _dot(u: tuple[Fraction, ...], v: tuple[Fraction, ...]) -> Fraction:
    return sum(a * b for a, b in zip(u, v))


def _cross(u: tuple[Fraction, ...], v: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _skew_dist_sq(p1: tuple, p2: tuple, q1: tuple, q2: tuple) -> Fraction:
    """Exact squared distance between two skew lines in Euclidean coordinates."""
    u = _sub(tuple(Fraction(x) for x in p2), tuple(Fraction(x) for x in p1))
    v = _sub(tuple(Fraction(x) for x in q2), tuple(Fraction(x) for x in q1))
    n = _cross(u, v)
    num = _dot(_sub(tuple(Fraction(x) for x in q1), tuple(Fraction(x) for x in p1)), n)
    return (num * num) / _dot(n, n)


# ── 1. Novel Autonomous Multi-Step Composition Across Solid Families ─────────────────────────────────────────────────

def test_novel_ask_distance_lines_across_solids_with_derived_endpoints():
    # Pyramid S.ABCD (side 2, SA = 2): S=(0,0,2), M1=mid(BC)=(2,1,0), C=(2,2,0), D=(0,2,0)
    t_b = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "
    q1 = "Tính khoảng cách giữa đường thẳng nối S với trung điểm của BC và đường thẳng CD"
    want1 = _skew_dist_sq((0, 0, 2), (2, 1, 0), (2, 2, 0), (0, 2, 0))
    assert want1 == Fraction(4, 5)
    _assert_oracle_and_continuity(
        t_b + q1 + ".",
        _pyr_payload(
            t_b + q1 + ".",
            [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["S", "@m1"], "line2": ["C", "D"]}, "quote": q1, "solid_id": "s1"}],
        ),
        {"q1": ("d2", want1)},
    )

    # Pyramid S.ABCD with @p1 = orthogonal_projection(A, (SBD)) = (2/3, 2/3, 2/3)
    q2 = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (SBD) với D và đường thẳng nối S với trung điểm của BC"
    want2 = _skew_dist_sq((Fraction(2, 3), Fraction(2, 3), Fraction(2, 3)), (0, 2, 0), (0, 0, 2), (2, 1, 0))
    assert want2 == Fraction(2, 25)
    _assert_oracle_and_continuity(
        t_b + q2 + ".",
        _pyr_payload(
            t_b + q2 + ".",
            [
                {"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "D"], "quote": "hình chiếu vuông góc của A lên (SBD)"},
                {"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "D"], "line2": ["S", "@m1"]}, "quote": q2, "solid_id": "s1"}],
        ),
        {"q1": ("d2", want2)},
    )

    # Right triangular prism ABC.A'B'C': AB=3, AC=4, AA'=2
    t_pr = "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 2. "
    q_pr = "Tính khoảng cách giữa đường thẳng nối A' với trung điểm của BC và đường thẳng B'C'"
    want_pr = _skew_dist_sq((0, 0, 2), (Fraction(3, 2), 2, 0), (3, 0, 2), (0, 4, 2))
    assert want_pr == Fraction(144, 61)
    _assert_oracle_and_continuity(
        t_pr + q_pr + ".",
        _prism_payload(
            t_pr + q_pr + ".",
            [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A'", "@m1"], "line2": ["B'", "C'"]}, "quote": q_pr, "solid_id": "s1"}],
        ),
        {"q1": ("d2", want_pr)},
    )

    # Cube ABCD.A'B'C'D' side 2: @p1 = proj(A, (A'BD)) = (2/3, 2/3, 2/3), @m1 = mid(CD') = (1, 2, 1)
    t_cu = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. "
    q_cu = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (A'BD) với C' và đường thẳng nối B với trung điểm của CD'"
    want_cu = _skew_dist_sq((Fraction(2, 3), Fraction(2, 3), Fraction(2, 3)), (2, 2, 2), (2, 0, 0), (1, 2, 1))
    assert want_cu == Fraction(2, 7)
    _assert_oracle_and_continuity(
        t_cu + q_cu + ".",
        _cube_payload(
            t_cu + q_cu + ".",
            [
                {"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["A'", "B", "D"], "quote": "hình chiếu vuông góc của A lên (A'BD)"},
                {"described_id": "m1", "kind": "midpoint", "segment": ["C", "D'"], "quote": "trung điểm của CD'"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "C'"], "line2": ["B", "@m1"]}, "quote": q_cu, "solid_id": "s1"}],
        ),
        {"q1": ("d2", want_cu)},
    )

    # Regular tetrahedron ABCD side 2: @p1 = proj(A, (BCD)), @m1 = mid(AD), d^2(B-@p1, C-@m1) = 8/35
    t_tet = "Cho tứ diện đều ABCD cạnh 2. "
    q_tet = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (BCD) với B và đường thẳng nối C với trung điểm của AD"
    _assert_oracle_and_continuity(
        t_tet + q_tet + ".",
        _tet_payload(
            t_tet + q_tet + ".",
            [
                {"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["B", "C", "D"], "quote": "hình chiếu vuông góc của A lên (BCD)"},
                {"described_id": "m1", "kind": "midpoint", "segment": ["A", "D"], "quote": "trung điểm của AD"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "B"], "line2": ["C", "@m1"]}, "quote": q_tet, "solid_id": "s1"}],
        ),
        {"q1": ("d2", Fraction(8, 35))},
    )


def test_novel_discovered_function_compositions_over_existing_primitives():
    t_b = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "

    # 1. intersect_line_line on two derived coplanar medians of face SBC (wording without "hai") -> G(SBC), z = 2/3
    q_ill = "Tính khoảng cách từ giao điểm của đường thẳng nối S với trung điểm của BC và đường thẳng nối B với trung điểm của SC đến (ABCD)"
    _assert_oracle_and_continuity(
        t_b + q_ill + ".",
        _pyr_payload(
            t_b + q_ill + ".",
            [
                {"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"},
                {"described_id": "m2", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"},
                {"described_id": "x1", "kind": "intersect_line_line", "line1": ["S", "@m1"], "line2": ["B", "@m2"], "quote": "giao điểm của đường thẳng nối S với trung điểm của BC và đường thẳng nối B với trung điểm của SC"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["A", "B", "C", "D"]}, "quote": q_ill, "solid_id": "s1"}],
        ),
        {"q1": ("d2", Fraction(4, 9))},
        expected_cls="DISCOVERED_FUNCTION_COMPOSITION",
    )

    # 2. orthogonal_projection_line from @orthocenter(SBD)=(2/3,2/3,2/3) onto derived line S-@m1(BC) -> z = 26/27
    q_opl = "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBD lên đường thẳng nối S với trung điểm của BC đến mặt phẳng (ABCD)"
    _assert_oracle_and_continuity(
        t_b + q_opl + ".",
        _pyr_payload(
            t_b + q_opl + ".",
            [
                {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
                {"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"},
                {"described_id": "f1", "kind": "orthogonal_projection_line", "point": "@o1", "line": ["S", "@m1"], "quote": "hình chiếu vuông góc của trực tâm của tam giác SBD lên đường thẳng nối S với trung điểm của BC"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@f1", "plane": ["A", "B", "C", "D"]}, "quote": q_opl, "solid_id": "s1"}],
        ),
        {"q1": ("d2", Fraction(26 * 26, 27 * 27))},
        expected_cls="DISCOVERED_FUNCTION_COMPOSITION",
    )

    # 3. midpoint combining @orthocenter(SBD)=(2/3,2/3,2/3) with vertex C=(2,2,0) -> (4/3,4/3,1/3), d to (SAB) = 4/3
    q_mid = "Tính khoảng cách từ trung điểm của đoạn nối trực tâm của tam giác SBD với C đến (SAB)"
    _assert_oracle_and_continuity(
        t_b + q_mid + ".",
        _pyr_payload(
            t_b + q_mid + ".",
            [
                {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
                {"described_id": "m1", "kind": "midpoint", "segment": ["@o1", "C"], "quote": "trung điểm của đoạn nối trực tâm của tam giác SBD với C"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m1", "plane": ["S", "A", "B"]}, "quote": q_mid, "solid_id": "s1"}],
        ),
        {"q1": ("d2", Fraction(16, 9))},
        expected_cls="DISCOVERED_FUNCTION_COMPOSITION",
    )


# ── 2. Within-Goal Sibling Reuse, Deduplication & Cross-Rule Reuse ───────────────────────────────────────────────────

def _assert_no_duplicate_points_or_h4(scene3d: dict) -> None:
    point_objs = [o for o in scene3d["objects"] if o.get("type") == "point3"]
    assert "H4" not in {o["id"] for o in point_objs}
    coords = [tuple(o["xyz"]) for o in point_objs]
    assert len(coords) == len(set(coords)), f"coinciding duplicate points detected: {[(o['id'], o['xyz']) for o in point_objs]}"


def test_within_goal_sibling_reuse_euler_segment_and_angle():
    t3 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "

    # T1: Euler segment length between @orthocenter(SBD) and @circumcenter(SBD) -> 5*sqrt(11)/22 on Gold & NL
    q_t1 = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD"
    r_t1, env_t1 = _assert_oracle_and_continuity(
        t3 + q_t1 + ".",
        _pyr_payload(
            t3 + q_t1 + ".",
            [
                {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
                {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@o1", "@c1"]}, "quote": q_t1, "solid_id": "s1"}],
            sa="3",
        ),
        {"q1": ("d2", Fraction(25 * 11, 22 * 22))},
        check_nl=True,
    )
    tel_t1 = r_t1["planner"]["search_telemetry"]
    assert tel_t1["plan_cost"] == 8
    assert tel_t1["reused_intermediates"] >= 2
    _assert_no_duplicate_points_or_h4(env_t1["scene3d"])

    # E1: Euler line angle with (ABCD) -> cos^2 = 2/11 on Gold
    q_e1 = "Tính góc giữa đường thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD và mặt phẳng (ABCD)"
    r_e1, env_e1 = _assert_oracle_and_continuity(
        t3 + q_e1 + ".",
        _pyr_payload(
            t3 + q_e1 + ".",
            [
                {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"},
                {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "angle", "target": {"line": ["@o1", "@c1"], "plane": ["A", "B", "C", "D"]}, "quote": q_e1, "solid_id": "s1"}],
            sa="3",
        ),
        {"q1": ("cos2", Fraction(2, 11))},
    )
    tel_e1 = r_e1["planner"]["search_telemetry"]
    assert tel_e1["plan_cost"] == 8
    assert tel_e1["reused_intermediates"] >= 2
    _assert_no_duplicate_points_or_h4(env_e1["scene3d"])


def test_cross_rule_intermediate_reuse_and_source_gate_grounding():
    t2 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "

    # T3: @orthocenter(SBD) reused directly by distance(point, line BD) on Gold & NL
    q_t3 = "Tính khoảng cách từ trực tâm của tam giác SBD đến đường thẳng BD"
    r_t3, _ = _assert_oracle_and_continuity(
        t2 + q_t3 + ".",
        _pyr_payload(
            t2 + q_t3 + ".",
            [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@o1", "line": ["B", "D"]}, "quote": q_t3, "solid_id": "s1"}],
        ),
        {"q1": ("d2", Fraction(6, 9))},
        check_nl=True,
    )
    assert r_t3["planner"]["search_telemetry"]["reused_intermediates"] >= 3

    # T4: MAT_VUONG_DUONG ((P) through A perp SB) reused by distance(A, SB)
    t_t4 = t2 + "Gọi (P) là mặt phẳng đi qua A và vuông góc với SB. Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính khoảng cách từ A đến SB."
    r_t4, _ = _assert_oracle_and_continuity(
        t_t4,
        _pyr_payload(
            t_t4,
            [],
            [
                {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)", "solid_id": "s1"},
                {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "tính khoảng cách từ A đến SB", "solid_id": "s1"},
            ],
            secs=({"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "through_point_perpendicular_line", "through_point": "A", "perpendicular_line": ["S", "B"], "stated_intersections": [], "quote": "Gọi (P) là mặt phẳng đi qua A và vuông góc với SB"},),
        ),
        {"q1": ("d2", Fraction(9, 2)), "q2": ("d2", Fraction(2))},
    )
    assert r_t4["planner"]["search_telemetry"]["reused_intermediates"] >= 1

    # T5: MAT_RANG_BUOC ((P) through A, C perp (SBD)) normal reused by @orthogonal_projection(A, (SBD)) on Gold & NL
    t_t5 = (
        t2
        + "Mặt phẳng (P) đi qua A, C và vuông góc với (SBD). "
        + "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó. "
        + "Tính khoảng cách từ hình chiếu vuông góc của A lên (SBD) đến mặt phẳng (ABCD)."
    )
    r_t5, _ = _assert_oracle_and_continuity(
        t_t5,
        _pyr_payload(
            t_t5,
            [{"described_id": "h1", "kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "D"], "quote": "hình chiếu vuông góc của A lên (SBD)"}],
            [
                {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó", "solid_id": "s1"},
                {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["A", "B", "C", "D"]}, "quote": "Tính khoảng cách từ hình chiếu vuông góc của A lên (SBD) đến mặt phẳng (ABCD)", "solid_id": "s1"},
            ],
            secs=({
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": ["A", "C"]},
                    {"kind": "perpendicular_to_plane", "operands": ["S", "B", "D"]},
                ],
                "stated_intersections": [],
                "quote": "Mặt phẳng (P) đi qua A, C và vuông góc với (SBD)",
            },),
        ),
        {"q1": ("d2", Fraction(8)), "q2": ("d2", Fraction(4, 9))},
        check_nl=True,
    )
    assert r_t5["planner"]["search_telemetry"]["reused_intermediates"] >= 1

    # DINH_CAT_CANH (`reuse_through_point`) reusing foot from orthogonal_projection_line(B, SC)
    t_dcc = t2 + "Mặt phẳng (P) đi qua hình chiếu vuông góc của B lên SC và song song với (ABCD). Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)."
    r_dcc, _ = _assert_oracle_and_continuity(
        t_dcc,
        _pyr_payload(
            t_dcc,
            [{"described_id": "f1", "kind": "orthogonal_projection_line", "point": "B", "line": ["S", "C"], "quote": "hình chiếu vuông góc của B lên SC"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)", "solid_id": "s1"}],
            secs=({
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "@f1",
                "parallel_plane": ["A", "B", "C"],
                "stated_intersections": [],
                "quote": "Mặt phẳng (P) đi qua hình chiếu vuông góc của B lên SC và song song với (ABCD)",
            },),
        ),
        {"q1": ("d2", Fraction(256, 81))},
    )
    assert r_dcc["planner"]["search_telemetry"]["reused_intermediates"] >= 1


# ── 3. MG9 Root-Cause & Fail-Closed Contract Preservation ─────────────────────────────────────────────────────────────

def test_mg9_precondition_pruning_succeeds_in_planner_and_fails_closed_at_ir_memory_budget():
    assert MAX_MEMORY_DECLARATIONS == 32
    assert planner.MAX_EFFECT_CANDIDATES == 48

    mg9 = RM_CASES["MG9"]
    v2 = TN.TypedFactNextPayloadV2.model_validate(mg9["payload"])
    bridged = TB.bridge_v2(v2)
    plan = planner.lap_ke_hoach(bridged)
    tel = plan.search_telemetry
    assert tel["candidate_evaluations"] == 33 <= planner.MAX_EFFECT_CANDIDATES
    assert tel["pruned_nodes"] == 21
    assert tel["explored_states"] == 72
    assert tel["plan_cost"] == 13

    route, env, _ = _run_gold(mg9["text"], mg9["payload"])
    assert route["status"] == "REFUSED"
    assert env["reason_code"] == "IR_MEMORY_BUDGET_EXCEEDED"


# ── 4. Negative, Degenerate, Cycle, Tamper, Budget & Surface/Policy Safety ────────────────────────────────────────────

def test_negative_degenerate_cycle_tamper_and_budget_fail_closed(monkeypatch):
    t2 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "

    # 1. Parallel lines in intersect_line_line -> PARALLEL_NO_INTERSECTION
    q_par = "Tính khoảng cách từ giao điểm của AB và CD đến (SAD)"
    r_par, e_par, _ = _run_gold(
        t2 + q_par + ".",
        _pyr_payload(
            t2 + q_par + ".",
            [{"described_id": "x1", "kind": "intersect_line_line", "line1": ["A", "B"], "line2": ["C", "D"], "quote": "giao điểm của AB và CD"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["S", "A", "D"]}, "quote": q_par, "solid_id": "s1"}],
        ),
    )
    assert r_par["status"] == "REFUSED" and e_par["reason_code"] == "PARALLEL_NO_INTERSECTION"

    # 2. Skew non-intersecting lines in intersect_line_line -> SKEW_NO_INTERSECTION
    q_sk = "Tính khoảng cách từ giao điểm của SB và CD đến (SAD)"
    r_sk, e_sk, _ = _run_gold(
        t2 + q_sk + ".",
        _pyr_payload(
            t2 + q_sk + ".",
            [{"described_id": "x1", "kind": "intersect_line_line", "line1": ["S", "B"], "line2": ["C", "D"], "quote": "giao điểm của SB và CD"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["S", "A", "D"]}, "quote": q_sk, "solid_id": "s1"}],
        ),
    )
    assert r_sk["status"] == "REFUSED" and e_sk["reason_code"] == "SKEW_NO_INTERSECTION"

    # 3. Cyclic described_points -> DEPENDENCY_CYCLE
    q_cyc = "Tính khoảng cách từ trung điểm của đoạn nối nó với C đến (SAD)"
    r_cyc, e_cyc, _ = _run_gold(
        t2 + q_cyc + ".",
        _pyr_payload(
            t2 + q_cyc + ".",
            [
                {"described_id": "m1", "kind": "midpoint", "segment": ["@m2", "C"], "quote": "trung điểm của đoạn nối nó với C"},
                {"described_id": "m2", "kind": "midpoint", "segment": ["@m1", "D"], "quote": "trung điểm của đoạn nối nó với C"},
            ],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m1", "plane": ["S", "A", "D"]}, "quote": q_cyc, "solid_id": "s1"}],
        ),
    )
    assert r_cyc["status"] == "REFUSED" and e_cyc["reason_code"] == "DEPENDENCY_CYCLE"

    # 4. Identical line1 == line2 in ask_distance_lines -> AUXILIARY_RULE_MISMATCH
    q_eq = "Tính khoảng cách giữa đường thẳng nối A với trung điểm của BC và đường thẳng nối A với trung điểm của BC"
    r_eq, e_eq, _ = _run_gold(
        t2 + q_eq + ".",
        _pyr_payload(
            t2 + q_eq + ".",
            [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}],
            [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A", "@m1"], "line2": ["A", "@m1"]}, "quote": q_eq, "solid_id": "s1"}],
        ),
    )
    assert r_eq["status"] == "REFUSED" and e_eq["reason_code"] == "AUXILIARY_RULE_MISMATCH"

    # 5. Collinear points in orthogonal_projection plane -> COLLINEAR_POINTS / DEGENERATE_POINTS
    q_col = "Gọi M là trung điểm của AB. Tính khoảng cách từ hình chiếu vuông góc của C lên (ABM) đến (SAD)"
    p_col = _pyr_payload(
        t2 + q_col + ".",
        [{"described_id": "p1", "kind": "orthogonal_projection", "point": "C", "plane": ["A", "B", "M"], "quote": "hình chiếu vuông góc của C lên (ABM)"}],
        [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@p1", "plane": ["S", "A", "D"]}, "quote": q_col, "solid_id": "s1"}],
    )
    p_col["premises"].append({"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"})
    r_col, e_col, _ = _run_gold(t2 + q_col + ".", p_col)
    assert r_col["status"] == "REFUSED" and e_col["reason_code"] in {"COLLINEAR_POINTS", "DEGENERATE_POINTS"}

    # 6. Ungrounded quote tamper & tampered auxiliary certificate & budget exhaustion
    pa3 = copy.deepcopy(RM_CASES["PA3"])
    pa3["payload"]["described_points"][0]["quote"] = "trung điểm của BC"
    r_ungr, e_ungr, _ = _run_gold(RM_CASES["PA3"]["text"], pa3["payload"])
    assert r_ungr["status"] == "REFUSED" and e_ungr["reason_code"] in {"QUOTE_NOT_IN_SOURCE", "SOURCE_OBJECT_MISMATCH"}

    real_plan = planner.lap_ke_hoach
    c_re10 = RM_CASES["RE10"]

    def _tamper(*a, **k):
        pl = real_plan(*a, **k)
        for cert in pl.auxiliary:
            if cert.get("rule") == "effect-chain" and cert.get("operand", {}).get("nested"):
                cert["operand"]["nested"]["points"] = ["S", "B", "C"]
        return pl

    with monkeypatch.context() as m:
        m.setattr(planner, "lap_ke_hoach", _tamper)
        r_tmp, e_tmp, _ = _run_gold(c_re10["text"], c_re10["payload"])
        assert r_tmp["status"] == "REFUSED" and e_tmp["reason_code"] in {"AUXILIARY_RULE_MISMATCH", "ENGINE_SELF_CHECK_FAILED"}

    with monkeypatch.context() as m:
        m.setattr(planner, "MAX_EFFECT_CANDIDATES", 4)
        r_cap, e_cap, _ = _run_gold(c_re10["text"], c_re10["payload"])
        assert r_cap["status"] == "REFUSED" and e_cap["reason_code"] == "PLAN_TOO_LARGE"


def test_student_mode_a_no_machine_id_leaks_and_locked_surface_fingerprints():
    t3 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
    q_t1 = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD."
    nr = route_text_input(t3 + q_t1, allow_live_ai=False)
    env = nr.response["envelope"]
    assert nr.response["route_d"]["status"] == "SERVED"
    assert env.get("result") is None

    forbidden_tokens = ("@o1", "@c1", "sec1_normal1", "__line_endpoints__")
    for obj in env["scene3d"]["objects"]:
        for fld in ("label", "display_label"):
            val = str(obj.get(fld) or "")
            assert not any(tok in val for tok in forbidden_tokens), (obj["id"], fld, val)
    for ev in env["scene3d"]["events"]:
        for fld in ("display_label", "learner_text", "explanation"):
            val = str(ev.get(fld) or "")
            assert not any(tok in val for tok in forbidden_tokens), (ev.get("step_index"), fld, val)

    assert function_calling.surface_fingerprint() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    assert fact_extraction.surface_fingerprint("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert fact_extraction.surface_fingerprint("v3") == "4bff35bbf690a9973b2b7834019b908d507bbbb4277928e36d12dcff657e226f"
    assert typed_fact_next_surface_fingerprint() == "33197a45e0620d94a669047b47907479d1e7f07b1dc76e7c6abd75ada7a6df14"


# ── 5. Route D `/api/analyze` SimulationCache `141:route-d` -> `142:route-d` Invalidation ─────────────────────────────

def test_stale_141_route_d_cache_row_is_invalidated_and_recomputed_under_142(monkeypatch):
    assert M.CACHE_VERSION == "144"
    assert M.ROUTE_D_CACHE_POLICY == "144:route-d"

    t_t1 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
        "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD."
    )
    key = prepare_local_first_hybrid(t_t1, model=resolve_hybrid_gemini_model()).cache_key
    stale_envelope = {
        "schema_version": next(iter(M.SUPPORTED_VERSIONS)),
        "envelope": {
            "status": "ready",
            "simulation_id": "generic.semantic_program",
            "domain": "solid_geometry",
            "visual_mode": "3d",
            "scene3d": {"objects": [{"id": "STALE_H4_MARKER", "type": "point3"}], "events": []},
        },
        "route_d": {"status": "SERVED", "planner": {"calls": [{"id": f"c{i}"} for i in range(10)]}},
    }

    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text=t_t1,
                simulation_id="generic.semantic_program",
                envelope_json=json.dumps(stale_envelope, ensure_ascii=False),
                dsl_version=next(iter(M.SUPPORTED_VERSIONS)),
                policy_version="141:route-d",
            )
        )
        s.commit()

    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    try:
        from tests.route_client import sign_in

        with TestClient(M.app) as client:
            sign_in(client)
            res = client.post("/api/analyze", json={"input": {"type": "text", "content": t_t1}})
        assert res.status_code == 200
        body = res.json()
        assert body["route_d"]["status"] == "SERVED"
        obj_ids = {o["id"] for o in body["envelope"]["scene3d"]["objects"]}
        assert "STALE_H4_MARKER" not in obj_ids
        assert "H4" not in obj_ids
        assert body["route_d"]["planner"]["search_telemetry"]["plan_cost"] == 8
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
