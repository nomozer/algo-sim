"""Phase A & B capability discovery and composition verification suite for Hybrid /4.

Covers:
1. Discriminating composition probes (`SOURCE_EXPLICIT_SEQUENCE`, `REGISTERED_DECOMPOSITION`,
   and multi-step `_EffectResolver` locus/chain composition across multiple solid topologies
   `S.ABCD` pyramid and `ABC.A'B'C'` triangular prism), multi-goal intermediate reuse
   (`reused_intermediates >= 1`), and contract-only ablation/extension proofs.
2. Proven Gap 1 (Planner structural incidence propagation in `_phap_tuyen` and
   `_EffectResolver._tren_duong` beyond `midpoint`: `divide_segment`, `centroid`,
   `orthogonal_projection_line`, and `intersect_line_line`) + negative/adversarial twins.
3. Proven Gap 2 (Live-observed C26 clarification wire-shape normalization in
   `typed_fact_next_extraction.py` for `S2-C-D05`, `S2-C-C04`, and `S2-C-A01`) +
   negative/adversarial twins.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import (
    ReplayExtractor,
    _normalize_transport_payload,
    extract_typed_fact_next_v2,
)
from app.simulation.geometry_functions import planner, registry
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

BASE_PYRAMID_TEXT = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
    "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
)
BASE_PYRAMID_PREMISES = [
    {
        "kind": "regular_polygon",
        "args": {"vertices": ["A", "B", "C", "D"], "side": "2"},
        "quote": "đáy ABCD là hình vuông cạnh 2",
        "solid_id": "s1",
    },
    {
        "kind": "perpendicular_line_plane",
        "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
        "quote": "SA vuông góc với mặt phẳng (ABCD)",
        "solid_id": "s1",
    },
    {
        "kind": "segment_length",
        "args": {"segment": ["S", "A"], "value": "2"},
        "quote": "SA = 2",
        "solid_id": "s1",
    },
]


def _run_offline(text: str, payload: dict):
    res = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    return res.response["route_d"], res.response["envelope"], res.receipt


# ---------------------------------------------------------------------------
# Part 1: Discriminating Composition Probes (Case 1, Case 2, Case 3)
# ---------------------------------------------------------------------------


def test_case1_direct_call_source_explicit_sequence():
    """Case 1: 1-to-1 mapping to registered functions -> SOURCE_EXPLICIT_SEQUENCE."""
    q_vol = "Tính thể tích khối chóp S.ABCD"
    q_dist = "khoảng cách từ A đến mặt phẳng (SBC)"
    text = f"{BASE_PYRAMID_TEXT}{q_vol} và {q_dist}."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "g_vol",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": q_vol,
            },
            {
                "goal_id": "g_dist",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "A", "plane": ["S", "B", "C"]},
                "quote": q_dist,
            },
        ],
    }
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED" and env["status"] == "ok"
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {
        "g_vol": "8/3",
        "g_dist": "√2",
    }
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "SOURCE_EXPLICIT_SEQUENCE"
    assert tel["planner_originated_steps"] == []


def test_case2_registered_decomposition_named_point_to_line():
    """Case 2: Named point-to-line distance expands via registered rule KHOANG_CACH_DIEM_DUONG."""
    q_dist = "Tính khoảng cách từ A đến đường thẳng SB"
    text = f"{BASE_PYRAMID_TEXT}{q_dist}."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "g1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "A", "line": ["S", "B"]},
                "quote": q_dist,
            }
        ],
    }
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED" and env["status"] == "ok"
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"g1": "√2"}
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "REGISTERED_DECOMPOSITION"
    assert len(tel["registered_decomposition_steps"]) == 1
    assert tel["search_generated_steps"] == []


def test_case3a_dynamic_multi_step_composition_pyramid_shared_foot_across_centers():
    """Case 3a: Multi-step composition in S.ABCD solving orthocenter(CDM) and circumcenter(CDM) with shared foot.

    Coordinates: A(0,0,0), B(2,0,0), C(2,2,0), D(0,2,0), S(0,0,2), M = mid(AB) = (1,0,0).
    - Goal 1: distance from orthocenter(CDM) = (1, 3/2, 0) to plane (SAB) (y=0) -> 3/2.
    - Goal 2: distance from circumcenter(CDM) = (1, 5/4, 0) to plane (SAB) (y=0) -> 5/4.
    Planner composes 8 intermediate calls (`orthogonal_projection_line`, `midpoint`, `translate_point`,
    `intersect_line_line`) via `_EffectResolver` and reuses the shared altitude foot at cost 0.
    """
    q1 = "Tính khoảng cách từ trực tâm của tam giác CDM đến mặt phẳng (SAB)"
    q2 = "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác CDM đến mặt phẳng (SAB)"
    text = f"{BASE_PYRAMID_TEXT}Gọi M là trung điểm của AB. {q1}. {q2}."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": [
            *deepcopy(BASE_PYRAMID_PREMISES),
            {
                "kind": "midpoint",
                "args": {"point": "M", "segment": ["A", "B"]},
                "quote": "Gọi M là trung điểm của AB",
                "solid_id": "s1",
            },
        ],
        "described_points": [
            {
                "described_id": "h1",
                "kind": "orthocenter",
                "polygon": ["C", "D", "M"],
                "quote": "trực tâm của tam giác CDM",
            },
            {
                "described_id": "o1",
                "kind": "circumcenter",
                "polygon": ["C", "D", "M"],
                "quote": "tâm đường tròn ngoại tiếp tam giác CDM",
            },
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "@h1", "plane": ["S", "A", "B"]},
                "quote": q1,
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "@o1", "plane": ["S", "A", "B"]},
                "quote": q2,
            },
        ],
    }
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED" and env["status"] == "ok", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {
        "q1": "3/2",
        "q2": "5/4",
    }
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "REGISTERED_DECOMPOSITION"
    assert len(tel["planner_originated_steps"]) >= 6
    assert tel["reused_intermediates"] >= 1
    assert len(env["scene3d"]["objects"]) > 0
    assert len(route["construction_trace"]) > 0


def test_case3b_dynamic_multi_step_composition_prism_shared_intermediate():
    """Case 3b: Multi-step composition in right prism ABC.A'B'C' solving orthocenter(BC'M) and circumcenter(BC'M).

    Right prism ABC.A'B'C' with right triangle base ABC at A (AB = 3, AC = 4, AA' = 2), M = mid(BC), N = mid(A'B'):
    - Goal 1: distance from orthocenter(BC'M) to base (ABC) -> 25/4.
    - Goal 2: distance from circumcenter(BC'M) to base (ABC) -> 33/8.
    """
    q1 = "Tính khoảng cách từ trực tâm của tam giác BC'M đến mặt phẳng (ABC)"
    q2 = "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác BC'M đến mặt phẳng (ABC)"
    text = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AA' = 2. "
        "Gọi M là trung điểm của BC. Gọi N là trung điểm của A'B'. "
        f"{q1}. {q2}."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
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
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "B"], "value": "3"},
                "quote": "AB = 3",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "C"], "value": "4"},
                "quote": "AC = 4",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "A'"], "value": "2"},
                "quote": "AA' = 2",
                "solid_id": "s1",
            },
            {
                "kind": "midpoint",
                "args": {"point": "M", "segment": ["B", "C"]},
                "quote": "Gọi M là trung điểm của BC",
                "solid_id": "s1",
            },
            {
                "kind": "midpoint",
                "args": {"point": "N", "segment": ["A'", "B'"]},
                "quote": "Gọi N là trung điểm của A'B'",
                "solid_id": "s1",
            },
        ],
        "described_points": [
            {
                "described_id": "h1",
                "kind": "orthocenter",
                "polygon": ["B", "C'", "M"],
                "quote": "trực tâm của tam giác BC'M",
            },
            {
                "described_id": "o1",
                "kind": "circumcenter",
                "polygon": ["B", "C'", "M"],
                "quote": "tâm đường tròn ngoại tiếp tam giác BC'M",
            },
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "@h1", "plane": ["A", "B", "C"]},
                "quote": q1,
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "@o1", "plane": ["A", "B", "C"]},
                "quote": q2,
            },
        ],
    }
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED" and env["status"] == "ok", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {
        "q1": "25/4",
        "q2": "33/8",
    }
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "REGISTERED_DECOMPOSITION"
    assert len(tel["planner_originated_steps"]) >= 6
    assert tel["reused_intermediates"] >= 1


def test_case3c_ablation_and_contract_only_producer_selection(monkeypatch):
    """Case 3c: Removing a producer contract causes UNSUPPORTED_CAPABILITY; a contract-only clone is selected."""
    q1 = "Tính khoảng cách từ trực tâm của tam giác CDM đến mặt phẳng (SAB)"
    text = f"{BASE_PYRAMID_TEXT}Gọi M là trung điểm của AB. {q1}."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": [
            *deepcopy(BASE_PYRAMID_PREMISES),
            {
                "kind": "midpoint",
                "args": {"point": "M", "segment": ["A", "B"]},
                "quote": "Gọi M là trung điểm của AB",
                "solid_id": "s1",
            },
        ],
        "described_points": [
            {
                "described_id": "h1",
                "kind": "orthocenter",
                "polygon": ["C", "D", "M"],
                "quote": "trực tâm của tam giác CDM",
            }
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "g1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "s1",
                "target": {"point": "@h1", "plane": ["S", "A", "B"]},
                "quote": q1,
            }
        ],
    }
    facts = bridge_v2(payload)
    src = registry.REGISTRY["orthogonal_projection_line"]
    # 1. Contract-only clone with alphabetically earlier name wins tie-break without any planner code reference
    monkeypatch.setitem(
        registry.REGISTRY,
        "aa_custom_perp_foot",
        replace(src, name="aa_custom_perp_foot", planning=None),
    )
    plan_with_clone = planner.lap_ke_hoach(deepcopy(facts), text)
    assert any(c["fn"] == "aa_custom_perp_foot" for c in plan_with_clone.calls)

    # 2. Removing intersect_line_line contracts makes orthocenter locus intersection impossible -> UNSUPPORTED_CAPABILITY
    real_contracts = planner.planning_contracts
    monkeypatch.setattr(
        planner,
        "planning_contracts",
        lambda spec: () if spec.name == "intersect_line_line" else real_contracts(spec),
    )
    with pytest.raises(registry.TuChoi) as exc_info:
        planner.lap_ke_hoach(deepcopy(facts), text)
    assert exc_info.value.code == "UNSUPPORTED_CAPABILITY"


# ---------------------------------------------------------------------------
# Part 2: Proven Gap 1 — Structural Incidence Propagation in `planner.py`
# ---------------------------------------------------------------------------


def _constrained_section_case(extra_premise: dict, extra_sentence: str, pts_through: list[str], perp_plane: list[str]):
    sec_sentence = (
        f"Mặt phẳng (P) đi qua {', '.join(pts_through)} và vuông góc với ({''.join(perp_plane)})"
    )
    ask_sentence = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    text = (
        f"{BASE_PYRAMID_TEXT}Gọi N là trung điểm của CD. "
        f"{extra_sentence}. {sec_sentence}. {ask_sentence}."
    )
    premises = [
        *deepcopy(BASE_PYRAMID_PREMISES),
        {
            "kind": "midpoint",
            "args": {"point": "N", "segment": ["C", "D"]},
            "quote": "Gọi N là trung điểm của CD",
            "solid_id": "s1",
        },
        extra_premise,
    ]
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "premises": premises,
        "relations": [],
        "derived_sections": [
            {
                "section_id": "sec1",
                "plane_name": "P",
                "target_solid_id": "s1",
                "quote": sec_sentence,
                "plane_kind": "constrained",
                "constraints": [
                    {"kind": "contains_points", "operands": list(pts_through)},
                    {"kind": "perpendicular_to_plane", "operands": list(perp_plane)},
                ],
                "stated_intersections": [],
            }
        ],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "area",
                "solid_id": "s1",
                "target": {"section_id": "sec1"},
                "quote": ask_sentence,
            }
        ],
    }
    return text, payload


def test_gap1a_constrained_plane_perp_through_divide_segment_point_rejects_collinear_vertex():
    """Proven Gap 1A: M divides AB (ratio 1/3) -> (SAM) is (SAB) -> vertex B lies on (SAM) and is rejected."""
    extra_sentence = "Lấy điểm M trên cạnh AB sao cho AM = 1/3 AB"
    extra_premise = {
        "kind": "divide_segment",
        "args": {"point": "M", "segment": ["A", "B"], "ratio": "1/3"},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    text, payload = _constrained_section_case(extra_premise, extra_sentence, ["S", "N"], ["S", "A", "M"])
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "√5"}
    sub = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))["search"]["subgoals"][0]
    assert {"S", "A", "B"} <= {r["point"] for r in sub["rejected"]}


def test_gap1b_constrained_plane_perp_through_centroid_rejects_coplanar_face_vertices():
    """Proven Gap 1B: G is centroid of SAB -> (SAG) is (SAB) -> vertex B lies on (SAG) and is rejected."""
    extra_sentence = "Gọi G là trọng tâm tam giác SAB"
    extra_premise = {
        "kind": "centroid",
        "args": {"point": "G", "polygon": ["S", "A", "B"]},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    text, payload = _constrained_section_case(extra_premise, extra_sentence, ["S", "N"], ["S", "A", "G"])
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "√5"}
    sub = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))["search"]["subgoals"][0]
    assert {"S", "A", "B"} <= {r["point"] for r in sub["rejected"]}


def test_gap1c_constrained_plane_perp_through_line_projection_rejects_collinear_vertex():
    """Proven Gap 1C: H is projection of A onto SB -> (SAH) is (SAB) -> vertex B lies on (SAH) and is rejected."""
    extra_sentence = "Gọi H là hình chiếu vuông góc của A lên đường thẳng SB"
    extra_premise = {
        "kind": "orthogonal_projection_line",
        "args": {"point": "A", "line": ["S", "B"], "image": "H"},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    text, payload = _constrained_section_case(extra_premise, extra_sentence, ["S", "N"], ["S", "A", "H"])
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "√5"}
    sub = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))["search"]["subgoals"][0]
    assert {"S", "A", "B"} <= {r["point"] for r in sub["rejected"]}


def test_gap1d_constrained_plane_perp_through_line_intersection_rejects_collinear_vertex():
    """Proven Gap 1D: O = AC ∩ BD -> (SCO) is (SAC) -> vertex A lies on (SCO) and is rejected."""
    extra_sentence = "Gọi O là giao điểm của AC và BD"
    extra_premise = {
        "kind": "intersect_line_line",
        "args": {"point": "O", "line1": ["A", "C"], "line2": ["B", "D"]},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    text, payload = _constrained_section_case(extra_premise, extra_sentence, ["S", "N"], ["S", "C", "O"])
    route, env, receipt = _run_offline(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert receipt["engine"]["status"] == "VERIFIED"
    assert {k: v["coef"] for k, v in route["answer_exact"].items()} == {"q1": "√17/2"}
    sub = next(d for d in route["planner"]["auxiliary"] if d.get("witnesses"))["search"]["subgoals"][0]
    assert {"S", "C", "A"} <= {r["point"] for r in sub["rejected"]}
    assert sub["selected"]["point"] == "B"


def test_gap1e_effect_resolver_tren_duong_recognizes_collinear_premises():
    """Proven Gap 1E: `_EffectResolver._tren_duong` recognizes points defined on a segment by divide_segment, projection, and intersect_line_line."""
    extra_sentence = "Lấy điểm M trên cạnh AB sao cho AM = 1/3 AB"
    extra_premise = {
        "kind": "divide_segment",
        "args": {"point": "M", "segment": ["A", "B"], "ratio": "1/3"},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    text, payload = _constrained_section_case(extra_premise, extra_sentence, ["S", "N"], ["S", "A", "M"])
    plan = planner.lap_ke_hoach(bridge_v2(payload), text)
    resolver = plan.resolver
    assert resolver._tren_duong("M", ("named", ("A", "B"))) is True
    assert resolver._tren_duong("B", ("named", ("A", "M"))) is False
    assert resolver._tren_duong("C", ("named", ("A", "B"))) is False


def test_gap1_negative_twins_still_refuse_fail_closed():
    """Adversarial/negative twins for Gap 1: non-unique or face-coincident constrained planes still refuse."""
    extra_sentence = "Lấy điểm M trên cạnh AB sao cho AM = 1/3 AB"
    extra_premise = {
        "kind": "divide_segment",
        "args": {"point": "M", "segment": ["A", "B"], "ratio": "1/3"},
        "quote": extra_sentence,
        "solid_id": "s1",
    }
    # 1. Through A, S perpendicular to (ABCD) -> AS is already normal to (ABCD) -> PLANE_NOT_UNIQUE
    t1, p1 = _constrained_section_case(extra_premise, extra_sentence, ["A", "S"], ["A", "B", "C", "D"])
    r1, env1, _ = _run_offline(t1, p1)
    assert r1["status"] == "REFUSED" and env1.get("reason_code") == "PLANE_NOT_UNIQUE"

    # 2. Through A, M, N perpendicular to (SAM) -> (AMN) is base (ABCD) -> SECTION_PLANE_IS_FACE
    t2, p2 = _constrained_section_case(extra_premise, extra_sentence, ["A", "M", "N"], ["S", "A", "M"])
    r2, env2, _ = _run_offline(t2, p2)
    assert r2["status"] == "REFUSED" and env2.get("reason_code") == "SECTION_PLANE_IS_FACE"


# ---------------------------------------------------------------------------
# Part 3: Proven Gap 2 — Live-Observed C26 Clarification Wire-Shape Recovery
# ---------------------------------------------------------------------------


def test_gap2a_s2_c_d05_projection_missing_target_recovers_verbatim_clarification():
    """Proven Gap 2A: Secondary non-verbatim `unresolved` item with ellipsis drops when primary verbatim item has roles & relations."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Gọi H là hình chiếu của S. Mô phỏng hình và điểm H."
    )
    raw = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Mô phỏng hình"}],
        "math_goals": [],
        "unresolved": [
            {
                "unresolved_id": "u1",
                "kind": "missing_operand",
                "subject_ref": "H",
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["orthogonal_projection"],
                "quote": "Gọi H là hình chiếu của S",
            },
            {
                "unresolved_id": "u2",
                "kind": "missing_operand",
                "missing_roles": ["goal_object"],
                "quote": "Mô phỏng ... điểm H",
                "candidate_relations": [],
            },
        ],
    }
    route, env, _ = _run_offline(text, raw)
    assert route["status"] == "REFUSED" and env.get("reason_code") == "AMBIGUOUS_FACT"
    clar = route["refusal"]["clarification"]
    assert clar["schema_version"] == "route-d-clarification/1"
    assert clar["nlu_class"] == "MISSING_DATA"
    assert clar["quote"] == "Gọi H là hình chiếu của S"


def test_gap2b_s2_c_c04_angle_plane_missing_folds_incomplete_goal_into_unresolved():
    """Proven Gap 2B: Incomplete `math_goal` whose missing operand is recorded in `unresolved` folds into `unresolved`."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Tính góc giữa SB và mặt phẳng."
    )
    raw = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "angle",
                "solid_id": "s1",
                "target": {"line": ["S", "B"]},
                "quote": "Tính góc giữa SB và mặt phẳng.",
            }
        ],
        "unresolved": [
            {
                "unresolved_id": "ur1",
                "kind": "missing_operand",
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["angle"],
                "quote": "mặt phẳng",
            }
        ],
    }
    route, env, _ = _run_offline(text, raw)
    assert route["status"] == "REFUSED" and env.get("reason_code") == "AMBIGUOUS_FACT"
    clar = route["refusal"]["clarification"]
    assert clar["schema_version"] == "route-d-clarification/1"
    assert clar["nlu_class"] == "MISSING_DATA"
    assert clar["quote"] == "Tính góc giữa SB và mặt phẳng."


def test_gap2c_s2_c_a01_goc_chieu_keeps_specific_unresolved_entry():
    """Proven Gap 2C: Empty-role/empty-relation companion `unresolved` items drop when a specific role+relation item exists."""
    text = "Mô phỏng điểm S là góc chiếu của hình lăng trụ xiên."
    raw = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [],
        "premises": [],
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [],
        "math_goals": [],
        "unresolved": [
            {
                "unresolved_id": "unr1",
                "kind": "missing_operand",
                "quote": "hình lăng trụ xiên",
                "missing_roles": [],
                "candidate_relations": [],
            },
            {
                "unresolved_id": "unr2",
                "kind": "ambiguous",
                "subject_ref": "S",
                "missing_roles": ["source_point", "target_line_or_plane", "relation_kind"],
                "candidate_relations": ["orthogonal_projection"],
                "quote": "điểm S là góc chiếu của hình lăng trụ xiên.",
            },
            {
                "unresolved_id": "unr3",
                "kind": "unsupported",
                "quote": "Mô phỏng điểm S",
                "missing_roles": [],
                "candidate_relations": [],
            },
        ],
    }
    route, env, _ = _run_offline(text, raw)
    assert route["status"] == "REFUSED" and env.get("reason_code") == "AMBIGUOUS_FACT"
    clar = route["refusal"]["clarification"]
    assert clar["unresolved_id"] == "unr2"
    assert clar["nlu_class"] == "AMBIGUOUS"
    assert clar["quote"] == "điểm S là góc chiếu của hình lăng trụ xiên."


def test_gap2_adversarial_twins_never_hide_ungrounded_quotes_or_broken_goals():
    """Adversarial twins for Gap 2: ungrounded quotes and unbacked broken math_goals still fail closed."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
        "Tính góc giữa SB và mặt phẳng."
    )
    # 1. Single unresolved with non-verbatim ellipsis quote -> still QUOTE_NOT_IN_SOURCE
    raw_ellipsis_only = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [],
        "unresolved": [
            {
                "unresolved_id": "u1",
                "kind": "missing_operand",
                "missing_roles": ["target_line_or_plane"],
                "candidate_relations": ["angle"],
                "quote": "Tính góc ... mặt phẳng",
            }
        ],
    }
    res1 = extract_typed_fact_next_v2(text, ReplayExtractor({text: raw_ellipsis_only}))
    assert res1.payload is None and res1.code == "QUOTE_NOT_IN_SOURCE"

    # 2. Incomplete math_goal without a matching unresolved entry -> still INVALID_MATH_GOAL
    raw_broken_goal = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "hình chóp S.ABCD"}],
        "premises": deepcopy(BASE_PYRAMID_PREMISES),
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "angle",
                "solid_id": "s1",
                "target": {"line": ["S", "B"]},
                "quote": "Tính góc giữa SB và mặt phẳng.",
            }
        ],
    }
    res2 = extract_typed_fact_next_v2(text, ReplayExtractor({text: _normalize_transport_payload(raw_broken_goal)}))
    assert res2.payload is None and res2.code == "INVALID_MATH_GOAL"
