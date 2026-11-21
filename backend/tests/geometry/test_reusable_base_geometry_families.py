# -*- coding: utf-8 -*-
"""Gate 2 TDD suite: Reusable Base Geometry Expansion (`CURRICULUM-FAMILY-1` & `CURRICULUM-FAMILY-2`, Section V).

Strictly distinct from `DEV72-G2` and `DEV72-G3`.
Tests positive, negative, missing-data, contradictory, vertex-renamed, paraphrased, multi-goal,
and Gate-1 angle-premise composed cases across:
  - FAMILY-1: Right trapezoid, Isosceles trapezoid, Isosceles triangle, Triangle altitude.
  - FAMILY-2: Rhombus (side + named angle 60°/120°, two diagonals, side + diagonal; NEVER assuming 60° on bare rhombus),
              Parallelogram (sides + angle or diagonal), Triangle SAS (30°/45°/60°/90°/120°/135°/150°).
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity


def _solve_text(text: str):
    return route_text_input(text, allow_live_ai=False)


def _reason_code(out) -> str | None:
    return ((out.response or {}).get("envelope") or {}).get("reason_code")


def _assert_served(text: str, expected_answers: list[str]):
    out = _solve_text(text)
    assert out.status == "SERVED", (out.status, _reason_code(out), out.telemetry.to_dict(), out.response)
    assert out.telemetry.total_provider_calls == 0
    assert out.telemetry.local_parse_status == LOCAL_PARSE_COMPLETE
    scene = out.response["envelope"].get("scene3d")
    assert scene is not None and scene.get("objects")
    assert validate_construction_continuity(scene) == []
    answers = out.response["route_d"]["answers"]
    assert sorted(answers.values()) == sorted(expected_answers)
    return out


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# CURRICULUM-FAMILY-1: Right Trapezoid, Isosceles Trapezoid, Isosceles Triangle & Triangle Altitude
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


def test_family1_right_trapezoid_positive_oblique_derivation_paraphrase_and_angle_composition():
    # 1) Direct bases + perpendicular leg + multi-goal (V and SC)
    t1 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, "
        "AD = 2a, BC = a, AB = a, SA vuông góc với mặt phẳng đáy và SA = a√3. "
        "Tính thể tích khối chóp S.ABCD và độ dài đoạn thẳng SC."
    )
    _assert_served(t1, ["a³√3/2", "a√5"])

    # 2) Derive perpendicular leg AB from parallel bases AD = 3a, BC = a and oblique leg CD = 2a√2 => AB = 2a, S = 4a², V = 4a³
    t2 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, "
        "AD = 3a, BC = a, CD = 2a√2, SA ⊥ (ABCD) và SA = 3a. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t2, ["4a³"])

    # 3) Paraphrase with explicit parallel bases + single right angle + Gate 1 angle premise (SC tạo với đáy góc 45°)
    t3 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang có AD song song với BC, góc DAB bằng 90°, "
        "AD = 2a, BC = a, AB = a, SA ⊥ (ABCD) và SC tạo với mặt phẳng đáy một góc 45°. "
        "Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t3, ["a³√2/2"])

    # 4) Renamed vertices (P.MNPQ vuông tại M và N)
    t4 = (
        "Cho hình chóp K.MNPQ có đáy MNPQ là hình thang vuông tại M và N, "
        "MQ = 4, NP = 2, MN = 3, KM ⊥ (MNPQ) và KM = 5. Tính thể tích khối chóp K.MNPQ."
    )
    _assert_served(t4, ["15"])


def test_family1_right_trapezoid_missing_and_contradictory_fail_closed():
    # Missing second base BC
    t_miss = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, "
        "AD = 2a, AB = a, SA ⊥ (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    out_miss = _solve_text(t_miss)
    assert out_miss.status != "SERVED"
    assert _reason_code(out_miss) == "MISSING_DIMENSION"

    # Contradictory oblique leg CD = a < |AD - BC| = 2a
    t_bad = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, "
        "AD = 3a, BC = a, CD = a, SA ⊥ (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    out_bad = _solve_text(t_bad)
    assert out_bad.status != "SERVED"
    assert _reason_code(out_bad) == "INCONSISTENT_FACTS"


def test_family1_isosceles_trapezoid_legs_and_base_angle_positive_and_negative():
    # 1) Isosceles trapezoid with bases AD = 4a, BC = 2a (AD // BC) and leg AB = a√5 => trap height = 2a, S = 6a², V = 6a³
    t1 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang cân với hai đáy AD và BC, "
        "AD = 4a, BC = 2a, AB = a√5, SA ⊥ (ABCD) và SA = 3a. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t1, ["6a³"])

    # 2) Isosceles trapezoid with bases AB = 3a, CD = a (AB // CD) and base angle ∠DAB = 60° on right prism AA' = 2a
    # => leg AD = 2a, trap height = a√3, S = 2a²√3 => V = 4a³√3
    t2 = (
        "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình thang cân có hai đáy AB và CD, "
        "AB = 3a, CD = a, góc DAB bằng 60° và AA' = 2a. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
    )
    _assert_served(t2, ["4a³√3"])

    # 3) Missing leg/angle on isosceles trapezoid -> MISSING_DIMENSION
    t_miss = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang cân có hai đáy AB và CD, "
        "AB = 3a, CD = a, SA ⊥ (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD."
    )
    out_miss = _solve_text(t_miss)
    assert out_miss.status != "SERVED"
    assert _reason_code(out_miss) == "MISSING_DIMENSION"

    # 4) Contradictory unequal legs AD = a, BC = 2a on isosceles trapezoid with bases AB // CD -> INCONSISTENT_FACTS
    t_bad = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang cân có hai đáy AB và CD, "
        "AB = 3a, CD = a, AD = a, BC = 2a, SA ⊥ (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD."
    )
    out_bad = _solve_text(t_bad)
    assert out_bad.status != "SERVED"
    assert _reason_code(out_bad) == "INCONSISTENT_FACTS"


def test_family1_isosceles_triangle_and_triangle_altitude():
    # 1) Isosceles triangle cân tại A: AB = 5a, BC = 6a => AC = 5a, h_A = 4a, S = 12a², SA = 2a => V = 8a³
    t1 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A, AB = 5a, BC = 6a, "
        "SA ⊥ (ABC) và SA = 2a. Tính thể tích khối chóp S.ABC."
    )
    _assert_served(t1, ["8a³"])

    # 2) Isosceles triangle cân tại A with base BC = 6a and named triangle altitude đường cao AH = 4a,
    #    combined with Gate 1 angle premise ∠(SB, (ABC)) = 45° => AB = 5a => SA = 5a => V = 20a³
    t2 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A, BC = 6a, đường cao AH của tam giác ABC bằng 4a, "
        "SA ⊥ (ABC) và cạnh bên SB tạo với mặt phẳng đáy một góc 45°. Tính thể tích khối chóp S.ABC."
    )
    _assert_served(t2, ["20a³"])

    # 3) Missing leg/altitude on isosceles triangle -> MISSING_DIMENSION
    t_miss = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A, BC = 6a, "
        "SA ⊥ (ABC) và SA = 2a. Tính thể tích khối chóp S.ABC."
    )
    out_miss = _solve_text(t_miss)
    assert out_miss.status != "SERVED"
    assert _reason_code(out_miss) == "MISSING_DIMENSION"

    # 4) Contradictory triangle inequality AB = 2a, BC = 5a on tam giác cân tại A -> INCONSISTENT_FACTS
    t_bad = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác cân tại A, AB = 2a, BC = 5a, "
        "SA ⊥ (ABC) và SA = 2a. Tính thể tích khối chóp S.ABC."
    )
    out_bad = _solve_text(t_bad)
    assert out_bad.status != "SERVED"
    assert _reason_code(out_bad) == "INCONSISTENT_FACTS"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# CURRICULUM-FAMILY-2: Rhombus, Parallelogram & Triangle SAS
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════


def test_family2_rhombus_angle_diagonals_and_strict_no_default_60_assumption():
    # 1) Rhombus side a + acute ∠BAD = 60°, SA ⊥ (ABCD), SA = a => S = a²√3/2 => V = a³√3/6, BD = a
    t1 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a, góc BAD bằng 60°, "
        "SA ⊥ (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD và độ dài đoạn thẳng BD."
    )
    _assert_served(t1, ["a³√3/6", "a"])

    # 2) Rhombus side a + obtuse ∠ABC = 120° + Gate 1 angle ∠(SC, (ABCD)) = 60°:
    # ∠BAD = 60° => AC = a√3 => SA = AC·tan(60°) = 3a => V = (1/3)·(a²√3/2)·3a = a³√3/2
    t2 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a, góc ABC bằng 120°, "
        "SA ⊥ (ABCD) và SC hợp với mặt phẳng đáy một góc 60°. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t2, ["a³√3/2"])

    # 3) Rhombus given by two diagonals AC = 2a, BD = 4a, O = AC ∩ BD, SO ⊥ (ABCD), SO = 3a => S = 4a², V = 4a³
    t3 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi có AC = 2a, BD = 4a. "
        "Gọi O là giao điểm của AC và BD. Biết SO ⊥ (ABCD) và SO = 3a. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t3, ["4a³"])

    # 4) Bare `hình thoi cạnh a` WITHOUT angle or diagonal MUST NEVER assume 60° -> MISSING_DIMENSION!
    t_bare = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a, SA ⊥ (ABCD) và SA = a. "
        "Tính thể tích khối chóp S.ABCD."
    )
    out_bare = _solve_text(t_bare)
    assert out_bare.status != "SERVED"
    assert _reason_code(out_bare) == "MISSING_DIMENSION"

    # 5) Unnamed vertex angle ("có một góc bằng 60°") on rhombus when asking SC -> AMBIGUOUS_FACT!
    t_ambig = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a có một góc bằng 60°, "
        "SA ⊥ (ABCD) và SA = a. Tính độ dài đoạn thẳng SC."
    )
    out_ambig = _solve_text(t_ambig)
    assert out_ambig.status != "SERVED"
    assert _reason_code(out_ambig) == "AMBIGUOUS_FACT"

    # 6) Contradictory diagonal AC = 3a on rhombus of side a (AC > 2a) -> INCONSISTENT_FACTS
    t_bad = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thoi cạnh a, AC = 3a, "
        "SA ⊥ (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    out_bad = _solve_text(t_bad)
    assert out_bad.status != "SERVED"
    assert _reason_code(out_bad) == "INCONSISTENT_FACTS"


def test_family2_parallelogram_sides_angle_and_diagonal():
    # 1) Parallelogram AB = a, AD = 2a, ∠BAD = 60° on right prism AA' = a√3 => S = a²√3, V = 3a³, BD = a√3
    t1 = (
        "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình bình hành, "
        "AB = a, AD = 2a, góc BAD bằng 60° và AA' = a√3. "
        "Tính thể tích khối lăng trụ ABCD.A'B'C'D' và độ dài đoạn thẳng BD."
    )
    _assert_served(t1, ["3a³", "a√3"])

    # 2) Parallelogram AB = 3a, AD = 4a, diagonal BD = 5a, SA ⊥ (ABCD), SA = 2a => S = 12a², V = 8a³
    t2 = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành, AB = 3a, AD = 4a, BD = 5a, "
        "SA ⊥ (ABCD) và SA = 2a. Tính thể tích khối chóp S.ABCD."
    )
    _assert_served(t2, ["8a³"])

    # 3) Missing angle/diagonal on parallelogram -> MISSING_DIMENSION
    t_miss = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành, AB = a, AD = 2a, "
        "SA ⊥ (ABCD) và SA = a. Tính thể tích khối chóp S.ABCD."
    )
    out_miss = _solve_text(t_miss)
    assert out_miss.status != "SERVED"
    assert _reason_code(out_miss) == "MISSING_DIMENSION"


def test_family2_triangle_sas_acute_obtuse_45_and_irrational_gram_refusal():
    # 1) SAS 60° + Gate 1 angle: AB = a, AC = 2a, ∠BAC = 60°, SA ⊥ (ABC), ∠(SB, (ABC)) = 45° => SA = a, BC = a√3, V = a³√3/6
    t1 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác có AB = a, AC = 2a, góc BAC bằng 60°, "
        "SA ⊥ (ABC) và SB tạo với mặt phẳng đáy một góc 45°. "
        "Tính thể tích khối chóp S.ABC và độ dài đoạn thẳng BC."
    )
    _assert_served(t1, ["a³√3/6", "a√3"])

    # 2) Obtuse SAS 120°: AB = a, AC = a, ∠BAC = 120°, SA ⊥ (ABC), SA = a√3 => S = a²√3/4, V = a³/4
    t2 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác có AB = a, AC = a, góc BAC bằng 120°, "
        "SA ⊥ (ABC) và SA = a√3. Tính thể tích khối chóp S.ABC."
    )
    _assert_served(t2, ["a³/4"])

    # 3) SAS 45° with rational Gram product: AB = a√2, AC = 2a, ∠BAC = 45°, SA ⊥ (ABC), SA = 3a => S = a², V = a³
    t3 = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác có AB = a√2, AC = 2a, góc BAC bằng 45°, "
        "SA ⊥ (ABC) và SA = 3a. Tính thể tích khối chóp S.ABC."
    )
    _assert_served(t3, ["a³"])

    # 4) Irrational Gram entry (AB = a, AC = a, ∠BAC = 45° => BC² = (2 - √2)a² ∉ ℚ) -> EXACT_DOMAIN_EXCEEDED
    t_irr = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác có AB = a, AC = a, góc BAC bằng 45°, "
        "SA ⊥ (ABC) và SA = a. Tính thể tích khối chóp S.ABC."
    )
    out_irr = _solve_text(t_irr)
    assert out_irr.status != "SERVED"
    assert _reason_code(out_irr) == "EXACT_DOMAIN_EXCEEDED"
