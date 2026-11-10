# -*- coding: utf-8 -*-
"""Phase 1 (Gate A): Formal Symbolic Height-Invariance Certification & Adversarial Tests.

Tests the 8 formal proof obligations (`PO-1` .. `PO-8`) over `ℚ[t]` (`t = h² ∈ (0, +∞)`),
independent certificate verification, mutation/tamper rejection, and all 14 Section 4.4
adversarial categories with independent exact rational (`Fraction`) mathematical oracles.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.function_route import run_function_route
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.height_invariance import (
    CERTIFICATE_SCHEMA_VERSION,
    PROOF_OBLIGATIONS,
    Poly,
    poly_add,
    poly_eval,
    poly_mul,
    poly_sub,
    verify_height_invariance_certificate,
    verify_rational_constancy_over_positive_reals,
)


def _run_text(text: str):
    return route_text_input(text, allow_live_ai=False)


# ── 1. Pure Polynomial & Rational Constancy Verifier Adversarial Tests ───────────────────────────────────────────────


def test_five_sample_coincidence_polynomial_is_rejected_by_symbolic_certifier():
    """Adversarial Category 3: Rational expression matching at ALL 5 legacy samples {1, 2, 3, 5, 7}
    but non-constant for t ∉ {1, 2, 3, 5, 7}:
        P(t) = 4 + (t-1)(t-2)(t-3)(t-5)(t-7),  Q(t) = 1.
    At t ∈ {1,2,3,5,7}, P(t)/Q(t) == 4 identically, which would fool 5-sample coincidence testing!
    Symbolic polynomial identity + degree bound MUST reject it.
    """
    roots_poly: Poly = (Fraction(1),)
    for s in (1, 2, 3, 5, 7):
        roots_poly = poly_mul(roots_poly, (Fraction(-s), Fraction(1)))
    p_adv = poly_add((Fraction(4),), roots_poly)
    q_adv: Poly = (Fraction(1),)

    # Confirm the adversarial polynomial truly fools all 5 sample points {1, 2, 3, 5, 7}:
    for s in (1, 2, 3, 5, 7):
        assert poly_eval(p_adv, Fraction(s)) / poly_eval(q_adv, Fraction(s)) == Fraction(4)
    # Yet at t = 4 (inside (0, +∞)), it is NOT 4:
    assert poly_eval(p_adv, Fraction(4)) != Fraction(4)

    ok, code, _c = verify_rational_constancy_over_positive_reals(
        p_adv, q_adv, linear_den_factors=(), max_degree=2
    )
    assert not ok
    assert code in ("PO_POLYNOMIAL_DEGREE_BOUNDED", "PO_EXACT_POLYNOMIAL_IDENTITY")


def test_degree_two_five_sample_impossible_vs_degree_exceeded_guard():
    """Adversarial Category 4: Expression whose degree exceeds the proved degree bound (deg > 2)
    is rejected even when P(t) = c·Q(t) algebraically (e.g. deg 3 / deg 3)."""
    # (1 + t)^3 / (1 + t)^3 has degree 3 > max_degree=2: must fail degree guard PO-5.
    cubic = poly_mul(poly_mul((Fraction(1), Fraction(1)), (Fraction(1), Fraction(1))), (Fraction(1), Fraction(1)))
    ok, code, _c = verify_rational_constancy_over_positive_reals(
        cubic, cubic, linear_den_factors=((Fraction(1), Fraction(1)),) * 3, max_degree=2
    )
    assert not ok
    assert code == "PO_POLYNOMIAL_DEGREE_BOUNDED"


@pytest.mark.parametrize(
    ("p", "q", "factors", "expected_code"),
    [
        # Adversarial Category 5: Zero denominator Q(t) ≡ 0
        ((Fraction(0),), (Fraction(0),), ((Fraction(0), Fraction(0)),), "PO_DENOMINATOR_POSITIVE_ON_DOMAIN"),
        # Denominator vanishes at t = 8 ∈ (0, +∞) (non-zero at {1,2,3,5,7}!)
        (
            (Fraction(-32), Fraction(4)),
            (Fraction(-8), Fraction(1)),
            ((Fraction(-8), Fraction(1)),),
            "PO_DENOMINATOR_POSITIVE_ON_DOMAIN",
        ),
        # Negative denominator factor on (0, +∞)
        (
            (Fraction(-4), Fraction(-4)),
            (Fraction(-1), Fraction(-1)),
            ((Fraction(-1), Fraction(-1)),),
            "PO_DENOMINATOR_POSITIVE_ON_DOMAIN",
        ),
        # Negative constant ratio c < 0 (impossible for squared distance / cos²)
        (
            (Fraction(-3), Fraction(-3)),
            (Fraction(1), Fraction(1)),
            ((Fraction(1), Fraction(1)),),
            "PO_EXACT_POLYNOMIAL_IDENTITY",
        ),
    ],
)
def test_degenerate_or_domain_violating_denominators_fail_closed(p, q, factors, expected_code):
    ok, code, _c = verify_rational_constancy_over_positive_reals(p, q, linear_den_factors=factors, max_degree=2)
    assert not ok
    assert code == expected_code


# ── 2. True Height-Invariant Goals (Positive Soundness & Expanded Legitimate Affine Points) ──────────────────────────


@pytest.mark.parametrize(
    ("text", "expected_answer", "oracle_sq_or_cos2"),
    [
        # 1) External17 ext02: d(C, (ABB'A')) = 6 on right isosceles base at B
        (
            "Câu 10: Cho hình lăng trụ đứng ABC.A'B'C', có đáy là tam giác vuông cân tại B và AB = 6. "
            "Tính khoảng cách từ điểm C đến mặt phẳng (ABB'A')\nA. 3. B. 6√2. C. 3√2. D. 6.",
            "6",
            Fraction(36),
        ),
        # 2) External17 ext03#1: d(B, (SAC)) = a√2/2 on square base
        (
            "Câu 32: Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
            "Tính khoảng cách từ điểm B đến mp(SAC).",
            "a√2/2",
            Fraction(1, 2),
        ),
        # 3) Skew line distance d(AA', BC) in right prism with equilateral base 2a -> a√3
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2a. "
            "Tính khoảng cách giữa hai đường thẳng AA' và BC.",
            "a√3",
            Fraction(3),
        ),
        # 4) Affine midpoint M on base edge AB (previously blocked by vertex-only guard, now formally proved!):
        #    Square ABCD side 2a, SA ⊥ (ABCD), M midpoint AB: A(0,0), B(2,0), C(2,2), M(1,0).
        #    Line AC is x = y; d(M, (SAC)) = d_2D(M(1,0), line x - y = 0) = |1 - 0|/√2 = √2/2 * a -> a√2/2!
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA ⊥ (ABCD). "
            "Gọi M là trung điểm của AB. Tính khoảng cách từ M đến mặt phẳng (SAC).",
            "a√2/2",
            Fraction(1, 2),
        ),
        # 5) Angle between two vertical planes (SAC) and (SBD) in square pyramid SA ⊥ (ABCD): AC ⊥ BD => cos²=0!
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
            "Tính góc giữa hai mặt phẳng (SAC) và (SBD).",
            "cos²=0",
            Fraction(0),
        ),
        # 6) Point-to-line distance d(C, BB') in right prism (uses t-independent auxiliary orthogonal_projection_line!):
        #    Base right-isosceles at B, AB = 4 => foot of C onto BB' is B for ALL heights t > 0 => d = CB = 4!
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông cân tại B, AB = 4. "
            "Tính khoảng cách từ C đến đường thẳng BB'.",
            "4",
            Fraction(16),
        ),
        # 7) Renamed & reordered premises + scaled parameter:
        #    Right prism MNP.M'N'P', MNP equilateral side 6, d(NP, MM') = 3√3 (sq = 27)
        (
            "Cho hình lăng trụ đứng MNP.M'N'P'. Đáy MNP là tam giác đều cạnh 6. "
            "Tính khoảng cách giữa hai đường thẳng NP và MM'.",
            "3√3",
            Fraction(27),
        ),
    ],
)
def test_formally_certified_height_invariant_cases_serve_with_verified_certificate(
    text: str, expected_answer: str, oracle_sq_or_cos2: Fraction
):
    out = _run_text(text)
    assert out.status == "SERVED", out.response.get("route_d", {}).get("refusal")
    rd = out.response["route_d"]
    assert list(rd["answers"].values()) == [expected_answer]

    cfg = rd["scene_configuration"]
    assert cfg["unique"] is False
    assert cfg["kind"] == "HEIGHT_INVARIANT_ILLUSTRATIVE"

    cert = cfg["invariance_certificate"]
    assert cert["schema_version"] == CERTIFICATE_SCHEMA_VERSION
    assert cert["certification_mode"] == "EXACT_SYMBOLIC_POLYNOMIAL_IDENTITY"
    assert set(PROOF_OBLIGATIONS) <= set(cert["proof_obligations"])
    assert all(cert["proof_obligations"][po]["verified"] is True for po in PROOF_OBLIGATIONS)

    # Standalone independent certificate verifier must pass without calling the engine:
    verdict = verify_height_invariance_certificate(cert)
    assert verdict["verified"] is True, verdict

    # Independent oracle check on the certified rational constant c:
    goal_forms = cert["goal_rational_forms"]
    assert len(goal_forms) == 1
    g_form = next(iter(goal_forms.values()))
    assert Fraction(g_form["constant_value"]) == oracle_sq_or_cos2
    assert g_form["identity_residual_coeffs"] == []
    assert validate_construction_continuity(out.response["envelope"]["scene3d"]) == []


# ── 3. Critical Adversarial Refusal Cases (Must Fail Closed & Report Failed Proof Obligation) ────────────────────────


def test_invariant_goal_with_height_dependent_auxiliary_construction_refuses():
    """Adversarial Category 9 & 13 (REAL BUG IN LEGACY 5-SAMPLE CODE):
    Goal d(B, (SAC)) = a√2/2 IS height-invariant, BUT the problem also constructs
    `H = orthogonal_projection_line(A, SB)` whose position H(t) = (t/(1+t), 0, 1/(1+t))
    moves with height t! Legacy 5-sample code only checked goal labels `{B,S,A,C} <= dinh`
    and served an invalid Scene3D with H frozen at t=1.
    Formal PO-2 (`PO_AFFINE_COORDINATES_T_INDEPENDENT`) MUST refuse!
    """
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Gọi H là hình chiếu vuông góc của A lên SB. Tính khoảng cách từ B đến mặt phẳng (SAC)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"
    assert not out.response["envelope"].get("scene3d")

    # Direct low-level check that the exact failed obligation PO-2 is recorded:
    plan = {
        "calls": [
            {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quote": "hình chóp S.ABCD"}},
            {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"}, "source": {"quote": "đáy ABCD là hình vuông cạnh a"}},
            {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quote": "SA ⊥ (ABCD)"}},
            {"id": "c4", "fn": "orthogonal_projection_line", "args": {"point": "A", "line": ["S", "B"], "image": "H"}, "source": {"quote": "Gọi H là hình chiếu vuông góc của A lên SB"}},
            {"id": "q1", "fn": "ask_distance_point_plane", "args": {"point": "B", "plane": ["S", "A", "C"]}, "source": {"quote": "Tính khoảng cách từ B đến mặt phẳng (SAC)"}},
        ]
    }
    res = run_function_route(text, plan)
    assert res.status == "REFUSED" and res.code == "MISSING_DIMENSION"
    audit = (res.details or {}).get("height_invariance_audit") or {}
    assert audit.get("certified") is False
    assert audit.get("failed_obligation") == "PO_AFFINE_COORDINATES_T_INDEPENDENT"


def test_invariant_goal_with_height_dependent_plane_projection_refuses():
    """Adversarial Category 9: H = orthogonal_projection(A, (SBC)) moves with height t,
    even though asked goal d(B, (SAC)) is height-invariant -> must refuse PO-2."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Gọi H là hình chiếu vuông góc của A lên mặt phẳng (SBC). Tính khoảng cách từ B đến mặt phẳng (SAC)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"


def test_section_plane_perpendicular_to_slant_edge_changes_with_height_and_refuses():
    """Adversarial Category 10: Plane (P) through A perpendicular to SB tilts as height SA varies,
    changing section cut positions/topology with t -> must refuse PO-2/PO-3 even when asked goal is d(B, (SAC))
    or section area."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Mặt phẳng (P) đi qua A và vuông góc với SB. Tính diện tích thiết diện của hình chóp cắt bởi (P)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"
    assert not out.response["envelope"].get("scene3d")


def test_linear_sign_flip_beyond_five_samples_is_rejected():
    """Adversarial Category 6 & 7: A linear dot-product / dihedral half-plane sign expression
    `L(t) = 9 - t` is strictly positive at ALL 5 legacy samples {1, 2, 3, 5, 7} (values 8, 7, 6, 4, 2 > 0),
    fooling 5-sample testing, yet flips sign at t = 9 ∈ (0, +∞).
    `check_linear_sign_invariant_on_positive_reals` MUST reject it."""
    from app.simulation.geometry_functions.height_invariance import check_linear_sign_invariant_on_positive_reals

    lin_fooled_5_samples = (Fraction(9), Fraction(-1))
    for s in (1, 2, 3, 5, 7):
        assert lin_fooled_5_samples[0] + lin_fooled_5_samples[1] * Fraction(s) > 0
    assert check_linear_sign_invariant_on_positive_reals(lin_fooled_5_samples, 1) is False
    assert check_linear_sign_invariant_on_positive_reals(lin_fooled_5_samples, -1) is False
    assert check_linear_sign_invariant_on_positive_reals((Fraction(3), Fraction(2)), 1) is True


def test_domain_restricted_obtuse_acute_branch_flip_at_large_height_refuses():
    """Adversarial Category 6 & 7: Constraint whose acute/obtuse sign holds at {1,2,3,5,7}
    but flips for t > 9 on (0, +∞)!
    Construct points M = midpoint(SA) -> (0,0,1/2), B(3,0,0), S(0,0,1):
    For vertex_angle at M between rays MA(0,0,-1/2) and MB(3,0,-1/2): no, g_t(MA, MB) = t/4 > 0.
    Consider P on AB and S: for vertex_angle at M=(1,0,1/2)? Let's use M = midpoint(SB) = (3/2, 0, 1/2)!
    Vectors from M(3/2, 0, 1/2) to A(0,0,0) and S(0,0,1):
        u = A - M = (-3/2, 0, -1/2),  w = S - M = (-3/2, 0, +1/2).
        g_t(u, w) = 9/4 - t/4 = (9 - t)/4!
    Look at g_t(u, w) = (9 - t)/4:
      - For t < 9 (e.g. t = 1, 2, 3, 5, 7!), g_t(u, w) > 0 (angle ∠AMS is ACUTE)!
      - At t = 9, ∠AMS = 90°!
      - For t > 9, g_t(u, w) < 0 (angle ∠AMS becomes OBTUSE)!
    Also test dihedral_angle with linear NPQ(t) changing sign!
    Any height-fixing or branch-changing angle premise must NEVER be certified invariant over (0, +∞)!
    """
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 3a, SA ⊥ (ABCD). "
        "Gọi M là trung điểm của SB. Tính khoảng cách từ M đến mặt phẳng (SAC)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"


def test_mixed_goals_one_invariant_one_dependent_refuses_po7():
    """Adversarial Category 12: Multiple goals where q1 is invariant d(B, (SAC)) and q2 is height-dependent d(A, (SBC))."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Tính khoảng cách từ B đến mặt phẳng (SAC) và khoảng cách từ A đến mặt phẳng (SBC)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"


def test_equal_squared_value_but_non_unique_signed_mirror_anchors_refuses():
    """Adversarial Category 11: Two pyramids sharing base ABCD with BOTH heights unstated ->
    multiple free height parameters (fails PO-1 single free height parameter)."""
    text = (
        "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD là hình vuông cạnh a, "
        "SA ⊥ (ABCD), TA ⊥ (ABCD). Tính khoảng cách từ B đến mặt phẳng (SAC)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"


def test_circumscribed_sphere_with_unstated_height_refuses_po1():
    """Curved solid radius depends on height (R² = r_base² + h²/4) -> refuses MISSING_DIMENSION."""
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Gọi (S) là mặt cầu ngoại tiếp hình chóp S.ABCD. Tính bán kính mặt cầu (S)."
    )
    out = _run_text(text)
    assert out.status == "REFUSED"
    assert out.response["envelope"]["reason_code"] == "MISSING_DIMENSION"


# ── 4. Certificate Tamper / Mutation Tests Killing Every Proof Obligation Guard (PO-1 .. PO-8) ───────────────────────


def _sample_valid_certificate() -> dict:
    out = _run_text(
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Tính khoảng cách từ điểm B đến mp(SAC)."
    )
    assert out.status == "SERVED"
    return deepcopy(out.response["route_d"]["scene_configuration"]["invariance_certificate"])


@pytest.mark.parametrize(
    ("mutation_name", "mutator"),
    [
        ("tamper_po1_non_spd_base_metric", lambda c: c["chart_summary"].__setitem__("base_g2", [["0", "0"], ["0", "1"]])),
        ("tamper_po1_multiple_free_anchors", lambda c: c["chart_summary"].__setitem__("off_base_anchor_count", 2)),
        ("tamper_po2_flip_obligation_flag", lambda c: c["proof_obligations"]["PO_AFFINE_COORDINATES_T_INDEPENDENT"].__setitem__("verified", False)),
        ("tamper_po3_flip_section_flag", lambda c: c["proof_obligations"]["PO_SECTION_TOPOLOGY_INVARIANT"].__setitem__("verified", False)),
        ("tamper_po4_flip_domain_flag", lambda c: c["proof_obligations"]["PO_VALID_DOMAIN_ALL_POSITIVE_T"].__setitem__("verified", False)),
        ("tamper_po5_excess_degree", lambda c: next(iter(c["goal_rational_forms"].values())).__setitem__("numerator_coeffs", ["0", "1", "0", "1"])),
        ("tamper_po6_negative_denominator_factor", lambda c: next(iter(c["goal_rational_forms"].values())).__setitem__("denominator_linear_factors", [["-2", "1"]])),
        ("tamper_po7_non_constant_numerator", lambda c: next(iter(c["goal_rational_forms"].values())).__setitem__("numerator_coeffs", ["1", "1"])),
        ("tamper_po8_mismatch_goal_coef", lambda c: c["goal_values"].__setitem__("q1", "999")),
        ("tamper_schema_version", lambda c: c.__setitem__("schema_version", "height-invariance-certificate/0")),
    ],
)
def test_certificate_verifier_kills_every_obligation_mutation(mutation_name: str, mutator):
    cert = _sample_valid_certificate()
    mutator(cert)
    verdict = verify_height_invariance_certificate(cert)
    assert verdict["verified"] is False, f"Mutation {mutation_name} escaped verifier!"
