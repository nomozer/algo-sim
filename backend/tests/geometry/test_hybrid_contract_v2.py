# -*- coding: utf-8 -*-
"""Run `hybrid-contract-v2` (Session 3): input-boundary safety, `typed-fact-next/2`, planner-derived cut vertices (D6),
shared Source Gate grammar, Adapter /4. Expected values are closed-form (independent of the engine)."""
from __future__ import annotations

from copy import deepcopy

import pytest

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.simulation.geometry_functions.typed_fact_next import TypedFactNextValidationError, parse_typed_fact_next
from tests.geometry.test_hybrid_contract_unification import _payload


# ── P1: malformed input is refused at the schema boundary, never compiled ─────────────────────────────────────────

@pytest.mark.parametrize("kind_index,arg,value", [
    (0, "vertices", 5), (0, "vertices", ["A", None]), (1, "line", "SA"), (1, "plane", ["A", "B"]),
    (2, "segment", ["S"]), (2, "value", {"a": 1}), (3, "point", ["M"]), (3, "segment", None),
])
def test_malformed_premise_args_are_refused_at_parse(kind_index, arg, value):
    p = _payload("ABC")
    p["premises"][kind_index]["args"][arg] = value
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next(p)
    assert e.value.code == "INVALID_PREMISE_ARGS", e.value.code
    r = run_typed_fact_next_route(p)
    assert (r.status, r.code) == ("REFUSED", "INVALID_PREMISE_ARGS")


def test_missing_required_premise_arg_is_refused_at_parse():
    p = _payload("ABC")
    del p["premises"][3]["args"]["segment"]
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next(p)
    assert e.value.code == "INVALID_PREMISE_ARGS"


@pytest.mark.parametrize("key", ["SB", "S-B-C", "S-", "-B", "s-b"])
def test_named_intersection_keys_must_be_one_edge(key):
    p = _payload("ABC")
    p["derived_sections"][0]["named_intersections"] = {key: "N"}
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next(p)
    assert e.value.code == "INVALID_DERIVED_SECTION"


def test_valid_payloads_still_parse_unchanged():
    for p in (_payload("ABC"), _payload("ABCD", "perpendicular", residual=True)):
        assert parse_typed_fact_next(deepcopy(p)).schema_version == "typed-fact-next/1"


@pytest.mark.parametrize("exc", [KeyError("k"), TypeError("t")])
def test_a_planner_fault_inside_the_shared_gate_is_not_reported_as_bad_input(monkeypatch, exc):
    """Session 2 review MINOR 3: only the bridge's input parsing may turn KeyError / TypeError into an input refusal."""
    import app.simulation.geometry_functions.planner as PL

    def boom(*_a, **_k):
        raise exc
    monkeypatch.setattr(PL, "lap_ke_hoach", boom)
    r = run_typed_fact_next_route(_payload("ABC"))
    assert (r.status, r.code) == ("REFUSED", "ADAPTER_INTERNAL_ERROR"), (r.code, r.reason)


def _plane(name, pts, label=None):
    st = {"kind": "construct_plane", "target_var": name, "through": pts}
    return {**st, "label": label} if label else st


def test_dedup_only_merges_engine_owned_names():
    """Session 2 review MINOR 4: the invariant is an explicit owned-name set, not the `derived_` prefix convention."""
    from app.simulation.geometry_functions.engine import gop_doi_tuong_trung

    lenh = [_plane("derived_N_plane", ["M", "H", "H1"]), _plane("derived_P_plane", ["M", "H", "H1"]),
            _plane("derived_fake_plane", ["M", "H", "H1"]),             # same construction, NOT owned: kept
            {"kind": "construct_point", "target_var": "P", "expr": {"kind": "intersect_line_plane", "line": "l",
                                                                    "plane": "derived_P_plane"}}]
    khai = [{"name": s["target_var"], "type": "x"} for s in lenh]
    khai2, lenh2 = gop_doi_tuong_trung(khai, lenh, {"derived_N_plane", "derived_P_plane"})
    assert [s["target_var"] for s in lenh2] == ["derived_N_plane", "derived_fake_plane", "P"]
    assert lenh2[-1]["expr"]["plane"] == "derived_N_plane"
    assert [d["name"] for d in khai2] == ["derived_N_plane", "derived_fake_plane", "P"]


def test_dedup_never_rewrites_a_label_or_kind_field():
    from app.simulation.geometry_functions.engine import gop_doi_tuong_trung

    lenh = [_plane("derived_N_plane", ["M", "H", "H1"]), _plane("derived_P_plane", ["M", "H", "H1"]),
            {"kind": "construct_point", "target_var": "Q", "label": "derived_P_plane",
             "expr": {"kind": "intersect_line_plane", "line": "l", "plane": "derived_P_plane"}}]
    _k, lenh2 = gop_doi_tuong_trung([{"name": s["target_var"]} for s in lenh], lenh, {"derived_N_plane", "derived_P_plane"})
    assert lenh2[-1]["label"] == "derived_P_plane" and lenh2[-1]["expr"]["plane"] == "derived_N_plane"


def test_an_unexpected_internal_fault_is_a_technical_refusal_not_a_data_error(monkeypatch):
    """The public boundary never leaks an exception, and never disguises a programming fault as the user's input."""
    import app.ai.adapter3_simulation as A

    def boom(self):
        raise ZeroDivisionError("planted")
    monkeypatch.setattr(A._Adapter3Compiler, "_compile_premises", boom)
    r = run_typed_fact_next_route(_payload("ABC"))
    assert (r.status, r.code) == ("REFUSED", "ADAPTER_INTERNAL_ERROR"), (r.status, r.code)
    assert "ZeroDivisionError" in r.reason


# ── P2: typed-fact-next/2 — stated intersections, declared boundary, explicit /1 → /2 conversion ────────────────────

def _v2(v1: dict, route: str = "bridge") -> dict:
    from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2
    return convert_v1_to_v2(v1, route)


def test_v1_converts_to_v2_only_with_an_explicit_route_label():
    from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2
    for route in (None, "", "auto", "both"):
        with pytest.raises(TypedFactNextValidationError) as e:
            convert_v1_to_v2(_payload("ABC"), route)
        assert e.value.code == "ROUTE_LABEL_REQUIRED"


def test_bridge_conversion_maps_cut_edges_to_stated_intersections():
    v2 = _v2(_payload("ABCD"))
    sec = v2["derived_sections"][0]
    assert v2["schema_version"] == "typed-fact-next/2" and "cut_edges" not in sec and "named_intersections" not in sec
    assert [(s["edge"], s["point"]) for s in sec["stated_intersections"]] == [(["S", "B"], "N"), (["S", "C"], "P"),
                                                                             (["S", "D"], "Q")]
    assert sec.get("declared_boundary") is None


def test_adapter3_conversion_maps_cut_edges_to_a_declared_boundary_and_names_only_to_stated():
    p = _payload("ABCD", cut=["SA", "SB", "SC", "SD"])
    v2 = _v2(p, "adapter3")
    sec = v2["derived_sections"][0]
    assert sec["declared_boundary"] == [["S", "A"], ["S", "B"], ["S", "C"], ["S", "D"]]
    assert [(s["edge"], s["point"]) for s in sec["stated_intersections"]] == [(["S", "A"], "M"), (["S", "B"], "N"),
                                                                             (["S", "C"], "P"), (["S", "D"], "Q")]


def test_v2_parses_and_v1_parser_never_reads_v2():
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2
    v2 = _v2(_payload("ABC"))
    assert parse_typed_fact_next_v2(v2).schema_version == "typed-fact-next/2"
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next(v2)
    assert e.value.code == "SCHEMA_VERSION_MISMATCH"
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next_v2(_payload("ABC"))
    assert e.value.code == "SCHEMA_VERSION_MISMATCH"


@pytest.mark.parametrize("mutate,code", [
    (lambda s: s.update(cut_edges=[["S", "B"]]), "INVALID_TYPED_FACT_NEXT"),
    (lambda s: s.update(named_intersections={"S-B": "N"}), "INVALID_TYPED_FACT_NEXT"),
    (lambda s: s["stated_intersections"][0].update(quote="một câu khác"), "INVALID_DERIVED_SECTION"),
    (lambda s: s["stated_intersections"].append(dict(s["stated_intersections"][0])), "INVALID_DERIVED_SECTION"),
    (lambda s: s["stated_intersections"][1].update(point="N"), "INVALID_DERIVED_SECTION"),
    (lambda s: s.update(declared_boundary=[["S", "A"], ["S", "B"]]), "INVALID_DERIVED_SECTION"),
    (lambda s: s.update(declared_boundary=[["S", "A"], ["S", "A"], ["S", "B"]]), "INVALID_DERIVED_SECTION"),
    (lambda s: s.update(requires_closed_boundary=False), "INVALID_TYPED_FACT_NEXT"),
])
def test_v2_section_shape_is_closed(mutate, code):
    from app.simulation.geometry_functions.typed_fact_next import parse_typed_fact_next_v2
    v2 = _v2(_payload("ABC"))
    mutate(v2["derived_sections"][0])
    with pytest.raises(TypedFactNextValidationError) as e:
        parse_typed_fact_next_v2(v2)
    assert e.value.code == code, (e.value.code, e.value.detail)


# ── P3 + P5: Adapter /4 over bridge /2 → planner (D6) → Source Gate → engine (closure certificate) ─────────────────

def _square(coef: str):
    from tests.geometry.test_hybrid_contract_unification import _square as sq
    return sq(coef)


def _run4(v2: dict):
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    return run_typed_fact_next_v2_route(v2)


def _partial(base="ABC", stated=("SB",), named=True, ask="construct"):
    """`/2` payload stating only some cuts; the request builds the derived pyramid (or asks a described ratio)."""
    from fractions import Fraction
    p = _v2(_payload(base))
    sec = p["derived_sections"][0]
    names = {e: n for e, n in zip([f"S{x}" for x in base[1:]], "NPQ")}
    cl = f"Mặt phẳng (α) qua M và song song với ({base[:3]})" + (
        (f" cắt {', '.join(stated)}" + (f" lần lượt tại {', '.join(names[e] for e in stated)}" if named else ""))
        if stated else "")
    p["problem_text"] = p["problem_text"].replace(sec["quote"].rstrip(".") + ".", cl + ".")
    sec["quote"] = cl
    sec["stated_intersections"] = [{"edge": [e[0], e[1]], "point": names[e] if named else None, "quote": cl} for e in stated]
    req = f"Dựng thiết diện của hình chóp S.{base} bởi (α) và khối chóp đỉnh S cắt bởi (α)."
    head = p["problem_text"].split(f"Dựng thiết diện của hình chóp S.{base} bởi (α).")[0]
    if ask == "construct":
        p["problem_text"] = head + req
        p["math_goals"] = []
        p["simulation_goals"] = [{"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec",
                                  "quote": req.rstrip(".")},
                                 {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                                  "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr", "quote": req.rstrip(".")}]
    else:
        q = ask
        p["problem_text"] = head + req + " " + q
        p["simulation_goals"] = [{"goal_id": "g_sec", "kind": "construct_plane_section", "target_section_id": "sec",
                                  "quote": req.rstrip(".")},
                                 {"goal_id": "g_sub", "kind": "construct_derived_solid", "derived_solid_id": "sub",
                                  "target_section_id": "sec", "apex_ref": "S", "parent_solid_id": "pyr", "quote": req.rstrip(".")}]
        p["math_goals"] = [{"goal_id": "g_ratio", "kind": "volume_ratio", "numerator_solid_id": "sub",
                            "denominator_solid_id": "pyr", "quote": q.rstrip(".")}]
    return p


def test_v2_fully_stated_cut_is_served_with_gate_authority_and_a_closure_certificate():
    from fractions import Fraction
    r = _run4(_v2(_payload("ABCD", residual=True)))
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g_ratio"]["coef"]) == Fraction(1, 64)
    env = r.route_d
    assert env["schema_version"] == "hybrid-route-d-simulation/4" and env["adapter_version"] == "hybrid-simulation-adapter/4"
    assert env["contract_version"] == "typed-fact-next/2"
    assert env["source_verification"] == {"authority": "registry.kiem_nguon"}
    (sec,) = env["sections"]
    assert sec["boundary"] == ["M", "N", "P", "Q"] and sec["closure_certificate"]["verified"] is True
    assert [v["provenance"] for v in sec["vertices"]] == ["THROUGH_POINT_REUSE", "SOURCE_NAMED", "SOURCE_NAMED", "SOURCE_NAMED"]


@pytest.mark.parametrize("base,stated", [("ABC", ("SB",)), ("ABCD", ("SB", "SD")), ("ABC", ())])
def test_d6_derives_unstated_cut_vertices_with_provenance_and_never_shows_them_as_source(base, stated):
    r = _run4(_partial(base, stated))
    assert r.status == "SERVED", (r.code, r.reason)
    (sec,) = r.route_d["sections"]
    prov = {"".join(v["edge"]): v["provenance"] for v in sec["vertices"]}
    for x in base[1:]:
        assert prov[f"S{x}"] == ("SOURCE_NAMED" if f"S{x}" in stated else "DERIVED_FRESH"), prov
    assert sec["closure_certificate"]["verified"] is True
    fresh = [v["label"] for v in sec["vertices"] if v["provenance"] == "DERIVED_FRESH"]
    import re
    tok = re.compile(r"(?<![\w'])[A-Z0-9'.]*(?:" + "|".join(map(re.escape, fresh)) + r")[A-Z0-9'.]*(?![\w'])")
    sc = r.scene3d
    text = [str(o.get(k)) for o in sc["objects"] for k in ("label", "display_label", "reference", "notation", "role")]
    text += [str(e.get(k)) for e in sc["events"] for k in ("display_label", "learner_text", "explanation")]
    text += [s.get("learner_text", "") for s in sc["formation"]["steps"]]
    assert [s for s in text if tok.search(s)] == []


def test_d6_described_derived_pyramid_ratio_is_exact():
    from fractions import Fraction
    r = _run4(_partial("ABC", ("SB",), ask="Tính tỉ số thể tích của khối chóp đỉnh S cắt bởi (α) và khối chóp S.ABC."))
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r.answer_exact["g_ratio"]["coef"]) == Fraction(1, 64)


def test_d6_is_not_available_to_v1_payloads():
    """/1 keeps its legacy outcome: the bridge does not close an open stated cycle (Session 1 S-open-cycle)."""
    from app.ai.function_route import run_typed_fact_next_planner_route
    p = _payload("ABC", cut=["SB"])
    assert run_typed_fact_next_planner_route(p).code == "SECTION_NOT_CLOSED_ON_LATERAL_EDGES"


def test_without_the_registry_meet_contract_no_cut_vertex_is_planned(monkeypatch):
    """Ablation: the planner reaches the line ∩ plane producer only through its Registry planning contract."""
    from dataclasses import replace
    from app.simulation.geometry_functions import registry
    monkeypatch.setitem(registry.REGISTRY, "intersect_line_plane",
                        replace(registry.REGISTRY["intersect_line_plane"], planning=None))
    for p in (_partial("ABC", ("SB",)), _v2(_payload("ABCD"))):
        r = _run4(p)
        assert (r.status, r.code) == ("REFUSED", "UNSUPPORTED_CAPABILITY"), (r.code, r.reason)


@pytest.mark.parametrize("boundary,status", [(["SD", "SC", "SB", "SA"], "SERVED"), (["SA", "SC", "SB", "SD"], "REFUSED"),
                                             (["SB", "SC", "SD"], "REFUSED")])
def test_a_declared_boundary_is_verified_never_trusted(boundary, status):
    p = _v2(_payload("ABCD"))
    p["derived_sections"][0]["declared_boundary"] = [list(e) for e in boundary]
    r = _run4(p)
    assert r.status == status, (r.code, r.reason)
    if status == "REFUSED":
        assert r.code == "SECTION_BOUNDARY_INCOMPLETE", r.code


def test_anonymous_ratio_without_operands_is_refused_on_v2():
    """Session 2 known invalid serve (P1.4): no numerator / denominator from order of appearance."""
    r = _run4(_partial("ABC", (), ask="Tính tỉ số thể tích."))
    assert r.status == "REFUSED", (r.code, r.answers)


def test_v2_never_falls_back_to_legacy_for_what_the_planner_cannot_express():
    p = _v2(_payload("ABC"))
    p["solids"][0]["vertex_bindings"] = {"S": "S1"}
    r = _run4(p)
    assert (r.status, r.code) == ("REFUSED", "BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY"), (r.code, r.reason)


def test_route_v2_boundary_records_internal_faults_as_technical_refusals(monkeypatch):
    import app.ai.function_route as FR

    def boom(*_a, **_k):
        raise ZeroDivisionError("planted")
    monkeypatch.setattr(FR, "run_fact_route", boom)
    r = _run4(_v2(_payload("ABC")))
    assert (r.status, r.code) == ("REFUSED", "ROUTE_INTERNAL_ERROR") and "ZeroDivisionError" in r.reason


def test_d3_closed_grammar_paraphrases_and_negative_controls():
    """D3 closed grammar expansion: PARA-0..5, CORPUS-DEV09/10, and negative controls on `/2`."""
    import json
    from fractions import Fraction
    from pathlib import Path
    from app.ai.hybrid_preview import classify_refusal

    root = Path(__file__).resolve().parents[3]
    cases = {
        c["id"]: c
        for c in json.loads(
            (root / "docs/evaluation/geometry/runs/hybrid-contract-v2/grammar-set.json").read_text(encoding="utf-8")
        )["cases"]
    }
    for cid in ("PARA-0", "PARA-1", "PARA-2", "PARA-3", "PARA-4", "PARA-5", "POS-per-edge-with-va-cat",
                "CORPUS-DEV09-construct", "CORPUS-DEV10-prism-area"):
        r = _run4(cases[cid]["payload"])
        assert r.status == "SERVED", (cid, r.code, r.reason)
        assert r.route_d["source_verification"] == {"authority": "registry.kiem_nguon"}
        for k, v in cases[cid]["answers"].items():
            assert _square(r.answer_exact[k]["coef"]) == Fraction(v), (cid, k, r.answer_exact)

    for cid in ("NEG-point-first-wrong-reference", "NEG-contains-a-line",
                "NEG-other-plane-subject", "NEG-swapped-names", "NEG-stated-edge-not-in-text"):
        r = _run4(cases[cid]["payload"])
        assert r.status == "REFUSED", cid
        assert classify_refusal(r.code).group in ("SOURCE_UNVERIFIED", "MISSING_DATA"), (cid, r.code)
    assert _run4(cases["NEG-per-edge-same-name"]["payload"]).code == "INVALID_DERIVED_SECTION"


def test_v2_plane_only_section_area_without_derived_solid_is_served():
    """Independent review I-1: a plane-only `/2` section (`stated_intersections: []`, `declared_boundary: None`)
    requesting only `construct_plane_section` + `measurement(area)` without `construct_derived_solid` is served."""
    from fractions import Fraction
    from app.ai.function_route import run_typed_fact_next_planner_route

    p1 = _payload("ABC")
    sec_q = p1["derived_sections"][0]["quote"]
    plain_q = "Mặt phẳng (α) qua M và song song với (ABC)."
    area_q = "Tính diện tích thiết diện của hình chóp S.ABC cắt bởi (α)."
    ratio_q = p1["math_goals"][0]["quote"]
    p1["problem_text"] = p1["problem_text"].replace(sec_q, plain_q).replace(ratio_q, area_q)
    p1["derived_sections"][0].update(quote=plain_q, cut_edges=[], named_intersections={})
    p1["simulation_goals"] = [p1["simulation_goals"][0]]
    p1["math_goals"] = [
        {"goal_id": "g_area", "kind": "measurement", "goal_type": "area",
         "target": {"section_id": "sec"}, "quote": area_q}
    ]
    r1 = run_typed_fact_next_planner_route(p1)
    assert r1.status == "SERVED", (r1.code, r1.reason)
    r2 = _run4(_v2(p1))
    assert r2.status == "SERVED", (r2.code, r2.reason)
    assert _square(r2.answer_exact["g_area"]["coef"]) == Fraction(3, 256)


