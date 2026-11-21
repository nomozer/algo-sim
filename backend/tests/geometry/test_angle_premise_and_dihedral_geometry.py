# -*- coding: utf-8 -*-
"""Gate 1 TDD suite: Exact Angle-Premise & Dihedral Geometry (`Section IV`).

Tests full end-to-end execution:
    Vietnamese Text -> Local Parser (`local-geometry-parser/1`)
    -> TypedFactNext `/2` -> Bridge `/2` -> Source Gate (`registry.kiem_nguon`)
    -> Planner `/26` -> Registry `/33` -> Exact Kernel `/24` -> Adapter `/4` -> `Scene3D`.
"""
from __future__ import annotations

import copy
import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
from app.simulation.geometry_functions import engine, planner, registry
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity


def _solve_text(text: str):
    return route_text_input(text, allow_live_ai=False)


def _reason_code(out) -> str | None:
    env = (out.response or {}).get("envelope") or {}
    return env.get("reason_code")


def _assert_served_with_valid_scene3d(text: str, expected_answers: dict[str, str] | list[str]):
    out = _solve_text(text)
    assert out.status == "SERVED", (out.status, _reason_code(out), out.telemetry.to_dict(), out.response)
    assert out.telemetry.total_provider_calls == 0
    assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    env = out.response["envelope"]
    scene = env.get("scene3d")
    assert scene is not None and scene.get("objects"), "Missing Scene3D objects"
    assert validate_construction_continuity(scene) == []
    rd = out.response["route_d"]
    answers = rd["answers"]
    if isinstance(expected_answers, dict):
        assert answers == expected_answers
    else:
        assert sorted(answers.values()) == sorted(expected_answers)
    return out


# ── 1. Line-Plane Angle (30°, 45°, 60° & Vietnamese Wording Variants) ─────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("angle_deg", "expected_vol"),
    [
        # Base ABCD square side a, SA ⊥ (ABCD), ∠(SB, (ABCD)) = ∠SBA = α => SA = a·tan(α), V = (1/3)·a²·SA
        (30, "a³√3/9"),
        (45, "a³/3"),
        (60, "a³√3/3"),
    ],
)
def test_line_plane_angle_30_45_60_square_pyramid_volume_and_scene3d(angle_deg: int, expected_vol: str):
    text = (
        f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy "
        f"và cạnh bên SB tạo với mặt phẳng đáy một góc {angle_deg}°. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served_with_valid_scene3d(text, [expected_vol])


def test_line_plane_angle_diagonal_sc_and_wording_variants():
    # Diagonal projection AC = a√2; ∠(SC, (ABCD)) = 45° => SA = AC·tan(45°) = a√2 => V = a³√2/3
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD), "
        "góc giữa đường thẳng SC và mặt phẳng (ABCD) bằng 45°. "
        "Tính thể tích khối chóp S.ABCD và khoảng cách từ A đến mặt phẳng (SBD)."
    )
    # d(A, (SBD)): 1/d² = 1/SA² + 2/a² = 1/(2a²) + 2/a² = 5/(2a²) => d = a√10/5
    _assert_served_with_valid_scene3d(text, ["a³√2/3", "a√10/5"])


def test_line_plane_angle_with_midpoint_auxiliary_composition():
    # Base ABC equilateral side 2a, SA ⊥ (ABC), M midpoint of BC => AM = a√3.
    # SM hợp với đáy góc 30° => SA = AM·tan(30°) = a.
    # Base area = (2a)²√3/4 = a²√3 => V = (1/3)·a²√3·a = a³√3/3.
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA vuông góc với (ABC). "
        "Gọi M là trung điểm của BC. Biết đường thẳng SM hợp với mặt đáy một góc 30°. "
        "Tính thể tích khối chóp S.ABC."
    )
    _assert_served_with_valid_scene3d(text, ["a³√3/3"])


def test_line_plane_angle_right_prism_height_and_inverse_base_side():
    # 1) Derive prism height AA' from A'B tạo với mặt đáy (ABC) góc 60°: AA' = a√3 => V = 3a³/4.
    text_base = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a, "
        "đường thẳng A'B tạo với mặt phẳng (ABC) một góc 60°. Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    _assert_served_with_valid_scene3d(text_base, ["3a³/4"])

    # 2) Derive prism height AA' from A'B tạo với mặt bên (ACC'A') góc 30°: BH = a√3/2 => A'B = a√3 => AA' = a√2 => V = a³√6/4.
    text_lat = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a, "
        "góc giữa đường thẳng A'B và mặt phẳng (ACC'A') bằng 30°. Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    _assert_served_with_valid_scene3d(text_lat, ["a³√6/4"])

    # 3) Inverse base-side deduction when AA' = a√3 is given and ∠(BC', đáy) = 60° => BC = AA'·cot(60°) = a => V = a³√3/2.
    text_inv = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = a, AA' = a√3, "
        "góc giữa đường thẳng BC' với mặt phẳng đáy bằng 60°. Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    _assert_served_with_valid_scene3d(text_inv, ["a³√3/2"])


def test_equal_lateral_edge_angles_uniquely_places_foot_at_circumcenter():
    # S.ABC with ΔABC right at A, AB = 6, AC = 8 => BC = 10, circumradius R = 5 (midpoint of BC).
    # SA, SB, SC cùng tạo với đáy (ABC) góc 45° => foot F = circumcenter, h = R·tan(45°) = 5.
    # S_ABC = 24 => V = (1/3)·24·5 = 40.
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 6, AC = 8. "
        "Biết các cạnh bên SA, SB, SC cùng tạo với mặt phẳng đáy một góc 45°. "
        "Tính thể tích khối chóp S.ABC."
    )
    _assert_served_with_valid_scene3d(text, ["40"])


# ── 2. Unoriented Plane-Plane Angle vs Oriented Half-Plane Dihedral Angle (`Section 4.5`) ─────────────────────────────

def test_plane_plane_angle_lateral_face_to_base():
    # S.ABC equilateral base side 2a, SA ⊥ (ABC). Distance from A to BC is AH = a√3.
    # Mặt bên (SBC) hợp với đáy (ABC) góc 60° => SA = AH·tan(60°) = 3a => V = a³√3.
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA ⊥ (ABC). "
        "Mặt bên (SBC) hợp với mặt phẳng đáy (ABC) một góc 60°. Tính thể tích khối chóp S.ABC."
    )
    _assert_served_with_valid_scene3d(text, ["a³√3"])


def test_dihedral_angle_acute_vs_supplementary_obtuse_distinction():
    # Case 1 (Acute [S, BC, A] = 60° when foot A is on the A-side of BC): valid, V = a³√3.
    text_acute = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA ⊥ (ABC). "
        "Biết số đo góc nhị diện [S, BC, A] bằng 60°. Tính thể tích khối chóp S.ABC."
    )
    _assert_served_with_valid_scene3d(text_acute, ["a³√3"])

    # Case 2 (Contradictory obtuse [S, BC, A] = 120° when SA ⊥ (ABC) forces [S, BC, A] < 90°): MUST REFUSE!
    text_contradict_obtuse = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh 2a, SA ⊥ (ABC). "
        "Biết số đo góc nhị diện [S, BC, A] bằng 120°. Tính thể tích khối chóp S.ABC."
    )
    out_bad = _solve_text(text_contradict_obtuse)
    assert out_bad.status != "SERVED"
    assert _reason_code(out_bad) == "INCONSISTENT_FACTS"

    # Case 3 (Valid supplementary obtuse [S, BD, C] = 120° on square ABCD side 2a when SA ⊥ (ABCD):
    # A and C lie on opposite sides of BD; AO = a√2 => SA = AO·tan(60°) = a√6 => V = 4a³√6/3).
    text_valid_obtuse = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a, SA ⊥ (ABCD). "
        "Biết góc nhị diện [S, BD, C] bằng 120°. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served_with_valid_scene3d(text_valid_obtuse, ["4a³√6/3"])


def test_ambiguous_dihedral_without_selected_half_planes_fails_closed():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD), "
        "góc nhị diện cạnh BD bằng 60°. Tính thể tích khối chóp S.ABCD."
    )
    out = _solve_text(text)
    assert out.status != "SERVED"
    assert _reason_code(out) == "AMBIGUOUS_FACT"


# ── 3. Underdetermined Foot / Non-Unique Scene3D, Contradictions, Degeneracy & Invariance (`Section 4.4 & 4.6`) ──────

def test_angle_and_slant_length_without_foot_refuses_non_unique_scene3d():
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, cạnh bên SA = 2a "
        "và SA tạo với mặt phẳng đáy một góc 30°. Tính thể tích khối chóp S.ABC."
    )
    out = _solve_text(text)
    assert out.status != "SERVED"
    assert _reason_code(out) in ("UNDERDETERMINED_POINT", "AMBIGUOUS_FACT")


def test_two_contradictory_angle_premises_fail_closed():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD). "
        "Cạnh bên SB tạo với đáy một góc 45° và cạnh bên SD tạo với đáy một góc 60°. "
        "Tính thể tích khối chóp S.ABCD."
    )
    out = _solve_text(text)
    assert out.status != "SERVED"
    assert _reason_code(out) == "INCONSISTENT_FACTS"


def test_perpendicular_edge_claimed_oblique_angle_fails_closed():
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA ⊥ (ABC) "
        "và góc giữa SA và mặt phẳng (ABC) bằng 60°. Tính thể tích khối chóp S.ABC."
    )
    out = _solve_text(text)
    assert out.status != "SERVED"
    assert _reason_code(out) == "INCONSISTENT_FACTS"


def test_source_gate_blocks_tampered_angle_value_quote():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) "
        "và SB tạo với đáy một góc 60°. Tính thể tích khối chóp S.ABCD."
    )
    parsed = parse_geometry_problem_locally(text)
    assert parsed.status == LOCAL_PARSE_COMPLETE and parsed.payload is not None
    bad_payload = copy.deepcopy(parsed.payload)
    for prem in bad_payload["premises"]:
        if prem["kind"] == "line_plane_angle":
            prem["args"]["value"] = "30"
    res = run_typed_fact_next_v2_route(bad_payload)
    assert res.status == "REFUSED"
    assert res.code == "UNGROUNDED_VALUE"


def test_vertex_renaming_and_premise_reordering_invariance():
    text1 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 6, SA ⊥ (ABCD) "
        "và SB tạo với mặt phẳng (ABCD) một góc 60°. Tính thể tích khối chóp S.ABCD."
    )
    text2 = (
        "Cho hình chóp T.MNPQ. Biết cạnh bên TN hợp với mặt phẳng (MNPQ) một góc 60°, "
        "TM vuông góc với (MNPQ) và đáy MNPQ là hình vuông cạnh 6. Tính thể tích khối chóp T.MNPQ."
    )
    _assert_served_with_valid_scene3d(text1, ["72√3"])
    _assert_served_with_valid_scene3d(text2, ["72√3"])


def test_line_line_angle_and_irrational_degree_domain_refusal():
    # Line-line angle: S.ABCD square side a, SA ⊥ (ABCD), góc giữa SB và BC? Wait: BC ⊥ (SAB) => SB ⊥ BC (90°).
    # Instead: góc giữa SC và AB bằng 60°! Since AB // CD and CD ⊥ (SAD) is NOT true — wait:
    # Let's check ∠(SC, AB) in S.ABCD square side a, SA ⊥ (ABCD):
    # u = C - S = (1, 1, -1), v = B - A = (1, 0, 0).
    # g(u, v) = a², g(u, u) = 2a² + h², g(v, v) = a².
    # cos²(60°) = 1/4 = a⁴ / (a²(2a² + h²)) => 2a² + h² = 4a² => h² = 2a² => SA = a√2 => V = a³√2/3!
    text_ll = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) "
        "và góc giữa hai đường thẳng SC và AB bằng 60°. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served_with_valid_scene3d(text_ll, ["a³√2/3"])

    # Unsupported non-rational trigonometric degree (20°) -> EXACT_DOMAIN_EXCEEDED
    text_20 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA ⊥ (ABCD) "
        "và SB tạo với đáy một góc 20°. Tính thể tích khối chóp S.ABCD."
    )
    out_20 = _solve_text(text_20)
    assert out_20.status != "SERVED"
    assert _reason_code(out_20) == "EXACT_DOMAIN_EXCEEDED"


def test_two_apices_mirror_branch_same_vs_different_results():
    # Two pyramids S.ABCD and T.ABCD sharing square base ABCD side a, SA ⊥ (ABCD), TB ⊥ (ABCD),
    # ∠(SB, (ABCD)) = 45° => SA = a, ∠(TC, (ABCD)) = 45° => TB = a.
    # Asking volume of S.ABCD is invariant whether T is on same or opposite side => SERVED (a³/3).
    text_same = (
        "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD. Đáy ABCD là hình vuông cạnh a. "
        "Biết SA ⊥ (ABCD), TB ⊥ (ABCD), SB tạo với mặt phẳng (ABCD) một góc 45° "
        "và TC tạo với mặt phẳng (ABCD) một góc 45°. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served_with_valid_scene3d(text_same, ["a³/3"])

    # Asking length ST depends on whether S and T are on the same side (ST = a) or opposite sides (ST = a√5) => AMBIGUOUS_FACT!
    text_diff = (
        "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD. Đáy ABCD là hình vuông cạnh a. "
        "Biết SA ⊥ (ABCD), TB ⊥ (ABCD), SB tạo với mặt phẳng (ABCD) một góc 45° "
        "và TC tạo với mặt phẳng (ABCD) một góc 45°. Tính độ dài đoạn thẳng ST."
    )
    out_diff = _solve_text(text_diff)
    assert out_diff.status != "SERVED"
    assert _reason_code(out_diff) == "AMBIGUOUS_FACT"


def test_baseline_component_versions_and_provider_surface_preserved():
    assert registry.REGISTRY_VERSION == "geometry-functions/33"
    assert planner.PLANNER_VERSION == "geometry-fact-planner/26"
    assert engine.ENGINE_VERSION == "geometry-function-engine/24"
    assert len(registry.PROVIDER_FUNCTIONS) == 30
