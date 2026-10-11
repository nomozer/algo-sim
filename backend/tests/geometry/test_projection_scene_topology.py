"""A forward projection must not re-root the declared solid in the scene (review finding I1).

Independent review of geometry-library-expansion, 2026-10-11: in tetrahedron S.ABC (apex S declared),
"K là hình chiếu vuông góc của A lên (SBC)" was computed correctly but the scene was built as apex A over
base SBC ("Đáy SBC", "Chiều cao AK", lateral edges from A). Cause: the function route called
`build_simulation_state` without the declared solid topology, so `formation.lop_khoi` resolved the four-way
tetrahedron reading from the new `project_onto` IR alone. The square-pyramid oracles cannot see it.

Oracles (hand-derived, Euclidean A=(0,0,0), B=(2,0,0), C=(1,√3,0), S=(0,0,3); affine chart A origin,
e1=AB, e2=AC, e3=AS/3):
  A→(SBC): foot on SM (M mid BC), SK/SM = 3/4 ⇒ (3/8, 3/8, 1/4)
  B→(SAC): (SAC) is the vertical plane through AC ⇒ foot = midpoint AC = (0, 1/2, 0)
  C→(SAB): (SAB) is the vertical plane through AB ⇒ foot = midpoint AB = (1/2, 0, 0)
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from tests.geometry import test_geometry_library_expansion as T

DECLARED = ["Cho hình chóp S.ABC.", "Đáy ABC là tam giác đều cạnh 2.", "SA vuông góc với (ABC).", "SA = 3."]
UNDECLARED = ["Cho tứ diện ABCD.", "Tam giác ABC đều cạnh 2.", "DA vuông góc với (ABC).", "DA = 3."]


def _base(monkeypatch, quotes, apex, solid_fact):
    a = apex
    monkeypatch.setattr(T, "BASE", quotes)
    monkeypatch.setattr(T, "CALLS", [
        ("pyramid", {"apex": a, "base": list("ABC")}, quotes[0]),
        ("regular_polygon", {"vertices": list("ABC"), "side": "2"}, quotes[1]),
        ("perpendicular_line_plane", {"line": [a, "A"], "plane": list("ABC")}, quotes[2]),
        ("segment_length", {"segment": [a, "A"], "value": "3"}, quotes[3])])
    monkeypatch.setattr(T, "FACTS", [
        solid_fact,
        {"kind": "polygon_shape", "points": list("ABC"), "shape": "equilateral_triangle", "value": "2"},
        {"kind": "perpendicular", "points_a": [a, "A"], "points_b": list("ABC")},
        {"kind": "length", "points": [a, "A"], "measure": "segment", "value": "3"}])


def _projection(src, plane, img="K"):
    return (("orthogonal_projection", {"point": src, "plane": list(plane), "image": img},
             {"kind": "projection", "point": src, "points": list(plane), "at": img},
             f"Gọi {img} là hình chiếu vuông góc của {src} lên ({plane})."))


def _drawn(r):
    return {o["display_label"] for o in r.scene3d["objects"] if o["type"] in ("polygon3", "segment3")}


DECLARED_SKELETON = {"Đáy ABC", "Cạnh bên SA", "Cạnh bên SB", "Cạnh bên SC"}
CASES = [("A", "SBC", ("3/8", "3/8", "1/4")), ("B", "SAC", ("0", "1/2", "0")), ("C", "SAB", ("1/2", "0", "0"))]


@pytest.mark.parametrize("arm", ["A", "B"])
@pytest.mark.parametrize("src,plane,foot", CASES, ids=[c[0] for c in CASES])
def test_projection_onto_opposite_face_keeps_declared_apex(arm, src, plane, foot, monkeypatch):
    _base(monkeypatch, DECLARED, "S", {"kind": "solid", "solid": "S.ABC", "solid_type": "pyramid"})
    r, _ = T.run(arm, [_projection(src, plane)], solid="S.ABC")
    assert r.status == "SERVED", (r.code, r.reason)
    k = T.scene_point(r, "K")
    assert tuple(k["xyz"]) == foot and k["origin"] == "derived"
    drawn = _drawn(r)
    assert DECLARED_SKELETON <= drawn, drawn
    assert not any(label.startswith("Chiều cao") or (label.startswith("Đáy") and label != "Đáy ABC")
                   for label in drawn), drawn
    # AK is the auxiliary perpendicular, carried as a witness of K — never a solid edge or the solid's height.
    w = k["perpendicular_witness"]
    assert w["from"] == src and tuple(w["foot"]) == foot
    p = next(o for o in r.scene3d["objects"] if o["id"] == src)["xyz"]
    v = tuple(F(x) for x in w["marker"]["v"])
    assert v == tuple(F(a) - F(b) for a, b in zip(p, foot))


@pytest.mark.parametrize("arm", ["A", "B"])
def test_declared_tetrahedron_without_projection_draws_its_declared_skeleton(arm, monkeypatch):
    _base(monkeypatch, DECLARED, "S", {"kind": "solid", "solid": "S.ABC", "solid_type": "pyramid"})
    r, _ = T.run(arm, [], solid="S.ABC")
    assert r.status == "SERVED", (r.code, r.reason)
    assert DECLARED_SKELETON <= _drawn(r)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_undeclared_tetrahedron_apex_is_not_invented(arm, monkeypatch):
    """'tứ diện ABCD' names no apex: the apex in the call is the model's/planner's choice, not the text's."""
    _base(monkeypatch, UNDECLARED, "D", {"kind": "solid", "solid": "ABCD", "solid_type": "tetrahedron"})
    r, _ = T.run(arm, [], solid="D.ABC")
    assert r.status == "SERVED", (r.code, r.reason)
    assert not any(label.startswith("Đáy") or label.startswith("Cạnh bên") for label in _drawn(r)), _drawn(r)


@pytest.mark.parametrize("arm", ["A", "B"])
def test_line_projection_carries_a_witness_at_its_foot(arm):
    r, _ = T.run(arm, [T.POSITIVE[2][:4]])  # H = projection of D on AC, square pyramid
    h = T.scene_point(r, "H")
    w = h["perpendicular_witness"]
    assert w["from"] == "D" and tuple(w["foot"]) == ("1/2", "1/2", "0")
    u, v = (tuple(F(x) for x in w["marker"][k]) for k in ("u", "v"))
    g = [[4, 0, 0], [0, 4, 0], [0, 0, 9]]  # chart Gram of the square pyramid (side 2, SA = 3)
    assert sum(u[i] * g[i][j] * v[j] for i in range(3) for j in range(3)) == 0


@pytest.mark.parametrize("mutant", ["drop_topology", "invent_topology", "drop_witness"])
def test_behavioral_mutant_is_killed(mutant, monkeypatch):
    from app.ai import function_route as FR
    from app.simulation.geometry_functions import engine as EN
    from app.simulation.semantic_program.request_contract import PyramidTopologySpec, RequestContract

    if mutant == "drop_topology":
        monkeypatch.setattr(EN, "hop_dong_to_po_da_khai", lambda calls: None)
        probe = lambda: test_projection_onto_opposite_face_keeps_declared_apex("A", *CASES[0], monkeypatch)  # noqa: E731
    elif mutant == "invent_topology":
        def bia(calls):
            c = next(c for c in calls if c.fn == "pyramid")
            return RequestContract(solid_topology=PyramidTopologySpec(apex=c.args.apex, base_cycle=tuple(c.args.base)))
        monkeypatch.setattr(EN, "hop_dong_to_po_da_khai", bia)
        probe = lambda: test_undeclared_tetrahedron_apex_is_not_invented("A", monkeypatch)  # noqa: E731
    else:
        monkeypatch.setattr(FR, "_gan_nhan_chung_hinh_chieu", lambda *a: None)
        probe = lambda: test_line_projection_carries_a_witness_at_its_foot("A")  # noqa: E731
    with pytest.raises((AssertionError, KeyError)):
        probe()


@pytest.mark.parametrize("arm", ["A", "B"])
def test_projection_of_point_already_on_target_has_no_witness(arm):
    r, _ = T.run(arm, [T.POSITIVE[4][:4]])  # A onto (ABC): image coincides with A
    assert "perpendicular_witness" not in T.scene_point(r, "H")
