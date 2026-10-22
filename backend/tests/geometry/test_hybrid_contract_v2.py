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
