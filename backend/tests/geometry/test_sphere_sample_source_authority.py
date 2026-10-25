# -*- coding: utf-8 -*-
"""P3 sphere sample: only what the problem gives is presented as given (run `sphere-sample-source-authority`).

The problem names the centre I, the radius 5, the plane (P) and its distance 3 from I. The old sample program declared
free points A, H, U, W only to pin a rim point and three plane points; free ⇒ `display_group: given`, so the learner saw
four invented "data" points and no plane. Checks read the generated sample (the shipped artefact) and an independent
exact computation from the plane object — never engine helpers.
"""
from __future__ import annotations

import json
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

GOC = Path(__file__).resolve().parents[3]
ID = "cau-cat-mat-phang"


def _scene(sample_id: str = ID) -> dict:
    d = json.loads((GOC / "frontend/src/data/geometry-samples.json").read_text(encoding="utf-8"))["samples"]
    return next(s for s in d if s["id"] == sample_id)["envelope"]["scene3d"]


def _obj(scene, oid):
    return next(o for o in scene["objects"] if o["id"] == oid)


def test_only_source_given_objects_are_free():
    sc = _scene()
    free = {o["id"] for o in sc["objects"] if o.get("origin") == "free"}
    given = {o["id"] for o in sc["objects"] if "given" in (o.get("display_group") or [])}
    assert {o["id"] for o in sc["objects"] if o["type"] == "point3"} == {"I"}
    assert free == given == {"I", "R"}


def test_given_radius_is_the_source_number():
    r = _obj(_scene(), "R")
    assert r["type"] == "quantity" and r["value"] == "5"


def test_plane_is_named_and_three_from_the_centre():
    sc = _scene()
    p, i = _obj(sc, "P"), _obj(sc, "I")
    assert p["type"] == "plane3" and p["label"] == "(P)"
    n = [F(x) for x in p["normal"]]
    q = [F(x) for x in p["point"]]
    c = [F(x) for x in i["xyz"]]
    dot = sum(a * (b - e) for a, b, e in zip(n, c, q))
    assert dot * dot / sum(a * a for a in n) == 9


@pytest.mark.parametrize("sample_id,plane", [(ID, "P"), ("tru-thiet-dien-tron", "P")])
def test_plane_cutting_a_curved_solid_is_the_cutting_object_not_auxiliary(sample_id, plane):
    """A plane whose intersection with a curved solid is the asked circle plays the same role as the cutting plane of a
    polyhedral section (`CONSTRUCT_CUTTING_OBJECT`); as auxiliary geometry the renderer hid it once the circle existed."""
    p = _obj(_scene(sample_id), plane)
    assert p["formation_roles"] == ["CONSTRUCT_CUTTING_OBJECT"]


def test_measurement_only_planes_stay_auxiliary():
    sc = _scene("the-tich-chop")
    assert _obj(sc, "day")["formation_roles"] == ["CONSTRUCT_AUXILIARY_GEOMETRY"]


def test_intersection_circle_matches_r2_minus_d2():
    sc = _scene()
    assert F(_obj(sc, "C")["radius_sq"]) == 25 - 9
    assert _obj(sc, "r")["value"] == "4" and _obj(sc, "S")["value"] == "16π"


def _layer():
    sys.path.insert(0, str(GOC / "docs/evaluation/geometry/runs/sphere-sample-source-authority"))
    import oracle_scalar_radius
    return oracle_scalar_radius


def _faulted(kind: str) -> dict:
    from copy import deepcopy
    sc = deepcopy(_scene())
    cau = _obj(sc, "cau")
    if kind == "radius_sq":
        cau["radius_sq"] = "26"
    elif kind == "given_radius":
        _obj(sc, "R")["value"] = "6"
    elif kind == "no_given_radius":
        cau["dependency_edges"] = [e for e in cau["dependency_edges"] if e["relation"] != "numerical"]
    elif kind == "non_euclidean":
        sc["chart_metric"] = [["2", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]
    elif kind == "circle_radius":
        _obj(sc, "C")["radius_sq"] = "20"
    return sc


def test_cylinder_sample_has_no_invented_rim_point():
    sc = _scene("tru-thiet-dien-tron")
    assert {o["id"] for o in sc["objects"] if o.get("origin") == "free"} == {"O", "O_prime", "R"}
    assert _obj(sc, "R")["label"] == "Bán kính đáy" and _obj(sc, "R")["value"] == "2"
    assert _obj(sc, "r")["value"] == "2"


@pytest.mark.parametrize("sample_id", [ID, "tru-thiet-dien-tron"])
def test_scalar_radius_oracle_layer_verifies_the_sample(sample_id):
    assert _layer().verify_scene_mathematics(_scene(sample_id), scene_id=sample_id).verdict == "VERIFIED"


def test_scalar_radius_oracle_layer_rejects_a_wrong_cylinder_radius():
    from copy import deepcopy
    sc = deepcopy(_scene("tru-thiet-dien-tron"))
    _obj(sc, "R")["value"] = "3"
    assert _layer().verify_scene_mathematics(sc, scene_id="cyl").verdict == "INVALID"


@pytest.mark.parametrize("kind", ["radius_sq", "given_radius", "no_given_radius", "non_euclidean", "circle_radius"])
def test_scalar_radius_oracle_layer_rejects_faults(kind):
    assert _layer().verify_scene_mathematics(_faulted(kind), scene_id=kind).verdict == "INVALID"


def _run(d: int):
    sys.path.insert(0, str(GOC / "backend" / "scripts"))
    from build_geometry_samples import chuong_trinh_cau_cat_mp
    from app.simulation.semantic_program.contract import SemanticProgramSpec
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter

    return SemanticProgramInterpreter().execute(SemanticProgramSpec.model_validate(chuong_trinh_cau_cat_mp(d)))


@pytest.mark.parametrize("d,code", [(5, "CURVED_PLANE_TANGENT"), (6, "CURVED_PLANE_DOES_NOT_CUT")])
def test_tangent_and_missing_intersection_never_become_a_circle(d, code):
    """No clamp: d = R (tangent) and d > R (no cut) stop with distinct typed errors, never with a circle."""
    from app.simulation.geometry.exact import GeometryError

    assert _run(3).status == "completed"
    with pytest.raises(GeometryError) as e:
        _run(d)
    assert str(e.value).startswith(code)


@pytest.mark.parametrize("sample_id", [ID, "tru-thiet-dien-tron"])
def test_scalar_radius_solid_is_never_named_through_a_quantity(sample_id):
    """A solid declared by its radius has no rim point: its name must not read "qua đại lượng" (learners saw it in the
    step text of the cylinder sample once the invented rim point was removed)."""
    sc = _scene(sample_id)
    texts = [str(o.get(k) or "") for o in sc["objects"] for k in ("label", "role", "reference", "display_label")]
    texts += [st.get("learner_text") or "" for st in sc["formation"]["steps"]]
    assert [t for t in texts if "đại lượng" in t and "qua" in t] == []


def test_cylinder_sample_is_named_by_its_two_centres():
    tru = _obj(_scene("tru-thiet-dien-tron"), "tru")
    assert tru["role"].startswith("Hình trụ đáy tâm O, tâm đáy trên O′"), tru["role"]
