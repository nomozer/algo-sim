# -*- coding: utf-8 -*-
"""Unit & adversarial verification suite for `trig-construction-certificate/1` (Phase 6 & Phase 8 §11.4).

Covers:
1. Exact special angles (30°, 45°, 60°, and 90°/120°/135°/150° polygon/dihedral domain) and exact given trig ratios
   (`sin`, `cos`, `tan`, `cot`) in `Fraction` / `Radical` with zero float approximations.
2. All 11 closed trigonometric & right-triangle construction identities across Euclidean and non-Euclidean SPD Gram charts.
3. All 9 Phase 8 (§11.4) adversarial certificate mutations — including 45° leg-swap and `sin` <-> `cos` identity-swap
   where numeric values coincide, non-projection base rays in `line_plane_angle`, and accidental Gram orthogonality
   without deductive right-angle premises.
4. Negative trigonometric domain counterexamples (§9.7): non-exact degrees (`37°`), degenerate/obtuse angles (`0°`,
   `90°`, `120°`, `180°`), non-positive or out-of-range trig ratios, ambiguous obtuse `sin`, and float inputs.
5. `adapter4_route.py` binding & tamper-rejection (`RESULT_BINDING_UNVERIFIED`) while keeping non-trig served envelopes
   byte-identical.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction

import pytest

from app.ai.adapter4_route import _phong_bi, build_adapter4_response
from app.simulation.geometry_functions.engine import dung_tu_loi_goi
from app.simulation.geometry_functions.trig_construction_certificates import (
    CLOSED_TRIG_IDENTITIES,
    ID_ADJ_FROM_HYP_COS,
    ID_ADJ_FROM_OPP_COT,
    ID_HYP_FROM_ADJ_COS,
    ID_HYP_FROM_OPP_SIN,
    ID_OPP_FROM_ADJ_TAN,
    ID_OPP_FROM_HYP_SIN,
    ID_PYTH_EQUAL_LEGS,
    ID_PYTH_HYP_FROM_LEGS,
    ID_PYTH_LEG_FROM_HYP,
    ID_PYTH_LEG_RATIO,
    ID_RHOMBUS_HALF_DIAG_COS,
    TRIG_CONSTRUCTION_CERTIFICATE_VERSION,
    TrigCertificateError,
    build_trig_construction_certificate,
    exact_trig_angle_params,
    format_exact_length_expr,
    verify_trig_construction_certificate,
)


# ── Helpers for synthetic exact configurations ────────────────────────────────────────────────────────────────────────

def _call(cid: str, fn: str, args: dict, quote: str) -> dict:
    return {"id": cid, "fn": fn, "args": args, "quotes": [quote]}


def _scene_objects_from_pts(pts: dict[str, tuple[Fraction, Fraction, Fraction]]) -> dict[str, dict]:
    out = {}
    for lbl, xyz in pts.items():
        oid = lbl.replace("'", "_prime")
        out[oid] = {"id": oid, "type": "point3", "xyz": [str(xyz[0]), str(xyz[1]), str(xyz[2])]}
    return out


def _base_45_pyramid_fixture(*, trig_id: str = ID_OPP_FROM_HYP_SIN, derived_role: str = "opposite_leg") -> tuple[dict, list[dict], dict, list[list[Fraction]]]:
    """Pyramid S.ABC with SA ⊥ (ABC), AB = a, SA = a, SB = a√2, ∠(SB, (ABC)) = 45° at vertex B (foot A)."""
    calls = [
        _call("s1", "pyramid", {"apex": "S", "base": ["A", "B", "C"]}, "hình chóp S.ABC"),
        _call("p1", "perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "SA vuông góc với đáy (ABC)"),
        _call("p2", "line_plane_angle", {"line": ["S", "B"], "plane": ["A", "B", "C"], "value": "45", "unit": "deg"},
              "góc giữa SB và (ABC) bằng 45°"),
        _call("p3", "segment_length", {"segment": ["S", "B"], "value": "a*sqrt(2)"}, "SB = a√2"),
    ]
    pts = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "S": (Fraction(0), Fraction(0), Fraction(1)),
    }
    g_mat = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    known_side = "hypotenuse" if trig_id in (ID_OPP_FROM_HYP_SIN, ID_ADJ_FROM_HYP_COS) else "adjacent_leg"
    cert = build_trig_construction_certificate(
        certificate_id="trig_cert_45",
        derived_role=derived_role,
        derived_right_triangle=("A", "B", "S"),
        perpendicularity_rule="line_perpendicular_to_plane",
        perpendicularity_calls=("p1",),
        angle_witness_kind="line_plane_angle",
        angle_witness_calls=("p2",),
        sin_sq=Fraction(1, 2),
        cos_sq=Fraction(1, 2),
        angle_unit="deg",
        angle_raw_value="45",
        trig_identity=trig_id,
        known_side_roles=(known_side,),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=calls,
        points_by_label=pts,
        chart_metric=g_mat,
        length_unit="a",
        extra_premise_calls=("p3",),
    )
    return cert, calls, pts, g_mat


# ── 1. Exact special angles & exact trig ratios ───────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("deg", "exp_sin_sq", "exp_cos_sq"),
    [
        ("30", Fraction(1, 4), Fraction(3, 4)),
        ("45", Fraction(1, 2), Fraction(1, 2)),
        ("60", Fraction(3, 4), Fraction(1, 4)),
    ],
)
def test_exact_special_acute_degrees(deg: str, exp_sin_sq: Fraction, exp_cos_sq: Fraction) -> None:
    params = exact_trig_angle_params(deg, "deg")
    assert params.sin_sq == exp_sin_sq
    assert params.cos_sq == exp_cos_sq
    assert params.cos_sign == 1
    assert params.sin_sq + params.cos_sq == Fraction(1)


@pytest.mark.parametrize(
    ("raw", "unit", "exp_sin_sq", "exp_cos_sq"),
    [
        ("3/5", "sin", Fraction(9, 25), Fraction(16, 25)),
        ("sqrt(2)/2", "sin", Fraction(1, 2), Fraction(1, 2)),
        ("4/5", "cos", Fraction(9, 25), Fraction(16, 25)),
        ("sqrt(3)/2", "cos", Fraction(1, 4), Fraction(3, 4)),
        ("sqrt(3)", "tan", Fraction(3, 4), Fraction(1, 4)),
        ("3/4", "tan", Fraction(9, 25), Fraction(16, 25)),
        ("sqrt(3)/3", "cot", Fraction(3, 4), Fraction(1, 4)),
        ("2*sqrt(2)", "cot", Fraction(1, 9), Fraction(8, 9)),
    ],
)
def test_exact_trig_ratio_inputs(raw: str, unit: str, exp_sin_sq: Fraction, exp_cos_sq: Fraction) -> None:
    params = exact_trig_angle_params(raw, unit)
    assert params.sin_sq == exp_sin_sq
    assert params.cos_sq == exp_cos_sq
    assert params.cos_sign == 1


@pytest.mark.parametrize(
    ("deg", "exp_sin_sq", "exp_cos_sq", "exp_sign"),
    [
        ("90", Fraction(1), Fraction(0), 0),
        ("120", Fraction(3, 4), Fraction(1, 4), -1),
        ("135", Fraction(1, 2), Fraction(1, 2), -1),
        ("150", Fraction(1, 4), Fraction(3, 4), -1),
    ],
)
def test_extended_obtuse_and_right_degrees_when_explicitly_enabled(
    deg: str, exp_sin_sq: Fraction, exp_cos_sq: Fraction, exp_sign: int
) -> None:
    params = exact_trig_angle_params(deg, "deg", allow_obtuse=True)
    assert (params.sin_sq, params.cos_sq, params.cos_sign) == (exp_sin_sq, exp_cos_sq, exp_sign)


# ── 2. Negative trigonometric counterexamples (§9.7) ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("raw", "unit", "allow_obtuse", "expected_code"),
    [
        ("37", "deg", False, "EXACT_DOMAIN_EXCEEDED"),
        ("15", "deg", False, "EXACT_DOMAIN_EXCEEDED"),
        ("75", "deg", True, "EXACT_DOMAIN_EXCEEDED"),
        ("sqrt(2)", "deg", False, "EXACT_DOMAIN_EXCEEDED"),
        ("0", "deg", False, "NON_POSITIVE_OR_DEGENERATE_ANGLE"),
        ("-30", "deg", False, "NON_POSITIVE_OR_DEGENERATE_ANGLE"),
        ("180", "deg", True, "NON_POSITIVE_OR_DEGENERATE_ANGLE"),
        ("210", "deg", True, "NON_POSITIVE_OR_DEGENERATE_ANGLE"),
        ("90", "deg", False, "ACUTE_RIGHT_TRIANGLE_VIOLATION"),
        ("120", "deg", False, "ACUTE_RIGHT_TRIANGLE_VIOLATION"),
        ("0", "sin", False, "NON_POSITIVE_TRIG_RATIO"),
        ("-1/2", "cos", False, "NON_POSITIVE_TRIG_RATIO"),
        ("0", "tan", False, "NON_POSITIVE_TRIG_RATIO"),
        ("-sqrt(3)", "tan", False, "NON_POSITIVE_TRIG_RATIO"),
        ("1", "sin", False, "TRIG_RATIO_OUT_OF_RANGE"),
        ("5/4", "sin", False, "TRIG_RATIO_OUT_OF_RANGE"),
        ("1", "cos", False, "TRIG_RATIO_OUT_OF_RANGE"),
        ("sqrt(2)", "cos", False, "TRIG_RATIO_OUT_OF_RANGE"),
        ("1/2", "sin", True, "AMBIGUOUS_TRIG_BRANCH"),
        ("pi/3", "rad", False, "UNSUPPORTED_ANGLE_UNIT"),
        ("π√2/4", "sin", False, "EXACT_DOMAIN_EXCEEDED"),
    ],
)
def test_negative_trig_counterexamples_fail_closed(
    raw: str, unit: str, allow_obtuse: bool, expected_code: str
) -> None:
    with pytest.raises(TrigCertificateError) as exc_info:
        exact_trig_angle_params(raw, unit, allow_obtuse=allow_obtuse)
    assert exc_info.value.code == expected_code


def test_float_inputs_are_strictly_rejected() -> None:
    with pytest.raises(TrigCertificateError) as exc_info:
        exact_trig_angle_params(30.0, "deg")
    assert exc_info.value.code == "FLOAT_APPROXIMATION_FORBIDDEN"

    with pytest.raises(TrigCertificateError) as exc_info2:
        format_exact_length_expr(1.5)  # type: ignore[arg-type]
    assert exc_info2.value.code == "FLOAT_APPROXIMATION_FORBIDDEN"


# ── 3. All 11 closed trigonometric & right-triangle identities ────────────────────────────────────────────────────────

def test_all_six_core_trig_scaling_identities_and_two_pythagorean_identities() -> None:
    """Verify 30°-60°-90° right triangle △HAB (right at H, ∠HBA = 30°, HA = a, HB = a√3, AB = 2a) across all 8 side/angle rules."""
    # Chart metric where e1 = HB has |e1|² = 3, e3 = HA has |e3|² = 1, <e1, e3> = 0 => |A - B|² = 4!
    g_mat = [
        [Fraction(3), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    pts = {
        "H": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "A": (Fraction(0), Fraction(0), Fraction(1)),
    }
    calls = [
        _call("p_proj", "orthogonal_projection", {"point": "A", "plane": ["H", "B", "C"], "image": "H"},
              "hình chiếu vuông góc của A lên (HBC) là H"),
        _call("p_ang", "line_plane_angle", {"line": ["A", "B"], "plane": ["H", "B", "C"], "value": "30", "unit": "deg"},
              "góc giữa AB và (HBC) bằng 30°"),
        _call("p_len", "segment_length", {"segment": ["A", "B"], "value": "2a"}, "AB = 2a"),
    ]
    cases = [
        (ID_OPP_FROM_HYP_SIN, "opposite_leg", ("hypotenuse",), "angle", "line_plane_angle", ("p_ang",), "a"),
        (ID_ADJ_FROM_HYP_COS, "adjacent_leg", ("hypotenuse",), "angle", "line_plane_angle", ("p_ang",), "a√3"),
        (ID_OPP_FROM_ADJ_TAN, "opposite_leg", ("adjacent_leg",), "angle", "line_plane_angle", ("p_ang",), "a"),
        (ID_ADJ_FROM_OPP_COT, "adjacent_leg", ("opposite_leg",), "angle", "line_plane_angle", ("p_ang",), "a√3"),
        (ID_HYP_FROM_ADJ_COS, "hypotenuse", ("adjacent_leg",), "angle", "line_plane_angle", ("p_ang",), "2a"),
        (ID_HYP_FROM_OPP_SIN, "hypotenuse", ("opposite_leg",), "angle", "line_plane_angle", ("p_ang",), "2a"),
        (ID_PYTH_HYP_FROM_LEGS, "hypotenuse", ("adjacent_leg", "opposite_leg"), None, "pythagorean_lengths", (), "2a"),
        (ID_PYTH_LEG_FROM_HYP, "adjacent_leg", ("hypotenuse", "opposite_leg"), None, "pythagorean_lengths", (), "a√3"),
    ]
    for trig_id, role, side_roles, non_side, aw_kind, aw_calls, exp_disp in cases:
        cert = build_trig_construction_certificate(
            certificate_id=f"cert_{trig_id}",
            derived_role=role,
            derived_right_triangle=("H", "B", "A"),
            perpendicularity_rule="line_perpendicular_to_plane",
            perpendicularity_calls=("p_proj",),
            angle_witness_kind=aw_kind,
            angle_witness_calls=aw_calls,
            sin_sq=Fraction(1, 4),
            cos_sq=Fraction(3, 4),
            angle_unit="deg",
            angle_raw_value="30",
            trig_identity=trig_id,
            known_side_roles=side_roles,
            non_side_input_role=non_side,
            non_side_input_dimension="ANGLE",
            calls=calls,
            points_by_label=pts,
            chart_metric=g_mat,
            length_unit="a",
            extra_premise_calls=("p_len",),
        )
        assert cert["schema_version"] == TRIG_CONSTRUCTION_CERTIFICATE_VERSION
        assert cert["exact_length_expr"]["display"] == exp_disp
        verify_trig_construction_certificate(
            cert,
            calls=calls,
            scene_objects=_scene_objects_from_pts(pts),
            chart_metric=g_mat,
            length_unit="a",
        )


def test_right_isosceles_equal_legs_and_leg_ratio_identities() -> None:
    """Verify `pythagoras_equal_legs` (right isosceles hypotenuse -> legs) and `pythagoras_leg_ratio`."""
    # Right isosceles △BAC right at B with BA = BC and hypotenuse AC = 2a => BA = BC = a√2 (BA² = BC² = 2, AC² = 4)
    g_iso = [
        [Fraction(2), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(2), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(2)],
    ]
    pts_iso = {
        "B": (Fraction(0), Fraction(0), Fraction(0)),
        "A": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
    }
    calls_iso = [
        _call("p_ra", "right_angle", {"vertex": "B", "rays": ["A", "C"]}, "tam giác ABC vuông cân tại B"),
        _call("p_eq", "equal_length", {"segment_a": ["B", "A"], "segment_b": ["B", "C"]}, "tam giác ABC vuông cân tại B"),
        _call("p_ac", "segment_length", {"segment": ["A", "C"], "value": "2a"}, "AC = 2a"),
    ]
    cert_iso = build_trig_construction_certificate(
        certificate_id="cert_iso",
        derived_role="both_legs",
        derived_right_triangle=("B", "A", "C"),
        perpendicularity_rule="explicit_right_angle",
        perpendicularity_calls=("p_ra",),
        angle_witness_kind="equal_legs_witness",
        angle_witness_calls=("p_eq",),
        sin_sq=Fraction(1, 2),
        cos_sq=Fraction(1, 2),
        angle_unit="deg",
        angle_raw_value="45",
        trig_identity=ID_PYTH_EQUAL_LEGS,
        known_side_roles=("hypotenuse",),
        non_side_input_role="equal_legs",
        non_side_input_dimension="SCALAR",
        calls=calls_iso,
        points_by_label=pts_iso,
        chart_metric=g_iso,
        length_unit="a",
        extra_premise_calls=("p_ac",),
    )
    assert cert_iso["exact_length_expr"]["display"] == "a√2"
    verify_trig_construction_certificate(
        cert_iso,
        calls=calls_iso,
        scene_objects=_scene_objects_from_pts(pts_iso),
        chart_metric=g_iso,
        length_unit="a",
    )

    # Leg ratio: BC / BA = √3 with hypotenuse AC = 2a => BA = a (BA² = 1), BC = a√3 (BC² = 3)
    g_rat = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(3), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    calls_rat = [
        _call("p_ra", "right_angle", {"vertex": "B", "rays": ["A", "C"]}, "tam giác ABC vuông tại B"),
        _call("p_sr", "segment_ratio", {"segment_a": ["B", "C"], "segment_b": ["B", "A"], "ratio": "sqrt(3)"},
              "BC = BA√3"),
        _call("p_ac", "segment_length", {"segment": ["A", "C"], "value": "2a"}, "AC = 2a"),
    ]
    cert_rat = build_trig_construction_certificate(
        certificate_id="cert_ratio",
        derived_role="both_legs",
        derived_right_triangle=("B", "A", "C"),
        perpendicularity_rule="explicit_right_angle",
        perpendicularity_calls=("p_ra",),
        angle_witness_kind="leg_ratio_witness",
        angle_witness_calls=("p_sr",),
        sin_sq=Fraction(3, 4),
        cos_sq=Fraction(1, 4),
        angle_unit="tan",
        angle_raw_value="√3",
        trig_identity=ID_PYTH_LEG_RATIO,
        known_side_roles=("hypotenuse",),
        non_side_input_role="leg_ratio",
        non_side_input_dimension="SCALAR",
        calls=calls_rat,
        points_by_label=pts_iso,
        chart_metric=g_rat,
        length_unit="a",
        extra_premise_calls=("p_ac",),
    )
    assert cert_rat["exact_length_expr"]["display"] == "a"
    verify_trig_construction_certificate(
        cert_rat,
        calls=calls_rat,
        scene_objects=_scene_objects_from_pts(pts_iso),
        chart_metric=g_rat,
        length_unit="a",
    )


def test_right_prism_cotangent_diagonal_and_rhombus_half_diagonal_cos_certificates() -> None:
    """Verify composite right-prism diagonal `AC = CC'*cot(30°) = 2a√3` + rhombus `AB = OA/cos(30°) = 2a` on non-Euclidean Gram."""
    # Rhombus ABCD of side 2a with ∠BAD = 60°: A=(0,0,0), B=(1,0,0), D=(0,1,0), C=(1,1,0), Gram_2D = [[4, 2], [2, 4]]
    # Right prism height AA' = 2a: z-axis Gram_33 = 4.
    # Check: |AB|² = 4, |AD|² = 4, <AB, AD> = 2 = 4*cos(60°), |AC|² = |(1,1,0)|_G² = 4 + 4 + 4 = 12 => AC = 2a√3!
    # Midpoint O = (1/2, 1/2, 0): |OA|² = 12/4 = 3, |OB|² = |(1/2, -1/2, 0)|_G² = (4 - 4 + 4)/4 = 1, <OA, OB>_G = 0!
    g_prism = [
        [Fraction(4), Fraction(2), Fraction(0)],
        [Fraction(2), Fraction(4), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(4)],
    ]
    pts_prism = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(1), Fraction(1), Fraction(0)),
        "D": (Fraction(0), Fraction(1), Fraction(0)),
        "A'": (Fraction(0), Fraction(0), Fraction(1)),
        "B'": (Fraction(1), Fraction(0), Fraction(1)),
        "C'": (Fraction(1), Fraction(1), Fraction(1)),
        "D'": (Fraction(0), Fraction(1), Fraction(1)),
    }
    calls_prism = [
        _call("s1", "prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"], "right": True},
              "hình lăng trụ đứng ABCD.A'B'C'D'"),
        _call("p1", "rhombus", {"vertices": ["A", "B", "C", "D"], "side": None}, "đáy ABCD là hình thoi"),
        _call("p2", "vertex_angle", {"vertex": "A", "rays": ["B", "D"], "value": "60", "unit": "deg"}, "góc BAD = 60°"),
        _call("p3", "segment_length", {"segment": ["A", "A'"], "value": "2a"}, "AA' = 2a"),
        _call("p4", "line_plane_angle", {"line": ["A", "C'"], "plane": ["A", "B", "C", "D"], "value": "30", "unit": "deg"},
              "góc giữa AC' và mặt đáy bằng 30°"),
    ]
    cert_diag = build_trig_construction_certificate(
        certificate_id="cert_prism_ac",
        derived_role="adjacent_leg",
        derived_right_triangle=("C", "A", "C'"),
        perpendicularity_rule="line_perpendicular_to_plane",
        perpendicularity_calls=("s1",),
        angle_witness_kind="line_plane_angle",
        angle_witness_calls=("p4",),
        sin_sq=Fraction(1, 4),
        cos_sq=Fraction(3, 4),
        angle_unit="deg",
        angle_raw_value="30",
        trig_identity=ID_ADJ_FROM_OPP_COT,
        known_side_roles=("opposite_leg",),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=calls_prism,
        points_by_label=pts_prism,
        chart_metric=g_prism,
        length_unit="a",
        extra_premise_calls=("p3",),
    )
    assert cert_diag["exact_length_expr"]["display"] == "2a√3"

    cert_rhombus = build_trig_construction_certificate(
        certificate_id="cert_rhombus_ab",
        derived_role="hypotenuse",
        derived_right_triangle=("O", "A", "B"),
        perpendicularity_rule="rhombus_perpendicular_diagonals",
        perpendicularity_calls=("p1",),
        angle_witness_kind="rhombus_bisected_vertex_angle",
        angle_witness_calls=("p2", "p1"),
        sin_sq=Fraction(1, 4),
        cos_sq=Fraction(3, 4),
        angle_unit="deg",
        angle_raw_value="30",
        trig_identity=ID_RHOMBUS_HALF_DIAG_COS,
        known_side_roles=("adjacent_leg",),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=calls_prism,
        points_by_label=pts_prism,
        chart_metric=g_prism,
        length_unit="a",
        auxiliary_witness_points={
            "O": {
                "rule": "segment_midpoint",
                "endpoints": ["A", "C"],
                "coincident_midpoint_of": ["B", "D"],
                "xyz": [Fraction(1, 2), Fraction(1, 2), Fraction(0)],
            }
        },
    )
    assert cert_rhombus["exact_length_expr"]["display"] == "2a"

    scene_objs = _scene_objects_from_pts(pts_prism)
    for c in (cert_diag, cert_rhombus):
        verify_trig_construction_certificate(
            c,
            calls=calls_prism,
            scene_objects=scene_objs,
            chart_metric=g_prism,
            length_unit="a",
        )
    assert len(CLOSED_TRIG_IDENTITIES) == 11


def test_dihedral_and_vertex_angle_witnesses_verify_cleanly() -> None:
    """Verify `dihedral_angle` and `vertex_angle` witnesses on exact rational scenes."""
    g_mat = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(3)],
    ]
    # S.ABC with SA ⊥ (ABC), AB ⊥ BC at B => ∠SBA is planar angle of dihedral [S, BC, A] = 60° (AB=1, SA=√3, SB=2)
    pts = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(1), Fraction(1), Fraction(0)),
        "S": (Fraction(0), Fraction(0), Fraction(1)),
    }
    calls = [
        _call("p1", "perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "SA ⊥ (ABC)"),
        _call("p2", "dihedral_angle", {"point_a": "S", "edge": ["B", "C"], "point_b": "A", "value": "60", "unit": "deg"},
              "góc nhị diện [S, BC, A] bằng 60°"),
        _call("p3", "segment_length", {"segment": ["A", "B"], "value": "a"}, "AB = a"),
    ]
    cert = build_trig_construction_certificate(
        certificate_id="cert_dihedral_60",
        derived_role="opposite_leg",
        derived_right_triangle=("A", "B", "S"),
        perpendicularity_rule="line_perpendicular_to_plane",
        perpendicularity_calls=("p1",),
        angle_witness_kind="dihedral_angle",
        angle_witness_calls=("p2",),
        sin_sq=Fraction(3, 4),
        cos_sq=Fraction(1, 4),
        angle_unit="deg",
        angle_raw_value="60",
        trig_identity=ID_OPP_FROM_ADJ_TAN,
        known_side_roles=("adjacent_leg",),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=calls,
        points_by_label=pts,
        chart_metric=g_mat,
        length_unit="a",
        extra_premise_calls=("p3",),
    )
    assert cert["exact_length_expr"]["display"] == "a√3"
    verify_trig_construction_certificate(
        cert,
        calls=calls,
        scene_objects=_scene_objects_from_pts(pts),
        chart_metric=g_mat,
        length_unit="a",
    )


# ── 4. All 9 Phase 8 (§11.4) Adversarial Certificate Mutations ────────────────────────────────────────────────────────

def test_adversarial_mutation_1_non_spd_or_float_gram_metric_rejected() -> None:
    cert, calls, pts, _g = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    # Degenerate (singular) Gram matrix
    bad_g_singular = [
        [Fraction(1), Fraction(1), Fraction(0)],
        [Fraction(1), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(cert, calls=calls, scene_objects=scene_objs, chart_metric=bad_g_singular, length_unit="a")
    assert exc1.value.code == "NON_SPD_METRIC"

    # Float-contaminated Gram matrix
    bad_g_float = [[1.0, 0, 0], [0, 1, 0], [0, 0, 1]]
    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(cert, calls=calls, scene_objects=scene_objs, chart_metric=bad_g_float, length_unit="a")
    assert exc2.value.code == "FLOAT_APPROXIMATION_FORBIDDEN"


def test_adversarial_mutation_2_mutated_right_angle_vertex_rejected() -> None:
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    tampered = deepcopy(cert)
    tampered["right_angle_vertex"] = "B"
    with pytest.raises(TrigCertificateError) as exc_info:
        verify_trig_construction_certificate(
            tampered, calls=calls, scene_objects=_scene_objects_from_pts(pts), chart_metric=g_mat, length_unit="a"
        )
    assert exc_info.value.code == "RIGHT_ANGLE_VERTEX_MISMATCH"


def test_adversarial_mutation_3_swapped_legs_at_45_degrees_and_swapped_hypotenuse_rejected() -> None:
    """At 45°, |AB|² == |AS|² == 1 (numeric coincidence!). Swapping adjacent_leg and opposite_leg MUST still fail."""
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    assert cert["adjacent_leg"]["length_sq"] == cert["opposite_leg"]["length_sq"] == "1"

    swapped_legs = deepcopy(cert)
    swapped_legs["adjacent_leg"], swapped_legs["opposite_leg"] = (
        deepcopy(cert["opposite_leg"]),
        deepcopy(cert["adjacent_leg"]),
    )
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(
            swapped_legs, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a"
        )
    assert exc1.value.code == "MISMATCHED_ADJACENT_LEG"

    swapped_hyp = deepcopy(cert)
    swapped_hyp["hypotenuse"] = deepcopy(cert["adjacent_leg"])
    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(
            swapped_hyp, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a"
        )
    assert exc2.value.code == "MISMATCHED_HYPOTENUSE"


def test_adversarial_mutation_4_mutated_angle_witness_and_non_projection_base_ray_rejected() -> None:
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    # 4a. Swapped ray_1 and ray_2
    bad_rays = deepcopy(cert)
    bad_rays["angle_witness"]["ray_1"], bad_rays["angle_witness"]["ray_2"] = (
        bad_rays["angle_witness"]["ray_2"],
        bad_rays["angle_witness"]["ray_1"],
    )
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(bad_rays, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc1.value.code == "ANGLE_WITNESS_RAY_MISMATCH"

    # 4b. Non-projection base ray in `line_plane_angle`:
    # Construct S=(0,1,1), B=(1,0,0), M=(0,1,0), C=(0,0,0) in plane z=0.
    # Notice: M lies in plane (MBC) (z=0), B-M = (1,-1,0), S-M = (0,0,1)? Wait: make S=(0,0,1), M=(1/2, 1/2, 0), B=(1,0,0):
    # Let S=(0,1,1), M=(0,0,0), B=(1,0,0), C=(0,1,0):
    # Here (S - M) = (0,1,1) IS orthogonal to (B - M) = (1,0,0) (<(0,1,1), (1,0,0)> == 0, so △MBS IS right-angled at M!),
    # AND M lies in plane (MBC) (z=0), BUT S - M = (0,1,1) is NOT orthogonal to the plane z=0 (its foot is C=(0,1,0), NOT M)!
    pts_oblique = {
        "M": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "S": (Fraction(0), Fraction(1), Fraction(1)),
    }
    g_oblique = [
        [Fraction(2), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    # Under g_oblique: |B-M|² = 2, |S-M|² = 1+1 = 2, <B-M, S-M>_G = 0 => △MBS is right isosceles (45°) at M!
    calls_oblique = [
        _call("p_perp", "perpendicular_lines", {"line1": ["S", "M"], "line2": ["B", "M"]}, "SM vuông góc với BM"),
        _call("p_lpa", "line_plane_angle", {"line": ["S", "B"], "plane": ["M", "B", "C"], "value": "45", "unit": "deg"},
              "góc giữa SB và (MBC) bằng 45°"),
    ]
    # Build with vertex_angle/equal_legs first, then tamper angle_witness to claim line_plane_angle!
    forged_lpa = deepcopy(cert)
    forged_lpa["derived_right_triangle"] = ["M", "B", "S"]
    forged_lpa["right_angle_vertex"] = "M"
    forged_lpa["source_premises"] = [
        {"call_id": "p_perp", "fn": "perpendicular_lines", "quotes": ["SM vuông góc với BM"]},
        {"call_id": "p_lpa", "fn": "line_plane_angle", "quotes": ["góc giữa SB và (MBC) bằng 45°"]},
    ]
    forged_lpa["construction_dependencies"] = {"prerequisite_calls": ["p_perp", "p_lpa"], "vertices": ["M", "B", "S"]}
    forged_lpa["perpendicularity_justification"] = {
        "rule": "explicit_perpendicular_lines",
        "supporting_calls": ["p_perp"],
        "gram_dot_zero_verified": True,
    }
    forged_lpa["angle_witness"] = {
        "kind": "line_plane_angle",
        "vertex": "B",
        "ray_1": ["B", "M"],
        "ray_2": ["B", "S"],
        "domain": "(0°, 90°)",
        "unit": "deg",
        "raw_value": "45",
        "sin_sq": "1/2",
        "cos_sq": "1/2",
        "supporting_calls": ["p_lpa"],
    }
    forged_lpa["hypotenuse"] = {"segment": ["B", "S"], "length_sq": "4"}
    forged_lpa["adjacent_leg"] = {"segment": ["M", "B"], "length_sq": "2"}
    forged_lpa["opposite_leg"] = {"segment": ["M", "S"], "length_sq": "2"}
    forged_lpa["derived_quantity_id"] = ["M", "S"]
    forged_lpa["known_inputs"] = [
        {"role": "hypotenuse", "segment": ["B", "S"], "length_sq": "4", "coef_json": {"kind": "rational", "value": "2"}, "dimension": "LENGTH"},
        {"role": "angle", "sin_sq": "1/2", "cos_sq": "1/2", "dimension": "ANGLE"},
    ]
    forged_lpa["exact_length_expr"] = format_exact_length_expr(Fraction(2), length_unit="a")

    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(
            forged_lpa,
            calls=calls_oblique,
            scene_objects=_scene_objects_from_pts(pts_oblique),
            chart_metric=g_oblique,
            length_unit="a",
        )
    assert exc2.value.code == "NON_PROJECTION_BASE_RAY"


def test_adversarial_mutation_5_accidental_gram_orthogonality_without_deductive_premise_rejected() -> None:
    """Even when `<B - A, C - A>_G == 0` in coordinates, missing a deductive right-angle premise MUST fail."""
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    # Replace perpendicularity supporting_calls with s1 (pyramid), which does NOT deductively prove SA ⊥ (ABC)
    unproven = deepcopy(cert)
    unproven["source_premises"].append({"call_id": "s1", "fn": "pyramid", "quotes": ["hình chóp S.ABC"]})
    unproven["construction_dependencies"]["prerequisite_calls"].append("s1")
    unproven["perpendicularity_justification"] = {
        "rule": "line_perpendicular_to_plane",
        "supporting_calls": ["s1"],
        "gram_dot_zero_verified": True,
    }
    with pytest.raises(TrigCertificateError) as exc_info:
        verify_trig_construction_certificate(
            unproven, calls=calls, scene_objects=_scene_objects_from_pts(pts), chart_metric=g_mat, length_unit="a"
        )
    assert exc_info.value.code == "UNPROVEN_RIGHT_ANGLE"


def test_adversarial_mutation_6_swapped_sin_cos_trig_identity_at_45_degrees_rejected() -> None:
    """At 45°, `c * sin(45°) == c * cos(45°) == a`. Mutating `h = c * sin(alpha)` -> `p = c * cos(alpha)` MUST fail."""
    cert, calls, pts, g_mat = _base_45_pyramid_fixture(trig_id=ID_OPP_FROM_HYP_SIN, derived_role="opposite_leg")
    tampered = deepcopy(cert)
    tampered["trig_identity"] = ID_ADJ_FROM_HYP_COS
    with pytest.raises(TrigCertificateError) as exc_info:
        verify_trig_construction_certificate(
            tampered, calls=calls, scene_objects=_scene_objects_from_pts(pts), chart_metric=g_mat, length_unit="a"
        )
    assert exc_info.value.code == "TRIG_IDENTITY_ROLE_MISMATCH"


def test_adversarial_mutation_7_tampered_exact_length_expr_or_wrong_dimension_rejected() -> None:
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    wrong_dim = deepcopy(cert)
    wrong_dim["dimension"] = "AREA"
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(wrong_dim, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc1.value.code == "WRONG_DIMENSION"

    wrong_expr = deepcopy(cert)
    wrong_expr["exact_length_expr"]["display"] = "2a"
    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(wrong_expr, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc2.value.code == "EXACT_LENGTH_EXPR_MISMATCH"


def test_adversarial_mutation_8_positivity_and_single_branch_uniqueness_tamper_rejected() -> None:
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    bad_pos = deepcopy(cert)
    bad_pos["positivity_domain"]["hypotenuse_sq_gt_legs_sq"] = False
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(bad_pos, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc1.value.code == "POSITIVITY_DOMAIN_INVALID"

    bad_branch = deepcopy(cert)
    bad_branch["single_branch_uniqueness"]["unique_positive_root"] = False
    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(bad_branch, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc2.value.code == "BRANCH_UNIQUENESS_INVALID"


def test_adversarial_mutation_9_circular_inputs_broken_provenance_and_scene_tamper_rejected() -> None:
    cert, calls, pts, g_mat = _base_45_pyramid_fixture()
    scene_objs = _scene_objects_from_pts(pts)

    # 9a. Circular known_inputs (claiming derived opposite_leg is a known input)
    circular = deepcopy(cert)
    circular["known_inputs"].append({
        "role": "opposite_leg",
        "segment": ["A", "S"],
        "length_sq": "1",
        "coef_json": {"kind": "rational", "value": "1"},
        "dimension": "LENGTH",
    })
    with pytest.raises(TrigCertificateError) as exc1:
        verify_trig_construction_certificate(circular, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc1.value.code == "CIRCULAR_KNOWN_INPUT"

    # 9b. Tampered quote in source_premises
    bad_quote = deepcopy(cert)
    bad_quote["source_premises"][0]["quotes"] = ["trích dẫn giả mạo"]
    with pytest.raises(TrigCertificateError) as exc2:
        verify_trig_construction_certificate(bad_quote, calls=calls, scene_objects=scene_objs, chart_metric=g_mat, length_unit="a")
    assert exc2.value.code == "SOURCE_PREMISE_QUOTES_MISMATCH"

    # 9c. Tampered scene_objects coordinate
    tampered_scene = deepcopy(scene_objs)
    tampered_scene["S"]["xyz"] = ["0", "0", "2"]
    with pytest.raises(TrigCertificateError) as exc3:
        verify_trig_construction_certificate(cert, calls=calls, scene_objects=tampered_scene, chart_metric=g_mat, length_unit="a")
    assert exc3.value.code == "MISMATCHED_HYPOTENUSE"


# ── 5. Adapter `/4` binding & non-trig fixture preservation ───────────────────────────────────────────────────────────

def test_adapter4_preserves_non_trig_envelope_and_enforces_trig_certificate_binding() -> None:
    from app.ai.adapter4_route import run_typed_fact_next_v2_route
    from app.ai.local_geometry_parser import parse_geometry_problem_locally

    non_trig_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng (ABCD), "
        "SA = a. Tính thể tích khối chóp S.ABCD."
    )
    parsed_non_trig = parse_geometry_problem_locally(non_trig_text, use_cache=False)
    assert parsed_non_trig.parsed_contract is not None
    res_non_trig = run_typed_fact_next_v2_route(parsed_non_trig.parsed_contract)
    assert res_non_trig.status == "SERVED"

    # Without trig_certificates, route_d omits the optional field completely (100% non-trig fixture compatibility).
    resp_plain = build_adapter4_response(res_non_trig, non_trig_text)
    assert resp_plain["envelope"]["status"] == "ok"
    assert "trig_construction_certificates" not in resp_plain["route_d"]

    problem_text = (
        "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), tam giác ABC vuông tại B, "
        "AB = a, BC = a, góc giữa SB và mặt phẳng (ABC) bằng 45°. Tính thể tích khối chóp S.ABC."
    )
    parsed = parse_geometry_problem_locally(problem_text, use_cache=False)
    assert parsed.parsed_contract is not None
    res = run_typed_fact_next_v2_route(parsed.parsed_contract)
    assert res.status == "SERVED"

    # Engine automatically emits and self-verifies trig_construction_certificates for trigonometric & right-triangle constructions.
    resp_auto = build_adapter4_response(res, problem_text)
    assert resp_auto["envelope"]["status"] == "ok"
    auto_certs = resp_auto["route_d"]["trig_construction_certificates"]
    assert any(c["trig_identity"] == ID_OPP_FROM_ADJ_TAN and c["exact_length_expr"]["display"] == "a" for c in auto_certs)

    perp_cid = next(c["id"] for c in res.calls if c["fn"] == "perpendicular_line_plane")
    ang_cid = next(c["id"] for c in res.calls if c["fn"] == "line_plane_angle")
    ab_cid = next(
        c["id"] for c in res.calls if c["fn"] == "segment_length" and set(c["args"]["segment"]) == {"A", "B"}
    )

    # Attach a valid trig-construction-certificate/1 for SA = AB * tan(45°) = a
    valid_cert = build_trig_construction_certificate(
        certificate_id="trig_cert_sa",
        derived_role="opposite_leg",
        derived_right_triangle=("A", "B", "S"),
        perpendicularity_rule="line_perpendicular_to_plane",
        perpendicularity_calls=(perp_cid,),
        angle_witness_kind="line_plane_angle",
        angle_witness_calls=(ang_cid,),
        sin_sq=Fraction(1, 2),
        cos_sq=Fraction(1, 2),
        angle_unit="deg",
        angle_raw_value="45",
        trig_identity=ID_OPP_FROM_ADJ_TAN,
        known_side_roles=("adjacent_leg",),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=res.calls,
        points_by_label=res.points,
        chart_metric=res.chart_metric,
        length_unit=res.length_unit,
        extra_premise_calls=(ab_cid,),
    )
    res_with_cert = deepcopy(res)
    res_with_cert.details = {**(res.details or {}), "trig_construction_certificates": [valid_cert]}
    res_with_cert.route_d = _phong_bi(res_with_cert)

    resp_valid = build_adapter4_response(res_with_cert, problem_text)
    assert resp_valid["envelope"]["status"] == "ok"
    assert len(resp_valid["route_d"]["trig_construction_certificates"]) == 1
    assert resp_valid["route_d"]["trig_construction_certificates"][0]["exact_length_expr"]["display"] == "a"

    # Tamper 1: swap adjacent_leg and opposite_leg at 45° on BOTH details and route_d -> adapter MUST refuse!
    res_tampered = deepcopy(res_with_cert)
    bad_cert = deepcopy(valid_cert)
    bad_cert["adjacent_leg"], bad_cert["opposite_leg"] = bad_cert["opposite_leg"], bad_cert["adjacent_leg"]
    res_tampered.details = {**(res.details or {}), "trig_construction_certificates": [bad_cert]}
    res_tampered.route_d = _phong_bi(res_tampered)

    resp_refused = build_adapter4_response(res_tampered, problem_text)
    assert resp_refused["envelope"]["status"] == "unsupported"
    assert resp_refused["envelope"]["reason_code"] == "RESULT_BINDING_UNVERIFIED"
    assert set(resp_refused["envelope"].keys()) == {
        "status",
        "reason_code",
        "reason",
        "learner_reason",
        "failure_category",
        "refusal_cause",
    }

    # Tamper 2: strip certificate from route_d while details still has it -> adapter MUST refuse!
    res_desync = deepcopy(res_with_cert)
    res_desync.route_d.pop("trig_construction_certificates", None)
    resp_desync = build_adapter4_response(res_desync, problem_text)
    assert resp_desync["envelope"]["status"] == "unsupported"
    assert resp_desync["envelope"]["reason_code"] == "RESULT_BINDING_UNVERIFIED"


# ── 6. `#30` §2.1 Regression: `deductive_two_lines_in_plane` Positive & Negative Verification ─────────────────────────

def test_deductive_two_lines_in_plane_perpendicularity_positive_and_negative() -> None:
    """Verify `rule='deductive_two_lines_in_plane'` checks scalar triple product == 0 without IndexError and rejects skew/non-coplanar rays."""
    # Positive: S=(0,0,1), A=(0,0,0), B=(1,0,0), C=(0,1,0), M=(1/2, 1/2, 0) in plane (ABC)
    # Premise 1: SA ⊥ AB; Premise 2: SA ⊥ AC (two non-parallel lines in plane z=0).
    # Ray 1 in plane: AM = (1/2, 1/2, 0) (coplanar with AB and AC!) => SA ⊥ AM deductively!
    pts_pos = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "M": (Fraction(1, 2), Fraction(1, 2), Fraction(0)),
        "S": (Fraction(0), Fraction(0), Fraction(1)),
    }
    g_pos = [
        [Fraction(2), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(2), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    # Under g_pos: |AM|² = 2*(1/4 + 1/4) = 1, |AS|² = 1, |SM|² = 2, ∠AMS = 45°!
    calls_pos = [
        _call("p_ab", "perpendicular_lines", {"line1": ["S", "A"], "line2": ["A", "B"]}, "SA ⊥ AB"),
        _call("p_ac", "perpendicular_lines", {"line1": ["S", "A"], "line2": ["A", "C"]}, "SA ⊥ AC"),
        _call("p_ang", "vertex_angle", {"vertex": "M", "rays": ["A", "S"], "value": "45", "unit": "deg"}, "góc SMA = 45°"),
        _call("p_am", "segment_length", {"segment": ["A", "M"], "value": "a"}, "AM = a"),
    ]
    cert_pos = build_trig_construction_certificate(
        certificate_id="cert_two_lines_pos",
        derived_role="opposite_leg",
        derived_right_triangle=("A", "M", "S"),
        perpendicularity_rule="deductive_two_lines_in_plane",
        perpendicularity_calls=("p_ab", "p_ac"),
        angle_witness_kind="vertex_angle",
        angle_witness_calls=("p_ang",),
        sin_sq=Fraction(1, 2),
        cos_sq=Fraction(1, 2),
        angle_unit="deg",
        angle_raw_value="45",
        trig_identity=ID_OPP_FROM_ADJ_TAN,
        known_side_roles=("adjacent_leg",),
        non_side_input_role="angle",
        non_side_input_dimension="ANGLE",
        calls=calls_pos,
        points_by_label=pts_pos,
        chart_metric=g_pos,
        length_unit="a",
        extra_premise_calls=("p_am",),
    )
    verify_trig_construction_certificate(
        cert_pos,
        calls=calls_pos,
        scene_objects=_scene_objects_from_pts(pts_pos),
        chart_metric=g_pos,
        length_unit="a",
    )

    # Negative 1: Two parallel lines AB and AM (collinear when C=(2,0,0)) do NOT span a plane -> UNPROVEN_RIGHT_ANGLE!
    pts_collinear = deepcopy(pts_pos)
    pts_collinear["C"] = (Fraction(2), Fraction(0), Fraction(0))
    pts_collinear["M"] = (Fraction(1), Fraction(0), Fraction(0))
    g_id = [
        [Fraction(1), Fraction(0), Fraction(0)],
        [Fraction(0), Fraction(1), Fraction(0)],
        [Fraction(0), Fraction(0), Fraction(1)],
    ]
    cert_col = deepcopy(cert_pos)
    cert_col["hypotenuse"]["length_sq"] = "2"
    cert_col["adjacent_leg"]["length_sq"] = "1"
    cert_col["opposite_leg"]["length_sq"] = "1"
    with pytest.raises(TrigCertificateError) as exc_col:
        verify_trig_construction_certificate(
            cert_col,
            calls=calls_pos,
            scene_objects=_scene_objects_from_pts(pts_collinear),
            chart_metric=g_id,
            length_unit="a",
        )
    assert exc_col.value.code == "UNPROVEN_RIGHT_ANGLE"

    # Negative 2: Non-coplanar ray AM (where SA is orthogonal to AB and AC in coordinates? No: make AM non-coplanar with AB, AC
    # while accidentally orthogonal to SA under a custom metric!) -> MUST still fail `UNPROVEN_RIGHT_ANGLE`!
    pts_non_coplanar = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(1), Fraction(0), Fraction(0)),
        "C": (Fraction(0), Fraction(1), Fraction(0)),
        "M": (Fraction(1), Fraction(0), Fraction(1)),  # non-coplanar with AB=(1,0,0), AC=(0,1,0)!
        "S": (Fraction(0), Fraction(1), Fraction(1)),  # Wait: construct g so <AS, AB>=0, <AS, AC>=0, <AS, AM>=0? Impossible in 3D SPD if AB,AC,AM span R^3!
    }
    # Instead test non-coplanar ray when supporting calls prove AB ⊥ AC and AB ⊥ AS, while certificate claims SA ⊥ AM (non-coplanar with AC, AS)!
    calls_wrong_plane = [
        _call("p_1", "perpendicular_lines", {"line1": ["A", "B"], "line2": ["A", "C"]}, "AB ⊥ AC"),
        _call("p_2", "perpendicular_lines", {"line1": ["S", "A"], "line2": ["A", "B"]}, "SA ⊥ AB"),
        _call("p_ang", "vertex_angle", {"vertex": "M", "rays": ["A", "S"], "value": "45", "unit": "deg"}, "góc SMA = 45°"),
        _call("p_am", "segment_length", {"segment": ["A", "M"], "value": "a"}, "AM = a"),
    ]
    cert_wrong = deepcopy(cert_pos)
    cert_wrong["source_premises"] = [
        {"call_id": "p_1", "fn": "perpendicular_lines", "quotes": ["AB ⊥ AC"]},
        {"call_id": "p_2", "fn": "perpendicular_lines", "quotes": ["SA ⊥ AB"]},
        {"call_id": "p_ang", "fn": "vertex_angle", "quotes": ["góc SMA = 45°"]},
        {"call_id": "p_am", "fn": "segment_length", "quotes": ["AM = a"]},
    ]
    cert_wrong["perpendicularity_justification"]["supporting_calls"] = ["p_1", "p_2"]
    cert_wrong["construction_dependencies"]["prerequisite_calls"] = ["p_1", "p_2", "p_ang", "p_am"]
    with pytest.raises(TrigCertificateError) as exc_wrong:
        verify_trig_construction_certificate(
            cert_wrong,
            calls=calls_wrong_plane,
            scene_objects=_scene_objects_from_pts(pts_pos),
            chart_metric=g_pos,
            length_unit="a",
        )
    assert exc_wrong.value.code == "UNPROVEN_RIGHT_ANGLE"


# ── 7. Stage P1c End-to-End Verified Constructions, Negative Counterexamples, Metamorphics & Scene3D Invariants ───────

@pytest.mark.parametrize(
    ("text", "expected_answer", "expected_identities"),
    [
        # 1. Right-isosceles base hypotenuse + off-base isosceles lateral face -> exact volume a³√2/3
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. "
            "Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. "
            "Tính thể tích khối chóp S.ABC theo a.",
            "a³√2/3",
            {ID_PYTH_EQUAL_LEGS},
        ),
        # 2. Same geometric family asking dihedral angle -> cos²=1/2 (45°)
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AC = 2a, "
            "SA vuông góc với mặt phẳng (ABC), tam giác SAB cân. "
            "Tính góc giữa hai mặt phẳng (SBC) và (ABC).",
            "cos²=1/2",
            {ID_PYTH_EQUAL_LEGS},
        ),
        # 3. Right prism on rhombus base with 60° vertex angle and 30° diagonal-to-base angle -> exact volume 4a³√3
        (
            "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình thoi, góc BAD = 60°, "
            "AA' = 2a, góc giữa đường thẳng AC' và mặt đáy bằng 30°. "
            "Tính thể tích khối lăng trụ ABCD.A'B'C'D'.",
            "4a³√3",
            {ID_ADJ_FROM_OPP_COT, ID_RHOMBUS_HALF_DIAG_COS},
        ),
        # 4. Vietnamese trig ratio `tang` on line-plane angle -> height h = a * √3 => V = (1/3)*(a²/2)*a√3 = a³√3/6
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) có tang bằng √3. "
            "Tính thể tích khối chóp S.ABC.",
            "a³√3/6",
            {ID_OPP_FROM_ADJ_TAN},
        ),
        # 5. Vietnamese trig ratio `côsin` on line-plane angle with slant SB = 5a, cos = 3/5 => AB = 3a, SA = 4a => V = 2a³
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, BC = a, SB = 5a, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) có côsin bằng 3/5. "
            "Tính thể tích khối chóp S.ABC.",
            "2a³",
            {ID_ADJ_FROM_HYP_COS, ID_OPP_FROM_HYP_SIN},
        ),
        # 6. Regular quadrilateral pyramid with slant SA = 2a and line-plane angle (SA, (ABCD)) = 60° -> OA = a, SO = a√3, AB = a√2 => V = 2a³√3/3
        (
            "Cho hình chóp tứ giác đều S.ABCD có cạnh bên SA = 2a, "
            "góc giữa SA và mặt phẳng đáy bằng 60°. Tính thể tích khối chóp S.ABCD.",
            "2a³√3/3",
            {ID_ADJ_FROM_HYP_COS, ID_OPP_FROM_HYP_SIN},
        ),
        # 7. Square base from diagonal AC = a√2 -> AB = a, SA = a => V = a³/3
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, AC = a√2, "
            "SA vuông góc với mặt phẳng (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD.",
            "a³/3",
            set(),
        ),
        # 8. Dihedral angle [S, BC, A] = 60° (Three Perpendiculars) -> height SA = a√3 => V = a³/2
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a√3, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa hai mặt phẳng (SBC) và (ABC) bằng 60°. "
            "Tính thể tích khối chóp S.ABC.",
            "a³/2",
            {ID_OPP_FROM_ADJ_TAN},
        ),
    ],
)
def test_stage_p1c_end_to_end_verified_constructions(
    text: str, expected_answer: str, expected_identities: set[str]
) -> None:
    from app.ai.adaptive_input_router import route_text_input

    out = route_text_input(text, allow_live_ai=False)
    assert out.local_parse_result.status == "LOCAL_PARSE_COMPLETE"
    env = out.response["envelope"]
    assert env["status"] == "ok"
    rd = out.response["route_d"]
    assert rd["status"] == "SERVED"
    assert rd.get("scene_configuration") is None
    assert list(rd["answers"].values()) == [expected_answer]

    certs = rd.get("trig_construction_certificates") or []
    got_ids = {c["trig_identity"] for c in certs}
    assert expected_identities.issubset(got_ids)
    for c in certs:
        assert c["schema_version"] == TRIG_CONSTRUCTION_CERTIFICATE_VERSION
        assert c["dimension"] == "LENGTH"
        assert c["positivity_domain"]["derived_length_sq_gt_0"] is True


@pytest.mark.parametrize(
    ("text", "expected_reason_code", "expected_failure_category"),
    [
        # Non-exact degree 37° -> honest capability gap
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) bằng 37°. "
            "Tính thể tích khối chóp S.ABC.",
            "EXACT_DOMAIN_EXCEEDED",
            "capability_gap",
        ),
        # Non-rational Gram SAS (AB=3a, BC=4a, ∠ABC=30° => <AB,BC> = 6√3 ∉ Q) -> honest capability gap
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác có AB = 3a, BC = 4a, góc ABC = 30°, "
            "SA vuông góc với mặt phẳng (ABC), SA = a. Tính thể tích khối chóp S.ABC.",
            "EXACT_DOMAIN_EXCEEDED",
            "capability_gap",
        ),
        # Off-foot 90° line-plane angle contradicts SA ⊥ (ABC) with A ≠ B
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) bằng 90°. "
            "Tính thể tích khối chóp S.ABC.",
            "INCONSISTENT_FACTS",
            "geometry_generation_failed",
        ),
        # Out-of-range sin = 3/2 (> 1)
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, "
            "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) có sin bằng 3/2. "
            "Tính thể tích khối chóp S.ABC.",
            "INCONSISTENT_FACTS",
            "geometry_generation_failed",
        ),
        # Coupling Guard: uncoupled square base without base dimension -> clarification/ambiguous refusal
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông, SA vuông góc với mặt phẳng (ABCD), SA = 2a. "
            "Tính thể tích khối chóp S.ABCD.",
            "AMBIGUOUS_FACT",
            "insufficient_specification",
        ),
    ],
)
def test_stage_p1c_end_to_end_negative_counterexamples(
    text: str, expected_reason_code: str, expected_failure_category: str
) -> None:
    from app.ai.adaptive_input_router import route_text_input

    out = route_text_input(text, allow_live_ai=False)
    env = out.response["envelope"]
    assert env["status"] == "unsupported"
    assert env["reason_code"] == expected_reason_code
    assert env["failure_category"] == expected_failure_category


def test_geometry_metamorphics_label_permutation_clause_order_angle_representation_and_scaling() -> None:
    """Phase 8 (§11.2): label renaming, clause reordering, 30° <-> sin=1/2 <-> tan=√3/3, and scale doubling `a -> 2a`."""
    from app.ai.adaptive_input_router import route_text_input

    # 1. Canonical 30° pyramid: SA ⊥ (ABC), △ABC right at B, AB = a√3, BC = a, ∠(SB, (ABC)) = 30° => SA = a, V = a²√3*a/6 = a³√3/6
    t_deg = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a√3, BC = a, "
        "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) bằng 30°. "
        "Tính thể tích khối chóp S.ABC."
    )
    # 2. Equivalent sin = 1/2
    t_sin = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a√3, BC = a, "
        "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) có sin bằng 1/2. "
        "Tính thể tích khối chóp S.ABC."
    )
    # 3. Equivalent tang = √3/3 with reordered clauses
    t_tan_reordered = (
        "Cho hình chóp S.ABC có SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) có tang bằng √3/3, "
        "đáy ABC là tam giác vuông tại B, BC = a, AB = a√3. Tính thể tích khối chóp S.ABC."
    )
    # 4. Vertex label permutation S.ABC -> P.MNP (A->M, B->N, C->Q, S->P)
    t_renamed = (
        "Cho hình chóp P.MNQ có đáy MNQ là tam giác vuông tại N, MN = a√3, NQ = a, "
        "PM vuông góc với mặt phẳng (MNQ), góc giữa PN và mặt phẳng (MNQ) bằng 30°. "
        "Tính thể tích khối chóp P.MNQ."
    )
    # 5. Scale doubling (AB = 2a√3, BC = 2a) => volume scales by 2³ = 8 -> 4a³√3/3!
    t_scaled_2x = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 2a√3, BC = 2a, "
        "SA vuông góc với mặt phẳng (ABC), góc giữa SB và mặt phẳng (ABC) bằng 30°. "
        "Tính thể tích khối chóp S.ABC."
    )

    for variant in (t_deg, t_sin, t_tan_reordered, t_renamed):
        res = route_text_input(variant, allow_live_ai=False)
        assert res.response["envelope"]["status"] == "ok"
        assert list(res.response["route_d"]["answers"].values()) == ["a³√3/6"]

    res_2x = route_text_input(t_scaled_2x, allow_live_ai=False)
    assert res_2x.response["envelope"]["status"] == "ok"
    assert list(res_2x.response["route_d"]["answers"].values()) == ["4a³√3/3"]


def test_phase_9_scene3d_invariants_output_policy_right_angle_hiding_and_zero_carrier_leaks() -> None:
    """Phase 9: Scene3D constructs exact height/foot + perpendicular witness, preserves `output-policy/1`, hides asked right angles, and leaks zero internal scalars."""
    from app.ai.adaptive_input_router import route_text_input
    from app.simulation.geometry_functions.output_policy import OUTPUT_POLICY_SCHEMA_VERSION

    # 1. Trig construction scene: height segment carries GIVEN perpendicular_witness, output-policy/1 governs display, zero bogus carrier object types
    trig_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, cạnh AC = 2a. "
        "Cạnh SA vuông góc với mặt đáy (ABC), tam giác SAB cân. "
        "Tính thể tích khối chóp S.ABC theo a."
    )
    out = route_text_input(trig_text, allow_live_ai=False)
    env = out.response["envelope"]
    assert env["status"] == "ok"
    rd = out.response["route_d"]
    assert rd["answer_exact"]["q1"] == {"coef": "√2/3", "dim": 3, "unit": "a"}

    sc = env["scene3d"]
    allowed_types = {
        "point3", "segment3", "line3", "plane3", "polygon3", "polyhedron3", "solid",
        "circle3", "sphere3", "cylinder3", "cone3", "ellipse3", "quantity",
    }
    obj_types = {o["type"] for o in sc["objects"]}
    assert obj_types.issubset(allowed_types)
    # No internal auxiliary witness labels (`_aux_`) or intermediate trig scalars leak into Scene3D objects
    assert not any(str(o["id"]).startswith("_aux_") for o in sc["objects"])
    qty_vol = [o for o in sc["objects"] if o["type"] == "quantity"]
    assert len(qty_vol) == 1 and qty_vol[0]["annotation"]["category"] == "result"
    # Height SA segment has exact GIVEN perpendicular_witness at foot A
    sa_segs = [o for o in sc["objects"] if o["type"] == "segment3" and o["id"] == "canh_ben_S_A"]
    assert sa_segs and sa_segs[0]["perpendicular_witness"]["foot_id"] == "A"
    assert sa_segs[0]["perpendicular_witness"]["status"] == "GIVEN"
    assert sa_segs[0]["perpendicular_witness"]["metric_spd"] is True

    # 1b. Explicit degree request exercises `output-policy/1` while preserving exact `cos²=1/2` kernel binding
    deg_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AC = 2a, "
        "SA vuông góc với mặt phẳng (ABC), tam giác SAB cân. "
        "Tính số đo góc giữa hai mặt phẳng (SBC) và (ABC) theo đơn vị độ."
    )
    out_deg = route_text_input(deg_text, allow_live_ai=False)
    assert out_deg.response["envelope"]["status"] == "ok"
    rd_deg = out_deg.response["route_d"]
    assert list(rd_deg["answers"].values()) == ["45°"]
    assert rd_deg["answer_exact"]["q1"]["output_policy"]["schema_version"] == OUTPUT_POLICY_SCHEMA_VERSION
    assert rd_deg["answer_exact"]["q1"]["output_policy"]["exact_answer"] == "cos²=1/2"

    # 2. Right-angle conclusion hiding: when line-plane angle is 90° (`BC` vs `(SAB)`), BC has NO GIVEN perpendicular_witness
    #    and the target `quantity` marks its witness strictly as `category == "result"` (never a premise right-angle spoiler)
    ask_right_angle_text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AC = 2a, "
        "SA vuông góc với mặt phẳng (ABC), SA = a√2. Tính góc giữa đường thẳng BC và mặt phẳng (SAB)."
    )
    out_ra = route_text_input(ask_right_angle_text, allow_live_ai=False)
    assert out_ra.response["envelope"]["status"] == "ok"
    assert list(out_ra.response["route_d"]["answers"].values()) == ["cos²=0"]
    sc_ra = out_ra.response["envelope"]["scene3d"]
    given_pw_ids = [o["id"] for o in sc_ra["objects"] if o.get("perpendicular_witness")]
    assert given_pw_ids == ["canh_ben_S_A"]
    qty_ra = next(o for o in sc_ra["objects"] if o["type"] == "quantity")
    assert qty_ra["annotation"]["category"] == "result"
    assert "angle_construction" not in qty_ra


# ── 8. Stage P1c-1 Source-Unit Dimension Consistency on Trig Ratios, Angles & Lengths ────────────────────────────────

def test_p1c1_repro_a_source_gate_blocks_truncated_quote_wrong_unit_on_trig_ratio() -> None:
    """Even if an extracted/bridged `line_plane_angle` call carries a truncated quote omitting the unit,
    `dung_tu_loi_goi` / `kiem_nguon` inspects the full source `de` and refuses `INCONSISTENT_FACTS`."""
    for bad_tail, trunc_val in (("2cm", "2"), ("30°", "30"), ("2 rad", "2"), ("2 (cm)", "2")):
        de_bad = (
            "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy. "
            f"Biết tan của góc giữa SB và mặt phẳng (ABC) bằng {bad_tail}. Tính thể tích khối chóp S.ABC."
        )
        plan = {
            "calls": [
                {
                    "id": "s1",
                    "fn": "pyramid",
                    "args": {"apex": "S", "base": ["A", "B", "C"]},
                    "source": {"quotes": ["Cho hình chóp S.ABC"]},
                },
                {
                    "id": "p1",
                    "fn": "regular_polygon",
                    "args": {"vertices": ["A", "B", "C"], "side": "3"},
                    "source": {"quotes": ["đáy ABC là tam giác đều cạnh 3cm"]},
                },
                {
                    "id": "p2",
                    "fn": "perpendicular_line_plane",
                    "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                    "source": {"quotes": ["SA vuông góc với đáy"]},
                },
                {
                    "id": "p3",
                    "fn": "line_plane_angle",
                    "args": {"line": ["S", "B"], "plane": ["A", "B", "C"], "value": trunc_val, "unit": "tan"},
                    "source": {"quotes": [f"Biết tan của góc giữa SB và mặt phẳng (ABC) bằng {trunc_val}"]},
                },
                {
                    "id": "q1",
                    "fn": "ask_volume",
                    "args": {"solid": "S.ABC"},
                    "source": {"quotes": ["Tính thể tích khối chóp S.ABC"]},
                },
            ]
        }
        res = dung_tu_loi_goi(de_bad, plan)
        assert res.status == "REFUSED", f"Expected REFUSED on {bad_tail!r}, got {res}"
        assert res.code == "INCONSISTENT_FACTS"


@pytest.mark.parametrize(
    "bad_clause",
    [
        "tan của góc giữa SB và mặt phẳng đáy bằng 2cm",
        "tan của góc giữa SB và mặt phẳng đáy bằng 30°",
        "tan của góc giữa SB và mặt phẳng đáy bằng 2 rad",
        "góc giữa SB và mặt phẳng đáy có tan bằng 30°",
        "góc giữa SB và mặt phẳng đáy bằng 2cm",
        "SB tạo với mặt phẳng đáy một góc 4cm²",
        "SA = 60°",
        "SA = 2 rad",
    ],
)
def test_p1c1_repro_b_offline_router_deterministically_refuses_wrong_dimension_units(bad_clause: str) -> None:
    """`route_text_input(..., allow_live_ai=False)` deterministically refuses wrong-dimension units as
    `INCONSISTENT_FACTS` with `0` provider calls (never falling back to `503 LIVE_AI_DISABLED`)."""
    from app.ai.adaptive_input_router import route_text_input

    text = (
        f"Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, {bad_clause}. "
        "Tính thể tích khối chóp S.ABC."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.telemetry.total_provider_calls == 0
    assert out.local_parse_result.status == "LOCAL_PARSE_COMPLETE"
    env = out.response["envelope"]
    assert env["status"] == "unsupported"
    assert env["reason_code"] == "INCONSISTENT_FACTS"
    assert env["failure_category"] == "geometry_generation_failed"


def test_p1c1_positive_controls_preserve_valid_metric_and_angle_combinations() -> None:
    """Valid combinations of metric lengths (`3cm`) with degree angles (`60°`), dimensionless trig ratios (`2`),
    or `=`-form line-line angles (`SC và AB = 60°`) remain deterministically `SERVED` offline."""
    from app.ai.adaptive_input_router import route_text_input

    t_deg = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, "
        "góc giữa SB và mặt phẳng đáy bằng 60°. Tính thể tích khối chóp S.ABC."
    )
    out_deg = route_text_input(t_deg, allow_live_ai=False)
    assert out_deg.telemetry.total_provider_calls == 0
    assert out_deg.response["envelope"]["status"] == "ok"
    assert list(out_deg.response["route_d"]["answers"].values()) == ["27/4"]

    t_trig = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, "
        "tan của góc giữa SB và mặt phẳng đáy bằng 2. Tính thể tích khối chóp S.ABC."
    )
    out_trig = route_text_input(t_trig, allow_live_ai=False)
    assert out_trig.telemetry.total_provider_calls == 0
    assert out_trig.response["envelope"]["status"] == "ok"
    assert list(out_trig.response["route_d"]["answers"].values()) == ["9√3/2"]

    t_lla_eq = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = a, BC = a, "
        "SA vuông góc với mặt phẳng (ABC), góc giữa hai đường thẳng SC và AB = 60°. "
        "Tính thể tích khối chóp S.ABC."
    )
    out_lla = route_text_input(t_lla_eq, allow_live_ai=False)
    assert out_lla.telemetry.total_provider_calls == 0
    assert out_lla.response["envelope"]["status"] == "ok"
    assert list(out_lla.response["route_d"]["answers"].values()) == ["a³√2/6"]


# ── 10. `#36` P1c-3 Regression: Structured Angle/Trig LHS Subjects Prevent Cross-Clause Over-Reach ────────────────────

@pytest.mark.parametrize(
    ("valid_text", "expected_seg", "expected_val"),
    [
        ("Cho hình chóp S.ABC có AB = 4 cos 60° và BC = 3cm. Tính thể tích khối chóp S.ABC.", {"B", "C"}, "3"),
        ("Cho hình chóp S.ABC có AB = 2 sin α và SA = 3cm. Tính thể tích khối chóp S.ABC.", {"S", "A"}, "3"),
        ("Cho hình chóp S.ABC có góc nhị diện [S, BC, A] nhọn và SA = 3cm. Tính thể tích khối chóp S.ABC.", {"S", "A"}, "3"),
        ("Cho hình chóp S.ABC có góc nhị diện [S, BC, A] vuông và SA = 3cm. Tính thể tích khối chóp S.ABC.", {"S", "A"}, "3"),
        (
            "Cho hình chóp S.ABC có góc giữa SB và đáy cùng góc giữa SC và đáy nhọn và SA = 3cm. Tính thể tích khối chóp S.ABC.",
            {"S", "A"},
            "3",
        ),
    ],
)
def test_p1c3_false_positive_guards_preserve_cross_clause_segment_lengths(
    valid_text: str,
    expected_seg: set[str],
    expected_val: str,
) -> None:
    """Structured angle/trig LHS subjects never bridge across `và <SEG> = 3cm` (`#36` P1c-3 items 1-3),
    and `local_geometry_parser` still extracts the trailing `segment_length` premise."""
    from app.ai.local_geometry_parser import (
        _AstBuilder,
        _clause_order,
        _parse_clause_into_ast,
        normalize_problem_text,
        parse_geometry_problem_locally,
        split_into_clauses,
    )
    from app.simulation.geometry_functions.registry import _kiem_don_vi_dai_luong_nguon, chuan_hoa

    _kiem_don_vi_dai_luong_nguon(chuan_hoa(valid_text))

    raw = normalize_problem_text(valid_text)
    clauses = split_into_clauses(raw)
    builder = _AstBuilder(raw)
    for i in _clause_order(clauses):
        _parse_clause_into_ast(builder, clauses[i])
    seg_premises = [
        p for p in builder.premises
        if p.get("kind") == "segment_length" and set(p.get("args", {}).get("segment", ())) == expected_seg
    ]
    assert seg_premises, f"Expected segment_length for {expected_seg} in {valid_text!r}, got {builder.premises}"
    assert seg_premises[0]["args"]["value"] == expected_val

    # Full LOCAL_PARSE_COMPLETE check on parseable `[S, BC, A] bằng 60° và SA = 3cm`
    full_parseable = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, "
        "góc nhị diện [S, BC, A] bằng 60° và SA = 3cm. Tính thể tích khối chóp S.ABC."
    )
    parsed_full = parse_geometry_problem_locally(full_parseable, use_cache=False)
    assert parsed_full.status == "LOCAL_PARSE_COMPLETE"
    assert parsed_full.payload is not None
    assert any(
        p.get("kind") == "segment_length" and set(p.get("args", {}).get("segment", ())) == {"S", "A"}
        for p in parsed_full.payload["premises"]
    )

    # Chained RHS trig expression `AB = 2 sin α = 1cm` also does not falsely trigger SCALAR mismatch
    _kiem_don_vi_dai_luong_nguon(chuan_hoa("Cho hình chóp S.ABC có AB = 2 sin α = 1cm."))


@pytest.mark.parametrize(
    "bad_text",
    [
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, biết góc giữa SM và đáy lớn nhất và SA = 60°.",
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA tạo với đáy một góc nhọn và SB = 60°.",
        "Cho hình chóp S.ABC có góc nhị diện [S, BC, A] nhọn và SA = 60°.",
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, gọi t là tan của góc giữa SB và đáy bằng 2cm.",
        "Cho hình chóp S.ABC có tỉ số giữa cạnh SA và cạnh SB = 60°.",
        "Cho hình chóp S.ABC có cos của số đo [S, BC, A] = 2cm.",
    ],
)
def test_p1c3_false_negative_bypass_guards_catch_cross_clause_wrong_units(bad_text: str) -> None:
    """Preceding non-assignment angle phrases (`lớn nhất`, `góc nhọn`, `[S, BC, A] nhọn`) never cause `LENGTH`
    to skip a subsequent `và <SEG> = 60°` wrong-unit segment assignment (`#36` P1c-3 items 4-5)."""
    from app.ai.adaptive_input_router import route_text_input
    from app.simulation.geometry_functions.registry import TuChoi, _kiem_don_vi_dai_luong_nguon, chuan_hoa

    with pytest.raises(TuChoi) as exc:
        _kiem_don_vi_dai_luong_nguon(chuan_hoa(bad_text))
    assert exc.value.code == "INCONSISTENT_FACTS"

    parseable_cross_clause = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy, "
        "SA tạo với đáy một góc 60° và SB = 60°. Tính thể tích khối chóp S.ABC."
    )
    out = route_text_input(parseable_cross_clause, allow_live_ai=False)
    assert out.telemetry.total_provider_calls == 0
    assert out.response["envelope"]["status"] == "unsupported"
    assert out.response["envelope"]["reason_code"] == "INCONSISTENT_FACTS"


# ── 11. `#38` P1c-4 Regression: No-Space `trig(X, Y)` Shorthand vs `d(X, Y)` Distance Control ─────────────────────────

def test_p1c4_nospace_trig_pair_shorthand_refuses_wrong_units_while_preserving_distance_notation() -> None:
    """`tan(SB, (ABC)) = 2cm` and `cos((SBC), (ABC)) = 30°` fail closed with `INCONSISTENT_FACTS` even under truncated
    quotes in `dung_tu_loi_goi`, while `d(SA, BC) = 2cm` remains valid (`#38` P1c-4)."""
    from app.simulation.geometry_functions.engine import dung_tu_loi_goi
    from app.simulation.geometry_functions.registry import TuChoi, _kiem_don_vi_dai_luong_nguon, chuan_hoa

    # 1. Exact `#38` live reproduction: `tan(SB, (ABC)) = 2cm` with truncated quote `"Biết tan(SB, (ABC)) = 2"`
    de_tan = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy. "
        "Biết tan(SB, (ABC)) = 2cm. Tính thể tích khối chóp S.ABC."
    )
    plan_tan = {
        "calls": [
            {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
            {"id": "p1", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "3"}, "source": {"quotes": ["đáy ABC là tam giác đều cạnh 3cm"]}},
            {"id": "p2", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
            {"id": "p3", "fn": "line_plane_angle", "args": {"line": ["S", "B"], "plane": ["A", "B", "C"], "value": "2", "unit": "tan"}, "source": {"quotes": ["Biết tan(SB, (ABC)) = 2"]}},
            {"id": "q1", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quotes": ["Tính thể tích khối chóp S.ABC"]}},
        ]
    }
    res_tan = dung_tu_loi_goi(de_tan, plan_tan)
    assert res_tan.status == "REFUSED"
    assert res_tan.code == "INCONSISTENT_FACTS"

    # 2. `cos((SBC), (ABC)) = 30°` with truncated quote `"Biết cos((SBC), (ABC)) = 30"` (and `cos(B) = 2cm`)
    de_cos = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, SA vuông góc với đáy. "
        "Biết cos((SBC), (ABC)) = 30°. Tính thể tích khối chóp S.ABC."
    )
    plan_cos = {
        "calls": [
            {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
            {"id": "p1", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "3"}, "source": {"quotes": ["đáy ABC là tam giác đều cạnh 3cm"]}},
            {"id": "p2", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]}, "source": {"quotes": ["SA vuông góc với đáy"]}},
            {"id": "p3", "fn": "plane_plane_angle", "args": {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"], "value": "30", "unit": "cos"}, "source": {"quotes": ["Biết cos((SBC), (ABC)) = 30"]}},
            {"id": "q1", "fn": "ask_volume", "args": {"solid": "S.ABC"}, "source": {"quotes": ["Tính thể tích khối chóp S.ABC"]}},
        ]
    }
    res_cos = dung_tu_loi_goi(de_cos, plan_cos)
    assert res_cos.status == "REFUSED"
    assert res_cos.code == "INCONSISTENT_FACTS"

    for bad_shorthand in (
        "Cho hình chóp S.ABC có tan(SB, (ABC)) = 2cm.",
        "Cho hình chóp S.ABC có cos((SBC), (ABC)) = 30°.",
        "Cho hình chóp S.ABC có đáy ABC có cos(B) = 2cm.",
        "Cho hình chóp S.ABC có đáy ABC có cos B = 30°.",
    ):
        with pytest.raises(TuChoi) as exc:
            _kiem_don_vi_dai_luong_nguon(chuan_hoa(bad_shorthand))
        assert exc.value.code == "INCONSISTENT_FACTS"

    # 3. Positive control: `d(SA, BC) = 2cm` and `d(A, (SBC)) = 2cm` must NEVER match ANGLE or SCALAR
    _kiem_don_vi_dai_luong_nguon(chuan_hoa("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, d(SA, BC) = 2cm."))
    _kiem_don_vi_dai_luong_nguon(chuan_hoa("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 3cm, d(A, (SBC)) = 2cm."))



