"""Goal-directed composition of Registry functions (run `goal-directed-function-composition`, Hybrid Wave 2A).

The planner composes a producer contract (`centroid`, `midpoint`, `orthogonal_projection_line`, a declared intersection)
with a goal contract (`ask_area`, `ask_length`, `ask_angle_line_plane`, `ask_angle_lines`, distance) by typed slots alone —
no planner branch names a function pair. Expected values come from `_oracle` below: Fraction arithmetic on Euclidean
coordinates written here, independent of the engine's chart, layout and Gram verifiers.
"""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from fractions import Fraction as F

import pytest

from app.ai import fact_extraction
from app.ai.function_calling import _TuChoiAI, parse_response, surface_fingerprint
from app.ai.function_route import run_fact_route
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.registry import TuChoi

# ── independent oracle: Euclidean coordinates of the base problem (square side 2, SA ⊥ base, SA = 3) ─────────────────
PTS = {"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 2, 0), "D": (0, 2, 0), "S": (0, 0, 3)}


def _v(p, q):
    return tuple(F(q[i]) - F(p[i]) for i in range(3))


def _dot(u, v):
    return sum(a * b for a, b in zip(u, v))


def _cross(u, v):
    return (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])


def _point(desc, ops, pts=PTS):
    return tuple(sum(F(pts[o][i]) for o in ops) / len(ops) for i in range(3))  # midpoint (2 ops) / centroid (3 ops)


class _oracle:
    @staticmethod
    def area2(p, q, r):
        c = _cross(_v(p, q), _v(p, r))
        return _dot(c, c) / 4

    @staticmethod
    def len2(p, q):
        return _dot(_v(p, q), _v(p, q))

    @staticmethod
    def dist2_plane(p, a, b, c):
        n = _cross(_v(a, b), _v(a, c))
        return _dot(n, _v(a, p)) ** 2 / _dot(n, n)

    @staticmethod
    def dist2_line(p, a, b):
        c = _cross(_v(a, b), _v(a, p))
        return _dot(c, c) / _dot(_v(a, b), _v(a, b))

    @staticmethod
    def cos2_lines(p, q, a, b):
        u, v = _v(p, q), _v(a, b)
        return _dot(u, v) ** 2 / (_dot(u, u) * _dot(v, v))

    @staticmethod
    def cos2_line_plane(p, q, a, b, c):
        n, w = _cross(_v(a, b), _v(a, c)), _v(p, q)
        return 1 - _dot(n, w) ** 2 / (_dot(n, n) * _dot(w, w))


BASE_TEXT = "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
BASE = [
    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD",
     "solid_type": "pyramid"},
    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 2."],
     "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."],
     "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3."], "points": ["S", "A"], "measure": "segment",
     "value": "3"},
]


def problem(ask: str, **q):
    return BASE_TEXT + ask, {"facts": deepcopy(BASE) + [{"id": "q", "kind": "question", "role": "question",
                                                        "quotes": [ask], **q}]}


def run(text, payload):
    return run_fact_route(text, json.loads(json.dumps(payload)))


def value(r, q="q"):
    v = r.exec_result.final_memory[f"kq_{q}"]
    if r.answers[q].startswith("cos²="):
        return F(v)
    return F(v.he) ** 2 * v.can if hasattr(v, "can") else F(v) ** 2


def chain(r):
    return [d for d in r.planner["auxiliary"] if d.get("rule") == "effect-chain"]


G = _point("centroid", "SBC")
M = _point("midpoint", "SC")
# (id, ask wording, question fields, expected exact value — squared quantity, or cos² for an angle, producer, consumer)
COMPOSITIONS = [
    ("centroid->area", "Tính diện tích tam giác tạo bởi trọng tâm của tam giác SBC và hai điểm A, B.",
     dict(quantity="area", point_kind="centroid", points=["S", "B", "C"], points_b=["A", "B"]),
     _oracle.area2(G, PTS["A"], PTS["B"]), "centroid", "ask_area"),
    ("centroid->length", "Tính độ dài đoạn nối trọng tâm của tam giác SBC với điểm A.",
     dict(quantity="length", point_kind="centroid", points=["S", "B", "C"], points_b=["A"]),
     _oracle.len2(G, PTS["A"]), "centroid", "ask_length"),
    ("centroid->distance-plane", "Tính khoảng cách từ trọng tâm của tam giác SBC đến (SAD).",
     dict(quantity="distance", point_kind="centroid", points=["S", "B", "C"], points_b=["S", "A", "D"]),
     _oracle.dist2_plane(G, PTS["S"], PTS["A"], PTS["D"]), "centroid", "ask_distance_point_plane"),
    ("centroid->projection->length", "Tính khoảng cách từ trọng tâm của tam giác SBC đến AD.",
     dict(quantity="distance", point_kind="centroid", points=["S", "B", "C"], points_b=["A", "D"]),
     _oracle.dist2_line(G, PTS["A"], PTS["D"]), "centroid", "ask_length"),
    ("centroid->angle-line-plane", "Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và (ABCD).",
     dict(quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=["A", "B", "C", "D"]),
     _oracle.cos2_line_plane(PTS["A"], G, PTS["A"], PTS["B"], PTS["C"]), "centroid", "ask_angle_line_plane"),
    ("centroid->angle-lines", "Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và đường thẳng BD.",
     dict(quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=["B", "D"]),
     _oracle.cos2_lines(PTS["A"], G, PTS["B"], PTS["D"]), "centroid", "ask_angle_lines"),
    ("midpoint->angle-line-plane", "Tính góc giữa đường thẳng nối trung điểm của SC với điểm A và (ABCD).",
     dict(quantity="angle", point_kind="midpoint", points=["S", "C"], points_a=["A"], points_b=["A", "B", "C", "D"]),
     _oracle.cos2_line_plane(M, PTS["A"], PTS["A"], PTS["B"], PTS["C"]), "midpoint", "ask_angle_line_plane"),
    ("midpoint->angle-lines", "Tính góc giữa đường thẳng nối B với trung điểm của SC và đường thẳng AC.",
     dict(quantity="angle", point_kind="midpoint", points=["S", "C"], points_a=["B"], points_b=["A", "C"]),
     _oracle.cos2_lines(PTS["B"], M, PTS["A"], PTS["C"]), "midpoint", "ask_angle_lines"),
]


@pytest.mark.parametrize("cid,ask,q,want,producer,consumer", COMPOSITIONS, ids=[c[0] for c in COMPOSITIONS])
def test_producer_and_goal_contracts_compose_without_a_pair_rule(cid, ask, q, want, producer, consumer):
    r = run(*problem(ask, **q))
    assert r.status == "SERVED", (cid, r.code, r.reason)
    assert value(r) == want, (cid, value(r), want)
    fns = {c["fn"] for c in r.planner["calls"]}
    assert {producer, consumer} <= fns, (cid, fns)
    # the described point is checked on the built figure by its DESCRIPTION, independently of the producer chosen
    (cert,) = chain(r)
    assert cert["operand"]["descriptor"] == q["point_kind"]
    lbl, ops = cert["operand"]["label"], cert["operand"]["points"]
    assert all(len(ops) * r.points[lbl][i] == sum(r.points[o][i] for o in ops) for i in range(3))


def test_no_planner_branch_names_a_composed_pair():
    """The search and the goal entry read contracts; they never name a producer/consumer pair they compose. (The older
    `_EffectResolver.distance` certificate names its foot function — a pre-Wave-2A coupling, reported, not used here.)"""
    import inspect
    R = planner._EffectResolver
    src = "".join(inspect.getsource(x) for x in (R._resolve, R._emit, R.goal, R._chuoi, planner._toan_hang_muc_tieu,
                                                  planner._dich_muc_tieu, planner._doc_toan_hang_mo_ta, planner._doi_tac))
    for name in ("centroid", "midpoint", "ask_angle_lines", "ask_angle_line_plane", "ask_area", "ask_length",
                 "orthogonal_projection_line"):
        assert f"'{name}'" not in src and f'"{name}"' not in src, name


@pytest.mark.parametrize("drop,cid", [("centroid", "centroid->angle-lines"), ("ask_angle_lines", "centroid->angle-lines"),
                                      ("ask_angle_line_plane", "midpoint->angle-line-plane")])
def test_removing_one_contract_removes_exactly_that_composition(monkeypatch, drop, cid):
    _cid, ask, q, *_rest = next(c for c in COMPOSITIONS if c[0] == cid)
    monkeypatch.setitem(registry.REGISTRY, drop, replace(registry.REGISTRY[drop], planning=None))
    r = run(*problem(ask, **q))
    assert r.status == "REFUSED" and r.code in ("UNSUPPORTED_CAPABILITY", "FACT_INCOMPLETE"), (r.code, r.reason)


@pytest.mark.parametrize("ask,q", [
    ("Tính góc giữa đường thẳng nối S với trung điểm của BC và (ABCD), và độ dài SC.",
     dict(quantity="angle", point_kind="midpoint", points=["B", "C"], points_a=["S"], points_b=list("ABCD"))),
    ("Tính độ dài đoạn nối trung điểm của BC với điểm S, và góc giữa SC và (ABCD).",
     dict(quantity="length", point_kind="midpoint", points=["B", "C"], points_b=["S"])),
    ("Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và đường thẳng BD, và độ dài SC.",
     dict(quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=["B", "D"])),
])
def test_a_second_ask_after_a_described_goal_is_never_dropped(ask, q):
    """Review N-1 (run goal-directed-function-composition): "với" INSIDE a listed object phrase ("nối S với …") is not a
    given marker; the object asked after it must be covered — refuse REQUEST_NOT_ANSWERED, never serve part."""
    r = run(*problem(ask, **q))
    assert r.status == "REFUSED" and r.code == "REQUEST_NOT_ANSWERED", (r.code, r.reason, r.answers)


def test_a_single_described_goal_with_a_partner_still_serves():
    """Control for the fix above: masking listed object phrases does not stop a lone described goal."""
    ask = "Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và (ABCD)."
    r = run(*problem(ask, quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"],
                     points_b=list("ABCD")))
    assert r.status == "SERVED", (r.code, r.reason)


# ── named angles: direct rules unchanged (trap 1); new line–line primitive ────────────────────────────────────────────
@pytest.mark.parametrize("ask,a,b,want", [
    ("Tính góc giữa SB và AC.", ["S", "B"], ["A", "C"], _oracle.cos2_lines(PTS["S"], PTS["B"], PTS["A"], PTS["C"])),
    ("Tính góc giữa SA và BC.", ["S", "A"], ["B", "C"], F(0)),
    ("Tính góc giữa AB và DC.", ["A", "B"], ["D", "C"], F(1)),
    ("Tính góc giữa hai đường thẳng SC và BD.", ["S", "C"], ["B", "D"],
     _oracle.cos2_lines(PTS["S"], PTS["C"], PTS["B"], PTS["D"])),
])
def test_named_angle_between_lines(ask, a, b, want):
    r = run(*problem(ask, quantity="angle", points_a=a, points_b=b))
    assert r.status == "SERVED", (r.code, r.reason)
    assert value(r) == want and r.answers["q"] == f"cos²={want}"
    assert [c["fn"] for c in r.planner["calls"] if c["fn"].startswith("ask_")] == ["ask_angle_lines"]
    assert not chain(r)                                                     # all named: nothing searched


@pytest.mark.parametrize("ask,a,b,fn", [
    ("Tính góc giữa (SBC) và (ABCD).", ["S", "B", "C"], ["A", "B", "C", "D"], "ask_angle_plane_plane"),
    ("Tính góc giữa SC và (ABCD).", ["S", "C"], ["A", "B", "C", "D"], "ask_angle_line_plane"),
])
def test_named_angles_keep_their_direct_rule(ask, a, b, fn):
    """Trap 1: goal="angle" contracts never pull a named plane–plane or line–plane question into the resolver."""
    r = run(*problem(ask, quantity="angle", points_a=a, points_b=b))
    assert r.status == "SERVED", (r.code, r.reason)
    assert [c["fn"] for c in r.planner["calls"] if c["fn"].startswith("ask_")] == [fn]
    assert not r.planner["auxiliary"] and not any(t.get("step") == "effect_resolution" for t in r.planner["trace"])
    want = _oracle.cos2_line_plane(PTS["S"], PTS["C"], PTS["A"], PTS["B"], PTS["C"]) if fn == "ask_angle_line_plane" else None
    if want is not None:
        assert value(r) == want


def test_plane_perpendicular_to_a_plane_stays_not_unique():
    """Trap 2: a plane through a point perpendicular to a PLANE is not unique — unchanged by Wave 2A."""
    ask = "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng qua S vuông góc với (ABCD)."
    text, payload = problem(ask, quantity="area", solid="S.ABCD", point="S", points_b=["A", "B", "C", "D"],
                            plane_relation="perpendicular")
    with pytest.raises(TuChoi) as e:
        planner.lap_ke_hoach(payload, text)
    assert e.value.code == "PLANE_NOT_UNIQUE"


# ── fail-closed: operands, roles, provenance ─────────────────────────────────────────────────────────────────────────
ANGLE = ("Tính góc giữa đường thẳng nối A với trọng tâm của tam giác SBC và (ABCD).",
         dict(quantity="angle", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=["A", "B", "C", "D"]))


@pytest.mark.parametrize("name,patch,codes", [
    ("two-partners", {"points_a": ["A", "B"]}, {"FACT_INCOMPLETE"}),
    ("partner-hidden-in-target", {"points_a": None, "points_b": ["A", "A", "B", "C"]}, {"FACT_INCOMPLETE"}),
    ("duplicate-target-labels", {"points_b": ["A", "B", "B"]}, {"FACT_INCOMPLETE"}),
    ("one-label-target", {"points_b": ["B"]}, {"FACT_INCOMPLETE"}),
    ("named-point-field", {"point": "G"}, {"SCHEMA_INVALID"}),
    ("centroid-of-four", {"points": ["S", "A", "B", "C"]}, {"FACT_INCOMPLETE"}),
    ("negated", {"negated": True}, {"NEGATED_CLAUSE"}),
    ("prove", {"role": "prove"}, {"GOAL_CLAUSE_NOT_PREMISE"}),
    ("condition", {"role": "condition"}, {"CONDITIONAL_CLAUSE"}),
    ("ambiguous", {"ambiguous": True}, {"AMBIGUOUS_FACT"}),
    ("unknown-partner", {"points_a": ["K"]}, {"UNKNOWN_LABEL"}),
    ("wrong-descriptor", {"point_kind": "midpoint", "points": ["S", "C"]}, {"SOURCE_OBJECT_MISMATCH"}),
    ("wrong-target-plane", {"points_b": ["S", "B", "C"]}, {"SOURCE_OBJECT_MISMATCH"}),
    ("wrong-partner", {"points_a": ["D"]}, {"SOURCE_OBJECT_MISMATCH"}),
])
def test_described_angle_fails_closed(name, patch, codes):
    text, payload = problem(ANGLE[0], **ANGLE[1])
    q = payload["facts"][-1]
    for k, v in patch.items():
        q.pop(k, None) if v is None else q.__setitem__(k, v)
    r = run(text, payload)
    assert r.status == "REFUSED" and r.code in codes, (name, r.code, r.reason, r.answers)
    assert not r.answers and r.scene3d is None


def test_described_area_still_rejects_a_partner_field():
    text, payload = problem("Tính diện tích tam giác tạo bởi trọng tâm của tam giác SBC và hai điểm A, B.",
                            quantity="area", point_kind="centroid", points=["S", "B", "C"], points_a=["A"], points_b=["B"])
    r = run(text, payload)
    assert r.status == "REFUSED" and r.code == "SCHEMA_INVALID", (r.code, r.reason)


def test_lying_goal_verifier_is_refused_at_the_gate(monkeypatch):
    spec = registry.REGISTRY["ask_angle_lines"]
    monkeypatch.setitem(registry.REGISTRY, "ask_angle_lines", replace(spec, planning=replace(spec.planning, verifier="area")))
    _cid, ask, q, *_ = next(c for c in COMPOSITIONS if c[0] == "centroid->angle-lines")
    r = run(*problem(ask, **q))
    assert r.status == "REFUSED" and r.code == "AUXILIARY_RULE_MISMATCH", (r.code, r.reason)


def test_line_line_verifier_is_independent_and_rejects_degenerate_lines():
    assert engine._KIEM_DICH["angle_lines"] is engine._Dung._kc2_goc_hai_duong
    assert registry.GOAL_VERIFIER_TARGET["angle_lines"] == frozenset({"point", "line"})
    d = engine._Dung.__new__(engine._Dung)
    d.pts = {"A": (0, 0, 0), "B": (1, 0, 0), "C": (0, 1, 0)}
    d.g = lambda u, v: sum(a * b for a, b in zip(u, v))
    assert d._goc_hai_duong_cos2(("A", "B"), ("A", "C")) == 0
    d.pts["X"] = (0, 0, 0)
    with pytest.raises(TuChoi) as e:
        d._goc_hai_duong_cos2(("A", "X"), ("A", "C"))
    assert e.value.code == "DEGENERATE_LINE"


# ── bounded search: depth ablation and caps ──────────────────────────────────────────────────────────────────────────
def _result_line_case():
    from tests.geometry.test_function_discovery_planning import by_id
    return by_id("discovery", "centroid-to-result-line")


@pytest.mark.parametrize("depth,served", [(1, set()), (2, {"single"}), (3, {"single", "multi"})])
def test_depth_bound_separates_single_and_multi_step_composition(monkeypatch, depth, served):
    monkeypatch.setattr(planner, "MAX_EFFECT_DEPTH", depth)
    single = run(*problem(COMPOSITIONS[0][1], **COMPOSITIONS[0][2]))   # centroid → area: one producer level
    multi_case = _result_line_case()                                    # centroid + declared line → foot → length
    multi = run_fact_route(multi_case["text"], json.loads(json.dumps(multi_case["payload"])))
    got = {n for n, r in (("single", single), ("multi", multi)) if r.status == "SERVED"}
    assert got == served
    for r in (single, multi):
        if r.status != "SERVED":
            assert r.code == "PLAN_TOO_LARGE", (r.code, r.reason)


def test_search_statistics_stay_within_the_declared_caps():
    for cid, ask, q, *_ in COMPOSITIONS:
        k = planner.lap_ke_hoach(*reversed(problem(ask, **q)))
        rv = k.resolver
        assert rv.needs <= planner.MAX_EFFECT_NEEDS and rv.candidates <= planner.MAX_EFFECT_CANDIDATES, cid
        assert rv.depth_max < planner.MAX_EFFECT_DEPTH and rv.feet <= planner.MAX_RESULT_FEET, cid


def test_a_typed_need_depending_on_itself_is_a_cycle(monkeypatch):
    spec = registry.REGISTRY["orthogonal_projection_line"]
    loop = replace(spec.planning, inputs=(registry.PlanningTerm("Foot", ("F", "P", "L")),))
    monkeypatch.setitem(registry.REGISTRY, "orthogonal_projection_line", replace(spec, planning=loop))
    text, payload = problem("Tính khoảng cách từ trọng tâm của tam giác SBC đến AD.", quantity="distance",
                            point_kind="centroid", points=["S", "B", "C"], points_b=["A", "D"])
    with pytest.raises(TuChoi) as e:
        planner.lap_ke_hoach(payload, text)
    assert e.value.code in ("DEPENDENCY_CYCLE", "UNSUPPORTED_CAPABILITY")


# ── invariance: fact order, label renaming, operand order, scaling ───────────────────────────────────────────────────
@pytest.mark.parametrize("cid", [c[0] for c in COMPOSITIONS])
@pytest.mark.parametrize("transform", ["reverse-facts", "reverse-descriptor", "rename", "scale"])
def test_compositions_are_invariant(cid, transform):
    _cid, ask, q, want, *_ = next(c for c in COMPOSITIONS if c[0] == cid)
    text, payload = problem(ask, **q)
    if transform == "reverse-facts":
        payload["facts"].reverse()
    elif transform == "reverse-descriptor":
        payload["facts"][-1]["points"].reverse()
    elif transform == "rename":                                         # S→T, C→E everywhere (text, facts)
        text, payload = (json.loads(json.dumps(x, ensure_ascii=False).replace("S", "T").replace("C", "E"))
                         for x in (text, payload))
    else:
        text = text.replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6")
        for f in payload["facts"]:
            f["quotes"] = [s.replace("cạnh 2", "cạnh 4").replace("SA = 3", "SA = 6") for s in f["quotes"]]
            if f.get("value") in ("2", "3"):
                f["value"] = str(int(f["value"]) * 2)
        want = want if q["quantity"] == "angle" else want * (16 if q["quantity"] == "area" else 4)
    r = run(text, payload)
    assert r.status == "SERVED", (cid, transform, r.code, r.reason)
    assert value(r) == want, (cid, transform, value(r), want)


# ── Scene3D / IR: fresh points after the solid, dependencies before dependents ────────────────────────────────────────
@pytest.mark.parametrize("cid", [c[0] for c in COMPOSITIONS])
def test_scene_timeline_builds_dependencies_first(cid):
    _cid, ask, q, *_ = next(c for c in COMPOSITIONS if c[0] == cid)
    r = run(*problem(ask, **q))
    steps = r.scene3d["formation"]["steps"]
    assert [s["step_index"] for s in steps] == list(range(len(steps)))
    born: dict[str, int] = {}
    for st in steps:
        for vid in st["visible_ids"]:
            born.setdefault(vid, st["step_index"])
    lbl = engine.ir_name(chain(r)[0]["operand"]["label"])
    assert lbl in born
    assert born[lbl] >= max(born[engine.ir_name(x)] for x in "SABCD")    # the composed point after the solid it lives on
    for obj in r.scene3d["objects"]:
        for dep in obj.get("depends") or ():
            if obj["id"] in born and dep in born:
                assert born[dep] <= born[obj["id"]], (obj["id"], dep)


# ── surfaces: route A and the default extraction contract unchanged; route A never offered the new primitive ─────────
def test_route_a_and_flat_extraction_surfaces_are_unchanged():
    decl = hashlib.sha256(json.dumps(registry.function_declarations(), sort_keys=True, ensure_ascii=False).encode())
    assert decl.hexdigest() == "5ceb0f999d4d7c1ee37c02207ea6470a7f972a168d6c52fa597392934d86f169"
    assert surface_fingerprint() == "7ea511a6e3828c9adcc8402aa2d7d6b1d433e67a01ec4329c3009c46af652b25"
    assert fact_extraction.surface_fingerprint("flat") == "485d3834db8b18cfdb24143bfbb14deb8f5b7a9d74cb612d48db8c08252e507a"
    assert "ask_angle_lines" in registry.REGISTRY and "ask_angle_lines" not in registry.PROVIDER_FUNCTIONS


def test_route_a_refuses_a_function_it_was_not_offered():
    body = {"candidates": [{"finishReason": "STOP", "content": {"parts": [{"functionCall": {
        "name": "ask_angle_lines", "args": {"call_id": "c1", "quotes": ["x"], "line1": ["S", "B"], "line2": ["A", "C"]}}}]}}]}
    with pytest.raises(_TuChoiAI) as e:
        parse_response(body, {"dropped_identical_duplicates": 0})
    assert e.value.code == "FUNCTION_NOT_OFFERED"
