# -*- coding: utf-8 -*-
"""Run `backend-hybrid-contract-unification`: `cut_edges` reading, shared Source Gate, IR canonicalization.

`typed-fact-next/1.cut_edges` means two different things on the two research routes (bridge: the edges the source STATES
are cut; Adapter /3: the COMPLETE section boundary). The schema is not changed here (owner decision, see the run's
CONTRACT_DECISION_PROPOSAL.md); each route instead VERIFIES its own reading, so one payload can never be served with two
different answers. Expected values are closed-form: a plane ∥ base (or ⊥ SA with SA ⊥ base) through M, SM/SA = t, cuts
every lateral edge at t ⇒ V(sub)/V = t³.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from itertools import permutations
import re

import pytest

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.function_route import run_typed_fact_next_planner_route


def _square(coef: str) -> Fraction:
    m = re.fullmatch(r"(?P<p>\d+)?(?:√(?P<r>\d+))?(?:/(?P<q>\d+))?", coef)
    assert m and (m["p"] or m["r"]), coef
    p, r, q = Fraction(m["p"] or 1), Fraction(m["r"] or 1), Fraction(m["q"] or 1)
    return p * p * r / (q * q)


def _payload(base: str = "ABCD", plane: str = "parallel", cut: list[str] | None = None, t: str = "1/2",
             residual: bool = False) -> dict:
    """Pyramid S.<base>, SA ⊥ base, M on SA (SM = t·SA), plane (α) through M; `cut` = the lateral edges the source text
    states are cut (default: every lateral edge except SA, the bridge convention), named N, P, Q in order."""
    b = list(base)
    cut = cut if cut is not None else [f"S{x}" for x in b[1:]]
    fresh = iter("NPQ")
    names = ["M" if e == "SA" else next(fresh) for e in cut]          # the cut on SA is M itself
    shape = ("Đáy ABCD là hình vuông cạnh a.", {"kind": "base_is_square", "args": {"vertices": b, "side": "a"}}) \
        if len(b) == 4 else ("Đáy ABC là tam giác đều cạnh a.",
                             {"kind": "base_is_equilateral_triangle", "args": {"vertices": b, "side": "a"}})
    m_q = "Gọi M là trung điểm của SA." if t == "1/2" else f"Điểm M thuộc cạnh SA sao cho SM = {t} SA."
    m_p = ({"kind": "point_is_midpoint", "args": {"point": "M", "segment": ["S", "A"]}} if t == "1/2" else
           {"kind": "point_divides_segment", "args": {"point": "M", "segment": ["S", "A"], "ratio": t}})
    rel = f"song song với ({base[:3]})" if plane == "parallel" else "vuông góc với SA"
    sec_q = f"Mặt phẳng (α) qua M và {rel} cắt {', '.join(cut)} lần lượt tại {', '.join(names)}."
    sub = f"S.M{''.join(n for e, n in zip(cut, names) if e != 'SA')}"
    ratio_q = f"Tính tỉ số thể tích của hai khối chóp {sub} và S.{base}."
    premises = [shape, ("SA vuông góc với mặt phẳng (ABC).",
                        {"kind": "line_perp_plane", "args": {"line": ["S", "A"], "plane": b[:3]}}),
                ("SA = a.", {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": "a"}}), (m_q, m_p)]
    res_q = f"Tính thể tích phần còn lại của khối chóp S.{base} sau khi cắt bỏ khối chóp {sub}."
    text = " ".join([f"Cho hình chóp S.{base}.", *(q for q, _ in premises), sec_q,
                     f"Dựng thiết diện của hình chóp S.{base} bởi (α).", ratio_q, *([res_q] if residual else [])])
    sec = {"section_id": "sec", "plane_name": "α", "target_solid_id": "pyr", "through_point": "M", "quote": sec_q,
           "cut_edges": [list(e) for e in cut],
           "named_intersections": {f"{e[0]}-{e[1]}": n for e, n in zip(cut, names)}}
    sec.update({"plane_kind": "through_point_parallel_plane", "parallel_plane": b[:3]} if plane == "parallel" else
               {"plane_kind": "through_point_perpendicular_line", "perpendicular_line": ["S", "A"]})
    return {"schema_version": "typed-fact-next/1", "problem_text": text,
            "solids": [{"solid_id": "pyr", "solid_type": "pyramid", "notation": f"S.{base}",
                        "quote": f"Cho hình chóp S.{base}."}],
            "premises": [{**p, "quote": q} for q, p in premises], "derived_sections": [sec],
            "simulation_goals": [
                {"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec",
                 "quote": f"Dựng thiết diện của hình chóp S.{base} bởi (α)."},
                {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                 "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr", "quote": ratio_q}],
            "math_goals": [{"goal_id": "g_ratio", "kind": "volume_ratio", "numerator_solid_id": "sub",
                            "denominator_solid_id": "pyr", "quote": ratio_q},
                           *([{"goal_id": "g_res", "kind": "residual_volume", "parent_solid_id": "pyr",
                               "cut_solid_id": "sub", "quote": res_q}] if residual else [])]}


def _ratio(r) -> Fraction:
    return _square(r.answer_exact["g_ratio"]["coef"])


# ── P1: `cut_edges` — each route verifies its own reading ────────────────────────────────────────────────────────────

def test_bridge_reading_of_stated_cuts_is_served_exactly():
    r = run_typed_fact_next_planner_route(_payload())
    assert r.status == "SERVED", (r.code, r.reason)
    assert _ratio(r) == Fraction(1, 8) ** 2


def test_adapter3_never_serves_a_bridge_style_partial_boundary_as_a_smaller_polygon():
    """Session 1 finding: Adapter /3 read [SB, SC, SD] as the whole boundary and served V(S.NPQ)/V(S.ABCD) (18 cases)."""
    r = run_typed_fact_next_route(_payload())
    assert (r.status, r.code) == ("REFUSED", "SECTION_BOUNDARY_INCOMPLETE"), (r.status, r.code, r.answers)


def test_adapter3_complete_boundary_is_served_with_a_closure_certificate():
    r = run_typed_fact_next_route(_payload(cut=["SA", "SB", "SC", "SD"]))
    assert r.status == "SERVED", (r.code, r.reason)
    assert _ratio(r) == Fraction(1, 8) ** 2
    cert = [v for v in r.verified_relations if v["kind"] == "section_closure"]
    assert len(cert) == 1 and cert[0]["verified"] and cert[0]["details"]["boundary"] == ["M", "N", "P", "Q"]


def test_adapter3_boundary_in_a_crossed_order_is_refused(monkeypatch):
    """Layer test: the source gate already refuses this payload (the text names a pyramid S.MNPQ the crossed cycle does
    not make); with the gate stubbed out, the closure certificate alone must still refuse it."""
    p = _payload(cut=["SA", "SC", "SB", "SD"])
    assert run_typed_fact_next_route(deepcopy(p)).code == "SOURCE_OBJECT_MISMATCH"
    monkeypatch.setattr("app.ai.adapter3_simulation._shared_source_gate", lambda _p: {"authority": "stub"})
    r = run_typed_fact_next_route(p)
    assert (r.status, r.code) == ("REFUSED", "SECTION_BOUNDARY_INCOMPLETE"), (r.status, r.code)


def test_adapter3_partial_boundary_is_refused_by_closure_alone(monkeypatch):
    monkeypatch.setattr("app.ai.adapter3_simulation._shared_source_gate", lambda _p: {"authority": "stub"})
    r = run_typed_fact_next_route(_payload())
    assert (r.status, r.code) == ("REFUSED", "SECTION_BOUNDARY_INCOMPLETE"), (r.status, r.code)


@pytest.mark.parametrize("base,plane", [("ABC", "parallel"), ("ABCD", "parallel"), ("ABC", "perpendicular"),
                                        ("ABCD", "perpendicular")])
def test_one_payload_never_gets_two_different_answers(base, plane):
    """Contract parity on every ordering of every subset of lateral edges: when both routes serve, the answers agree."""
    edges = [f"S{x}" for x in base]
    for n in range(1, len(edges) + 1):
        for cut in permutations(edges, n):
            p = _payload(base, plane, list(cut))
            a, b = run_typed_fact_next_planner_route(deepcopy(p)), run_typed_fact_next_route(deepcopy(p))
            if a.status == b.status == "SERVED":
                assert _ratio(a) == _ratio(b) == Fraction(1, 8) ** 2, cut
            for r in (a, b):
                if r.status == "SERVED":
                    assert _ratio(r) == Fraction(1, 8) ** 2, (cut, r)


def _adapter_convention(p: dict) -> dict:
    """Adapter /3's own corpus convention: no `cut_edges` (every lateral edge; the through-point reused)."""
    q = deepcopy(p)
    q["derived_sections"][0]["cut_edges"] = []
    return q


def _swapped_names() -> dict:
    p = _payload("ABC")
    p["derived_sections"][0]["named_intersections"] = {"S-B": "P", "S-C": "N"}   # text: "cắt SB, SC lần lượt tại N, P"
    return p


def _unread_condition() -> dict:
    p = _payload("ABC")
    p["problem_text"] = p["problem_text"].replace("lần lượt tại N, P.", "lần lượt tại N, P sao cho NP = BC.")
    p["derived_sections"][0]["quote"] = p["derived_sections"][0]["quote"].replace("N, P.", "N, P sao cho NP = BC.")
    return p


def _anonymous_ratio_operand() -> dict:
    p = _payload("ABC")
    sec_q = p["derived_sections"][0]["quote"]
    p["problem_text"] = p["problem_text"].replace(sec_q, sec_q.replace(" lần lượt tại N, P.", ".")) \
        .replace("Tính tỉ số thể tích của hai khối chóp S.MNP và S.ABC.", "Tính tỉ số thể tích.")
    p["derived_sections"][0].update(quote=sec_q.replace(" lần lượt tại N, P.", "."), named_intersections={})
    for g in (*p["simulation_goals"][1:], *p["math_goals"]):
        g["quote"] = "Tính tỉ số thể tích."
    return p


@pytest.mark.parametrize("make", [
    _swapped_names, _unread_condition,
    # Known gap, locked: in Adapter /3's own convention (no stated cut) the bridge cannot express the payload, so the gate
    # has no verdict and Adapter /3 still serves on its legacy checks, labelled. Closing it = owner decision D2.
    pytest.param(_anonymous_ratio_operand, marks=pytest.mark.xfail(strict=True, reason="owner decision D2 pending")),
])
def test_adapter3_refuses_what_the_shared_source_gate_refuses(make):
    """Session 1 finding: Adapter /3's substring checks served these three invalid inputs; the Registry Source Gate (via
    the bridge) refuses them. Adapter /3 must take the SAME verdict — the same code when the gate read the payload."""
    for payload in (make(), _adapter_convention(make())):
        gate = run_typed_fact_next_planner_route(deepcopy(payload))
        assert gate.status == "REFUSED", (gate.code, gate.answers)
        r = run_typed_fact_next_route(payload)
        assert (r.status, r.code) == ("REFUSED", gate.code), (r.status, r.code, gate.code, r.answers)


def test_every_served_adapter3_result_names_its_source_authority():
    gated = run_typed_fact_next_route(_payload(cut=["SA", "SB", "SC", "SD"]))
    legacy = run_typed_fact_next_route(_adapter_convention(_anonymous_ratio_operand()))
    assert gated.status == legacy.status == "SERVED", (gated.code, legacy.code)
    assert gated.source_verification == {"authority": "registry.kiem_nguon"}
    assert legacy.source_verification == {"authority": "adapter3.substring_legacy",
                                          "gate_unavailable": "BRIDGE_CUT_EDGES_NOT_STATED"}
    assert gated.scene3d["simulation_contract"]["source_verification"] == gated.source_verification


def test_adapter3_polyhedral_plane_kind_without_a_construction_refuses_not_crashes():
    p = _payload(base="ABC")
    p["derived_sections"][0].update(plane_kind="plane_equation", equation_coeffs=("0", "0", "1", "-1"))
    r = run_typed_fact_next_route(p)
    assert (r.status, r.code) == ("REFUSED", "UNSUPPORTED_PLANE_KIND"), (r.status, r.code)


# ── P4: IR canonicalization — one object per identical derived construction ─────────────────────────────────────────

def _derived_constructs(program: dict) -> list[tuple]:
    return [(st["kind"], st.get("through_a"), st.get("through_b"), tuple(st.get("through") or ()))
            for st in program["statements"] if st["kind"] in ("construct_line", "construct_plane")
            and st["target_var"].startswith("derived_")]


@pytest.mark.parametrize("base", ["ABC", "ABCD"])
@pytest.mark.parametrize("plane", ["parallel", "perpendicular"])
def test_identical_derived_lines_and_planes_are_declared_once(base, plane):
    """Session 1: 9/49 quadrilateral ⊥-plane residual plans hit IR_MEMORY_BUDGET_EXCEEDED (33 > 32) because every cut
    vertex re-declared the same section plane and both perpendicular feet re-declared line SA. The budget stays 32."""
    from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS

    r = run_typed_fact_next_planner_route(_payload(base, plane, residual=True))
    assert r.status == "SERVED", (r.code, r.reason)
    assert MAX_MEMORY_DECLARATIONS == 32
    assert len(r.program["memory_declarations"]) <= MAX_MEMORY_DECLARATIONS
    d = _derived_constructs(r.program)
    assert len(d) == len(set(d)), d
    names = [m["name"] for m in r.program["memory_declarations"]]
    assert len(names) == len(set(names))
    v_sq = (Fraction(1) if base == "ABCD" else Fraction(3, 16)) / 9   # V² = S²·h²/9, side a, h = a; triangle S² = 3/16
    assert _ratio(r) == Fraction(1, 64)
    assert _square(r.answer_exact["g_res"]["coef"]) == Fraction(7, 8) ** 2 * v_sq


# ── P5: Scene3D semantics once the teaching expansion fits the budget ──────────────────────────────────────────────

def _anonymous_construction(base: str) -> dict:
    """Construction only, unnamed cuts: "… cắt SB, SC, SD. Dựng khối chóp đỉnh S cắt bởi (α)." """
    p = _payload(base)
    sec = p["derived_sections"][0]
    plain = re.sub(r" lần lượt tại [^.]*\.", ".", sec["quote"])
    ask = "Dựng khối chóp đỉnh S cắt bởi (α)."
    p["problem_text"] = p["problem_text"].replace(sec["quote"], plain).split(" Tính tỉ số")[0] + " " + ask
    sec.update(quote=plain, named_intersections={})
    p["simulation_goals"][1]["quote"] = ask
    p["math_goals"] = []
    return p


@pytest.mark.parametrize("base", ["ABC", "ABCD"])
def test_fresh_cut_labels_never_reach_the_learner_and_derived_edges_are_named_as_such(base):
    """Canonicalization lets the formation expansion of the derived pyramid fit the budget (square base); its base polygon
    and lateral edges must not speak planner labels (I, I1, …), and a lateral edge is not 'a segment of the section'."""
    r = run_typed_fact_next_planner_route(_anonymous_construction(base))
    assert r.status == "SERVED", (r.code, r.reason)
    fresh = next(d for d in r.planner["auxiliary"] if d.get("vertices"))["labels"]
    tok = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(map(re.escape, fresh)) + r")[A-Z0-9'.]*(?![\w'])")
    sc = r.scene3d
    text = [str(o.get(k)) for o in sc["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    text += [str(e.get(k)) for e in sc["events"] for k in ("display_label", "learner_text", "explanation")]
    text += [s.get("learner_text", "") for s in sc["formation"]["steps"]]
    assert [s for s in text if tok.search(s)] == []
    edges = [o for o in sc["objects"] if o["id"].startswith("canh_ben_S_") and any(o["id"].endswith(f"_{x}") for x in fresh)]
    assert all(o["label"] == "Cạnh bên của khối chóp đỉnh S cắt bởi (α)" for o in edges), edges


def test_a_served_curved_adapter3_result_is_labelled_legacy_source_authority():
    """The planner has no curved solids, so a served curved result was verified by Adapter /3's legacy checks only."""
    q = "Cho mặt cầu (S) tâm I bán kính R = 5"
    sec = "Mặt phẳng (α) có phương trình z - 3 = 0 cắt mặt cầu theo một đường tròn giao tuyến"
    r = run_typed_fact_next_route({
        "schema_version": "typed-fact-next/1", "problem_text": f"{q}. {sec}. Tính thể tích khối cầu.",
        "solids": [{"solid_id": "sph", "solid_type": "sphere", "notation": "(S)", "center": "I", "radius": "5", "quote": q}],
        "derived_sections": [{"section_id": "s", "plane_name": "α", "target_solid_id": "sph", "plane_kind": "plane_equation",
                              "equation_coeffs": ["0", "0", "1", "-3"], "section_shape": "circle", "quote": sec}],
        "simulation_goals": [{"goal_id": "g", "kind": "construct_plane_section", "target_section_id": "s", "quote": sec}],
        "math_goals": [{"goal_id": "v", "kind": "measurement", "goal_type": "volume", "target": {"solid": "sph"},
                        "quote": "Tính thể tích khối cầu"}]})
    assert r.status == "SERVED", (r.code, r.reason)
    assert r.source_verification == {"authority": "adapter3.substring_legacy", "gate_unavailable": "BRIDGE_UNSUPPORTED_CURVED"}
