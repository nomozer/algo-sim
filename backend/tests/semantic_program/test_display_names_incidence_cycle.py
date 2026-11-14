# -*- coding: utf-8 -*-
"""GEO-BE-001 integrated into AlgoSim (fix of axo-geometry-library `5a229507b`, display_names.py hunk only).

A point lying ON a plane is not an input that defines the plane: resolving a plane's declared multi-point name used to
resolve every point of `points_on_plane`, including intersection points whose own `sources` contain that very plane; the
call back into the half-built plane returned early (`dang_giai`) and their sentence fell back to the raw id
("Giao điểm của SD và mp_MNP"), depending on iteration order.

The name tables are the real `ten_hien_thi` inputs of the two samples that reproduced the defect
(`fixtures/display_name_incidence_tables.json`, derived data); plus a raw-id scan of scenes this route builds itself.
"""
from __future__ import annotations

import copy
import json
import random
import re
from fractions import Fraction
from pathlib import Path

import pytest

from app.simulation.geometry.exact import Vec3
from app.simulation.semantic_program import display_names as DN

PRESENTATION = ("label", "notation", "reference", "role")
_FIX = json.loads((Path(__file__).parent / "fixtures/display_name_incidence_tables.json").read_text(encoding="utf-8"))


def _dec(o):
    if isinstance(o, dict):
        if set(o) == {"__vec3__"}:
            return Vec3(*(Fraction(x) for x in o["__vec3__"]))
        return {k: _dec(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_dec(v) for v in o]
    return o


def _table(name):
    t = _FIX["tables"][name]
    kw = dict(t["kwargs"])
    if "source_plane_names" in kw:
        kw["source_plane_names"] = frozenset(kw["source_plane_names"])
    return _dec(copy.deepcopy(t["table"])), kw


def _ids_in(text, ids):
    machine = {i for i in ids if "_" in i or (len(i) >= 2 and i[0].islower())}
    return [t for t in re.findall(r"[A-Za-z0-9_′']+", text or "") if t in machine]


@pytest.mark.parametrize("name, oid, role", [("pyramid_mnp", "F", "Giao điểm của SD và (MNP)"),
                                             ("prism_npq", "E", "Giao điểm của A′B′ và (NPQ)")])
def test_an_intersection_point_names_the_plane_it_lies_on(name, oid, role):
    table, kw = _table(name)
    assert DN.ten_hien_thi(table, **kw)[oid]["role"] == role


@pytest.mark.parametrize("name", ["pyramid_mnp", "prism_npq"])
def test_no_presentation_field_carries_an_internal_id(name):
    table, kw = _table(name)
    names = DN.ten_hien_thi(table, **kw)
    assert [(t, f) for t, r in names.items() for f in PRESENTATION if _ids_in(str(r.get(f) or ""), set(table))] == []


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("name", ["pyramid_mnp", "prism_npq"])
def test_names_do_not_depend_on_the_iteration_order(name, seed):
    table, kw = _table(name)
    base = DN.ten_hien_thi(table, **kw)
    keys = list(table)
    random.Random(seed).shuffle(keys)
    assert DN.ten_hien_thi({k: table[k] for k in keys}, **kw) == base
    assert DN.ten_hien_thi({k: table[k] for k in reversed(list(table))}, **kw) == base


def _rename(table, mapping):
    def r(v):
        if isinstance(v, str):
            return mapping.get(v, v)
        if isinstance(v, list):
            return [r(x) for x in v]
        if isinstance(v, dict):
            return {k: r(x) for k, x in v.items()}
        return v
    out = {}
    for k, o in table.items():
        o = r(o)
        if isinstance(o.get("label"), str):
            for a, b in mapping.items():
                if len(a) == 1:
                    o["label"] = o["label"].replace(a, b)
        out[mapping.get(k, k)] = o
    return out


def test_renamed_plane_points_follow_the_new_names():
    table, kw = _table("pyramid_mnp")
    names = DN.ten_hien_thi(_rename(table, {"M": "X", "N": "Y", "P": "Z", "mp_MNP": "mp_XYZ"}), **kw)
    assert names["F"]["role"] == "Giao điểm của SD và (XYZ)" and names["mp_XYZ"]["notation"] == "(XYZ)"


def test_a_greek_named_plane_keeps_its_name():
    table, kw = _table("pyramid_mnp")
    table["mp_MNP"]["label"] = "(α)"
    names = DN.ten_hien_thi(table, **{**kw, "prefer_declared_plane_names": True})
    assert names["mp_MNP"]["notation"] == "(α)" and names["F"]["role"] == "Giao điểm của SD và (α)"


def test_graph_references_are_left_as_ids():
    table, kw = _table("pyramid_mnp")
    before = copy.deepcopy(table)
    DN.ten_hien_thi(table, **kw)
    assert table == before                                   # the table (sources, producers, ids) is never rewritten


def test_a_true_definition_cycle_never_prints_an_id_and_is_reported():
    table = {
        "S": {"type": "point3", "producer": "assign", "sources": [], "label": "S"},
        "D": {"type": "point3", "producer": "assign", "sources": [], "label": "D"},
        "sd": {"type": "line3", "producer": "construct_line.through", "sources": ["S", "D"], "label": None},
        "mp_a": {"type": "plane3", "producer": "construct_plane", "sources": ["sd", "G"], "label": None},
        "G": {"type": "point3", "producer": "construct_point.intersect_line_plane", "sources": ["sd", "mp_a"], "label": None},
    }
    report: set[str] = set()
    names = DN.ten_hien_thi(table, unresolved=report)
    assert report & {"G", "mp_a"}
    assert not [(t, f) for t, r in names.items() for f in PRESENTATION if _ids_in(str(r.get(f) or ""), set(table))]


@pytest.mark.parametrize("text", [
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. Gọi M, N, P lần lượt "
    "là trung điểm của SA, SB, SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (MNP).",
    "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. Gọi M, N, P lần lượt là trung điểm của AB, BC, CC'. Dựng thiết "
    "diện của hình lập phương cắt bởi mặt phẳng (MNP).",
])
def test_scenes_built_by_this_route_carry_no_internal_id_in_presentation(monkeypatch, text):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    from app.ai.adaptive_input_router import route_text_input
    objs = route_text_input(text, allow_live_ai=False).response["envelope"]["scene3d"]["objects"]
    ids = {o["id"] for o in objs}
    assert [(o["id"], f) for o in objs for f in PRESENTATION if _ids_in(str(o.get(f) or ""), ids)] == []
