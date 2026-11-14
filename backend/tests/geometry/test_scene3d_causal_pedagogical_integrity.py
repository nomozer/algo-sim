# -*- coding: utf-8 -*-
"""Run `scene3d-causal-pedagogical-integrity`: unused-auxiliary flags decided with the source's goals, source data kept
out of visual prerequisites, right angles drawn for perpendicular planes and skew lines, and the causal order of served
Route D scenes. Agent-written development texts; no dataset case id or exact problem text is used by the product.
"""
from __future__ import annotations

import copy
from fractions import Fraction

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import parse_geometry_problem_locally

SQ = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
RB = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _scene(text):
    r = route_text_input(text, allow_live_ai=False).response or {}
    assert (r.get("route_d") or {}).get("status") == "SERVED", text
    return r["envelope"]["scene3d"]


def _route(text):
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    return run_typed_fact_next_v2_route(parse_geometry_problem_locally(text, use_cache=False).payload)


# ── unused auxiliary: decided with the source's goals ──────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text, oid", [
    (SQ + "Gọi M, N lần lượt là trung điểm của SB, SD. Tính khoảng cách từ M đến mặt phẳng (ABCD).", "N"),  # stated, unused
    (SQ + "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD).", "gt_g_il2"),                                  # the asked line
])
def test_a_source_stated_object_is_never_an_unused_auxiliary(text, oid):
    sc = _scene(text)
    assert oid in {o["id"] for o in sc["objects"]}
    assert oid not in sc["unused_auxiliary_ids"] and not any(o.get("is_unused_auxiliary") for o in sc["objects"])


def test_the_recomputation_still_flags_what_only_the_system_added(monkeypatch):
    """Positive control: with no source-gated call behind N, the same scene flags N (the mechanism is not disabled)."""
    from app.ai import function_route as F
    real = F._tinh_lai_phu_tro_du_thua

    def without_calls(state, r):
        fake = copy.copy(r)
        fake.calls = []
        real(state, fake)
    monkeypatch.setattr(F, "_tinh_lai_phu_tro_du_thua", without_calls)
    sc = _scene(SQ + "Gọi M, N lần lượt là trung điểm của SB, SD. Tính khoảng cách từ M đến mặt phẳng (ABCD).")
    assert "N" in sc["unused_auxiliary_ids"]


# ── visible prerequisites hold drawn objects only ──────────────────────────────────────────────────────────────────
def test_source_data_is_not_a_visual_prerequisite():
    from app.simulation.semantic_program.simulation_state import _unwrap_visible_sources
    types = {"I": "point3", "R": "quantity", "O": "point3", "B": "point3", "vec_OB": "vector3", "A": "point3"}
    deps = {"R": [], "vec_OB": ["O", "B"]}
    assert _unwrap_visible_sources(["I", "R"], types, deps) == ["I"]                     # given radius: a number
    assert _unwrap_visible_sources(["A", "vec_OB"], types, deps) == ["A", "O", "B"]      # a vector OB: its points


# ── right angles that `_goc_vuong` cannot mark ─────────────────────────────────────────────────────────────────────
def _gram(sc):
    return [[Fraction(x) for x in r] for r in sc["chart_metric"]]


def _dot(G, u, v):
    return sum(u[i] * G[i][j] * v[j] for i in range(3) for j in range(3))


def _sub(p, q):
    return [Fraction(b) - Fraction(a) for a, b in zip(q, p)]


@pytest.mark.parametrize("goal, relation", [
    ("Tính góc giữa hai mặt phẳng (SAC) và (ABC).", "plane_plane"),
    ("Tính góc giữa hai mặt phẳng (SBC) và (SAB).", "plane_plane"),
    ("Tính góc giữa hai đường thẳng SA và BC.", "line_line_skew"),
])
def test_a_proven_right_angle_without_a_meeting_point_is_drawn(goal, relation):
    sc = _scene(RB + goal)
    q = next(o for o in sc["objects"] if o["id"] == "kq_q1")
    ac = q["angle_construction"]
    assert ac["relation"] == relation and ac["angle_domain"] == "[0°, 90°]"
    G, o = _gram(sc), ac["vertex"]
    a, b = _sub(ac["arms"][0]["to"], o), _sub(ac["arms"][1]["to"], o)
    assert _dot(G, a, b) == 0                                                    # the drawn angle IS a right angle
    if relation == "plane_plane":
        e = [Fraction(x) for x in ac["edge"]["direction"]]
        assert _dot(G, e, a) == 0 and _dot(G, e, b) == 0                       # both rays ⊥ the common line


@pytest.mark.parametrize("goal", ["Tính góc giữa hai đường thẳng SB và BC.", "Tính góc giữa đường thẳng SA và mặt phẳng (ABC)."])
def test_a_right_angle_at_a_meeting_point_keeps_its_marker(goal):
    q = next(o for o in _scene(RB + goal)["objects"] if o["id"] == "kq_q1")
    assert "angle_construction" not in q and q["annotation"]["anchor"] == "witness"


@pytest.mark.parametrize("goal, forged", [
    ("Tính góc giữa hai mặt phẳng (SAC) và (ABC).", "line_plane"),
    ("Tính góc giữa hai đường thẳng SA và BC.", "plane_plane"),
])
def test_a_right_angle_of_another_kind_is_refused(goal, forged, monkeypatch):
    from app.ai import adapter4_route as A
    text = RB + goal
    r = _route(text)
    assert A.build_adapter4_response(r, text)["route_d"]["status"] == "SERVED"
    bad = copy.deepcopy(r)
    next(o for o in bad.scene3d["objects"] if o["id"] == "kq_q1")["angle_construction"]["relation"] = forged
    assert A.build_adapter4_response(bad, text)["route_d"]["status"] == "REFUSED"
    monkeypatch.setattr(A, "_RIGHT_ANGLE_DRAWING", {k: frozenset({forged}) for k in A._RIGHT_ANGLE_DRAWING})
    assert A.build_adapter4_response(bad, text)["route_d"]["status"] == "SERVED"     # fault injection: the binding bites


# ── causal order of served scenes ──────────────────────────────────────────────────────────────────────────────────
def _event_birth(sc):
    birth = {x: 0 for x in sc.get("free_objects") or ()}
    for e in sc["events"]:
        members = [e.get("object"), *(((e.get("details") or {}) if isinstance(e.get("details"), dict) else {}).get("objects") or ())]
        for x in members:
            if x:
                birth.setdefault(x, e["step_index"])
    return birth


@pytest.mark.parametrize("text", [
    SQ + "Gọi M, N lần lượt là trung điểm của SB, SD. Tính khoảng cách từ M đến mặt phẳng (ABCD).",
    SQ + "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD).",
    SQ + "Tính khoảng cách từ A đến mặt phẳng (SBD).",
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a, M là trung điểm của SA, "
    "mặt phẳng (P) đi qua M và song song với mặt đáy. Xác định thiết diện của hình chóp bởi (P).",
    RB + "Tính góc giữa hai mặt phẳng (SAC) và (ABC).",
    RB + "Tính góc giữa hai đường thẳng SA và BC.",
])
def test_every_visual_prerequisite_is_born_first_and_is_drawn(text):
    sc = _scene(text)
    by = {o["id"]: o for o in sc["objects"]}
    birth = _event_birth(sc)
    for e in sc["events"]:
        if e.get("action") != "CREATE" or e.get("object") not in by:
            continue
        for x in by[e["object"]].get("visible_prerequisites") or ():
            assert by[x].get("render") not in ("non_visual", "readout"), (e["object"], x)
            assert birth.get(x, 10**9) <= e["step_index"], (e["object"], x)
    for s in sc["formation"]["steps"]:
        assert isinstance(s.get("readout_ids"), list) and set(s["readout_ids"]) <= set(by)


# ── GEO-BE-V9415-001 on Route D: section vertices explained by the trace method ───────────────────────────────────
PENTA = SQ + "Gọi M, N, P lần lượt là trung điểm của SA, BC, CD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MNP)."
QUAD = SQ + "Gọi M là trung điểm của SA, N là trung điểm của BC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MND)."
PARALLEL = SQ + "Gọi M, N, P lần lượt là trung điểm của SA, SB, SC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (MNP)."


def _edges(sc):
    return [e for e in sc["events"] if e["action"] == "EXTEND"]


@pytest.mark.parametrize("text, theorems", [
    (PENTA, {"COPLANAR_TRACE_INTERSECTION"}),
    (QUAD, {"COPLANAR_TRACE_INTERSECTION"}),
    (PARALLEL, {"PARALLEL_LINE_PLANE_INTERSECTION"}),          # the parallel reason is kept where it applies
])
def test_every_section_edge_has_a_verified_reason(text, theorems):
    es = _edges(_scene(text))
    assert es and all(e.get("justification_text") for e in es)
    assert {e["details"]["justification"]["theorem"] for e in es} == theorems
    assert all(e["details"]["justification"]["verified_exact"] is True for e in es)


def test_the_auxiliary_points_are_the_textbook_intersections_and_keep_one_name():
    sc = _scene(PENTA)
    aux = {}
    for e in _edges(sc):
        for a in e["details"]["justification"]["auxiliary_points"]:
            assert aux.setdefault(a["name"], a["xyz"]) == a["xyz"]          # one letter, one point, on every step
    assert sorted(aux.values()) == [["0", "3/2", "0"], ["3/2", "0", "0"]]   # NP ∩ AD and NP ∩ AB (square of side 1)
    names = {o.get("notation") or o.get("label") for o in sc["objects"]}
    assert not set(aux) & names                                             # never a letter the scene already uses
    sd = next(e for e in _edges(sc) if "SD" in e["learner_text"] and "CD" in e["learner_text"])
    assert "giao điểm của NP và đường thẳng AD" in sd["justification_text"] and "cắt cạnh SD" in sd["justification_text"]


def test_the_trace_derivation_reproduces_the_kernel_section():
    """Every endpoint the derivation reaches is a vertex the kernel computed; a derivation never moves geometry."""
    sc = _scene(PENTA)
    sec = next(o for o in sc["objects"] if o["type"] == "section")
    poly = [list(p) for p in sec["polygon"]]
    for st in sec["steps"]:
        for d in st["trace_derivation"]["derivations"]:
            assert (d["xyz"] in poly) == d["on_edge_segment"]


def test_no_reason_is_claimed_without_known_points(monkeypatch):
    """Fault injection: with no named point of the cutting plane known, the trace method derives nothing."""
    from app.simulation.semantic_program import simulation_state as SS
    real = SS._vet_giao_tuyen_thiet_dien

    def blind(objects):
        real([o for o in objects if o.get("type") != "point3"])
    monkeypatch.setattr(SS, "_vet_giao_tuyen_thiet_dien", blind)
    es = _edges(_scene(PENTA))
    assert not any(e.get("justification_text") for e in es)
