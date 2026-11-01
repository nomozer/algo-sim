# -*- coding: utf-8 -*-
"""Multi-Object FactGraph + Composite Geometry + Generalized Geometric Relations on Route D `/4`
(run `hybrid-master-backend-replacement`, Continuation 9). 0 live provider calls.

Verifies:
1. Certified sphere inscribed in convex polyhedra (exact Fraction solver across ALL boundary faces,
   strict inward half-spaces, strict interior face-polygon contacts, independent 9V^2 = rho^2*(sum S_k)^2 check).
2. Certified sphere-plane tangency (`tangent_to`) distinguishing tangency (d^2 == R^2), secant cut
   (`PLANE_INTERSECTS_SPHERE_NOT_TANGENT`), disjointness (`PLANE_DOES_NOT_TOUCH_SPHERE`), and wrong contact point.
3. Composite topologies: dual spheres ((S1) circumscribed + (S2) inscribed), multi-polyhedron `shared_faces` + sphere,
   polyhedron plane section + sphere, and host cylinder/cone + inscribed/circumscribed spheres.
4. Multi-object Vietnamese Source Gate grounding & disambiguation.
5. Four-layer `relation_certificates` (`SOURCE_GROUNDING_PROOF`, `GEOMETRIC_RELATION_PROOF`,
   `KERNEL_EXECUTION_PROOF`, `RESULT_CERTIFICATE`) and composite `construction_trace`.
6. Metamorphic scaling, representation equivalence, permutation invariance, and legacy `/1` isolation.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter3_simulation import run_typed_fact_next_route
from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from app.simulation.geometry.radical import parse_exact
from app.simulation.geometry_functions.typed_fact_next import (
    TypedFactNextValidationError,
    parse_typed_fact_next,
    parse_typed_fact_next_v2,
)

_P = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/composite_relations_probe.py"
)
_spec = importlib.util.spec_from_file_location("composite_relations_probe", _P)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

REQUIRED_PROOF_LAYERS = {
    "SOURCE_GROUNDING_PROOF",
    "GEOMETRIC_RELATION_PROOF",
    "KERNEL_EXECUTION_PROOF",
    "RESULT_CERTIFICATE",
}


@pytest.mark.parametrize("cid,payload,want_map", P.POSITIVE_CASES, ids=[x[0] for x in P.POSITIVE_CASES])
def test_composite_relation_positives_serve_with_four_layer_certificates(
    cid: str, payload: dict, want_map: dict[str, str]
) -> None:
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (cid, r.code, r.reason)
    for gid, want_expr in want_map.items():
        assert gid in r.answer_exact, (cid, gid, r.answer_exact)
        assert parse_exact(r.answer_exact[gid]["coef"]) == parse_exact(want_expr), (
            cid,
            gid,
            r.answer_exact[gid]["coef"],
            want_expr,
        )
    for step in r.trace:
        assert step.get("preconditions") and step.get("postconditions"), (cid, step)

    env = build_adapter4_response(r, payload["problem_text"])
    certs = env["route_d"].get("relation_certificates") or []
    assert len(certs) >= 1, cid
    for cert in certs:
        assert REQUIRED_PROOF_LAYERS <= set(cert.keys()), (cid, cert.keys())
        assert cert["SOURCE_GROUNDING_PROOF"]["verified"] is True
        assert cert["GEOMETRIC_RELATION_PROOF"]["verified"] is True
        assert cert["KERNEL_EXECUTION_PROOF"]["verified"] is True
        assert cert["RESULT_CERTIFICATE"]["verified"] is True


@pytest.mark.parametrize("cid,payload,want_code", P.NEGATIVE_CASES, ids=[x[0] for x in P.NEGATIVE_CASES])
def test_composite_relation_negatives_refuse_fail_closed_without_leaking_claims(
    cid: str, payload: dict, want_code: str
) -> None:
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.scene3d is None, (cid, r.status, r.code)
    assert r.code == want_code, (cid, r.code, r.reason)
    assert r.route_d.get("relation_certificates", []) == []
    env = build_adapter4_response(r, payload["problem_text"])
    assert env["route_d"]["status"] == "REFUSED"
    assert "relation_certificates" not in env["route_d"]


def test_named_incenter_and_tangency_contact_coordinates_and_unnamed_cleanliness() -> None:
    p_tan = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.tetra_asym_132.tangent_plane_with_contact_point")
    r_tan = run_typed_fact_next_v2_route(p_tan)
    assert r_tan.status == "SERVED"
    assert r_tan.points["I"] == (Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))
    assert r_tan.points["T"] == (Fraction(3, 7), Fraction(10, 21), Fraction(13, 21))

    p_unnamed = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.inscribed.radius")
    r_unnamed = run_typed_fact_next_v2_route(p_unnamed)
    assert r_unnamed.status == "SERVED"
    assert set(r_unnamed.points) == {"A", "B", "C", "D", "A'", "B'", "C'", "D'"}


def test_dual_spheres_scene3d_emits_two_distinct_curved_solids() -> None:
    p_dual = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.pyr_sq_6_4.dual_spheres.distinct_centers")
    r = run_typed_fact_next_v2_route(p_dual)
    assert r.status == "SERVED"
    curved_objs = [o for o in r.scene3d["objects"] if o.get("type") == "curved_solid"]
    assert len(curved_objs) == 2
    radii = sorted(parse_exact(o["radius_exact"]) for o in curved_objs if "radius_exact" in o)
    if radii:
        assert radii == sorted([parse_exact("3/2"), parse_exact("17/4")])


def test_symbolic_unit_inscribed_sphere_formats_exact_expressions() -> None:
    for goal_type, question, want_coef, want_dim, want_text in (
        ("radius", "Tính bán kính mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.", "1/2", 1, "a/2"),
        ("area", "Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.", "π", 2, "πa²"),
        ("volume", "Tính thể tích khối cầu nội tiếp hình lập phương ABCD.A'B'C'D'.", "π/6", 3, "πa³/6"),
    ):
        payload = P.make_inscribed_payload(
            problem_text=P.CUBE_A_GIVEN + " " + question,
            poly_solid=P.CUBE_A_SOLID,
            premises=P.CUBE_A_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote=question,
            goal_type=goal_type,
            goal_quote=question,
            length_unit="a",
        )
        r = run_typed_fact_next_v2_route(payload)
        assert r.status == "SERVED", (goal_type, r.code, r.reason)
        assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(want_coef)
        assert r.answer_exact["mg1"]["dim"] == want_dim and r.answer_exact["mg1"]["unit"] == "a"
        assert r.answers["mg1"] == want_text


def test_metamorphic_scaling_and_representation_and_permutation_invariance() -> None:
    # 1. Representation equivalence: SolidSpec.inscribed_in == GeometricRelationSpecV2(kind="inscribed_in")
    p_field = P.make_inscribed_payload(
        problem_text=P.CUBE_2_GIVEN + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'. Tính thể tích khối cầu (S).",
        poly_solid=P.CUBE_2_SOLID,
        premises=P.CUBE_2_PREMS,
        sphere_notation="(S)",
        sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
        goal_type="volume",
        goal_quote="Tính thể tích khối cầu (S).",
        use_relation_spec=False,
    )
    p_rel = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.inscribed.volume_rel_v2")
    r_field = run_typed_fact_next_v2_route(p_field)
    r_rel = run_typed_fact_next_v2_route(p_rel)
    assert r_field.status == "SERVED" and r_rel.status == "SERVED"
    assert r_field.answer_exact == r_rel.answer_exact

    # 2. Metamorphic scaling: S.ABCD (6, 4) -> (12, 8) doubles radius (3/2 -> 3) and octuples volume (9π/2 -> 36π)
    p_scaled = P.make_inscribed_payload(
        problem_text=(
            "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 12, chiều cao bằng 8. "
            "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD. Tính thể tích khối cầu (S)."
        ),
        poly_solid=P.PYR_SQ_64_SOLID,
        premises=[
            P._prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]}, "Cho hình chóp tứ giác đều S.ABCD"),
            P._prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "12"},
                    "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 12"),
            P._prem("height", {"value": "8"}, "chiều cao bằng 8", solid_id=None),
        ],
        sphere_notation="(S)",
        sphere_quote="Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD.",
        goal_type="volume",
        goal_quote="Tính thể tích khối cầu (S).",
    )
    r_scaled = run_typed_fact_next_v2_route(p_scaled)
    assert r_scaled.status == "SERVED"
    assert parse_exact(r_scaled.answer_exact["mg1"]["coef"]) == parse_exact("36π")

    # 3. Goal & solid permutation invariance on dual-sphere composite
    p_dual = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.dual_spheres.multi_goal"))
    p_dual["solids"] = [p_dual["solids"][0], p_dual["solids"][2], p_dual["solids"][1]]
    p_dual["math_goals"] = list(reversed(p_dual["math_goals"]))
    r_perm = run_typed_fact_next_v2_route(p_dual)
    assert r_perm.status == "SERVED"
    assert parse_exact(r_perm.answer_exact["mg1"]["coef"]) == parse_exact("12π")
    assert parse_exact(r_perm.answer_exact["mg2"]["coef"]) == parse_exact("4π")
    assert parse_exact(r_perm.answer_exact["mg3"]["coef"]) == parse_exact("8")


def test_scope_directionality_and_legacy_v1_isolation() -> None:
    p_rel = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.inscribed.volume_rel_v2"))
    parsed = parse_typed_fact_next_v2(p_rel)
    assert parsed.relations[0].kind == "inscribed_in"

    # Legacy `/1` schema rejects `inscribed_in` relation kind and `inscribed_in` solid field
    v1_rel = deepcopy(p_rel)
    v1_rel["schema_version"] = "typed-fact-next/1"
    with pytest.raises(TypedFactNextValidationError):
        parse_typed_fact_next(v1_rel)

    v1_field = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.inscribed.radius"))
    v1_field["schema_version"] = "typed-fact-next/1"
    res_v1 = run_typed_fact_next_route(v1_field)
    assert res_v1.status == "REFUSED"


def test_v2_closed_relation_allowed_fields_cover_all_v2_kinds() -> None:
    from typing import get_args
    from app.simulation.geometry_functions import typed_fact_next as T

    v2_kinds = set(get_args(T.GeometricRelationSpecV2.model_fields["kind"].annotation))
    assert set(T.KIND_ALLOWED_FIELDS_V2["relation_v2"]) == v2_kinds
    all_fields = set(T.GeometricRelationSpecV2.model_fields)
    covered = set().union(*(set(v) for v in T.KIND_ALLOWED_FIELDS_V2["relation_v2"].values()))
    assert covered == all_fields


def test_blocker1_4_label_tangent_plane_with_collinear_prefix_and_named_center_serves() -> None:
    payload = P.make_inscribed_payload(
        problem_text=(
            P.CUBE_2_GIVEN
            + " Gọi M là trung điểm của AB."
            + " Gọi (S) là mặt cầu có tâm I nội tiếp hình lập phương ABCD.A'B'C'D'."
            + " Mặt cầu (S) tiếp xúc với mặt phẳng (AMBC) tại H."
            + " Tính bán kính mặt cầu (S)."
        ),
        poly_solid=P.CUBE_2_SOLID,
        premises=[
            *deepcopy(P.CUBE_2_PREMS),
            P._prem("midpoint", {"point": "M", "segment": ["A", "B"]}, "Gọi M là trung điểm của AB."),
        ],
        sphere_notation="(S)",
        sphere_center="I",
        sphere_quote="Gọi (S) là mặt cầu có tâm I nội tiếp hình lập phương ABCD.A'B'C'D'.",
        goal_type="radius",
        goal_quote="Tính bán kính mặt cầu (S).",
        extra_relations=[
            {
                "relation_id": "rel_tan_ambc",
                "kind": "tangent_to",
                "solid_a": "sph",
                "solid_b": "poly",
                "entity_b": ["A", "M", "B", "C"],
                "contact_ref": "H",
                "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (AMBC) tại H.",
            }
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("1")
    assert r.points["H"] == (Fraction(1), Fraction(1), Fraction(0))


def test_major1_axial_host_sphere_question_clauses_single_and_multi_goal_serve() -> None:
    cone_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            "Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4. "
            "Tính bán kính của mặt cầu ngoại tiếp hình nón (N)."
        ),
        "solids": [
            {
                "solid_id": "cone",
                "solid_type": "cone",
                "notation": "(N)",
                "radius": "3",
                "height": "4",
                "quote": "Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4.",
            },
            {
                "solid_id": "sph",
                "solid_type": "sphere",
                "notation": "()",
                "circumscribes": "cone",
                "quote": "Tính bán kính của mặt cầu ngoại tiếp hình nón (N).",
            },
        ],
        "premises": [],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "cone",
                "quote": "Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4.",
            }
        ],
        "math_goals": [
            P._sphere_goal("mg1", "radius", "sph", "()", "Tính bán kính của mặt cầu ngoại tiếp hình nón (N).")
        ],
    }
    r1 = run_typed_fact_next_v2_route(cone_payload)
    assert r1.status == "SERVED" and r1.kernel_check is True, (r1.code, r1.reason)
    assert parse_exact(r1.answer_exact["mg1"]["coef"]) == parse_exact("25/8")

    cyl_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            "Cho hình trụ có hai đáy có tâm O và O', bán kính đáy bằng 3 và chiều cao bằng 6. "
            "Tính diện tích xung quanh của hình trụ và diện tích của mặt cầu nội tiếp hình trụ."
        ),
        "solids": [
            {
                "solid_id": "cyl",
                "solid_type": "cylinder",
                "notation": "O.O'",
                "center": "O",
                "apex_or_top": "O'",
                "radius": "3",
                "height": "6",
                "quote": "Cho hình trụ có hai đáy có tâm O và O', bán kính đáy bằng 3 và chiều cao bằng 6.",
            },
            {
                "solid_id": "sph",
                "solid_type": "sphere",
                "notation": "()",
                "inscribed_in": "cyl",
                "quote": "diện tích của mặt cầu nội tiếp hình trụ.",
            },
        ],
        "premises": [],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "cyl",
                "quote": "Cho hình trụ có hai đáy có tâm O và O', bán kính đáy bằng 3 và chiều cao bằng 6.",
            }
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "lateral_area",
                "solid_id": "cyl",
                "target": {"solid": "O.O'"},
                "quote": "Tính diện tích xung quanh của hình trụ và diện tích của mặt cầu nội tiếp hình trụ.",
            },
            P._sphere_goal(
                "mg2",
                "area",
                "sph",
                "()",
                "Tính diện tích xung quanh của hình trụ và diện tích của mặt cầu nội tiếp hình trụ.",
            ),
        ],
    }
    r2 = run_typed_fact_next_v2_route(cyl_payload)
    assert r2.status == "SERVED" and r2.kernel_check is True, (r2.code, r2.reason)
    assert parse_exact(r2.answer_exact["mg1"]["coef"]) == parse_exact("36π")
    assert parse_exact(r2.answer_exact["mg2"]["coef"]) == parse_exact("36π")


def test_major2_two_unnamed_spheres_with_tangent_to_uses_disambiguated_curved_sym() -> None:
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            P.CUBE_2_GIVEN
            + " Gọi O là tâm mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'."
            + " Gọi I là tâm mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
            + " Mặt cầu có tâm I tiếp xúc với mặt phẳng (ABCD) tại H."
            + " Tính độ dài đoạn thẳng OH."
        ),
        "solids": [
            deepcopy(P.CUBE_2_SOLID),
            {
                "solid_id": "sph_out",
                "solid_type": "sphere",
                "notation": "()",
                "center": "O",
                "circumscribes": "poly",
                "quote": "Gọi O là tâm mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            },
            {
                "solid_id": "sph_in",
                "solid_type": "sphere",
                "notation": "()",
                "center": "I",
                "inscribed_in": "poly",
                "quote": "Gọi I là tâm mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            },
        ],
        "premises": deepcopy(P.CUBE_2_PREMS),
        "relations": [
            {
                "relation_id": "rel_tan",
                "kind": "tangent_to",
                "solid_a": "sph_in",
                "solid_b": "poly",
                "entity_b": ["A", "B", "C", "D"],
                "contact_ref": "H",
                "quote": "Mặt cầu có tâm I tiếp xúc với mặt phẳng (ABCD) tại H.",
            }
        ],
        "derived_sections": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": P.CUBE_2_SOLID["quote"]}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "poly",
                "target": {"segment": ["O", "H"]},
                "quote": "Tính độ dài đoạn thẳng OH.",
            }
        ],
    }
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("1")


def test_major3_downstream_premise_consuming_tangent_contact_ref_serves() -> None:
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            P.CUBE_2_GIVEN
            + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
            + " Mặt cầu (S) tiếp xúc với mặt phẳng (ABCD) tại H."
            + " Gọi M là trung điểm của A'H."
            + " Tính độ dài đoạn thẳng AM."
        ),
        "solids": [
            deepcopy(P.CUBE_2_SOLID),
            {
                "solid_id": "sph",
                "solid_type": "sphere",
                "notation": "(S)",
                "inscribed_in": "poly",
                "quote": "Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            },
        ],
        "premises": [
            *deepcopy(P.CUBE_2_PREMS),
            P._prem("midpoint", {"point": "M", "segment": ["A'", "H"]}, "Gọi M là trung điểm của A'H."),
        ],
        "relations": [
            {
                "relation_id": "rel_tan_h",
                "kind": "tangent_to",
                "solid_a": "sph",
                "solid_b": "poly",
                "entity_b": ["A", "B", "C", "D"],
                "contact_ref": "H",
                "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (ABCD) tại H.",
            }
        ],
        "derived_sections": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": P.CUBE_2_SOLID["quote"]}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "distance",
                "solid_id": "poly",
                "target": {"segment": ["A", "M"]},
                "quote": "Tính độ dài đoạn thẳng AM.",
            }
        ],
    }
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("√6/2")


def test_major4_non_coplanar_or_non_convex_4_vertex_face_rejected_in_mat_ngoai_khoi() -> None:
    from fractions import Fraction
    from app.simulation.geometry_functions import engine as E, registry as R

    calls = R.doc_ke_hoach({"calls": [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["q"]}},
        {"id": "c2", "fn": "curved_solid", "args": {"kind": "sphere", "solid": "(S)", "inscribed_in": "S.ABCD"}, "source": {"quotes": ["q"]}},
    ]})
    d_skew = E._Dung(calls, "q")
    d_skew.thu_khoi()
    d_skew.G2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
    d_skew.h2 = Fraction(1)
    d_skew.pts = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(6), Fraction(0), Fraction(0)),
        "C": (Fraction(6), Fraction(6), Fraction(0)),
        "D": (Fraction(3, 2), Fraction(9, 2), Fraction(2)),
        "S": (Fraction(3), Fraction(3), Fraction(4)),
    }
    with pytest.raises(R.TuChoi) as exc_skew:
        d_skew._giai_mat_cau_noi_tiep(calls[1], d_skew.khoi["S.ABCD"])
    assert exc_skew.value.code == "NON_COPLANAR_POINTS"

    d_nonconv = E._Dung(calls, "q")
    d_nonconv.thu_khoi()
    d_nonconv.G2 = ((Fraction(1), Fraction(0)), (Fraction(0), Fraction(1)))
    d_nonconv.h2 = Fraction(1)
    d_nonconv.pts = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(4), Fraction(0), Fraction(0)),
        "C": (Fraction(1), Fraction(1), Fraction(0)),
        "D": (Fraction(0), Fraction(4), Fraction(0)),
        "S": (Fraction(1), Fraction(1), Fraction(3)),
    }
    with pytest.raises(R.TuChoi) as exc_nc:
        d_nonconv._giai_mat_cau_noi_tiep(calls[1], d_nonconv.khoi["S.ABCD"])
    assert exc_nc.value.code == "DEGENERATE_SOLID"


def test_minor1_duplicate_relation_id_and_tangent_fact_id_collision() -> None:
    p_dup = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.cube_2.inscribed.volume_rel_v2"))
    p_dup["solids"].append({
        "solid_id": "sph_out",
        "solid_type": "sphere",
        "notation": "(S2)",
        "quote": p_dup["solids"][1]["quote"],
    })
    p_dup["relations"].append({
        "relation_id": p_dup["relations"][0]["relation_id"],
        "kind": "circumscribes",
        "solid_a": "sph_out",
        "solid_b": "poly",
        "quote": p_dup["relations"][0]["quote"],
    })
    with pytest.raises(TypedFactNextValidationError) as exc:
        parse_typed_fact_next_v2(p_dup)
    assert exc.value.code == "INVALID_RELATION_SPEC"

    # Valid `tangent_to` with relation_id == "p1" (colliding with auto-generated premise ID "p1") must disambiguate cleanly
    p_col = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.tetra_asym_132.tangent_plane_with_contact_point"))
    p_col["relations"][0]["relation_id"] = "p1"
    r_col = run_typed_fact_next_v2_route(p_col)
    assert r_col.status == "SERVED" and r_col.kernel_check is True, (r_col.code, r_col.reason)


def test_minor2_unreachable_tangent_plane_cycle_refuses_dependency_cycle() -> None:
    from app.simulation.geometry_functions import planner as PL, registry as R

    facts = [
        {"id": "f1", "kind": "solid", "role": "premise", "solid": "S.ABC", "solid_type": "pyramid", "quotes": ["Cho hình chóp S.ABC."]},
        {"id": "f2", "kind": "solid", "role": "premise", "solid": "(S)", "quotes": ["Cho hình chóp S.ABC."],
         "curved": {"kind": "sphere", "inscribed_in": "S.ABC"}},
        {"id": "f3", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint",
         "points": ["A", "H"], "quotes": ["Cho hình chóp S.ABC."]},
        {"id": "f4", "kind": "projection", "role": "premise", "solid": "(S)", "quotes": ["Cho hình chóp S.ABC."],
         "curved_part": {"role": "tangent_plane", "plane": ["A", "B", "M"], "point": "H"}},
        {"id": "q1", "kind": "question", "role": "question", "quantity": "radius", "solid": "(S)", "quotes": ["Cho hình chóp S.ABC."]},
    ]
    with pytest.raises(R.TuChoi) as exc:
        PL.lap_ke_hoach({"facts": facts}, "Cho hình chóp S.ABC.")
    assert exc.value.code == "DEPENDENCY_CYCLE"


def test_minor3_and_nit2_single_authority_no_sphere_branch_and_qf_inv_zero_guard() -> None:
    import re
    from pathlib import Path
    from app.simulation.geometry_functions import engine as E, typed_fact_next as T

    branch_re = re.compile(r'(?:==|!=|\bin\b)\s*["\']sphere["\']')
    for mod in (T, E):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert not branch_re.search(src), f"literal 'sphere' branch found in {mod.__name__}"

    with pytest.raises(ZeroDivisionError):
        E._qf_inv({}, [2])


def test_blocker_r2_1_axial_composite_duplicate_solid_symbol_refuses_ambiguous_reference() -> None:
    from app.ai.function_route import run_function_route

    txt = (
        "Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4. "
        "Gọi (N) là mặt cầu ngoại tiếp hình nón (N). "
        "Tính thể tích của khối nón (N)."
    )
    plan = {
        "calls": [
            {
                "id": "c1",
                "fn": "curved_solid",
                "args": {"kind": "cone", "solid": "(N)", "radius": "3", "height": "4"},
                "source": {"quotes": ["Cho hình nón (N) có bán kính đáy bằng 3 và chiều cao bằng 4."]},
            },
            {
                "id": "c2",
                "fn": "curved_solid",
                "args": {"kind": "sphere", "solid": "(N)", "circumscribes": "(N)"},
                "source": {"quotes": ["Gọi (N) là mặt cầu ngoại tiếp hình nón (N)."]},
            },
            {
                "id": "q1",
                "fn": "ask_curved_volume",
                "args": {"solid": "(N)"},
                "source": {"quotes": ["Tính thể tích của khối nón (N)."]},
            },
        ]
    }
    res = run_function_route(txt, plan)
    assert res.status == "REFUSED"
    assert res.code == "AMBIGUOUS_REFERENCE"


def test_major_r2_1_and_r2_2_dual_unnamed_spheres_on_parenthesized_axial_host_and_wrong_scope_refusal() -> None:
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": (
            "Cho hình trụ (T) có bán kính đáy bằng 3 và chiều cao bằng 6. "
            "Tính diện tích của mặt cầu ngoại tiếp hình trụ (T) và diện tích của mặt cầu nội tiếp hình trụ (T)."
        ),
        "solids": [
            {
                "solid_id": "cyl",
                "solid_type": "cylinder",
                "notation": "(T)",
                "radius": "3",
                "height": "6",
                "quote": "Cho hình trụ (T) có bán kính đáy bằng 3 và chiều cao bằng 6.",
            },
            {
                "solid_id": "sph_out",
                "solid_type": "sphere",
                "notation": "()",
                "circumscribes": "cyl",
                "quote": "Tính diện tích của mặt cầu ngoại tiếp hình trụ (T)",
            },
            {
                "solid_id": "sph_in",
                "solid_type": "sphere",
                "notation": "()",
                "inscribed_in": "cyl",
                "quote": "diện tích của mặt cầu nội tiếp hình trụ (T).",
            },
        ],
        "premises": [],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "cyl",
                "quote": "Cho hình trụ (T) có bán kính đáy bằng 3 và chiều cao bằng 6.",
            }
        ],
        "math_goals": [
            P._sphere_goal(
                "mg1",
                "area",
                "sph_out",
                "()",
                "Tính diện tích của mặt cầu ngoại tiếp hình trụ (T) và diện tích của mặt cầu nội tiếp hình trụ (T).",
            ),
            P._sphere_goal(
                "mg2",
                "area",
                "sph_in",
                "()",
                "Tính diện tích của mặt cầu ngoại tiếp hình trụ (T) và diện tích của mặt cầu nội tiếp hình trụ (T).",
            ),
        ],
    }
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact("72π")
    assert parse_exact(r.answer_exact["mg2"]["coef"]) == parse_exact("36π")

    # Wrong scope (`solid_id="cyl"` with `target={"solid": "()"}`) must refuse SOURCE_OBJECT_MISMATCH
    bad_scope = deepcopy(payload)
    bad_scope["math_goals"][0]["solid_id"] = "cyl"
    with pytest.raises(TypedFactNextValidationError) as exc_bad:
        parse_typed_fact_next_v2(bad_scope)
    assert exc_bad.value.code == "SOURCE_OBJECT_MISMATCH"

    # Unscoped `target={"solid": "()"}` with two unnamed spheres must still refuse UNKNOWN_SOLID
    unscoped = deepcopy(payload)
    unscoped["math_goals"][0]["solid_id"] = None
    with pytest.raises(TypedFactNextValidationError) as exc_unscoped:
        parse_typed_fact_next_v2(unscoped)
    assert exc_unscoped.value.code == "UNKNOWN_SOLID"


def test_minor_r2_1_bridge_disambiguates_solid_premise_perpendicular_and_goal_id_collisions() -> None:
    # 1. solid_id == "p1" with a non-merged premise (segment_length -> fid="p1") must not collide at doc_du_kien
    p_solid = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.tetra_asym_132.inscribed.named_center"))
    p_solid["solids"][0]["solid_id"] = "p1"
    p_solid["solids"][1]["inscribed_in"] = "p1"
    for prem in p_solid["premises"]:
        if prem.get("solid_id") == "poly":
            prem["solid_id"] = "p1"
        if prem.get("args", {}).get("solid") == "poly":
            prem["args"]["solid"] = "p1"
    p_solid["simulation_goals"][0]["target_solid_id"] = "p1"
    for mg in p_solid["math_goals"]:
        if mg.get("solid_id") == "poly":
            mg["solid_id"] = "p1"
    r1 = run_typed_fact_next_v2_route(p_solid)
    assert r1.status == "SERVED" and r1.kernel_check is True, (r1.code, r1.reason)

    # 2. perpendicular relation_id == "p1" must not collide with premise "p1"
    p_perp = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.tetra_asym_132.inscribed.named_center"))
    p_perp["relations"].append({
        "relation_id": "p1",
        "kind": "perpendicular",
        "solid_id": "poly",
        "entity_a": ["S", "A"],
        "entity_b": ["A", "B", "C"],
        "quote": "SA vuông góc với mặt phẳng (ABC)",
    })
    r_perp = run_typed_fact_next_v2_route(p_perp)
    assert r_perp.status == "SERVED" and r_perp.kernel_check is True, (r_perp.code, r_perp.reason)

    # 3. tangent_to relation_id == "p1" AND math_goal goal_id == "rel_p1" must not collide
    p_goal = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cr.tetra_asym_132.tangent_plane_with_contact_point"))
    p_goal["relations"][0]["relation_id"] = "p1"
    p_goal["math_goals"][0]["goal_id"] = "rel_p1"
    r2 = run_typed_fact_next_v2_route(p_goal)
    assert r2.status == "SERVED" and r2.kernel_check is True, (r2.code, r2.reason)


def test_minor_r2_2_irrational_axial_host_top_or_rim_reused_as_sphere_center_refuses_inconsistent_facts() -> None:
    from app.simulation.geometry_functions import engine as E, registry as R

    for bad_center in ("S", "A"):
        calls = R.doc_ke_hoach({
            "calls": [
                {
                    "id": "c1",
                    "fn": "curved_solid",
                    "args": {
                        "kind": "cone",
                        "solid": "S.O",
                        "center": "O",
                        "top": "S",
                        "rim": "A",
                        "radius": "√2",
                        "height": "√2",
                    },
                    "source": {"quotes": ["Cho hình nón S.O."]},
                },
                {
                    "id": "c2",
                    "fn": "curved_solid",
                    "args": {
                        "kind": "sphere",
                        "solid": "(S1)",
                        "center": bad_center,
                        "circumscribes": "S.O",
                    },
                    "source": {"quotes": ["Gọi (S1) là mặt cầu ngoại tiếp hình nón S.O."]},
                },
                {
                    "id": "q1",
                    "fn": "ask_radius",
                    "args": {"solid": "(S1)"},
                    "source": {"quotes": ["Tính bán kính mặt cầu (S1)."]},
                },
            ]
        })
        with pytest.raises(R.TuChoi) as exc:
            E._dung_cong_ghep(calls, "Cho hình nón S.O.")
        assert exc.value.code == "INCONSISTENT_FACTS"

