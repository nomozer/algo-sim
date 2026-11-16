# -*- coding: utf-8 -*-
"""Compositional Geometry Planner Expansion verification suite (`compositional-planner-capability-expansion`).

Verifies genuine compositional discovery, bridge/source-gate DAG propagation, multi-step function
composition, Scene3D continuity, Mode A output-policy preservation, metamorphic/ablation invariants,
and fail-closed tamper/negative boundaries without hardcoding or LLM-guided function selection.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import re
import sys

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

_RM_TOOLS = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools"
if str(_RM_TOOLS) not in sys.path:
    sys.path.insert(0, str(_RM_TOOLS))
import reasoning_matrix as RM  # noqa: E402  (read-only dev benchmark payloads & oracles)

_R1_PATH = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/r1-described-point-probe.json"
import json  # noqa: E402

RM_CASES = {c["id"]: c for c in RM.build_cases()}
R1_CASES = {c["id"]: c for c in json.loads(_R1_PATH.read_text(encoding="utf-8"))["cases"]}
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _base_pyramid(side: str = "2", height: str = "2", extra_text: str = "") -> tuple[str, dict]:
    text = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, SA vuông góc với (ABCD), SA = {height}. {extra_text}".strip()
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
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
                "args": {"segment": ["S", "A"], "value": height},
                "quote": f"SA = {height}",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "described_points": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [],
    }
    return text, payload


def _run_gold(text: str, payload: dict):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route, env = out.response["route_d"], out.response["envelope"]
    answers = ({k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()} if route["status"] == "SERVED" else None)
    return route, env, answers


def _run_nl(text: str):
    lp = parse_geometry_problem_locally(text)
    out = route_text_input(text, allow_live_ai=False)
    rd = out.response.get("route_d") or {}
    env = out.response.get("envelope") or {}
    answers = ({k: v["coef"] for k, v in (rd.get("answer_exact") or {}).items()} if rd.get("status") == "SERVED" else None)
    return lp, rd, env, answers


# ── Family 1: midpoint -> derived_line -> intersect_line_plane -> angle / distance ──────────────────────────────────

def test_family_1_midpoint_intersect_derived_line_angle_and_distance():
    # F1a: C3 angle(line([B, @intersect(AM, (SBD))]), (ABCD)) = 5/6 (cos²).
    c3 = R1_CASES["C3"]
    route_a, env_a, ans_a = _run_gold(c3["text"], c3["payload"])
    assert route_a["status"] == "SERVED", env_a.get("reason_code")
    assert ans_a == {"q1": "5/6"}
    assert validate_construction_continuity(env_a["scene3d"]) == []

    # F1b: C3-dist -> distance from derived line(B, @intersect(AM, (SBD))) to (ABCD) is 0.
    c3d = copy.deepcopy(c3)
    old_q = c3d["payload"]["math_goals"][0]["quote"]
    ask_q = old_q.replace("Tính góc", "Tính khoảng cách")
    c3d["text"] = c3d["text"].replace(old_q, ask_q)
    c3d["payload"]["problem_text"] = c3d["text"]
    c3d["payload"]["math_goals"][0].update(goal_type="distance", quote=ask_q)
    route_b, env_b, ans_b = _run_gold(c3d["text"], c3d["payload"])
    assert route_b["status"] == "SERVED", env_b.get("reason_code")
    assert ans_b == {"q1": "0"}
    assert validate_construction_continuity(env_b["scene3d"]) == []

    # F1c: point A to derived line(B, @intersect(AM, (SBD))): I = (2/3,2/3,2/3), u=(-2,1,1), d²=8/6=4/3 -> 2√3/3.
    t1c, p1c = _base_pyramid(
        "2", "2",
        "Gọi M là trung điểm của SC. Tính khoảng cách từ A đến đường thẳng nối B với giao điểm của AM và (SBD).",
    )
    p1c["premises"].append({"kind": "midpoint", "args": {"point": "M", "segment": ["S", "C"]}, "quote": "Gọi M là trung điểm của SC", "solid_id": "s1"})
    p1c["described_points"] = [{"described_id": "i1", "kind": "intersect_line_plane", "line": ["A", "M"], "plane": ["S", "B", "D"], "quote": "giao điểm của AM và (SBD)"}]
    p1c["math_goals"] = [{
        "goal_id": "q1", "kind": "measurement", "goal_type": "distance",
        "target": {"point": "A", "line": ["B", "@i1"]},
        "quote": "Tính khoảng cách từ A đến đường thẳng nối B với giao điểm của AM và (SBD)",
        "solid_id": "s1",
    }]
    route_c, env_c, ans_c = _run_gold(t1c, p1c)
    assert route_c["status"] == "SERVED", env_c.get("reason_code")
    assert ans_c == {"q1": "2√3/3"}
    assert validate_construction_continuity(env_c["scene3d"]) == []


# ── Family 2: PL5 (point to derived line) & PA3 (derived line to plane), Gold + Local Parser NL ─────────────────────

@pytest.mark.parametrize("cid,want_coef", [("PL5", "2√6/3"), ("PA3", "1")])
def test_family_2_pl5_and_pa3_served_on_gold_and_local_parser_nl(cid, want_coef):
    c = RM_CASES[cid]
    route_g, env_g, ans_g = _run_gold(c["text"], c["payload"])
    assert route_g["status"] == "SERVED", (cid, env_g.get("reason_code"))
    assert ans_g == {"q1": want_coef}
    assert validate_construction_continuity(env_g["scene3d"]) == []

    lp, rd_nl, env_nl, ans_nl = _run_nl(c["text"])
    assert lp.status == LOCAL_PARSE_COMPLETE, (cid, lp.fallback_reason)
    assert rd_nl["status"] == "SERVED", (cid, env_nl.get("reason_code"))
    assert ans_nl == {"q1": want_coef}
    assert validate_construction_continuity(env_nl["scene3d"]) == []


# ── Family 3: Described through_point sections + DINH_CAT_CANH cut reuse ──────────────────────────────────────────────

def test_family_3_described_through_point_sections_and_cut_reuse():
    # F3a: depth-2 @id (projection of centroid(SBC) onto (ABCD)) as through_point of section (P) || (SAB) -> 16/9.
    q3a = "Mặt phẳng (P) đi qua hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) và song song với (SAB)"
    t3a, p3a = _base_pyramid("2", "2", f"{q3a}. Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P).")
    p3a["described_points"] = [
        {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
        {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"],
         "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
    ]
    p3a["derived_sections"] = [{
        "section_id": "sec1", "plane_name": "P", "target_solid_id": "s1",
        "plane_kind": "through_point_parallel_plane", "through_point": "@h1", "parallel_plane": ["S", "A", "B"], "quote": q3a,
    }]
    p3a["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"},
                          "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)", "solid_id": "s1"}]
    route_a, env_a, ans_a = _run_gold(t3a, p3a)
    assert route_a["status"] == "SERVED", env_a.get("reason_code")
    assert ans_a == {"q1": "16/9"}
    assert validate_construction_continuity(env_a["scene3d"]) == []

    # F3b: @orthocenter(SBD) through_point section on BOTH Gold and Local Parser NL -> 16/9.
    q3b = "Mặt phẳng (P) đi qua trực tâm của tam giác SBD và song song với (SAB)"
    t3b, p3b = _base_pyramid("2", "2", f"{q3b}. Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P).")
    p3b["described_points"] = [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}]
    p3b["derived_sections"] = [{
        "section_id": "sec1", "plane_name": "P", "target_solid_id": "s1",
        "plane_kind": "through_point_parallel_plane", "through_point": "@o1", "parallel_plane": ["S", "A", "B"], "quote": q3b,
    }]
    p3b["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"},
                          "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)", "solid_id": "s1"}]
    route_b, env_b, ans_b = _run_gold(t3b, p3b)
    assert route_b["status"] == "SERVED", env_b.get("reason_code")
    assert ans_b == {"q1": "16/9"}
    lp_b, rd_b_nl, env_b_nl, ans_b_nl = _run_nl(t3b)
    assert lp_b.status == LOCAL_PARSE_COMPLETE, lp_b.fallback_reason
    assert rd_b_nl["status"] == "SERVED", env_b_nl.get("reason_code")
    assert ans_b_nl == {"q1": "16/9"}

    # F3c: @orthocenter(SBD) section parallel to base (ABC) with DINH_CAT_CANH cut reuse: d(K, (ABCD)) = 2/3.
    cut_q = (
        "Xác định thiết diện của hình chóp S.ABCD với mặt phẳng (Q) đi qua trực tâm của tam giác SBD "
        "và song song với (ABCD), cắt các cạnh bên SA, SB, SC, SD lần lượt tại M, N, E, K"
    )
    t3c, p3c = _base_pyramid("2", "2", f"{cut_q}. Tính khoảng cách từ K đến (ABCD).")
    p3c["described_points"] = [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}]
    p3c["derived_sections"] = [{
        "section_id": "sec1", "plane_name": "Q", "target_solid_id": "s1",
        "plane_kind": "through_point_parallel_plane", "through_point": "@o1", "parallel_plane": ["A", "B", "C"],
        "stated_intersections": [
            {"edge": ["S", "A"], "point": "M", "quote": "cắt các cạnh bên SA, SB, SC, SD lần lượt tại M, N, E, K"},
            {"edge": ["S", "B"], "point": "N", "quote": "cắt các cạnh bên SA, SB, SC, SD lần lượt tại M, N, E, K"},
            {"edge": ["S", "C"], "point": "E", "quote": "cắt các cạnh bên SA, SB, SC, SD lần lượt tại M, N, E, K"},
            {"edge": ["S", "D"], "point": "K", "quote": "cắt các cạnh bên SA, SB, SC, SD lần lượt tại M, N, E, K"},
        ],
        "quote": cut_q,
    }]
    p3c["simulation_goals"].append({"goal_id": "gs1", "kind": "construct_plane_section", "target_section_id": "sec1", "quote": cut_q})
    p3c["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                          "target": {"point": "K", "plane": ["A", "B", "C", "D"]}, "quote": "Tính khoảng cách từ K đến (ABCD)", "solid_id": "s1"}]
    route_c, env_c, ans_c = _run_gold(t3c, p3c)
    assert route_c["status"] == "SERVED", env_c.get("reason_code")
    assert ans_c == {"q1": "2/3"}
    assert validate_construction_continuity(env_c["scene3d"]) == []


# ── Family 4: POINT_DEFINITIONS (orthocenter / circumcenter) + named 3-point section SE3 ───────────────────────────

def test_family_4_point_definitions_and_named_three_point_section():
    # RE10 (nested orthocenter -> proj -> dist = 2/3) & SE3 ((Q) qua M, N, P -> area = 1) on Gold & NL.
    for cid, want in (("RE10", "2/3"), ("SE3", "1")):
        c = RM_CASES[cid]
        rg, eg, ag = _run_gold(c["text"], c["payload"])
        assert rg["status"] == "SERVED" and ag == {"q1": want}, (cid, eg.get("reason_code"))
        lp, rn, en, an = _run_nl(c["text"])
        assert lp.status == LOCAL_PARSE_COMPLETE, (cid, lp.fallback_reason)
        assert rn["status"] == "SERVED" and an == {"q1": want}, (cid, en.get("reason_code"))
        assert validate_construction_continuity(en["scene3d"]) == []

    # F4c: circumcenter of right triangle SBC (at B) lies at midpoint of SC = (1,1,1) -> dist((SAD)) = 1.
    q4c = "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác SBC đến (SAD)"
    t4c, p4c = _base_pyramid("2", "2", q4c + ".")
    p4c["described_points"] = [{"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác SBC"}]
    p4c["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                          "target": {"point": "@c1", "plane": ["S", "A", "D"]}, "quote": q4c, "solid_id": "s1"}]
    rg, eg, ag = _run_gold(t4c, p4c)
    assert rg["status"] == "SERVED" and ag == {"q1": "1"}, eg.get("reason_code")
    lp, rn, en, an = _run_nl(t4c)
    assert lp.status == LOCAL_PARSE_COMPLETE and rn["status"] == "SERVED" and an == {"q1": "1"}


# ── Family 5: Multiple @id operands in one goal (length, distance, angle_lines, triangle area) ─────────────────────

def test_family_5_multi_described_points_in_single_goal():
    # MG5 (length between two @ids = √5, Gold & NL)
    mg5 = RM_CASES["MG5"]
    rg, eg, ag = _run_gold(mg5["text"], mg5["payload"])
    assert rg["status"] == "SERVED" and ag == {"q1": "√5"}, eg.get("reason_code")
    lp, rn, en, an = _run_nl(mg5["text"])
    assert lp.status == LOCAL_PARSE_COMPLETE and rn["status"] == "SERVED" and an == {"q1": "√5"}

    # D2 (distance S to line([@m1, @m2]) = √6)
    d2 = R1_CASES["D2"]
    rd2, ed2, ad2 = _run_gold(d2["text"], d2["payload"])
    assert rd2["status"] == "SERVED" and ad2 == {"q1": "√6"}, ed2.get("reason_code")

    # F5c: dual-@id angle_lines: line1=[@mid(SC), A] dir (1,1,1), line2=[@mid(SA), B] dir (2,0,-1) -> cos² = 1/15.
    q5c = "Tính góc giữa đường thẳng nối trung điểm của SC với A và đường thẳng nối trung điểm của SA với B"
    t5c, p5c = _base_pyramid("2", "2", q5c + ".")
    p5c["described_points"] = [
        {"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"},
        {"described_id": "m2", "kind": "midpoint", "segment": ["S", "A"], "quote": "trung điểm của SA"},
    ]
    p5c["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "angle",
                          "target": {"line1": ["@m1", "A"], "line2": ["@m2", "B"]}, "quote": q5c, "solid_id": "s1"}]
    r5c, e5c, a5c = _run_gold(t5c, p5c)
    assert r5c["status"] == "SERVED" and a5c == {"q1": "1/15"}, e5c.get("reason_code")
    assert validate_construction_continuity(e5c["scene3d"]) == []

    # F5d: triple-@id triangle area: [@mid(SA), @mid(SB), @mid(SC)] has vertices (0,0,1), (1,0,1), (1,1,1) -> area = 1/2.
    q5d = "Tính diện tích tam giác tạo bởi trung điểm của SA, trung điểm của SB và trung điểm của SC"
    t5d, p5d = _base_pyramid("2", "2", q5d + ".")
    p5d["described_points"] = [
        {"described_id": "m1", "kind": "midpoint", "segment": ["S", "A"], "quote": "trung điểm của SA"},
        {"described_id": "m2", "kind": "midpoint", "segment": ["S", "B"], "quote": "trung điểm của SB"},
        {"described_id": "m3", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"},
    ]
    p5d["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "area",
                          "target": {"polygon": ["@m1", "@m2", "@m3"]}, "quote": q5d, "solid_id": "s1"}]
    r5d, e5d, a5d = _run_gold(t5d, p5d)
    assert r5d["status"] == "SERVED" and a5d == {"q1": "1/2"}, e5d.get("reason_code")
    assert validate_construction_continuity(e5d["scene3d"]) == []


# ── Metamorphic, Search Reuse, Determinism & Contract Ablation Invariants ────────────────────────────────────────────

def test_metamorphic_rename_reorder_scale_shared_reuse_and_ablation(monkeypatch):
    # Base multi-@id case (angle_lines with dual-@id): cos² = 1/15, invariant to rename, reorder, scale, REGISTRY order.
    q_quote = "Tính góc giữa đường thẳng nối trung điểm của SC với A và đường thẳng nối trung điểm của SA với B"
    text, payload = _base_pyramid("2", "2", q_quote + ".")
    payload["described_points"] = [
        {"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"},
        {"described_id": "m2", "kind": "midpoint", "segment": ["S", "A"], "quote": "trung điểm của SA"},
    ]
    payload["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "angle",
                              "target": {"line1": ["@m1", "A"], "line2": ["@m2", "B"]}, "quote": q_quote, "solid_id": "s1"}]

    # 1. Rename vertices S->V, A->E, B->F, C->G, D->K
    _ren_tok = {"S.ABCD": "V.EFGK", "ABCD": "EFGK", "SC": "VG", "SA": "VE", "A": "E", "B": "F", "C": "G", "D": "K"}
    sub_txt = lambda s: re.sub(r"\b(?:S\.ABCD|ABCD|SC|SA|A|B|C|D)\b", lambda m: _ren_tok[m[0]], s)  # noqa: E731
    t_ren = sub_txt(text)
    p_ren = copy.deepcopy(payload)
    p_ren["problem_text"] = t_ren
    p_ren["solids"][0].update(notation="V.EFGK", quote=sub_txt(p_ren["solids"][0]["quote"]))
    p_ren["premises"][0]["args"]["vertices"] = ["E", "F", "G", "K"]
    p_ren["premises"][0]["quote"] = sub_txt(p_ren["premises"][0]["quote"])
    p_ren["premises"][1]["args"].update(line=["V", "E"], plane=["E", "F", "G", "K"])
    p_ren["premises"][1]["quote"] = sub_txt(p_ren["premises"][1]["quote"])
    p_ren["premises"][2]["args"]["segment"] = ["V", "E"]
    p_ren["premises"][2]["quote"] = sub_txt(p_ren["premises"][2]["quote"])
    p_ren["described_points"][0].update(segment=["V", "G"], quote=sub_txt(p_ren["described_points"][0]["quote"]))
    p_ren["described_points"][1].update(segment=["V", "E"], quote=sub_txt(p_ren["described_points"][1]["quote"]))
    p_ren["simulation_goals"][0]["quote"] = sub_txt(p_ren["simulation_goals"][0]["quote"])
    p_ren["math_goals"][0]["target"] = {"line1": ["@m1", "E"], "line2": ["@m2", "F"]}
    p_ren["math_goals"][0]["quote"] = sub_txt(p_ren["math_goals"][0]["quote"])
    r_ren, e_ren, a_ren = _run_gold(t_ren, p_ren)
    assert r_ren["status"] == "SERVED" and a_ren == {"q1": "1/15"}, e_ren.get("reason_code")

    # 2. Premise reorder + uniform scale (k=2 on MG5 length -> 2√5)
    mg5 = copy.deepcopy(RM_CASES["MG5"])
    mg5["payload"]["premises"].reverse()
    mg5["payload"]["described_points"].reverse()
    r_ord, e_ord, a_ord = _run_gold(mg5["text"], mg5["payload"])
    assert r_ord["status"] == "SERVED" and a_ord == {"q1": "√5"}, e_ord.get("reason_code")

    mg5_s = copy.deepcopy(RM_CASES["MG5"])
    mg5_s["text"] = mg5_s["text"].replace("cạnh 2", "cạnh 4").replace("SA = 2", "SA = 4")
    mg5_s["payload"]["problem_text"] = mg5_s["text"]
    mg5_s["payload"]["premises"][0]["args"]["side"] = "4"
    mg5_s["payload"]["premises"][0]["quote"] = "đáy ABCD là hình vuông cạnh 4"
    mg5_s["payload"]["premises"][2]["args"]["value"] = "4"
    mg5_s["payload"]["premises"][2]["quote"] = "SA = 4"
    r_scl, e_scl, a_scl = _run_gold(mg5_s["text"], mg5_s["payload"])
    assert r_scl["status"] == "SERVED" and a_scl == {"q1": "2√5"}, e_scl.get("reason_code")

    # 3. Shared intermediate reuse across 2 goals referencing the same @o1 orthocenter
    q1_s = "Tính khoảng cách từ trực tâm của tam giác SBD đến (ABCD)"
    q2_s = "Tính khoảng cách từ trực tâm của tam giác SBD đến (SAB)"
    t_sh, p_sh = _base_pyramid("2", "2", f"{q1_s}. {q2_s}.")
    p_sh["described_points"] = [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}]
    p_sh["math_goals"] = [
        {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@o1", "plane": ["A", "B", "C", "D"]}, "quote": q1_s, "solid_id": "s1"},
        {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@o1", "plane": ["S", "A", "B"]}, "quote": q2_s, "solid_id": "s1"},
    ]
    r_sh, e_sh, a_sh = _run_gold(t_sh, p_sh)
    assert r_sh["status"] == "SERVED" and a_sh == {"q1": "2/3", "q2": "2/3"}, e_sh.get("reason_code")
    assert r_sh["planner"]["search_telemetry"]["reused_intermediates"] >= 1
    assert [c["fn"] for c in r_sh["planner"]["calls"]].count("intersect_line_line") == 1

    # 4. Reversed REGISTRY order determinism
    with monkeypatch.context() as m:
        m.setattr(registry, "REGISTRY", dict(reversed(list(registry.REGISTRY.items()))))
        r_rev, e_rev, a_rev = _run_gold(t_sh, p_sh)
        assert r_rev["status"] == "SERVED" and a_rev == a_sh, e_rev.get("reason_code")

    # 5. Contract ablation: disabling `ask_distance_line_plane.planning` fails closed with UNSUPPORTED_CAPABILITY
    pa3 = RM_CASES["PA3"]
    with monkeypatch.context() as m:
        m.setitem(registry.REGISTRY, "ask_distance_line_plane", replace(registry.REGISTRY["ask_distance_line_plane"], planning=None))
        r_abl, e_abl, a_abl = _run_gold(pa3["text"], pa3["payload"])
        assert r_abl["status"] == "REFUSED" and a_abl is None
        assert e_abl["reason_code"] == "UNSUPPORTED_CAPABILITY"


# ── Negative, Tamper & Fail-Closed Boundaries ────────────────────────────────────────────────────────────────────────

def test_negative_degenerate_collinear_missing_contradictory_tamper_and_budget(monkeypatch):
    # 1. Coincident endpoints on derived line (@mid(AC) == @intersect(AC, BD) -> DEGENERATE_POINTS)
    t_deg, p_deg = _base_pyramid(
        "2", "2", "Tính khoảng cách từ S đến đường thẳng nối trung điểm của AC với giao điểm của AC và BD."
    )
    p_deg["described_points"] = [
        {"described_id": "m1", "kind": "midpoint", "segment": ["A", "C"], "quote": "trung điểm của AC"},
        {"described_id": "i1", "kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"], "quote": "giao điểm của AC và BD"},
    ]
    p_deg["math_goals"] = [{
        "goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "S", "line": ["@m1", "@i1"]},
        "quote": "Tính khoảng cách từ S đến đường thẳng nối trung điểm của AC với giao điểm của AC và BD", "solid_id": "s1",
    }]
    r_deg, e_deg, _ = _run_gold(t_deg, p_deg)
    assert r_deg["status"] == "REFUSED" and e_deg["reason_code"] in {"DEGENERATE_LINE", "DEGENERATE_POINTS"}

    # 2. Collinear triangle for orthocenter -> COLLINEAR_POINTS
    t_col, p_col = _base_pyramid(
        "2", "2", "Gọi M là trung điểm của AB. Tính khoảng cách từ trực tâm của tam giác ABM đến (ABCD)."
    )
    p_col["premises"].append({"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"})
    p_col["described_points"] = [{"described_id": "o1", "kind": "orthocenter", "polygon": ["A", "B", "M"], "quote": "trực tâm của tam giác ABM"}]
    p_col["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                            "target": {"point": "@o1", "plane": ["A", "B", "C", "D"]},
                            "quote": "Tính khoảng cách từ trực tâm của tam giác ABM đến (ABCD)", "solid_id": "s1"}]
    r_col, e_col, _ = _run_gold(t_col, p_col)
    assert r_col["status"] == "REFUSED" and e_col["reason_code"] in {"COLLINEAR_POINTS", "DEGENERATE_POINTS"}

    # 3. Missing height on PA3 -> MISSING_DIMENSION / UNDERDETERMINED_POINT
    pa3_miss = copy.deepcopy(RM_CASES["PA3"])
    sa_len = next(x for x in pa3_miss["payload"]["premises"] if x["kind"] == "segment_length")
    pa3_miss["text"] = pa3_miss["text"].replace(f" và {sa_len['quote']}", "").replace(f", {sa_len['quote']}", "")
    pa3_miss["payload"]["problem_text"] = pa3_miss["text"]
    pa3_miss["payload"]["premises"] = [x for x in pa3_miss["payload"]["premises"] if x["kind"] != "segment_length"]
    r_miss, e_miss, _ = _run_gold(pa3_miss["text"], pa3_miss["payload"])
    assert r_miss["status"] == "REFUSED" and e_miss["reason_code"] in {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"}

    # 4. Contradictory edge length (SC = 1 contradicts SA = 2, AB = 2 -> INCONSISTENT_FACTS)
    t_bad, p_bad = _base_pyramid("2", "2", "SC = 1. Tính khoảng cách từ trung điểm của SC đến (SAB).")
    p_bad["premises"].append({"kind": "segment_length", "args": {"segment": ["S", "C"], "value": "1"}, "quote": "SC = 1", "solid_id": "s1"})
    p_bad["described_points"] = [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"}]
    p_bad["math_goals"] = [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                            "target": {"point": "@m1", "plane": ["S", "A", "B"]},
                            "quote": "Tính khoảng cách từ trung điểm của SC đến (SAB)", "solid_id": "s1"}]
    r_bad, e_bad, _ = _run_gold(t_bad, p_bad)
    assert r_bad["status"] == "REFUSED" and e_bad["reason_code"] == "INCONSISTENT_FACTS"

    # 5. Ungrounded quote -> QUOTE_NOT_IN_SOURCE
    p_ungr = copy.deepcopy(RM_CASES["PA3"]["payload"])
    p_ungr["described_points"][0]["quote"] = "trung điểm của BC"
    r_ungr, e_ungr, _ = _run_gold(RM_CASES["PA3"]["text"], p_ungr)
    assert r_ungr["status"] == "REFUSED" and e_ungr["reason_code"] in {"QUOTE_NOT_IN_SOURCE", "SOURCE_OBJECT_MISMATCH"}

    # 6. Tampered operand_trees & definition certificate in engine -> REFUSED (AUXILIARY_RULE_MISMATCH / ENGINE_SELF_CHECK_FAILED)
    real_plan = planner.lap_ke_hoach
    c_re10 = RM_CASES["RE10"]

    def _tampered_tree(*a, **k):
        pl = real_plan(*a, **k)
        for cert in pl.auxiliary:
            if cert.get("rule") == "effect-chain" and cert.get("operand", {}).get("nested"):
                cert["operand"]["nested"]["points"] = ["S", "B", "C"]
        return pl

    with monkeypatch.context() as m:
        m.setattr(planner, "lap_ke_hoach", _tampered_tree)
        r_tmp, e_tmp, _ = _run_gold(c_re10["text"], c_re10["payload"])
        assert r_tmp["status"] == "REFUSED" and e_tmp["reason_code"] in {"AUXILIARY_RULE_MISMATCH", "ENGINE_SELF_CHECK_FAILED"}

    # 7. Search budget exhaustion (MAX_EFFECT_CANDIDATES = 4) -> PLAN_TOO_LARGE
    with monkeypatch.context() as m:
        m.setattr(planner, "MAX_EFFECT_CANDIDATES", 4)
        r_cap, e_cap, _ = _run_gold(c_re10["text"], c_re10["payload"])
        assert r_cap["status"] == "REFUSED" and e_cap["reason_code"] == "PLAN_TOO_LARGE"


# ── Scene3D Continuity, Mode A output-policy/1 & State Isolation ─────────────────────────────────────────────────────

def test_scene3d_continuity_mode_a_output_policy_and_state_isolation():
    # 1. Causal CREATE order & continuity on RE10
    re10 = RM_CASES["RE10"]
    rg, eg, ag = _run_gold(re10["text"], re10["payload"])
    assert rg["status"] == "SERVED" and ag == {"q1": "2/3"}
    assert validate_construction_continuity(eg["scene3d"]) == []
    ev_created = {e["object"]: e["step_index"] for e in eg["scene3d"]["events"] if e.get("action") == "CREATE"}
    for lbl in rg["planner"]["auxiliary"][0]["labels"]:
        assert engine.ir_name(lbl) in ev_created

    # 2. Mode A output-policy/1 ROUND_HALF_UP on D1 (exact coef √2 preserved, rounded_display "1,4", zero float)
    d1 = copy.deepcopy(R1_CASES["D1"])
    old_q = d1["payload"]["math_goals"][0]["quote"]
    new_q = old_q + " (làm tròn kết quả đến hàng phần mười)"
    d1["text"] = d1["text"].replace(old_q, new_q)
    d1["payload"]["problem_text"] = d1["text"]
    d1["payload"]["math_goals"][0]["quote"] = new_q
    d1["payload"]["math_goals"][0]["rounding"] = {"mode": "ROUND_HALF_UP", "decimals": 1}
    r_m, e_m, _ = _run_gold(d1["text"], d1["payload"])
    assert r_m["status"] == "SERVED", e_m.get("reason_code")
    assert r_m["answers"] == {"q1": "1,4"}
    ex = r_m["answer_exact"]["q1"]
    assert ex["coef"] == "√2"
    assert ex["output_policy"]["rounded_display"] == "1,4"
    assert ex["output_policy"]["requested_formatting"]["used_floating_point"] is False
    assert validate_construction_continuity(e_m["scene3d"]) == []

    # 3. Consecutive SERVED -> REFUSED -> SERVED state isolation
    pa3 = RM_CASES["PA3"]
    r1, e1, a1 = _run_gold(pa3["text"], pa3["payload"])
    bad_p = copy.deepcopy(pa3["payload"])
    bad_p["described_points"][0]["quote"] = "sai hoàn toàn"
    r2, e2, _ = _run_gold(pa3["text"], bad_p)
    r3, e3, a3 = _run_gold(pa3["text"], pa3["payload"])
    assert r1["status"] == "SERVED" and r2["status"] == "REFUSED" and r3["status"] == "SERVED"
    assert a1 == a3 == {"q1": "1"}
    assert e1["scene3d"] == e3["scene3d"]
    # Also ensure registry HARD-PIN (`NO_PLANNER_HARDCODING`): resolver methods carry no hardcoded function literals
    import inspect
    for meth in (planner._EffectResolver._resolve, planner._EffectResolver._emit):
        src = inspect.getsource(meth)
        assert "orthocenter" not in src and "centroid" not in src and "ask_distance" not in src
