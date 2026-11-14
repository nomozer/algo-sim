# -*- coding: utf-8 -*-
"""Run `proof-soundness-generalized-angle-invariance`: the structured angle witness, goal/value binding, and the
generalized angle goals (perpendicular planes, line–plane, line–line incl. skew) of `target-invariance-certificate/2`.

Agent-written development texts; no dataset case id or exact problem text is used by the product.
"""
from __future__ import annotations

import ast
import copy
import inspect
from types import SimpleNamespace

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions import planner, target_invariance as ti
from app.simulation.geometry_functions.registry import doc_ke_hoach
from app.simulation.geometry_functions.target_invariance import prove_angle_goal, verify_target_invariance_certificate
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2

H = "Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và "
PLANES = "Tính góc giữa hai mặt phẳng (SBC) và (ABC)."
D = ti.ANGLE_DOMAIN


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _rd(text):
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def _calls(text):
    lp = parse_geometry_problem_locally(text, use_cache=False)
    pl = planner.lap_ke_hoach({"facts": bridge_v2(lp.parsed_contract)["facts"]}, text)
    return doc_ke_hoach({"calls": pl.calls})


def _proof(text):
    calls = _calls(text)
    ask = next(c for c in calls if c.fn in ti.GOAL_FUNCTIONS)
    return prove_angle_goal(calls, ask), calls, ask


def _ok(cert, calls, ask):
    return verify_target_invariance_certificate(cert, calls, ask)["verified"]


def _step(c, rule):
    return next(s for s in c["steps"] if s["rule"] == rule)


# ── P0: the r520 witness defect ────────────────────────────────────────────────────────────────────────────────────
def test_the_r520_vertex_first_triple_certificate_is_not_accepted():
    """/1 wrote the plane angle as `equals_angle: ["B", "S", "A"]` with the vertex FIRST; read in standard notation that
    is ∠BSA (vertex S). No /1 certificate, and no bare triple, is accepted any more."""
    cert, calls, ask = _proof(H + "SA = AB. " + PLANES)
    old = copy.deepcopy(cert)
    old["schema_version"] = "target-invariance-certificate/1"
    _step(old, "PLANE_ANGLE")["conclusion"] = {"intersection": ["B", "C"], "equals_angle": ["B", "S", "A"]}
    assert _ok(old, calls, ask) is False
    old["schema_version"] = ti.TARGET_INVARIANCE_VERSION                # even relabelled /2, the bare triple is malformed
    assert verify_target_invariance_certificate(old, calls, ask)["failed_step"] == _step(old, "PLANE_ANGLE")["id"]


def test_the_non_isosceles_counterexample_distinguishes_the_two_readings():
    """SA = 2AB: ∠SBA (at B, the plane angle) has cos² 1/5; ∠BSA (at S, the standard reading of the /1 triple) has
    cos² 4/5. The served value is 1/5 and a certificate re-pointed to vertex S fails even when internally consistent."""
    rd = _rd(H + "SA = 2AB. " + PLANES)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == "1/5"
    cert, calls, ask = _proof(H + "SA = 2AB. " + PLANES)
    assert cert["conclusion"]["witness"]["vertex"] == "B" and cert["conclusion"]["cos_sq"] == "1/5"
    bad = copy.deepcopy(cert)
    w = {"vertex": "S", "ray_1": ["S", "B"], "ray_2": ["S", "A"], "domain": D}
    _step(bad, "PLANE_ANGLE")["conclusion"]["witness"] = w
    sh = _step(bad, "TRIANGLE_SHAPE_FIXED")["conclusion"]
    sh.update(angle_at="S", cos_sq="4/5")                                 # the shape step made consistent with vertex S
    bad["conclusion"].update(witness=w, cos_sq="4/5")
    assert _ok(bad, calls, ask) is False


def test_a_shape_fixed_at_another_vertex_is_rejected_even_when_the_figure_makes_it_equal():
    """SA = AB: ∠ASB = ∠SBA = 45°. A shape step at S proves the right NUMBER for the wrong angle; /1 accepted that."""
    cert, calls, ask = _proof(H + "SA = AB. " + PLANES)
    bad = copy.deepcopy(cert)
    _step(bad, "TRIANGLE_SHAPE_FIXED")["conclusion"]["angle_at"] = "S"
    assert _step(bad, "TRIANGLE_SHAPE_FIXED")["conclusion"]["cos_sq"] == "1/2"
    assert _ok(bad, calls, ask) is False


def test_a_certificate_is_bound_to_the_goal_it_was_proven_for():
    cert, calls, ask = _proof(H + "SA = AB. " + PLANES)
    other = SimpleNamespace(id=ask.id, fn="ask_angle_plane_plane", args={"plane1": ["S", "A", "C"], "plane2": ["A", "B", "C"]})
    assert _ok(cert, calls, other) is False                                # same id, other planes
    assert _ok(cert, calls, SimpleNamespace(id="q9", fn=ask.fn, args=ask.args)) is False
    assert verify_target_invariance_certificate(cert, calls)["verified"] is False   # no goal ⇒ never verified


def test_the_engine_binds_the_proven_value_to_the_kernel(monkeypatch):
    """TI-6: a verified certificate whose cos² is not the kernel's answer is refused (fault injection)."""
    real = ti.prove_angle_goal

    def lying(calls, goal):
        c = real(calls, goal)
        c["conclusion"]["cos_sq"] = "1/3"
        _step(c, "TRIANGLE_SHAPE_FIXED")["conclusion"]["cos_sq"] = "1/3"
        return c

    monkeypatch.setattr(ti, "verify_target_invariance_certificate", lambda cert, calls, goal=None: {"verified": True})
    monkeypatch.setattr(ti, "prove_angle_goal", lying)
    assert _rd(H + "SA = 2AB. " + PLANES)["status"] != "SERVED"


# ── existing rules: every rule has a mutation the verifier catches ─────────────────────────────────────────────────
def _set(rule, key, value):
    return lambda c: _step(c, rule)["conclusion"].__setitem__(key, value)


MUTATIONS = [
    (H + "SA = AB. " + PLANES, "RIGHT_ANGLE", _set("RIGHT_ANGLE", "perpendicular", [["A", "B"], ["A", "C"]])),
    ("Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), AB vuông góc với BC và SA = AB. " + PLANES,
     "PERPENDICULAR_LINES", _set("PERPENDICULAR_LINES", "perpendicular", [["A", "B"], ["A", "C"]])),
    (H + "SA = AB. " + PLANES, "SOURCE_LINE_PERP_PLANE", _set("SOURCE_LINE_PERP_PLANE", "line_perp_plane", [["B", "S"], ["A", "B", "C"]])),
    (H + "SA = AB. " + PLANES, "PERP_PLANE_TO_LINE", _set("PERP_PLANE_TO_LINE", "perpendicular", [["A", "S"], ["S", "C"]])),
    (H + "SA = AB. " + PLANES, "PERP_TWO_LINES", _set("PERP_TWO_LINES", "line_perp_plane", [["B", "C"], ["A", "C", "S"]])),
    (H + "SA = AB. " + PLANES, "TRIANGLE_SHAPE_FIXED", _set("TRIANGLE_SHAPE_FIXED", "by", "RIGHT_AT_B_LEG_RATIO")),
    (H + "SA = AB. " + PLANES, "TRIANGLE_SHAPE_FIXED", _set("TRIANGLE_SHAPE_FIXED", "cos_sq", "1/3")),
    (H + "SA = AB. " + PLANES, "PLANE_ANGLE", _set("PLANE_ANGLE", "intersection_line", ["A", "C"])),
    (H + "SA = AB. " + PLANES, "PLANE_ANGLE", _set("PLANE_ANGLE", "witness",
                                                     {"vertex": "C", "ray_1": ["C", "S"], "ray_2": ["C", "A"], "domain": D})),
    (H + "SA = AB. " + PLANES, "PLANE_ANGLE", _set("PLANE_ANGLE", "witness",
                                                     {"vertex": "B", "ray_1": ["B", "S"], "ray_2": ["B", "A"], "domain": "ORIENTED"})),
    (H + "SA = AB. Tính góc giữa hai mặt phẳng (SAC) và (ABC).", "PERP_PLANES",
     _set("PERP_PLANES", "contained_line", ["S", "C"])),
    (H + "SA = AB. Tính góc giữa đường thẳng SB và mặt phẳng (ABC).", "LINE_PLANE_ANGLE",
     _set("LINE_PLANE_ANGLE", "foot", "C")),
    (H + "SA = AB. Tính góc giữa đường thẳng SA và mặt phẳng (ABC).", "LINE_PERP_PLANE_ANGLE",
     _set("LINE_PERP_PLANE_ANGLE", "cos_sq", "1/2")),
    (H + "SA = AB. Tính góc giữa hai đường thẳng SB và SA.", "LINE_ANGLE",
     _set("LINE_ANGLE", "witness", {"vertex": "A", "ray_1": ["A", "S"], "ray_2": ["A", "B"], "domain": D})),
    (H + "SA = AB. Tính góc giữa hai đường thẳng SA và BC.", "LINES_PERPENDICULAR",
     _set("LINES_PERPENDICULAR", "line_2", ["A", "C"])),
]


@pytest.mark.parametrize("text, rule, mutate", MUTATIONS, ids=[f"{m[1]}-{i}" for i, m in enumerate(MUTATIONS)])
def test_every_rule_has_a_mutation_the_verifier_catches(text, rule, mutate):
    cert, calls, ask = _proof(text)
    assert _ok(cert, calls, ask) is True and rule in {s["rule"] for s in cert["steps"]}
    bad = copy.deepcopy(cert)
    mutate(bad)
    assert _ok(bad, calls, ask) is False


def test_every_rule_is_covered_by_a_mutation():
    assert {m[1] for m in MUTATIONS} == set(ti.RULES)


def test_dropping_a_premise_step_or_adding_an_unknown_rule_is_caught():
    cert, calls, ask = _proof(H + "SA = AB. " + PLANES)
    for mutate in (lambda c: c["steps"].pop(0), lambda c: c["steps"].insert(0, {"id": "x", "rule": "PARALLEL"}),
                   lambda c: c["steps"].append(copy.deepcopy(_step(c, "PLANE_ANGLE")) | {"id": "t99"})):
        bad = copy.deepcopy(cert)
        mutate(bad)
        assert _ok(bad, calls, ask) is False


def test_the_verifier_never_calls_the_search():
    tree = ast.parse(inspect.getsource(ti.verify_target_invariance_certificate))
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not names & {"_Search", "_prove", "prove_angle_goal", "_finish", "_closure"}


# ── P1: generalized angle goals ────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text, coef, last_rule", [
    (H + "SA = AB. Tính góc giữa hai mặt phẳng (SAC) và (ABC).", "0", "PERP_PLANES"),
    (H + "SA = AB. Tính góc giữa hai mặt phẳng (SBC) và (SAB).", "0", "PERP_PLANES"),
    (H + "SA = AB. Tính góc giữa đường thẳng SB và mặt phẳng (ABC).", "1/2", "TRIANGLE_SHAPE_FIXED"),
    (H + "SA = 2AB. Tính góc giữa đường thẳng SB và mặt phẳng (ABC).", "1/5", "TRIANGLE_SHAPE_FIXED"),
    (H + "SA = AB. Tính góc giữa đường thẳng SA và mặt phẳng (ABC).", "0", "LINE_PERP_PLANE_ANGLE"),
    (H + "SA = AB. Tính góc giữa hai đường thẳng SB và BC.", "0", "LINES_PERPENDICULAR"),
    (H + "SA = AB. Tính góc giữa hai đường thẳng SA và BC.", "0", "LINES_PERPENDICULAR"),       # skew lines
    (H + "SA = AB. Tính góc giữa hai đường thẳng SB và SA.", "1/2", "TRIANGLE_SHAPE_FIXED"),
    ("Cho hình chóp T.XYZ có đáy là tam giác vuông tại Y, TX vuông góc với đáy và TX = 2XY. "
     "Tính góc giữa đường thẳng TY và mặt phẳng (XYZ).", "1/5", "TRIANGLE_SHAPE_FIXED"),       # renamed
])
def test_generalized_angle_goals_are_proven_and_served(text, coef, last_rule):
    cert, calls, ask = _proof(text)
    assert _ok(cert, calls, ask) is True and cert["conclusion"]["cos_sq"] == coef
    assert cert["steps"][-1]["rule"] == last_rule
    rd = _rd(text)
    assert rd["status"] == "SERVED" and rd["answer_exact"]["q1"]["coef"] == coef
    assert rd["scene_configuration"]["kind"] == "TARGET_INVARIANT_ILLUSTRATIVE"


@pytest.mark.parametrize("text", [
    H + "SA = AB. Tính góc giữa hai đường thẳng SC và AB.",          # skew, cos depends on BC
    H + "SA = AB. Tính góc giữa đường thẳng SC và mặt phẳng (SAB).",  # ∠CSB, BC : SB free
    H + "SA = AB. Tính góc giữa đường thẳng SC và mặt phẳng (ABC).",  # ∠SCA, AC free
    "Cho hình chóp S.ABC có đáy là tam giác vuông tại B và SA vuông góc với đáy. "
    "Tính góc giữa đường thẳng SB và mặt phẳng (ABC).",               # no ratio: varies with the height
    "Cho hình lăng trụ đứng ABC.A'B'C' có đáy là tam giác vuông tại B và AA' = AB. "
    "Tính góc giữa hai mặt phẳng (A'BC) và (ABC).",                    # prism: outside the proof domain
])
def test_varying_or_out_of_domain_goals_get_no_proof_and_are_refused(text):
    cert, _calls_, _ask = _proof(text)
    assert cert is None
    assert _rd(text)["status"] != "SERVED"


# ── proof ↔ scene binding (adapter) ────────────────────────────────────────────────────────────────────────────────
# Each forgery is CONSISTENT (engine details and envelope agree, drawn points are real kernel points), so only the
# proof ↔ scene binding can catch it; `test_the_scene_binding_is_what_catches_them` removes it and sees them pass.
def _cfgs(r):
    return [r.details["scene_configuration"], r.route_d["scene_configuration"]]


def _both(f):
    return lambda r: [f(c["invariance_certificate"]["goals"][0]) for c in _cfgs(r)]


def _draw_at(vertex, ends):
    def f(r):
        pts = {o["id"]: o["xyz"] for o in r.scene3d["objects"] if o["type"] == "point3"}
        ac = next(o for o in r.scene3d["objects"] if o.get("angle_construction"))["angle_construction"]
        ac.update(vertex_id=vertex, vertex=list(pts[vertex]))
        for arm, e in zip(ac["arms"], ends):
            arm.update(to_id=e, to=list(pts[e]))
        ac.pop("perpendicular", None)
    return f


SCENE_FORGERIES = [
    (H + "SA = 2AB. " + PLANES, _draw_at("S", ("B", "A"))),                                  # ∠BSA drawn, ∠SBA proven
    (H + "SA = 2AB. " + PLANES, _both(lambda g: g["conclusion"]["witness"].__setitem__("vertex", "S"))),
    (H + "SA = 2AB. " + PLANES, _both(lambda g: g["conclusion"].__setitem__("cos_sq", "4/5"))),
    (H + "SA = 2AB. " + PLANES, _both(lambda g: g["independent_verification"].__setitem__("verified", False))),
    (H + "SA = 2AB. " + PLANES, lambda r: [c["invariance_certificate"].__setitem__(
        "schema_version", "target-invariance-certificate/1") for c in _cfgs(r)]),
    (H + "SA = AB. Tính góc giữa hai đường thẳng SB và SA.", _draw_at("S", ("B", "C"))),
]


@pytest.mark.parametrize("text, mutate", SCENE_FORGERIES)
def test_the_scene_is_bound_to_the_proof(text, mutate):
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    r = run_typed_fact_next_v2_route(parse_geometry_problem_locally(text, use_cache=False).payload)
    assert build_adapter4_response(r, text)["route_d"]["status"] == "SERVED"
    m = copy.deepcopy(r)
    mutate(m)
    assert build_adapter4_response(m, text)["route_d"]["status"] == "REFUSED"


def test_the_envelope_cannot_drop_or_change_the_configuration():
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    text = H + "SA = 2AB. " + PLANES
    r = run_typed_fact_next_v2_route(parse_geometry_problem_locally(text, use_cache=False).payload)
    m = copy.deepcopy(r)
    m.route_d.pop("scene_configuration")
    assert build_adapter4_response(m, text)["route_d"]["status"] == "REFUSED"


def test_the_scene_binding_is_what_catches_them(monkeypatch):
    """Fault injection: without `_invariance_proof_bound` every forgery above is SERVED."""
    from app.ai import adapter4_route as a

    monkeypatch.setattr(a, "_invariance_proof_bound", lambda *x: True)
    for text, mutate in SCENE_FORGERIES:
        r = a.run_typed_fact_next_v2_route(parse_geometry_problem_locally(text, use_cache=False).payload)
        m = copy.deepcopy(r)
        mutate(m)
        assert a.build_adapter4_response(m, text)["route_d"]["status"] == "SERVED"


def test_the_proof_search_is_budgeted(monkeypatch):
    monkeypatch.setattr(ti, "MAX_DERIVED", 2)
    cert, _c, _a = _proof(H + "SA = AB. " + PLANES)
    assert cert["status"] == "PROOF_SEARCH_BUDGET_EXCEEDED"
    assert _rd(H + "SA = AB. " + PLANES)["status"] != "SERVED"


# ── degenerate goals and points outside the proof domain ───────────────────────────────────────────────────────────
@pytest.mark.parametrize("fn, args", [
    ("ask_angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["C", "B", "S"]}),        # the same plane twice
    ("ask_angle_plane_plane", {"plane1": ["S", "B"], "plane2": ["A", "B", "C"]}),             # two labels are no plane
    ("ask_angle_plane_plane", {"plane1": ["S", "A", "B", "C"], "plane2": ["A", "B", "C"]}),   # four non-coplanar labels
    ("ask_angle_lines", {"line1": ["S", "S"], "line2": ["B", "C"]}),                           # a repeated label
    ("ask_angle_lines", {"line1": ["S", "B"], "line2": ["B", "S"]}),                           # the same line twice
    ("ask_angle_line_plane", {"line": ["A", "B"], "plane": ["A", "B", "C"]}),                  # the line lies in the plane
    ("ask_angle_line_plane", {"line": ["S", "X"], "plane": ["A", "B", "C"]}),                  # a label of no solid
])
def test_degenerate_goals_get_no_proof(fn, args):
    calls = _calls(H + "SA = AB. " + PLANES)
    assert prove_angle_goal(calls, SimpleNamespace(id="q1", fn=fn, args=args)) is None


def test_a_witness_with_one_ray_twice_is_rejected():
    cert, calls, ask = _proof(H + "SA = AB. " + PLANES)
    bad = copy.deepcopy(cert)
    _step(bad, "PLANE_ANGLE")["conclusion"]["witness"]["ray_2"] = ["B", "S"]
    assert _ok(bad, calls, ask) is False


def test_a_derived_point_is_outside_the_proof_domain():
    text = H + "SA = AB. Gọi M là trung điểm của BC. Tính góc giữa đường thẳng SM và mặt phẳng (ABC)."
    calls = _calls(text)
    ask = next((c for c in calls if c.fn in ti.GOAL_FUNCTIONS), None)
    assert ask is None or prove_angle_goal(calls, ask) is None
    assert _rd(text)["status"] != "SERVED"
