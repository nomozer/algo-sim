# -*- coding: utf-8 -*-
"""Goal-Driven Planner & Generalization Verification suite (Phases 0, A, B & Section IX).

Covers:
- Phase 0.1: Mathematical check on `orthogonal_projection` & `off_plane(P, Q)` — valid in-plane point projections are not
  falsely refused at descriptor parsing when the downstream goal is non-degenerate.
- Family A: Goal-Only Multi-Step Discovery (point-to-line foot discovery, point-to-intersection-line discovery,
  constrained-plane normal witness discovery).
- Family B: Competing Candidate Plans, Precondition Pruning (`off_line`, `off_plane`), Cost Ranking & Search Telemetry
  (`candidate_count`, `explored_states`, `pruned_nodes`, `rejection_reasons`, `selected_plan`, `plan_cost`, `search_depth`).
- Family C: Implicit Auxiliary Construction Taxonomy (`SOURCE_EXPLICIT_SEQUENCE` vs `REGISTERED_DECOMPOSITION` vs
  `DISCOVERED_FUNCTION_COMPOSITION`).
- Family D: Shared Intermediate Results Across Multiple Goals (single construction, stable identity, distinct provenance,
  construction continuity).
- Family E: 13 Mandatory Negative, Degenerate & Adversarial Failure Modes (E.1–E.13), including E.9 where a valid
  in-plane projection coincides with the other endpoint of a measured segment (`DEGENERATE_POINTS`).
- Section IX: Ablation & Counterfactual Testing (Tests 1–5: Explicit vs Goal-Only, Remove Specialized Decomposition,
  Remove Required Producer with Fallback/Refusal, Competing Plans, Metamorphic Renaming & Scaling).
"""
from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction

import pytest

from app.ai.function_route import run_fact_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry.radical import Radical
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _run(text: str, payload: dict):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route = out.response["route_d"]
    answers = (
        {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()}
        if route["status"] == "SERVED"
        else None
    )
    return route, out.response["envelope"], answers, out.receipt


def _pyramid_base_premises(side: str = "2", height: str = "3", verts: tuple[str, str, str, str, str] = ("S", "A", "B", "C", "D")) -> tuple[str, list[dict]]:
    s, a, b, c, d = verts
    base_str = f"{a}{b}{c}{d}"
    solid_str = f"{s}.{base_str}"
    base_text = (
        f"Cho hình chóp {solid_str} có đáy {base_str} là hình vuông cạnh {side}, "
        f"{s}{a} vuông góc với mặt phẳng ({base_str}) và {s}{a} = {height}. "
    )
    premises = [
        {
            "kind": "regular_polygon",
            "args": {"vertices": [a, b, c, d], "side": side},
            "quote": f"đáy {base_str} là hình vuông cạnh {side}",
            "solid_id": "s1",
        },
        {
            "kind": "perpendicular_line_plane",
            "args": {"line": [s, a], "plane": [a, b, c, d]},
            "quote": f"{s}{a} vuông góc với mặt phẳng ({base_str})",
            "solid_id": "s1",
        },
        {
            "kind": "segment_length",
            "args": {"segment": [s, a], "value": height},
            "quote": f"{s}{a} = {height}",
            "solid_id": "s1",
        },
    ]
    return base_text, premises


# ── Phase 0.1: Valid In-Plane Point Projection Must Not Be Falsely Refused ───────────────────────────────────────────

def test_phase0_1_valid_in_plane_projection_not_falsely_refused():
    """Phase 0.1 mathematical check:
    If P lies on plane Q (`G = centroid(ABC)` on `(ABCD)`), its orthogonal projection onto Q is mathematically well-defined
    (`H = G = (4/3, 2/3, 0)`). Measuring `d(H, (SBC))` (`√2/3`) and segment length `|HS|` (`2√14/3`) must be SERVED,
    never falsely refused at descriptor parsing (`FACT_INCOMPLETE`).
    """
    base_text, premises = _pyramid_base_premises("2", "2")
    q1_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác ABC "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SBC)"
    )
    q2_quote = (
        "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trọng tâm của tam giác ABC "
        "lên mặt phẳng (ABCD) với S"
    )
    text = base_text + q1_quote + ". " + q2_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["A", "B", "C"],
                "quote": "trọng tâm của tam giác ABC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác ABC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "B", "C"]},
                "quote": q1_quote,
                "solid_id": "s1",
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"segment": ["@h1", "S"]},
                "quote": q2_quote,
                "solid_id": "s1",
            },
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    # Hand oracle: A(0,0,0), B(2,0,0), C(2,2,0), S(0,0,2)
    # G = centroid(ABC) = (4/3, 2/3, 0) in (ABCD) => H = proj(G, (ABCD)) = (4/3, 2/3, 0).
    # Plane (SBC) is x + z = 2 => d(H, (SBC)) = |4/3 + 0 - 2| / √2 = (2/3)/√2 = √2/3.
    # |HS|^2 = (4/3)^2 + (2/3)^2 + 2^2 = 16/9 + 4/9 + 36/9 = 56/9 => |HS| = 2√14/3.
    assert answers == {"q1": "√2/3", "q2": "2√14/3"}
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Family A: Goal-Only Multi-Step Discovery ─────────────────────────────────────────────────────────────────────────

def test_family_a1_goal_only_point_to_line_distance():
    """Family A.1: Problem states only solid premises and asks `d(A, SB)` without naming the foot `H`.
    Planner regresses `AnswerDistance(A, SB)` -> `Foot(H, A, SB)` -> `orthogonal_projection_line(A, SB, H) + ask_length(AH)`."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = "Tính khoảng cách từ A đến đường thẳng SB"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "A", "line": ["S", "B"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    # Right triangle SAB at A: AB = 2, SA = 3 => SB = √13, altitude AH = (2*3)/√13 = 6√13/13.
    assert answers == {"q1": "6√13/13"}
    fns = [c["fn"] for c in route["planner"]["calls"]]
    assert "orthogonal_projection_line" in fns and "ask_length" in fns
    assert validate_construction_continuity(env["scene3d"]) == []


def test_family_a2_goal_only_point_to_intersection_line_distance():
    """Family A.2: Problem asks for the distance from `A` to the intersection line of `(SAD)` and `(SBC)` without naming
    the perpendicular foot `H`. Planner chains `intersection_line` (`Line` result `g`) -> `orthogonal_projection_line`
    (`Foot` on `("result", "g")`) -> `ask_length` (`AnswerDistance`)."""
    text = (
        "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
        "Tìm giao tuyến của (SAD) và (SBC). Tính khoảng cách từ A đến giao tuyến của (SAD) và (SBC)."
    )
    fact_payload = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD", "solid_type": "pyramid"},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 2."], "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
            {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
            {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3."], "points": ["S", "A"], "measure": "segment", "value": "3"},
            {"id": "g", "kind": "intersection_line", "role": "premise", "quotes": ["Tìm giao tuyến của (SAD) và (SBC)."], "points_a": ["S", "A", "D"], "points_b": ["S", "B", "C"]},
            {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính khoảng cách từ A đến giao tuyến của (SAD) và (SBC)."], "quantity": "distance", "points_a": ["A"], "line_ref": "g"},
        ]
    }
    r = run_fact_route(text, fact_payload)
    assert r.status == "SERVED", (r.code, r.reason)
    # Intersection of (SAD) and (SBC) is line through S(0,0,3) parallel to AD(0,1,0): x=0, z=3.
    # Distance from A(0,0,0) to line (x=0, z=3) is 3.
    assert r.answers["q1"] == "3"
    fns = [c["fn"] for c in r.planner["calls"]]
    assert "intersection_line" in fns and "orthogonal_projection_line" in fns and "ask_length" in fns
    assert validate_construction_continuity(r.scene3d) == []


def test_family_a3_goal_only_constrained_plane_section_area():
    """Family A.3: Constrained plane `(P)` through `M, N` perpendicular to `(SBC)` where no normal line is given.
    Planner regresses `Normal(SBC)`, prunes `{S, B, C}`, projects `A` onto `(SBC)`, translates `M` along the normal,
    and computes section area `7√2/8`."""
    base_text, premises = _pyramid_base_premises("2", "2")
    premises = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "D"]}, "quote": "Gọi N là trung điểm của CD", "solid_id": "s1"},
    ]
    sec_quote = "Mặt phẳng (P) đi qua M, N và vuông góc với (SBC)"
    ask_quote = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    text = (
        base_text
        + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. "
        + sec_quote + ". " + ask_quote + "."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "quote": sec_quote,
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": ["M", "N"]},
                    {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]},
                ],
                "stated_intersections": [],
            }
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec1"},
                "quote": ask_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "7√2/8"}
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Family B: Competing Candidate Plans, Precondition Pruning & Cost Ranking ─────────────────────────────────────────

def test_family_b1_competing_perpline_plans_orthocenter_telemetry():
    """Family B.1: Orthocenter of `SBC` regresses 3 `PerpLine` loci in plane `W = (S, B, C)`.
    For each locus `PerpLine(vertex ⊥ opposite_side in (SBC))`:
    - Candidate 1 (`orthogonal_projection_line` direct `PerpLine` contract): `cost = 1`
    - Candidate 2 (`orthogonal_projection_line` `PerpDir` + `translate_point` `PerpLine` contract):
      binds free `Z in (S, B, C)`: two vertices on the side are pruned by `off_line(Z, L)`, third vertex gives `cost = 2`.
    Planner selects the `cost = 1` plan for the first two loci + `intersect_line_line` (`plan_cost = 3`) and records all
    mandatory search telemetry fields (`candidate_count`, `explored_states`, `pruned_nodes`, `rejection_reasons`,
    `selected_plan`, `plan_cost`, `search_depth`)."""
    base_text, premises = _pyramid_base_premises("2", "2")
    q_quote = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBC với A"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "o1",
                "kind": "orthocenter",
                "polygon": ["S", "B", "C"],
                "quote": "trực tâm của tam giác SBC",
            }
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"segment": ["@o1", "A"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    # Triangle SBC is right at B (BC ⊥ AB and BC ⊥ SA => BC ⊥ SB), so orthocenter of SBC is B(2,0,0); |BA| = 2.
    assert answers == {"q1": "2"}
    tel = route["planner"]["search_telemetry"]
    for key in (
        "candidate_count",
        "explored_states",
        "pruned_nodes",
        "rejection_reasons",
        "selected_plan",
        "plan_cost",
        "search_depth",
    ):
        assert key in tel, f"Missing telemetry key: {key}"
    assert tel["candidate_count"] == tel["candidate_evaluations"] >= 10
    assert tel["explored_states"] >= 4
    assert tel["pruned_nodes"] >= 6
    assert "precondition: the point lies on the line" in tel["rejection_reasons"]
    assert tel["plan_cost"] == 3
    assert tel["search_depth"] >= 2
    assert isinstance(tel["selected_plan"], list) and len(tel["selected_plan"]) >= 4


def test_family_b2_competing_perpline_plans_circumcenter_precondition_pruning():
    """Family B.2: Circumcenter of `SBC` regresses perpendicular bisector loci `PerpLine(midpoint(side) ⊥ side in (SBC))`.
    The direct `orthogonal_projection_line` `PerpLine` candidate (cost 1) is PRUNED because `midpoint(side)` lies on `side`
    (`off_line(P, L)` violated!), so the planner must select the 2-step `midpoint + PerpDir(off-line vertex) + translate_point`
    plan (`cost = 3` per locus, `plan_cost = 7`)."""
    base_text, premises = _pyramid_base_premises("2", "2")
    q_quote = "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBC với A"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "c1",
                "kind": "circumcenter",
                "polygon": ["S", "B", "C"],
                "quote": "tâm đường tròn ngoại tiếp tam giác SBC",
            }
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"segment": ["@c1", "A"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    # SBC is right at B => circumcenter is midpoint of hypotenuse SC: S(0,0,2), C(2,2,0) => O(1,1,1), |OA| = √3.
    assert answers == {"q1": "√3"}
    tel = route["planner"]["search_telemetry"]
    assert tel["pruned_nodes"] >= 9
    assert "precondition: the point lies on the line" in tel["rejection_reasons"]
    assert tel["plan_cost"] == 7
    cert = next(d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain")
    for locus in cert["search"]["loci"][:2]:
        assert locus["cost"] == 3
        assert any(r["fn"] == "orthogonal_projection_line" for r in locus["rejected"])


def test_family_b3a_competing_normal_plans_selects_cost0_premise_on_structurally_equivalent_plane():
    """Family B.3a: Constrained plane `(P)` goes through `M, N` and is perpendicular to `(ABM)` where `M = midpoint(CD)`.
    Since `M` lies on `CD`, `(ABM)` is structurally the base plane `(ABCD)`.
    Given `SA ⊥ (ABCD)`, the planner evaluates:
    - Cost-0 premise normal `SA` (`cost = 0`, `producer = "premise"`)
    - Cost-1 projection candidate `orthogonal_projection(S, (ABM))` (`cost = 1`), while `A, B, C, D` are structurally
      rejected as lying on `(ABM)` (`off_plane`).
    Planner must select the cost-0 premise `SA` (`cost = 0`) instead of constructing a redundant projection!"""
    base_text, premises = _pyramid_base_premises("2", "2")
    premises = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "D"]}, "quote": "Gọi N là trung điểm của CD", "solid_id": "s1"},
    ]
    sec_quote = "Mặt phẳng (P) đi qua M, N và vuông góc với (ANB)"
    ask_quote = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    text = (
        base_text
        + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. "
        + sec_quote + ". " + ask_quote + "."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "quote": sec_quote,
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": ["M", "N"]},
                    {"kind": "perpendicular_to_plane", "operands": ["A", "N", "B"]},
                ],
                "stated_intersections": [],
            }
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec1"},
                "quote": ask_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "3/2"}
    aux = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))
    sub = aux["search"]["subgoals"][0]
    assert sub["selected"]["producer"] == "premise"
    assert sub["selected"]["cost"] == 0
    assert {"A", "B", "C", "D"} <= {r["point"] for r in sub["rejected"]}
    assert not any(c["fn"] == "orthogonal_projection" for c in route["planner"]["calls"])


def test_family_b3b_competing_normal_plans_reuses_existing_projection_at_cost0():
    """Family B.3b: Premise already defines `K` as the orthogonal projection of `A` onto `(SBC)`.
    When constrained plane `(P)` goes through `M, N` perpendicular to `(SBC)`, `_phap_tuyen` evaluates competing
    candidates for `Normal(SBC)` and reuses `[K, A]` from the existing projection at `cost = 0` (`reused_intermediates >= 1`)
    rather than constructing a duplicate `orthogonal_projection(A, (SBC))` at `cost = 1`."""
    base_text, premises = _pyramid_base_premises("2", "2")
    premises = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "D"]}, "quote": "Gọi N là trung điểm của CD", "solid_id": "s1"},
        {
            "kind": "orthogonal_projection",
            "args": {"point": "A", "plane": ["S", "B", "C"], "image": "K"},
            "quote": "Gọi K là hình chiếu vuông góc của A lên mặt phẳng (SBC)",
            "solid_id": "s1",
        },
    ]
    sec_quote = "Mặt phẳng (P) đi qua M, N và vuông góc với (SBC)"
    ask_quote = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    text = (
        base_text
        + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. "
        + "Gọi K là hình chiếu vuông góc của A lên mặt phẳng (SBC). "
        + sec_quote + ". " + ask_quote + "."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "quote": sec_quote,
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": ["M", "N"]},
                    {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]},
                ],
                "stated_intersections": [],
            }
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"section_id": "sec1"},
                "quote": ask_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "7√2/8"}
    proj_calls = [c for c in route["planner"]["calls"] if c["fn"] == "orthogonal_projection"]
    assert len(proj_calls) == 1, f"Expected 1 orthogonal_projection call (reused K), got {proj_calls}"
    aux = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))
    assert aux["witnesses"][0]["vector"] == ["K", "A"]
    assert aux["search"]["subgoals"][0]["selected"]["cost"] == 0
    assert route["planner"]["search_telemetry"]["reused_intermediates"] >= 1


def test_family_b3c_normal_contract_precondition_and_structural_tren_mat():
    """Family B.3c: Verify `orthogonal_projection` `Normal(Q)` contract declares `free=('Z',)` and
    `requires=(('off_plane', 'Z', 'Q'),)`, and `_EffectResolver._tren_mat` recognizes points structurally coplanar
    with `plane` (such as face vertices and midpoints of edges on that face)."""
    normal_contracts = [
        c for c in registry.planning_contracts(registry.REGISTRY["orthogonal_projection"])
        if c.effect.kind == "Normal"
    ]
    assert len(normal_contracts) == 1
    nc = normal_contracts[0]
    assert nc.free == ("Z",)
    assert ("off_plane", "Z", "Q") in nc.requires

    base_text, premises = _pyramid_base_premises("2", "2")
    premises = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["C", "D"]}, "quote": "Gọi M là trung điểm của CD", "solid_id": "s1"},
    ]
    text = base_text + "Gọi M là trung điểm của CD. Tính thể tích khối chóp S.ABCD."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "volume", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối chóp S.ABCD", "solid_id": "s1"}],
    }
    k = planner.lap_ke_hoach(bridge_v2(payload), text)
    # D and M (midpoint of CD) lie on the base face (ABCD), so they lie structurally on plane (A, B, C):
    assert k.resolver._tren_mat("D", ("A", "B", "C")) is True
    assert k.resolver._tren_mat("M", ("A", "B", "C")) is True
    assert k.resolver._tren_mat("S", ("A", "B", "C")) is False
    assert k.resolver._unmet(nc, {"Z": "M", "Q": ("A", "B", "C")}) == "precondition: the point lies on the plane"
    assert k.resolver._unmet(nc, {"Z": "S", "Q": ("A", "B", "C")}) is None


# ── Family C: Implicit Auxiliary Construction Taxonomy ───────────────────────────────────────────────────────────────

def test_family_c_implicit_auxiliary_taxonomy_comparison():
    """Family C: Side-by-side comparison of the 3 mandatory taxonomy classes:
    1. Direct evaluator (`d(A, (SBC))` -> `SOURCE_EXPLICIT_SEQUENCE`, 0 auxiliaries)
    2. Registered auxiliary decomposition (`d(A, SB)` -> `REGISTERED_DECOMPOSITION`, 1 auxiliary foot)
    3. Dynamically discovered multi-step sequence (`d(proj(centroid(SBC), (ABCD)), AB)` -> `DISCOVERED_FUNCTION_COMPOSITION`, 3 auxiliaries)
    """
    base_text, premises = _pyramid_base_premises("2", "3")

    # 1. Direct evaluator (0 auxiliaries)
    q1 = "Tính khoảng cách từ A đến mặt phẳng (SBC)"
    t1 = base_text + q1 + "."
    r1, _e1, a1, _ = _run(t1, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t1,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "plane": ["S", "B", "C"]}, "quote": q1, "solid_id": "s1"}],
    })
    assert r1["status"] == "SERVED" and a1 == {"q1": "6√13/13"}
    tel1 = r1["planner"]["search_telemetry"]
    assert tel1["classification"] == "SOURCE_EXPLICIT_SEQUENCE"
    assert tel1["planner_originated_steps"] == []

    # 2. Registered auxiliary decomposition (1 auxiliary foot)
    q2 = "Tính khoảng cách từ A đến đường thẳng SB"
    t2 = base_text + q2 + "."
    r2, _e2, a2, _ = _run(t2, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t2,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": q2, "solid_id": "s1"}],
    })
    assert r2["status"] == "SERVED" and a2 == {"q1": "6√13/13"}
    tel2 = r2["planner"]["search_telemetry"]
    assert tel2["classification"] == "REGISTERED_DECOMPOSITION"
    assert tel2["registered_decomposition_steps"] == ["q1_aux"]
    assert tel2["search_generated_steps"] == []

    # 3. Dynamically discovered sequence (3 auxiliary points: centroid -> orthogonal_projection -> orthogonal_projection_line)
    q3 = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    t3 = base_text + q3 + "."
    r3, _e3, a3, _ = _run(t3, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t3,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q3, "solid_id": "s1"}],
    })
    assert r3["status"] == "SERVED" and a3 == {"q1": "2/3"}
    tel3 = r3["planner"]["search_telemetry"]
    assert tel3["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel3["search_generated_steps"] == ["q1_aux2"]


# ── Family D: Shared Intermediate Results Across Multiple Goals ──────────────────────────────────────────────────────

def test_family_d_shared_intermediate_results_across_multiple_goals():
    """Family D: Multiple goals depend on the same intermediate objects (`@g1` and `@h1`).
    Verifies:
    - Each shared intermediate is constructed once (`reused_intermediates >= 2`).
    - Both goals reference the exact same call IDs and point labels.
    - Provenance distinguishes `SOURCE_NAMED` vs `AUXILIARY`.
    - `Scene3D` and `construction_continuity` have zero duplicate objects or violations."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q1_quote = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    q2_quote = "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD), S và A"
    text = base_text + q1_quote + ". " + q2_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q1_quote, "solid_id": "s1"},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "area", "target": {"polygon": ["@h1", "S", "A"]}, "quote": q2_quote, "solid_id": "s1"},
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "2/3", "q2": "√5"}
    calls = route["planner"]["calls"]
    assert sum(1 for c in calls if c["fn"] == "centroid") == 1
    assert sum(1 for c in calls if c["fn"] == "orthogonal_projection") == 1
    assert route["planner"]["search_telemetry"]["reused_intermediates"] >= 2
    certs = [d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain"]
    assert certs[0]["operand"]["label"] == certs[1]["operand"]["label"]
    assert certs[0]["operand"]["nested"]["label"] == certs[1]["operand"]["nested"]["label"]
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Family E: 13 Mandatory Negative, Degenerate & Adversarial Failure Modes ──────────────────────────────────────────

def test_family_e9_projection_coinciding_with_source_point_degenerate_segment_refused():
    """Family E.9: When a point `M` already lies on plane `(ABCD)` (`M = midpoint(AB)`), its orthogonal projection
    onto `(ABCD)` coincides with `M` (`H = M`).
    1. Using the degenerate 0-length segment `[H, M]` where a geometric line/direction is required (`ask_angle_line_plane`)
       MUST fail closed with `DEGENERATE_POINTS`.
    2. Measuring the point-to-point distance / length between `H` and `M` (`ask_length` on `[H, M]`) evaluates to `"0"`,
       consistent with the explicit-premise sequence (`Gọi H là hình chiếu... Tính độ dài HM`)."""
    base_text, premises = _pyramid_base_premises("2", "2")
    premises = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
    ]
    q_deg = "Tính góc giữa đoạn thẳng nối hình chiếu vuông góc của trung điểm của AB lên mặt phẳng (ABCD) với M và mặt phẳng (SBC)"
    text_deg = base_text + "Gọi M là trung điểm của AB. " + q_deg + "."
    payload_deg = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text_deg,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {"described_id": "m1", "kind": "midpoint", "segment": ["A", "B"], "quote": "trung điểm của AB"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@m1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trung điểm của AB lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "angle", "target": {"line": ["@h1", "M"], "plane": ["S", "B", "C"]}, "quote": q_deg, "solid_id": "s1"}
        ],
    }
    route_deg, env_deg, _answers_deg, _receipt_deg = _run(text_deg, payload_deg)
    assert route_deg["status"] == "REFUSED"
    assert env_deg.get("reason_code") == "DEGENERATE_POINTS"

    q_len = "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trung điểm của AB lên mặt phẳng (ABCD) với M"
    text_len = base_text + "Gọi M là trung điểm của AB. " + q_len + "."
    payload_len = {
        **payload_deg,
        "problem_text": text_len,
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@h1", "M"]}, "quote": q_len, "solid_id": "s1"}
        ],
    }
    route_len, env_len, answers_len, _ = _run(text_len, payload_len)
    assert route_len["status"] == "SERVED", env_len.get("reason_code")
    assert answers_len == {"q1": "0"}


def test_family_e1_to_e8_and_e10_to_e13_negative_adversarial_matrix(monkeypatch):
    """Family E (E.1–E.8, E.10–E.13): Verify all remaining mandatory negative/adversarial failure modes fail closed."""
    base_text, premises = _pyramid_base_premises("2", "2")

    # E.1: Missing data (missing height SA) -> MISSING_DIMENSION
    t_e1 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD). Tính khoảng cách từ A đến đường thẳng SB."
    r_e1, env_e1, _, _ = _run(t_e1, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e1,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises[:2],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "Tính khoảng cách từ A đến đường thẳng SB", "solid_id": "s1"}],
    })
    assert r_e1["status"] == "REFUSED" and env_e1["reason_code"] == "MISSING_DIMENSION"

    # E.2: Contradictory data (SA = 2, AB = 2, SA ⊥ (ABCD), but SB = 10) -> INCONSISTENT_FACTS
    t_e2 = base_text + "Biết SB = 10. Tính khoảng cách từ A đến đường thẳng SB."
    r_e2, env_e2, _, _ = _run(t_e2, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e2,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [*premises, {"kind": "segment_length", "args": {"segment": ["S", "B"], "value": "10"}, "quote": "Biết SB = 10", "solid_id": "s1"}],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "Tính khoảng cách từ A đến đường thẳng SB", "solid_id": "s1"}],
    })
    assert r_e2["status"] == "REFUSED" and env_e2["reason_code"] == "INCONSISTENT_FACTS"

    # E.3: Negation in premise ("SA không vuông góc với mặt phẳng (ABCD)") -> NEGATED_CLAUSE
    t_e3 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA không vuông góc với mặt phẳng (ABCD) và SA = 2. Tính khoảng cách từ A đến đường thẳng SB."
    p_e3 = copy.deepcopy(premises)
    p_e3[1]["quote"] = "SA không vuông góc với mặt phẳng (ABCD)"
    r_e3, env_e3, _, _ = _run(t_e3, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e3,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": p_e3,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "Tính khoảng cách từ A đến đường thẳng SB", "solid_id": "s1"}],
    })
    assert r_e3["status"] == "REFUSED" and env_e3["reason_code"] == "NEGATED_CLAUSE"

    # E.4: Non-unique plane ((P) through A, S and perpendicular to (ABCD)) -> PLANE_NOT_UNIQUE
    s_e4 = "Mặt phẳng (P) đi qua A, S và vuông góc với (ABCD)"
    q_e4 = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    t_e4 = base_text + s_e4 + ". " + q_e4 + "."
    r_e4, env_e4, _, _ = _run(t_e4, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e4,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "derived_sections": [{"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "quote": s_e4, "plane_kind": "constrained", "constraints": [{"kind": "contains_points", "operands": ["A", "S"]}, {"kind": "perpendicular_to_plane", "operands": ["A", "B", "C", "D"]}], "stated_intersections": []}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": q_e4, "solid_id": "s1"}],
    })
    assert r_e4["status"] == "REFUSED" and env_e4["reason_code"] == "PLANE_NOT_UNIQUE"

    # E.5 & E.8: Collinear points defining a triangle / degenerate plane (A, M, B where M = midpoint(AB)) -> COLLINEAR_POINTS
    q_e5 = "Tính khoảng cách từ trọng tâm của tam giác AMB đến mặt phẳng (ABCD)"
    t_e5 = base_text + "Gọi M là trung điểm của AB. " + q_e5 + "."
    r_e5, env_e5, _, _ = _run(t_e5, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e5,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [*premises, {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"}],
        "relations": [],
        "described_points": [{"described_id": "g1", "kind": "centroid", "polygon": ["A", "M", "B"], "quote": "trọng tâm của tam giác AMB"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@g1", "plane": ["A", "B", "C", "D"]}, "quote": q_e5, "solid_id": "s1"}],
    })
    assert r_e5["status"] == "REFUSED" and env_e5["reason_code"] == "COLLINEAR_POINTS"

    q_e8 = "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của S lên mặt phẳng (AMB) với C"
    t_e8 = base_text + "Gọi M là trung điểm của AB. " + q_e8 + "."
    r_e8, env_e8, _, _ = _run(t_e8, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e8,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [*premises, {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"}],
        "relations": [],
        "described_points": [{"described_id": "h1", "kind": "orthogonal_projection", "point": "S", "plane": ["A", "M", "B"], "quote": "hình chiếu vuông góc của S lên mặt phẳng (AMB)"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@h1", "C"]}, "quote": q_e8, "solid_id": "s1"}],
    })
    assert r_e8["status"] == "REFUSED" and env_e8["reason_code"] in ("COLLINEAR_POINTS", "DEGENERATE_POINTS")

    # E.6: Parallel lines intersection (AB and CD) -> PARALLEL_LINES / INCONSISTENT_FACTS
    q_e6 = "Tính khoảng cách từ giao điểm của hai đường thẳng AB và CD đến mặt phẳng (SAD)"
    t_e6 = base_text + q_e6 + "."
    r_e6, env_e6, _, _ = _run(t_e6, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e6,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [{"described_id": "i1", "kind": "intersect_line_line", "line1": ["A", "B"], "line2": ["C", "D"], "quote": "giao điểm của hai đường thẳng AB và CD"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@i1", "plane": ["S", "A", "D"]}, "quote": q_e6, "solid_id": "s1"}],
    })
    assert r_e6["status"] == "REFUSED" and env_e6["reason_code"] in ("PARALLEL_NO_INTERSECTION", "PARALLEL_LINES", "INCONSISTENT_FACTS")

    # E.7: Skew lines intersection (SA and BC) -> NON_COPLANAR_POINTS / SKEW_NO_INTERSECTION
    q_e7 = "Tính khoảng cách từ giao điểm của hai đường thẳng SA và BC đến mặt phẳng (SAD)"
    t_e7 = base_text + q_e7 + "."
    r_e7, env_e7, _, _ = _run(t_e7, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_e7,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [{"described_id": "i1", "kind": "intersect_line_line", "line1": ["S", "A"], "line2": ["B", "C"], "quote": "giao điểm của hai đường thẳng SA và BC"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@i1", "plane": ["S", "A", "D"]}, "quote": q_e7, "solid_id": "s1"}],
    })
    assert r_e7["status"] == "REFUSED" and env_e7["reason_code"] in ("NON_COPLANAR_POINTS", "SKEW_NO_INTERSECTION", "INCONSISTENT_FACTS")

    # E.10: Dependency cycle in candidate plan -> DEPENDENCY_CYCLE
    k_cycle = planner.KeHoach()
    k_cycle.taken = {"S", "A", "B", "C", "D"}
    res_cycle = planner._EffectResolver([], k_cycle, lambda *a, **kw: {})
    res_cycle.active.add(("AnswerDistance", ("A", ("named", ("B", "S")))))
    with pytest.raises(registry.TuChoi) as exc_cycle:
        res_cycle._resolve("AnswerDistance", ("A", ("named", ("B", "S"))))
    assert exc_cycle.value.code == "DEPENDENCY_CYCLE"

    # E.11: Unmet precondition in all candidates (all PerpLine contracts require off_line on a point that lies on every side) -> UNSUPPORTED_CAPABILITY
    with pytest.raises(registry.TuChoi) as exc_unmet:
        res_unmet = planner._EffectResolver([], k_cycle, lambda *a, **kw: {})
        # Point B lies on line ("named", ("B", "C")), and plane W=("B", "C") has no off-line vertex:
        res_unmet._resolve("PerpLine", (None, "B", ("named", ("B", "C")), ("B", "C")))
    assert exc_unmet.value.code == "UNSUPPORTED_CAPABILITY"

    # E.12: No valid producer in Registry -> UNSUPPORTED_CAPABILITY
    with pytest.raises(registry.TuChoi) as exc_noprod:
        res_noprod = planner._EffectResolver([], k_cycle, lambda *a, **kw: {})
        res_noprod._resolve("NonExistentEffect", ("A",))
    assert exc_noprod.value.code == "UNSUPPORTED_CAPABILITY"

    # E.13: Search budget exceeded -> PLAN_TOO_LARGE (outcome == "SEARCH_EXHAUSTED")
    with monkeypatch.context() as m:
        m.setattr(planner, "MAX_EFFECT_DEPTH", 2)
        q_e13 = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
        t_e13 = base_text + q_e13 + "."
        r_e13, env_e13, _, _ = _run(t_e13, {
            "schema_version": "typed-fact-next/2",
            "problem_text": t_e13,
            "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
            "premises": premises,
            "relations": [],
            "described_points": [
                {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
                {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
            ],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
            "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q_e13, "solid_id": "s1"}],
        })
        assert r_e13["status"] == "REFUSED" and env_e13["reason_code"] == "PLAN_TOO_LARGE"


# ── Section IX: Mandatory Ablation & Counterfactual Testing (Tests 1–5) ──────────────────────────────────────────────

def test_section_ix_test1_explicit_vs_goal_only():
    """Section IX Test 1 — Explicit vs Goal-Only:
    Compare Case 1A (explicit intermediate steps named in premises) vs Case 1B (goal-only problem statement)
    across 3 geometry tasks:
    - Pair 1: Point-to-line distance (`d(A, SB)` = `6√13/13`)
    - Pair 2: Composed centroid -> plane projection -> line distance (`2/3`)
    - Pair 3: Constrained plane section area (`7√2/8`)
    Both variants must produce the exact same verified mathematical answer."""
    base_text, premises = _pyramid_base_premises("2", "3")

    # Pair 1A (Explicit foot H on SB) vs Pair 1B (Goal-only d(A, SB)):
    t_1a = base_text + "Gọi H là hình chiếu vuông góc của A lên đường thẳng SB. Tính độ dài đoạn thẳng AH."
    r_1a, _, a_1a, _ = _run(t_1a, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_1a,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            *premises,
            {"kind": "orthogonal_projection_line", "args": {"point": "A", "line": ["S", "B"], "image": "H"}, "quote": "Gọi H là hình chiếu vuông góc của A lên đường thẳng SB", "solid_id": "s1"},
        ],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["A", "H"]}, "quote": "Tính độ dài đoạn thẳng AH", "solid_id": "s1"}],
    })
    t_1b = base_text + "Tính khoảng cách từ A đến đường thẳng SB."
    r_1b, _, a_1b, _ = _run(t_1b, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_1b,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "Tính khoảng cách từ A đến đường thẳng SB", "solid_id": "s1"}],
    })
    assert r_1a["status"] == r_1b["status"] == "SERVED"
    assert a_1a == a_1b == {"q1": "6√13/13"}

    # Pair 2A (Explicit G = centroid(SBC), H = proj(G, (ABCD))) vs Pair 2B (Goal-only nested description):
    t_2a = (
        base_text
        + "Gọi G là trọng tâm của tam giác SBC. Gọi H là hình chiếu vuông góc của G lên mặt phẳng (ABCD). "
        + "Tính khoảng cách từ H đến đường thẳng AB."
    )
    r_2a, _, a_2a, _ = _run(t_2a, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_2a,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            *premises,
            {"kind": "centroid", "args": {"point": "G", "polygon": ["S", "B", "C"]}, "quote": "Gọi G là trọng tâm của tam giác SBC", "solid_id": "s1"},
            {"kind": "orthogonal_projection", "args": {"point": "G", "plane": ["A", "B", "C", "D"], "image": "H"}, "quote": "Gọi H là hình chiếu vuông góc của G lên mặt phẳng (ABCD)", "solid_id": "s1"},
        ],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "H", "line": ["A", "B"]}, "quote": "Tính khoảng cách từ H đến đường thẳng AB", "solid_id": "s1"}],
    })
    q_2b = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    t_2b = base_text + q_2b + "."
    r_2b, _, a_2b, _ = _run(t_2b, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_2b,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q_2b, "solid_id": "s1"}],
    })
    assert r_2a["status"] == r_2b["status"] == "SERVED"
    assert a_2a == a_2b == {"q1": "2/3"}


def test_section_ix_test2_remove_specialized_decomposition(monkeypatch):
    """Section IX Test 2 — Remove Specialized Decomposition:
    When `ask_distance_point_plane` has its `AnswerDistance(P, Q)` planning contract removed, a goal asking for point-to-plane
    distance from a described point cannot use the direct evaluator and cleanly refuses with `UNSUPPORTED_CAPABILITY`
    (no false fallback or unverified guess)."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = "Tính khoảng cách từ trọng tâm của tam giác SBC đến mặt phẳng (SAD)"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [{"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@g1", "plane": ["S", "A", "D"]}, "quote": q_quote, "solid_id": "s1"}],
    }
    # Baseline with contract present:
    r_ok, _, a_ok, _ = _run(text, payload)
    assert r_ok["status"] == "SERVED" and a_ok == {"q1": "4/3"}

    # Ablation: remove ask_distance_point_plane.planning:
    orig = registry.REGISTRY["ask_distance_point_plane"]
    monkeypatch.setitem(registry.REGISTRY, "ask_distance_point_plane", replace(orig, planning=None))
    r_abl, env_abl, _, _ = _run(text, payload)
    assert r_abl["status"] == "REFUSED" and env_abl["reason_code"] == "UNSUPPORTED_CAPABILITY"


def test_section_ix_test3_remove_required_producer_fallback_and_refusal(monkeypatch):
    """Section IX Test 3 — Remove Required Producer:
    - Case 3A (Alternative producer exists): Remove the direct `PerpLine` contract (`cost = 1`) from
      `orthogonal_projection_line` (leaving only `PerpDir` + `translate_point` at `cost = 2`).
      On orthocenter of `SBC`, the planner automatically falls back to the 2-step `PerpDir + translate_point` producer
      (`plan_cost = 5` instead of `3`) and still computes the exact answer `2`!
    - Case 3B (No alternative producer exists): Remove both `PerpLine` and `PerpDir` from `orthogonal_projection_line`.
      The planner fails closed with `UNSUPPORTED_CAPABILITY` (`outcome == "MISSING_PRIMITIVE"`)."""
    base_text, premises = _pyramid_base_premises("2", "2")
    q_quote = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBC với A"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@o1", "A"]}, "quote": q_quote, "solid_id": "s1"}],
    }
    orig_spec = registry.REGISTRY["orthogonal_projection_line"]

    # Case 3A: Remove direct PerpLine contract from orthogonal_projection_line, keeping PerpDir
    with monkeypatch.context() as m:
        m.setitem(
            registry.REGISTRY,
            "orthogonal_projection_line",
            replace(orig_spec, planning_extra=tuple(c for c in orig_spec.planning_extra if c.effect.kind != "PerpLine")),
        )
        r_fallback, env_fallback, a_fallback, _ = _run(text, payload)
        assert r_fallback["status"] == "SERVED", env_fallback.get("reason_code")
        assert a_fallback == {"q1": "2"}
        assert r_fallback["planner"]["search_telemetry"]["plan_cost"] == 5
        assert "translate_point" in r_fallback["planner"]["search_telemetry"]["selected_functions"]

    # Case 3B: Remove both PerpLine and PerpDir from orthogonal_projection_line -> clean refusal
    with monkeypatch.context() as m:
        m.setitem(
            registry.REGISTRY,
            "orthogonal_projection_line",
            replace(orig_spec, planning_extra=tuple(c for c in orig_spec.planning_extra if c.effect.kind not in ("PerpLine", "PerpDir"))),
        )
        r_refused, env_refused, _, _ = _run(text, payload)
        assert r_refused["status"] == "REFUSED"
        assert env_refused["reason_code"] == "UNSUPPORTED_CAPABILITY"


def test_section_ix_test4_competing_plans_evaluation_and_selection():
    """Section IX Test 4 — Competing Plans:
    When two valid candidate plans exist for each `PerpLine` locus of `orthocenter(SBC)` (`cost = 1` direct foot vs
    `cost = 2` `PerpDir + translate_point`), both are evaluated (`candidate_count >= 10`) and the lower-cost plan
    (`plan_cost = 3`) is deterministically selected and verified."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = "Tính khoảng cách từ trực tâm của tam giác SBC đến mặt phẳng (ABCD)"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"}],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@o1", "plane": ["A", "B", "C", "D"]}, "quote": q_quote, "solid_id": "s1"}],
    }
    route, env, answers, _ = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    # SBC is right at B(2,0,0), which lies on (ABCD) => distance to (ABCD) is 0!
    assert answers == {"q1": "0"}
    tel = route["planner"]["search_telemetry"]
    assert tel["candidate_count"] >= 10
    assert tel["plan_cost"] == 3


def test_section_ix_test5_metamorphic_renaming_and_scaling():
    """Section IX Test 5 — Metamorphic Geometry Testing:
    1. Vertex renaming (`S.ABCD` -> `T.MNPQ` with `side=2, height=3`): plan structure (`selected_functions`, `plan_cost`,
       `search_depth`) is identical to `S.ABCD` and exact answers (`4/3` for plane distance, `2/3` for line distance,
       `√5` for triangle area) are invariant.
    2. Scaling (`k = 3`, `side=6, height=9` on `S.ABCD`): plan structure (`selected_functions`, `plan_cost`, `search_depth`)
       is identical, linear distances scale by `k = 3` (`4/3 -> 4`, `2/3 -> 2`), and triangle area scales by `k^2 = 9`
       (`√5 -> 9√5`)."""
    # 0. Baseline S.ABCD (side=2, height=3)
    base_orig, prem_orig = _pyramid_base_premises("2", "3", verts=("S", "A", "B", "C", "D"))
    q1_orig = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    q2_orig = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    q3_orig = "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD), S và A"
    t_orig = base_orig + q1_orig + ". " + q2_orig + ". " + q3_orig + "."
    r_orig, env_orig, a_orig, _ = _run(t_orig, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_orig,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": prem_orig,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["S", "A", "D"]}, "quote": q1_orig, "solid_id": "s1"},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q2_orig, "solid_id": "s1"},
            {"goal_id": "q3", "kind": "measurement", "goal_type": "area", "target": {"polygon": ["@h1", "S", "A"]}, "quote": q3_orig, "solid_id": "s1"},
        ],
    })
    assert r_orig["status"] == "SERVED", env_orig.get("reason_code")
    assert a_orig == {"q1": "4/3", "q2": "2/3", "q3": "√5"}

    # 1. Renamed vertices T.MNPQ (side=2, height=3)
    base_renamed, prem_renamed = _pyramid_base_premises("2", "3", verts=("T", "M", "N", "P", "Q"))
    q1_ren = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác TNP lên mặt phẳng (MNPQ) đến mặt phẳng (TMQ)"
    q2_ren = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác TNP lên mặt phẳng (MNPQ) đến đường thẳng MN"
    q3_ren = "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác TNP lên mặt phẳng (MNPQ), T và M"
    t_ren = base_renamed + q1_ren + ". " + q2_ren + ". " + q3_ren + "."
    r_ren, env_ren, a_ren, _ = _run(t_ren, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_ren,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "T.MNPQ", "quote": "Cho hình chóp T.MNPQ"}],
        "premises": prem_renamed,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["T", "N", "P"], "quote": "trọng tâm của tam giác TNP"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["M", "N", "P", "Q"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác TNP lên mặt phẳng (MNPQ)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp T.MNPQ"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["T", "M", "Q"]}, "quote": q1_ren, "solid_id": "s1"},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["M", "N"]}, "quote": q2_ren, "solid_id": "s1"},
            {"goal_id": "q3", "kind": "measurement", "goal_type": "area", "target": {"polygon": ["@h1", "T", "M"]}, "quote": q3_ren, "solid_id": "s1"},
        ],
    })
    assert r_ren["status"] == "SERVED", env_ren.get("reason_code")
    assert a_ren == a_orig == {"q1": "4/3", "q2": "2/3", "q3": "√5"}
    tel_orig = r_orig["planner"]["search_telemetry"]
    tel_ren = r_ren["planner"]["search_telemetry"]
    assert tel_ren["selected_functions"] == tel_orig["selected_functions"]
    assert tel_ren["plan_cost"] == tel_orig["plan_cost"] == 3
    assert tel_ren["search_depth"] == tel_orig["search_depth"] == 3

    # 2. Scaled by k = 3 (side=6, height=9) on S.ABCD
    base_scaled, prem_scaled = _pyramid_base_premises("6", "9")
    q1_sc = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    q2_sc = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    q3_sc = "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD), S và A"
    t_sc = base_scaled + q1_sc + ". " + q2_sc + ". " + q3_sc + "."
    r_sc, env_sc, a_sc, _ = _run(t_sc, {
        "schema_version": "typed-fact-next/2",
        "problem_text": t_sc,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": prem_scaled,
        "relations": [],
        "described_points": [
            {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["S", "A", "D"]}, "quote": q1_sc, "solid_id": "s1"},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q2_sc, "solid_id": "s1"},
            {"goal_id": "q3", "kind": "measurement", "goal_type": "area", "target": {"polygon": ["@h1", "S", "A"]}, "quote": q3_sc, "solid_id": "s1"},
        ],
    })
    assert r_sc["status"] == "SERVED", env_sc.get("reason_code")
    assert a_sc == {"q1": "4", "q2": "2", "q3": "9√5"}
    tel_sc = r_sc["planner"]["search_telemetry"]
    assert tel_sc["selected_functions"] == tel_orig["selected_functions"]
    assert tel_sc["plan_cost"] == tel_orig["plan_cost"] == 3
    assert tel_sc["search_depth"] == tel_orig["search_depth"] == 3
    assert r_ren["planner"]["search_telemetry"]["plan_cost"] == 3
    assert r_sc["planner"]["search_telemetry"]["plan_cost"] == 3
