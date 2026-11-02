"""C18 genuine function composition on Hybrid /4: a point the source names only by a PROPERTY ("trực tâm của tam giác
CDM", "tâm đường tròn ngoại tiếp tam giác CDM") has no Registry function. The planner must regress its definition into
loci, find a producer for each locus from function contracts, and compose them; the engine checks the definition.

Cases come from the independent oracle `tools/composition_oracle.py` (no product import). Hand check on the pyramid
S.ABCD, square side 2, SA ⊥ (ABCD), SA = 2: A(0,0,0) B(2,0,0) C(2,2,0) D(0,2,0) S(0,0,2), M = mid AB = (1,0,0),
N = mid SC = (1,1,1).
- CDM is isosceles at M: its altitude from M is x = 1; the altitude from C ⊥ DM = (1,−2,0) meets it at y = 3/2 ⇒
  H = (1, 3/2, 0), at 3/2 from (SAB) (y = 0).
- Its circumcentre is on x = 1 with (5/4)² = 1 + (2 − y)² ⇒ y = 5/4 ⇒ O = (1, 5/4, 0), at 5/4 from (SAB).
- CSM: H = (1, −1/2, −1/2) (the oracle's linear solve), AH² = 3/2 ⇒ √6/2.
"""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry_functions import planner, registry

RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement"
_spec = importlib.util.spec_from_file_location("c18_composition_oracle", RUN / "tools" / "composition_oracle.py")
O = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(O)
CASES = {c["id"]: c for c in O.cases(topologies=O.TOPOLOGIES[:1], search=False)}
POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
H_CDM, O_CDM, H_CSM = ("pyramid(2,2)|orthocenter|CDM|G1", "pyramid(2,2)|circumcenter|CDM|G1",
                       "pyramid(2,2)|orthocenter|CSM|G2")


def _run(text, payload):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route = out.response["route_d"]
    answers = ({k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()}
               if route["status"] == "SERVED" else None)
    return route, out.response["envelope"], answers


def _case(cid):
    c = CASES[cid]
    return _run(c["text"], c["payload"])


def _chain(route):
    return next(d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain")


@pytest.mark.parametrize("cid,want", [(H_CDM, "3/2"), (O_CDM, "5/4"), (H_CSM, "√6/2")])
def test_c18_a_property_defined_point_is_served_by_a_composition_the_planner_found(cid, want):
    assert CASES[cid]["necessity"] == "COMPOSITION_NECESSARY"        # the oracle: no single Registry call reaches it
    route, env, answers = _case(cid)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": want}
    tel = route["planner"]["search_telemetry"]
    # review MAJOR-1/2: the definition is a declared rule (C17 standard) — necessary composition, not discovery
    assert tel["classification"] == "REGISTERED_DECOMPOSITION" and not tel["search_generated_steps"]
    assert registry.DINH_NGHIA_DIEM in registry.AUXILIARY_RULES
    d = _chain(route)
    fns = [e["fn"] for e in d["chain"]]
    assert "orthogonal_projection_line" in fns and "intersect_line_line" in fns and fns[-1].startswith("ask_")
    assert d["definition"]["descriptor"] == CASES[cid]["center"]           # what the source named, built by no function
    assert env["scene3d"]["objects"] and route["construction_trace"]


def test_c18_orthocenter_meets_two_altitudes_each_through_a_foot_the_source_never_names():
    route, _env, _a = _case(H_CDM)
    d = _chain(route)
    feet = [e for e in d["chain"] if e["fn"] == "orthogonal_projection_line"]
    meet = next(e for e in d["chain"] if e["fn"] == "intersect_line_line")
    assert len(feet) == 2 and all(e["fresh"] for e in feet)
    # every fresh foot is consumed by the meet: line i passes through its vertex and its foot
    lines = [set(meet["env"]["L1"][1]), set(meet["env"]["L2"][1])]
    assert all(any(f["env"]["X"] in ln for ln in lines) for f in feet)
    assert set(route["planner"]["search_telemetry"]["registered_decomposition_steps"]) >= {e["call"] for e in feet}


def test_c18_circumcenter_cannot_use_the_foot_of_a_midpoint_on_its_own_side_and_translates_instead():
    route, _env, _a = _case(O_CDM)
    d = _chain(route)
    fns = [e["fn"] for e in d["chain"]]
    assert {"midpoint", "orthogonal_projection_line", "translate_point", "intersect_line_line"} <= set(fns)
    rejected = [r for s in d["search"]["loci"] for r in s["rejected"]]
    assert rejected and all(r["reason"] == "precondition: the point lies on the line" for r in rejected)


def test_c18_a_collinear_triangle_is_refused_never_served():
    route, env, _a = _case("pyramid(2,2)|orthocenter|ABM|G1")
    assert route["status"] == "REFUSED", env.get("reason_code")


def test_c18_the_definition_resolver_has_no_function_name_literal():
    """A string check only (review MINOR-1): the meet IS chosen by signature (exactly one `Point ← Line, Line` contract)
    and a locus line is bound through `contract.line` — so this proves no literal, not independence from the library."""
    src = Path(planner.__file__).read_text(encoding="utf-8")
    body = src[src.index("    def _dinh_nghia("):src.index("    def _emit(")]
    assert not any(f'"{fn}"' in body or f"'{fn}'" in body for fn in registry.REGISTRY)
    assert set(registry.POINT_DEFINITIONS) == {"orthocenter", "circumcenter"}


def test_c18_without_the_translate_locus_contract_the_circumcenter_is_refused_and_the_orthocenter_survives(monkeypatch):
    spec = registry.REGISTRY["translate_point"]
    monkeypatch.setitem(registry.REGISTRY, "translate_point",
                        registry.FunctionSpec(**{**spec.__dict__, "planning_extra": ()}))
    route, env, _a = _case(O_CDM)
    assert route["status"] == "REFUSED" and env["reason_code"] == "UNSUPPORTED_CAPABILITY"
    route, _env, answers = _case(H_CDM)
    assert answers == {"q1": "3/2"}


def test_c18_without_the_foot_locus_contract_the_orthocenter_is_found_by_another_composition(monkeypatch):
    spec = registry.REGISTRY["orthogonal_projection_line"]
    keep = tuple(c for c in spec.planning_extra if c.effect.kind != "PerpLine")
    monkeypatch.setitem(registry.REGISTRY, "orthogonal_projection_line",
                        registry.FunctionSpec(**{**spec.__dict__, "planning_extra": keep}))
    route, _env, answers = _case(H_CDM)
    assert answers == {"q1": "3/2"}                                        # same point, different plan
    assert "translate_point" in [e["fn"] for e in _chain(route)["chain"]]


def test_c18_two_goals_on_one_triangle_share_the_foot_they_both_need():
    a, b = CASES[H_CDM], CASES[O_CDM]
    text = a["text"][:-1] + ". " + b["payload"]["math_goals"][0]["quote"] + "."
    p = copy.deepcopy(a["payload"])
    p["problem_text"] = text
    p["described_points"].append(dict(b["payload"]["described_points"][0], described_id="o1"))
    p["math_goals"].append(dict(b["payload"]["math_goals"][0], goal_id="q2", target={"point": "@o1", "plane": ["S", "A", "B"]}))
    route, env, answers = _run(text, p)
    assert answers == {"q1": "3/2", "q2": "5/4"}, env.get("reason_code")
    feet = [c for c in route["planner"]["calls"] if c["fn"] == "orthogonal_projection_line"]
    assert len({(c["args"]["point"], tuple(sorted(c["args"]["line"]))) for c in feet}) == len(feet)   # none built twice
    assert route["planner"]["search_telemetry"]["reused_intermediates"] >= 1


def _mutate(cid, fn):
    c = CASES[cid]
    p = copy.deepcopy(c["payload"])
    text = fn(p) or c["text"]
    p["problem_text"] = text
    return _run(text, p)


def _swap(old, new):
    def go(p):
        p["math_goals"][0]["quote"] = p["math_goals"][0]["quote"].replace(old, new)
        p["described_points"][0]["quote"] = p["described_points"][0]["quote"].replace(old, new)
        return p["problem_text"].replace(old, new)
    return go


@pytest.mark.parametrize("name,fn", [
    # the source says "trực tâm"; the extraction claims the circumcentre
    ("wrong_kind", lambda p: p["described_points"][0].update(kind="circumcenter")),
    # the extraction names another triangle than the source's
    ("wrong_triangle", lambda p: p["described_points"][0].update(polygon=["C", "D", "S"])),
    # a description the source never states
    ("invented_quote", lambda p: p["described_points"][0].update(quote="trực tâm của tam giác CDS")),
    # the source asks about the centroid; the extraction claims the orthocentre
    ("source_says_centroid", _swap("trực tâm của", "trọng tâm của")),
])
def test_c18_a_defined_point_the_source_does_not_state_is_never_served(name, fn):
    route, env, _a = _mutate(H_CDM, fn)
    assert route["status"] == "REFUSED", (name, env.get("reason_code"))


def _foot_on_another_side(d, plan):
    """A CONSISTENT forgery: the first foot of the chain and its call both moved to another line, so every call still
    matches its contract — only the definition check can see that the meet is no longer of two of its loci."""
    e = next(e for e in d["chain"] if e.get("effect") == "PerpLine" and e["fn"] == "orthogonal_projection_line")
    e["env"]["L"] = ["named", ["C", "S"]]
    next(c for c in plan.calls if c["id"] == e["call"])["args"]["line"] = ["C", "S"]


@pytest.mark.parametrize("name,tamper,reason", [
    ("point_is_a_vertex", lambda d, _p: d["definition"]["env"].update(X="C"), "không là giao điểm của chuỗi"),
    ("other_definition", lambda d, _p: d["definition"].update(descriptor="circumcenter"), "không là giao điểm của chuỗi"),
    ("meet_of_non_loci", _foot_on_another_side, "không phải của hai quỹ tích"),
])
def test_c18_the_gate_rederives_the_definition_and_refuses_a_forged_certificate(monkeypatch, name, tamper, reason):
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    real = planner.lap_ke_hoach

    def forged(*a, **k):
        plan = real(*a, **k)
        for d in plan.auxiliary:
            if d.get("rule") == "effect-chain":
                tamper(d, plan)
        return plan
    monkeypatch.setattr(planner, "lap_ke_hoach", forged)
    r = run_typed_fact_next_v2_route(CASES[H_CDM]["payload"])
    assert r.status == "REFUSED" and r.code == "AUXILIARY_RULE_MISMATCH" and reason in (r.reason or ""), (r.code, r.reason)


def test_c18_plans_follow_the_definition_data_and_the_engine_is_the_authority_on_what_it_means(monkeypatch):
    """Data only, no code: give "trực tâm" the loci of the circumcentre — the planner composes the OTHER construction
    (midpoints, translates) from the Registry alone; the engine's own predicate for the orthocentre refuses the point."""
    from dataclasses import replace
    defs = registry.POINT_DEFINITIONS
    monkeypatch.setitem(defs, "orthocenter", replace(defs["orthocenter"], loci=defs["circumcenter"].loci))
    plan = planner.lap_ke_hoach(_bridge(H_CDM), CASES[H_CDM]["text"])
    assert {"midpoint", "translate_point"} <= {c["fn"] for c in plan.calls}
    route, env, _a = _case(H_CDM)
    assert route["status"] == "REFUSED" and env["reason_code"] == "ENGINE_SELF_CHECK_FAILED"


def test_c18_a_definition_the_engine_cannot_check_is_never_served(monkeypatch):
    from app.simulation.geometry_functions import engine
    monkeypatch.delitem(engine._MO_TA, "orthocenter")
    route, env, _a = _case(H_CDM)
    assert route["status"] == "REFUSED" and env["reason_code"] == "UNSUPPORTED_CAPABILITY"


def _bridge(cid):
    from app.simulation.geometry_functions import typed_fact_next as T
    from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2
    return bridge_v2(T._parse(T.TypedFactNextPayloadV2, CASES[cid]["payload"]))


def test_c18_a_section_plane_through_a_defined_point_is_a_stated_boundary_refused_not_served():
    """Out of C18 scope: the plane-point certificate (`plane_point_chain`) reads a function descriptor only."""
    import json
    c = next(c for c in json.loads((RUN / "r1-described-point-probe.json").read_text(encoding="utf-8"))["cases"]
             if c["id"] == "C6a")
    p, old, new = copy.deepcopy(c["payload"]), "trung điểm của SA", "trực tâm của tam giác SBD"
    text = c["text"].replace(old, new)
    p["problem_text"] = text
    p["described_points"][0] = {"described_id": "m1", "kind": "orthocenter", "quote": new, "polygon": ["S", "B", "D"]}
    for x in (*p["derived_sections"], *p["math_goals"]):
        x["quote"] = x["quote"].replace(old, new)
    route, env, _a = _run(text, p)
    assert route["status"] == "REFUSED", env.get("reason_code")


def test_c18_search_is_bounded_and_exhaustion_is_typed(monkeypatch):
    monkeypatch.setattr(planner, "MAX_EFFECT_DEPTH", 2)
    route, env, _a = _case(O_CDM)
    assert route["status"] == "REFUSED" and env["reason_code"] == "PLAN_TOO_LARGE"
