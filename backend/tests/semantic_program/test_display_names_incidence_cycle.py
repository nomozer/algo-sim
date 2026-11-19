# -*- coding: utf-8 -*-
"""GEO-BE-001: a point lying ON a plane is not an input that defines the plane.

`display_names._mot_luot` resolved a plane's declared multi-point name by first resolving every point of
`points_on_plane` — including the intersection points (F = SD ∩ (MNP)) whose own `sources` contain that very plane. The
call back into the plane returned early (`dang_giai`), so F's sentence was built while the plane had no symbol and fell
back to the raw id: "Giao điểm của SD và mp_MNP". Which point broke depended on the iteration order.

These tests run the real advanced-sample generator, then the captured name tables permuted, renamed and made cyclic.
"""
from __future__ import annotations

import copy
import json
import random
import re
import sys
from pathlib import Path

import pytest

from app.simulation.semantic_program import display_names as DN
from app.simulation.semantic_program import simulation_state as SS

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
PRESENTATION = ("label", "notation", "reference", "role")


@pytest.fixture(scope="module")
def generated(monkeypatch_module):
    captured: list[dict] = []
    real = SS.ten_hien_thi

    def spy(table, **kw):
        captured.append((copy.deepcopy(table), kw))
        return real(table, **kw)

    monkeypatch_module.setattr(SS, "ten_hien_thi", spy)
    sys.path.insert(0, str(SCRIPTS))
    import build_advanced_geometry_samples as B
    samples = B.build_all_advanced_samples()
    return samples, captured


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def _obj(samples, sid, oid):
    s = next(x for x in samples if x["id"] == sid)
    return next(o for o in s["envelope"]["scene3d"]["objects"] if o["id"] == oid)


@pytest.mark.parametrize("sid, oid, role", [
    ("chop-thiet-dien-ba-diem", "F", "Giao điểm của SD và (MNP)"),
    ("lap-phuong-thiet-dien-bat-ky", "F", "Giao điểm của A′B′ và (MNP)"),
    ("lap-phuong-thiet-dien-bat-ky", "Q", "Giao điểm của AA′ và (MNP)"),
    ("lang-tru-tam-giac-thiet-dien", "E", "Giao điểm của A′B′ và (NPQ)"),
])
def test_the_four_reported_intersection_points_name_their_plane(generated, sid, oid, role):
    samples, _ = generated
    assert _obj(samples, sid, oid)["role"] == role


def _ids_in(text: str, ids: set[str]) -> list[str]:
    """Internal ids (machine names: containing '_' or lowercase-led, ≥ 2 chars) appearing as whole tokens."""
    machine = {i for i in ids if "_" in i or (len(i) >= 2 and i[0].islower())}
    return [t for t in re.findall(r"[A-Za-z0-9_′']+", text or "") if t in machine]


def test_no_presentation_field_of_any_generated_sample_carries_an_internal_id(generated):
    samples, _ = generated
    leaks = []
    for s in samples:
        objs = s["envelope"]["scene3d"]["objects"]
        ids = {o["id"] for o in objs}
        for o in objs:
            for f in PRESENTATION:
                if (bad := _ids_in(str(o.get(f) or ""), ids)):
                    leaks.append((s["id"], o["id"], f, o.get(f), bad))
    assert leaks == []


def _table(generated, needle):
    return next(copy.deepcopy(t) for t, kw in generated[1] if needle in t)


def _names(table, **kw):
    return DN.ten_hien_thi(table, **kw)


@pytest.mark.parametrize("seed", range(6))
def test_names_do_not_depend_on_the_iteration_order(generated, seed):
    for needle in ("mp_MNP", "mp_NPQ"):
        table = _table(generated, needle)
        base = _names(table)
        keys = list(table)
        random.Random(seed).shuffle(keys)
        assert _names({k: table[k] for k in keys}) == base
        assert _names({k: table[k] for k in reversed(list(table))}) == base


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


def test_renamed_plane_points_follow_the_new_names(generated):
    table = _table(generated, "mp_MNP")
    ren = _rename(table, {"M": "X", "N": "Y", "P": "Z", "mp_MNP": "mp_XYZ"})
    names = _names(ren)
    assert names["F"]["role"] == "Giao điểm của SD và (XYZ)"
    assert names["mp_XYZ"]["notation"] == "(XYZ)"


def test_ids_stay_machine_names_in_the_dependency_graph(generated):
    samples, _ = generated
    for sid, oid in (("chop-thiet-dien-ba-diem", "F"), ("lang-tru-tam-giac-thiet-dien", "E")):
        deps = _obj(samples, sid, oid).get("depends") or _obj(samples, sid, oid).get("sources") or []
        assert all(not d.startswith("(") for d in deps)          # graph references are ids, never symbols


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
    assert report >= {"G"} or report >= {"mp_a"}
    for t, row in names.items():
        for f in PRESENTATION:
            assert not _ids_in(str(row.get(f) or ""), set(table)), (t, f, row.get(f))


def test_a_greek_named_plane_keeps_its_name_in_the_intersection_role(generated):
    table = _table(generated, "mp_MNP")
    table["mp_MNP"]["label"] = "(α)"
    names = DN.ten_hien_thi(table, prefer_declared_plane_names=True)
    assert names["mp_MNP"]["notation"] == "(α)"
    assert names["F"]["role"] == "Giao điểm của SD và (α)"
