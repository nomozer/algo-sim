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
