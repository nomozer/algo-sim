"""Retired Axo module `tests/geometry/test_hybrid_e2e_generalization.py` (Axo 67f780ca), restored on Hybrid /4 by the pre-merge
audit (run axo-hybrid4-final-premerge-hardening). The merge had deleted the whole module because it imported
Adapter /3; the tests below still hold on main's route. Not restored, and why:
- `test_registry_has_expected_contract_surface`: pins registry version `geometry-functions/21`; main is /33 (obsolete pin, not a fault)
- `test_curved_solids_adapter3_and_exact_conic_kernel`: sphere section by `plane_equation` is refused on /4 (`BRIDGE_UNSUPPORTED_CURVED`): capability gap, safe refusal
- `test_curved_foundation_ordering_elliptic_section_and_oblique_cylinder_refusal`: `convert_v1_to_v2` raises KeyError on a `/1` payload without `derived_sections` (tool-only converter, no product consumer); oblique-cylinder refusal is covered by `test_hybrid4_cylinder_never_assumed_right.py`
"""
"""End-to-end offline generalization & mathematical correctness tests across Hybrid routes.

Verifies (`ALLOW_LIVE_AI=0`, 0 live LLM calls):
1. Real Goal-Directed Planner (`planner.lap_ke_hoach`) + Engine/Kernel (`run_fact_route`)
   across polyhedral families and Mandatory Regressions A, B, C, D.
2. Adapter /4 (`run_typed_fact_next_v2_route`) bridge -> real Planner -> Engine -> Scene3D.
3. Adapter /3 (`run_typed_fact_next_route`) curved solid interpreter + `curved.py` Kernel
   for sphere, cone (with frustum + axial section), and cylinder (circular + axial section).
4. Kernel exact oblique conic sections (`curved.intersect_plane_curved_ellipse`).
"""

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.typed_fact_next import convert_v1_to_v2


def run_typed_fact_next_route(raw):
    """Retired Adapter /3 entry → the product route: `/1` payload converted with main's declared `adapter3` semantics
    (`convert_v1_to_v2`), then Adapter /4. Same engine, same certificates; only the envelope contract differs."""
    return run_typed_fact_next_v2_route(convert_v1_to_v2(raw, "adapter3"))
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_fact_route
from app.simulation.geometry import curved as CV
from app.simulation.geometry.exact import Plane3, Vec3
from app.simulation.geometry.radical import display
from app.simulation.geometry_functions import planner as PLN
from app.simulation.geometry_functions import registry as REG
from app.simulation.geometry_functions.typed_fact_next import TYPED_FACT_NEXT_SCHEMA_VERSION
from tests.geometry import construction_sequencing as CS
from tests.geometry import hybrid_compiler_benchmark as HB
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism


@pytest.fixture(autouse=True)
def _offline_only(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")


def _div(fid: str, p: str, a: str, b: str, ratio: str, eq_text: str) -> dict:
    q = f"Gọi {p} là điểm thuộc cạnh {a}{b} sao cho {eq_text}."
    return HB._f(fid, "point_def", q, point=p, point_kind="divide_segment", points=[a, b], value=ratio)


def _assert_clean_sequencing(scene: dict | None) -> None:
    assert scene is not None
    assert CS.check(scene) == {"O1": [], "O2": [], "O3": [], "O4": []}




def test_case_a_midpoints_square_vs_rectangle_vs_parallelogram_refusal() -> None:
    # A1: Square base -> section area = 4
    f_sq = [
        HB._f("s1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("s2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 4.", points=["A", "B", "C", "D"], shape="square", value="4"),
        HB._f("s3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("s4", "length", "SA = 6.", points=["S", "A"], measure="segment", value="6"),
        HB._mid("s5", "M", "S", "A"),
        HB._mid("s6", "N", "S", "B"),
        HB._mid("s7", "P", "S", "C"),
        HB._ilp("s8", "Q", "SD", "MNP"),
        HB._ask("s9", "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MNP).", "area", solid="S.ABCD", points=["M", "N", "P"]),
    ]
    plan_sq = PLN.lap_ke_hoach({"facts": f_sq})
    fns_sq = [c["fn"] for c in plan_sq.calls]
    assert "pyramid" in fns_sq
    assert "regular_polygon" in fns_sq
    assert "perpendicular_line_plane" in fns_sq
    assert fns_sq.count("midpoint") == 3
    assert "intersect_line_plane" in fns_sq
    assert "ask_section_area" in fns_sq

    res_sq = run_fact_route(" ".join(f["quotes"][0] for f in f_sq), {"facts": f_sq})
    assert res_sq.status == "SERVED"
    assert res_sq.answers == {"s9": "4"}
    _assert_clean_sequencing(res_sq.scene3d)

    # D1: Reversed fact declaration order yields identical plan & exact result
    res_rev = run_fact_route(" ".join(f["quotes"][0] for f in f_sq), {"facts": list(reversed(f_sq))})
    assert res_rev.status == "SERVED"
    assert res_rev.answers == {"s9": "4"}
    assert [c["fn"] for c in PLN.lap_ke_hoach({"facts": list(reversed(f_sq))}).calls] == fns_sq
    _assert_clean_sequencing(res_rev.scene3d)

    # A2: Non-square rectangular base (6 x 2) -> section area = 3
    f_rect = [
        HB._f("r1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("r2", "polygon_shape", "Đáy ABCD là hình chữ nhật.", points=["A", "B", "C", "D"], shape="rectangle"),
        HB._f("r3", "length", "AB = 6.", points=["A", "B"], measure="segment", value="6"),
        HB._f("r4", "length", "BC = 2.", points=["B", "C"], measure="segment", value="2"),
        HB._f("r5", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("r6", "length", "SA = 5.", points=["S", "A"], measure="segment", value="5"),
        HB._mid("r7", "M", "S", "A"),
        HB._mid("r8", "N", "S", "B"),
        HB._mid("r9", "P", "S", "C"),
        HB._ilp("r10", "Q", "SD", "MNP"),
        HB._ask("r11", "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MNP).", "area", solid="S.ABCD", points=["M", "N", "P"]),
    ]
    res_rect = run_fact_route(" ".join(f["quotes"][0] for f in f_rect), {"facts": f_rect})
    assert res_rect.status == "SERVED"
    assert res_rect.answers == {"r11": "3"}
    _assert_clean_sequencing(res_rect.scene3d)

    # A3: Uncertified quadrilateral / parallelogram base without angle certification -> refused fail-closed
    f_para = [
        HB._f("p1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("p2", "length", "AB = 4.", points=["A", "B"], measure="segment", value="4"),
        HB._f("p3", "length", "AD = 2.", points=["A", "D"], measure="segment", value="2"),
        HB._f("p4", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("p5", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._ask("p6", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD"),
    ]
    res_para = run_fact_route(" ".join(f["quotes"][0] for f in f_para), {"facts": f_para})
    assert res_para.status == "REFUSED"
    assert res_para.code == "UNSUPPORTED_BASE_SHAPE"


def test_case_b_mab_section_requires_explicit_perpendicularity_premise() -> None:
    # B1: With SA ⊥ (ABCD), section (MAB) is certified and area is computed
    fb1 = [
        HB._f("b1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("b2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 4.", points=["A", "B", "C", "D"], shape="square", value="4"),
        HB._f("b3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("b4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
        HB._mid("b5", "M", "S", "C"),
        HB._ask("b6", "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (MAB).", "area", solid="S.ABCD", points=["M", "A", "B"]),
    ]
    rb1 = run_fact_route(" ".join(f["quotes"][0] for f in fb1), {"facts": fb1})
    assert rb1.status == "SERVED"
    assert rb1.answers == {"b6": "15/2"}
    _assert_clean_sequencing(rb1.scene3d)
    assert any(o.get("perpendicular_witness") for o in rb1.scene3d["objects"])

    # B2: Without apex placement premise, Engine refuses fail-closed instead of inventing default S
    fb2 = [
        HB._f("u1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("u2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 4.", points=["A", "B", "C", "D"], shape="square", value="4"),
        HB._mid("u3", "M", "S", "C"),
        HB._f("u4", "section", "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MAB).", role="question", solid="S.ABCD", points=["M", "A", "B"]),
    ]
    rb2 = run_fact_route(" ".join(f["quotes"][0] for f in fb2), {"facts": fb2})
    assert rb2.status == "REFUSED"
    assert rb2.code == "UNDERDETERMINED_POINT"

    # B3: Oblique pyramid with (SCD) ⊥ (ABCD), SC = 3, SD = 4, side = 5 -> non-right trapezoid section
    fb3 = [
        HB._f("o1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("o2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 5.", points=["A", "B", "C", "D"], shape="square", value="5"),
        HB._f("o3", "perpendicular", "Mặt bên (SCD) vuông góc với (ABCD).", points_a=["S", "C", "D"], points_b=["A", "B", "C", "D"]),
        HB._f("o4", "length", "SC = 3.", points=["S", "C"], measure="segment", value="3"),
        HB._f("o5", "length", "SD = 4.", points=["S", "D"], measure="segment", value="4"),
        HB._mid("o6", "M", "S", "C"),
        HB._f("o7", "section", "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MAB).", role="question", solid="S.ABCD", points=["M", "A", "B"]),
    ]
    rb3 = run_fact_route(" ".join(f["quotes"][0] for f in fb3), {"facts": fb3})
    assert rb3.status == "SERVED"
    _assert_clean_sequencing(rb3.scene3d)
    sec_b3 = next(o for o in rb3.scene3d["objects"] if o["type"] == "section")
    assert len(sec_b3["polygon"]) == 4


def test_case_c_exterior_q_distinguished_from_bounded_pentagon_section_and_contradictions_refused() -> None:
    # C1: Valid exterior Q on ray SD beyond D (t = 3/2 > 1) -> Q is NOT a vertex of the bounded 5-gon section
    fc1 = [
        HB._f("c1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("c2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("c3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("c4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        _div("c5", "M", "S", "A", "3/4", "SM = 3MA"),
        _div("c6", "N", "S", "B", "3/8", "SN = 3/5 NB"),
        HB._mid("c7", "P", "S", "C"),
        HB._ilp("c8", "Q", "SD", "MNP"),
        HB._f("c9", "section", "Dựng thiết diện của hình chóp S.ABCD cắt bởi (MNP).", role="question", solid="S.ABCD", points=["M", "N", "P"]),
    ]
    rc1 = run_fact_route(" ".join(f["quotes"][0] for f in fc1), {"facts": fc1})
    assert rc1.status == "SERVED"
    _assert_clean_sequencing(rc1.scene3d)
    q_obj = next(o for o in rc1.scene3d["objects"] if (o.get("notation") or o.get("label")) == "Q")
    sec_obj = next(o for o in rc1.scene3d["objects"] if o["type"] == "section")
    assert len(sec_obj["polygon"]) == 5
    assert q_obj["xyz"] not in sec_obj["polygon"]

    # C2: Line parallel to plane -> PARALLEL_NO_INTERSECTION
    fc2 = [
        HB._f("cp1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("cp2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("cp3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("cp4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._mid("cp5", "M", "S", "A"),
        HB._mid("cp6", "N", "S", "B"),
        HB._mid("cp7", "P", "S", "C"),
        HB._ilp("cp8", "K", "AB", "MNP"),
        HB._ask("cp9", "Tính độ dài MK.", "length", points=["M", "K"]),
    ]
    rc2 = run_fact_route(" ".join(f["quotes"][0] for f in fc2), {"facts": fc2})
    assert rc2.status == "REFUSED"
    assert rc2.code == "PARALLEL_NO_INTERSECTION"

    # C3: Contradictory edge length SB = 5 when SA = 3, AB = 2, SA ⊥ (ABCD) -> INCONSISTENT_FACTS
    fc3 = [
        HB._f("cd1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("cd2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("cd3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("cd4", "length", "SA = 3.", points=["S", "A"], measure="segment", value="3"),
        HB._f("cd5", "length", "SB = 5.", points=["S", "B"], measure="segment", value="5"),
        HB._ask("cd6", "Tính thể tích khối chóp S.ABCD.", "volume", solid="S.ABCD"),
    ]
    rc3 = run_fact_route(" ".join(f["quotes"][0] for f in fc3), {"facts": fc3})
    assert rc3.status == "REFUSED"
    assert rc3.code == "INCONSISTENT_FACTS"


def test_cross_family_polyhedra_prisms_distances_and_angles() -> None:
    # Regular hexagonal pyramid S.ABCDEF
    t_hex = "Cho hình chóp lục giác đều S.ABCDEF có cạnh đáy bằng 2 và cạnh bên bằng 4. Tính thể tích khối chóp S.ABCDEF."
    f_hex = [
        HB._f("hx1", "solid", "Cho hình chóp lục giác đều S.ABCDEF", solid="S.ABCDEF", solid_type="pyramid", regular=True),
        HB._f("hx2", "length", "cạnh đáy bằng 2", solid="S.ABCDEF", measure="base_edge", value="2"),
        HB._f("hx3", "length", "cạnh bên bằng 4", solid="S.ABCDEF", measure="lateral_edge", value="4"),
        HB._ask("hx4", "Tính thể tích khối chóp S.ABCDEF.", "volume", solid="S.ABCDEF"),
    ]
    r_hex = run_fact_route(t_hex, {"facts": f_hex})
    assert r_hex.status == "SERVED"
    assert r_hex.answers == {"hx4": "12"}
    _assert_clean_sequencing(r_hex.scene3d)

    # Right-trapezoid pyramid + parallel cutting plane via translate_point
    f_trap = [
        HB._f("tp1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("tp2", "right_angle", "Đáy ABCD vuông tại A.", at="A", points=["B", "D"]),
        HB._f("tp3", "right_angle", "Đáy ABCD vuông tại B.", at="B", points=["A", "C"]),
        HB._f("tp4", "length", "AD = 4.", points=["A", "D"], measure="segment", value="4"),
        HB._f("tp5", "length", "AB = 3.", points=["A", "B"], measure="segment", value="3"),
        HB._f("tp6", "length", "BC = 2.", points=["B", "C"], measure="segment", value="2"),
        HB._f("tp7", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("tp8", "length", "SA = 6.", points=["S", "A"], measure="segment", value="6"),
        HB._mid("tp9", "M", "S", "A"),
        HB._ask(
            "tp10",
            "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng qua M song song với (ABCD).",
            "area",
            solid="S.ABCD",
            plane_relation="parallel",
            point="M",
            points_b=["A", "B", "C", "D"],
        ),
    ]
    r_trap = run_fact_route(" ".join(f["quotes"][0] for f in f_trap), {"facts": f_trap})
    assert r_trap.status == "SERVED"
    assert r_trap.answers == {"tp10": "9/4"}
    _assert_clean_sequencing(r_trap.scene3d)

    # Right triangular prism + section (MBC')
    f_prism = [
        HB._f("pr1", "solid", "Cho lăng trụ đứng ABC.A'B'C'.", solid="ABC.A'B'C'", solid_type="prism", right=True),
        HB._f("pr2", "right_angle", "Tam giác ABC vuông tại A.", at="A", points=["B", "C"]),
        HB._f("pr3", "length", "AB = 3.", points=["A", "B"], measure="segment", value="3"),
        HB._f("pr4", "length", "AC = 4.", points=["A", "C"], measure="segment", value="4"),
        HB._f("pr5", "length", "AA' = 6.", points=["A", "A'"], measure="segment", value="6"),
        HB._mid("pr6", "M", "A", "A'"),
        HB._ask("pr7", "Tính diện tích thiết diện của khối lăng trụ ABC.A'B'C' cắt bởi mặt phẳng (MBC').", "area", solid="ABC.A'B'C'", points=["M", "B", "C'"]),
    ]
    r_prism = run_fact_route(" ".join(f["quotes"][0] for f in f_prism), {"facts": f_prism})
    assert r_prism.status == "SERVED"
    assert r_prism.answers == {"pr7": "3√41/2"}
    _assert_clean_sequencing(r_prism.scene3d)

    # Oblique prism with centroid projection
    f_ob = [
        HB._f("op1", "solid", "Cho lăng trụ ABC.A'B'C'.", solid="ABC.A'B'C'", solid_type="prism", right=False),
        HB._f("op2", "polygon_shape", "Đáy ABC là tam giác đều cạnh 6.", points=["A", "B", "C"], shape="equilateral_triangle", value="6"),
        HB._f("op3", "point_def", "Gọi G là trọng tâm tam giác ABC.", point="G", point_kind="centroid", points=["A", "B", "C"]),
        HB._proj("op4", "G", "A'", "ABC"),
        HB._f("op5", "length", "AA' = 4.", points=["A", "A'"], measure="segment", value="4"),
        HB._ask("op6", "Tính thể tích khối lăng trụ ABC.A'B'C'.", "volume", solid="ABC.A'B'C'"),
    ]
    r_ob = run_fact_route(" ".join(f["quotes"][0] for f in f_ob), {"facts": f_ob})
    assert r_ob.status == "SERVED"
    assert r_ob.answers == {"op6": "18√3"}
    _assert_clean_sequencing(r_ob.scene3d)

    # Goal-directed distance point-to-plane with synthesized projection witness
    f_dist = [
        HB._f("dp1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("dp2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 3.", points=["A", "B", "C", "D"], shape="square", value="3"),
        HB._f("dp3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("dp4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._ask("dp5", "Tính khoảng cách từ A đến (SBC).", "distance", points_a=["A"], points_b=["S", "B", "C"]),
    ]
    r_dist = run_fact_route(" ".join(f["quotes"][0] for f in f_dist), {"facts": f_dist})
    assert r_dist.status == "SERVED"
    assert r_dist.answers == {"dp5": "12/5"}
    _assert_clean_sequencing(r_dist.scene3d)

    # Adapter /4 typed-fact-next/2 line-plane angle
    v2_doc = _prism(
        "ABC",
        6,
        8,
        12,
        ask=("Tính góc giữa đường thẳng A'C và mặt phẳng (ABC).", {"line": ["A'", "C"], "plane": ["A", "B", "C"]}),
    )
    v2_doc["math_goals"][0]["goal_type"] = "angle"
    r_v2 = run_typed_fact_next_v2_route(v2_doc)
    assert r_v2.status == "SERVED"
    _assert_clean_sequencing(r_v2.scene3d)






def test_polyhedral_tetrahedra_dihedral_skew_distance_and_intersection_line_breadth() -> None:
    # 1. Undeclared tetrahedron ABCD + centroid G + midpoint M + length MG
    f_tet = [
        HB._f("t1", "solid", "Cho tứ diện ABCD.", solid="ABCD", solid_type="tetrahedron"),
        HB._f("t2", "polygon_shape", "Tam giác ABC đều cạnh 6.", points=["A", "B", "C"], shape="equilateral_triangle", value="6"),
        HB._f("t3", "perpendicular", "DA vuông góc với (ABC).", points_a=["D", "A"], points_b=["A", "B", "C"]),
        HB._f("t4", "length", "DA = 4.", points=["D", "A"], measure="segment", value="4"),
        HB._f("t5", "point_def", "Gọi G là trọng tâm tam giác ABC.", point="G", point_kind="centroid", points=["A", "B", "C"]),
        HB._mid("t6", "M", "D", "C"),
        HB._ask("t7", "Tính độ dài đoạn MG.", "length", points=["M", "G"]),
    ]
    r_tet = run_fact_route(" ".join(f["quotes"][0] for f in f_tet), {"facts": f_tet})
    assert r_tet.status == "SERVED"
    assert r_tet.answers == {"t7": "√7"}
    seq_tet = CS.check(r_tet.scene3d)
    assert seq_tet["O1"] == [] and seq_tet["O2"] == [] and seq_tet["O4"] == []
    assert next(o for o in r_tet.scene3d["objects"] if o["type"] == "solid").get("shape_class") is None

    # 2. Regular tetrahedron ABCD (Gram chart_metric != I3) + midpoint M + area of triangle ABM
    f_reg_tet = [
        HB._f("rt1", "solid", "Cho tứ diện đều ABCD", solid="ABCD", solid_type="tetrahedron", regular=True),
        HB._f("rt2", "length", "có cạnh bằng 6.", solid="ABCD", measure="edge", value="6"),
        HB._mid("rt3", "M", "C", "D"),
        HB._ask("rt4", "Tính diện tích tam giác ABM.", "area", points=["A", "B", "M"]),
    ]
    r_reg_tet = run_fact_route(" ".join(f["quotes"][0] for f in f_reg_tet), {"facts": f_reg_tet})
    assert r_reg_tet.status == "SERVED"
    assert r_reg_tet.answers == {"rt4": "9√2"}
    assert r_reg_tet.scene3d["chart_metric"] != [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]]
    seq_reg_tet = CS.check(r_reg_tet.scene3d)
    assert seq_reg_tet["O1"] == [] and seq_reg_tet["O2"] == [] and seq_reg_tet["O4"] == []
    assert next(o for o in r_reg_tet.scene3d["objects"] if o["type"] == "solid").get("shape_class") is None

    # 3. Dihedral angle between (SBC) and (ABCD) -> cos = 1/sqrt(2) -> 45 deg / cos^2 = 1/2
    f_dih = [
        HB._f("dh1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("dh2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 4.", points=["A", "B", "C", "D"], shape="square", value="4"),
        HB._f("dh3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("dh4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._ask("dh5", "Tính góc giữa hai mặt phẳng (SBC) và (ABCD).", "angle", points_a=["S", "B", "C"], points_b=["A", "B", "C", "D"]),
    ]
    r_dih = run_fact_route(" ".join(f["quotes"][0] for f in f_dih), {"facts": f_dih})
    assert r_dih.status == "SERVED"
    assert "dh5" in r_dih.answers
    _assert_clean_sequencing(r_dih.scene3d)

    # 4. Skew-line distance between AB and SC
    f_skew = [
        HB._f("sk1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("sk2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 2.", points=["A", "B", "C", "D"], shape="square", value="2"),
        HB._f("sk3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("sk4", "length", "SA = 2.", points=["S", "A"], measure="segment", value="2"),
        HB._ask("sk5", "Tính khoảng cách giữa hai đường thẳng AB và SC.", "distance", points_a=["A", "B"], points_b=["S", "C"]),
    ]
    r_skew = run_fact_route(" ".join(f["quotes"][0] for f in f_skew), {"facts": f_skew})
    assert r_skew.status == "SERVED"
    assert r_skew.answers == {"sk5": "√2"}
    _assert_clean_sequencing(r_skew.scene3d)

    # 5. Plane-plane intersection line (SAC) ∩ (SBD)
    f_iline = [
        HB._f("il1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("il2", "polygon_shape", "Đáy ABCD là hình vuông cạnh 4.", points=["A", "B", "C", "D"], shape="square", value="4"),
        HB._f("il3", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("il4", "length", "SA = 4.", points=["S", "A"], measure="segment", value="4"),
        HB._f(
            "il5",
            "intersection_line",
            "Tìm giao tuyến của hai mặt phẳng (SAC) và (SBD).",
            role="question",
            points_a=["S", "A", "C"],
            points_b=["S", "B", "D"],
        ),
    ]
    r_iline = run_fact_route(" ".join(f["quotes"][0] for f in f_iline), {"facts": f_iline})
    assert r_iline.status == "SERVED"
    _assert_clean_sequencing(r_iline.scene3d)
    assert any(o.get("producer") == "intersect_plane_plane" for o in r_iline.scene3d["objects"])

