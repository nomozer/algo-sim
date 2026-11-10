# -*- coding: utf-8 -*-
"""Phase 3 (Gate C) — Reusable Geometry Gap Closure Tests (`ext04`, `ext05`, `ext06` + Variants & Refusals).

Covers:
1. Family A (`ext04`): Affine length ratios (`KC/KB`) with parallel cutting planes (`MAT_HAI_DUONG`) on metric-free
   trapezoid bases with parallel base ratio (`AD = 2BC`, `AD = 3BC`).
2. Family B (`ext05`): Coplanar / parallel-plane polygon area ratios (`S1/S2`) on metric-free parallelogram bases
   with line-plane intersections (`(SAD) ∩ ME = I`).
3. Family C (`ext06`): Inverse base-edge deduction (`CA = CB = 2a`) from right-prism lateral-face `line_plane_angle`
   (`BC'` with `(ABB'A')`) + compound heterogeneous goals (`volume` and `skew_line_distance`).
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally


EXT04_VERBATIM = (
    "Câu 6. Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC và AD = 2BC. "
    "Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. "
    "Gọi K là giao điểm của BC với (P). Khi đó tính tỉ số KC/KB."
)

EXT05_VERBATIM = (
    "Câu 24: (2,5 điểm) Cho hình chóp S.ABCD có đáy ABCD là hình bình hành tâm O. "
    "M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. "
    "Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I. "
    "Gọi S1; S2 lần lượt là diện tích tam giác SMI và tứ giác BCEM. Tính S1/S2."
)

EXT06_VERBATIM = (
    "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = a. "
    "Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°. "
    "Gọi M, N, P lần lượt là trung điểm của các cạnh BB', CC' và BC. "
    "Tính thể tích khối lăng trụ ABC.A'B'C' và khoảng cách giữa hai đường thẳng AM và NP theo a."
)


# ── 1. Family A: Affine Length Ratio (`ext04` + Variants + Refusals) ────────────────────────────────────────────────


def test_ext04_verbatim_serves_exact_affine_length_ratio():
    res = parse_geometry_problem_locally(EXT04_VERBATIM)
    assert res.status == LOCAL_PARSE_COMPLETE, res.to_dict()

    out = route_text_input(EXT04_VERBATIM, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    rd = out.response["route_d"]
    assert rd["answers"]["q1"] == "1/2"
    assert rd["answer_exact"]["q1"]["coef"] == "1/2"
    assert rd["scene_configuration"]["kind"] == "HEIGHT_INVARIANT_ILLUSTRATIVE"


@pytest.mark.parametrize(
    "text,expected_ratio",
    [
        (
            "Cho hình chóp T.MNPQ có đáy MNPQ là hình thang với MQ song song NP và MQ = 2NP. "
            "Gọi E là trung điểm cạnh MQ. Mặt phẳng (Q) qua E và song song với hai đường thẳng TM, TP. "
            "Gọi F là giao điểm của NP với (Q). Khi đó tính tỉ số FP/FN.",
            "1/2",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC và AD = 3BC. "
            "Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. "
            "Gọi K là giao điểm của BC với (P). Tính tỉ số KC/KB.",
            "3/5",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC và AD = 2BC. "
            "Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. "
            "Gọi K là giao điểm của BC với (P). Tính tỉ số KB/KC.",
            "2",
        ),
    ],
)
def test_ext04_renamed_scaled_and_reciprocal_variants_serve(text: str, expected_ratio: str):
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    assert out.response["route_d"]["answers"]["q1"] == expected_ratio


def test_ext04_missing_base_ratio_refuses_missing_dimension():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC. "
        "Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. "
        "Gọi K là giao điểm của BC với (P). Tính tỉ số KC/KB."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED"
    assert out.response["route_d"]["refusal"]["code"] == "MISSING_DIMENSION"


def test_ext04_non_collinear_segment_ratio_on_metric_free_base_refuses_missing_dimension():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang với AD song song BC và AD = 2BC. "
        "Gọi I là trung điểm cạnh AD. Mặt phẳng (P) qua I và song song với hai đường thẳng SA, SC. "
        "Gọi K là giao điểm của BC với (P). Tính tỉ số KC/AB."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED"
    assert out.response["route_d"]["refusal"]["code"] == "MISSING_DIMENSION"


# ── 2. Family B: Coplanar / Parallel-Plane Polygon Area Ratio (`ext05` + Variants + Refusals) ───────────────────────


def test_ext05_verbatim_serves_exact_polygon_area_ratio():
    res = parse_geometry_problem_locally(EXT05_VERBATIM)
    assert res.status == LOCAL_PARSE_COMPLETE, res.to_dict()

    out = route_text_input(EXT05_VERBATIM, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    rd = out.response["route_d"]
    assert rd["answers"]["q1"] == "6/5"
    assert rd["answer_exact"]["q1"]["coef"] == "6/5"
    assert rd["scene_configuration"]["kind"] == "HEIGHT_INVARIANT_ILLUSTRATIVE"


@pytest.mark.parametrize(
    "text,expected_ratio",
    [
        (
            "Cho hình chóp T.EFGH có đáy EFGH là hình bình hành tâm O. "
            "K là trung điểm của TF. Gọi L là điểm thuộc cạnh TG sao cho TL = 3LG. "
            "Mặt phẳng (TEH) và đường thẳng KL cắt nhau tại J. "
            "Gọi S1; S2 lần lượt là diện tích tam giác TKJ và tứ giác FGLK. Tính S1/S2.",
            "6/5",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. "
            "M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 2EC. "
            "Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I. "
            "Gọi S1; S2 lần lượt là diện tích tam giác SMI và tứ giác BCEM. Tính S1/S2.",
            "3/2",
        ),
        (
            "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành tâm O. "
            "M là trung điểm của SB. Gọi E là điểm thuộc cạnh SC sao cho SE = 3EC. "
            "Mặt phẳng (SAD) và đường thẳng ME cắt nhau tại I. "
            "Tính tỉ số diện tích tam giác SMI và tứ giác BCEM.",
            "6/5",
        ),
    ],
)
def test_ext05_renamed_scaled_and_paraphrased_variants_serve(text: str, expected_ratio: str):
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    assert out.response["route_d"]["answers"]["q1"] == expected_ratio


def test_ext05_non_coplanar_area_ratio_on_metric_free_parallelogram_refuses():
    text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình bình hành. "
        "Gọi S1; S2 lần lượt là diện tích tam giác SAB và tam giác SBC. Tính S1/S2."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED"
    assert out.response["route_d"]["refusal"]["code"] == "MISSING_DIMENSION"


# ── 3. Family C: Inverse Base Dimension from Lateral Angle + Compound Goals (`ext06` + Variants + Refusals) ─────────


def test_ext06_verbatim_serves_both_compound_goals_exactly():
    res = parse_geometry_problem_locally(EXT06_VERBATIM)
    assert res.status == LOCAL_PARSE_COMPLETE, res.to_dict()

    out = route_text_input(EXT06_VERBATIM, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    rd = out.response["route_d"]
    assert rd["answers"] == {"q1": "a³√15/4", "q2": "a√15/5"}
    assert rd["answer_exact"]["q1"]["coef"] == "√15/4"
    assert rd["answer_exact"]["q2"]["coef"] == "√15/5"


@pytest.mark.parametrize(
    "text,expected_answers",
    [
        (
            "Cho hình lăng trụ đứng DEF.D'E'F' có đáy DEF là tam giác cân tại F, DE = DD' = a. "
            "Góc tạo bởi đường thẳng EF' với mặt phẳng (DEE'D') bằng 60°. "
            "Gọi H, K, L lần lượt là trung điểm của các cạnh EE', FF' và EF. "
            "Tính thể tích khối lăng trụ DEF.D'E'F' và khoảng cách giữa hai đường thẳng DH và KL theo a.",
            {"q1": "a³√15/4", "q2": "a√15/5"},
        ),
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = 2. "
            "Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°. "
            "Tính thể tích khối lăng trụ ABC.A'B'C'.",
            {"q1": "2√15"},
        ),
        (
            "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = AA' = a. "
            "Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 45°. "
            "Tính thể tích khối lăng trụ ABC.A'B'C' theo a.",
            {"q1": "a³√5/4"},
        ),
    ],
)
def test_ext06_renamed_scaled_and_angle_variants_serve(text: str, expected_answers: dict[str, str]):
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "SERVED", out.response
    assert out.telemetry.total_provider_calls == 0
    assert out.response["route_d"]["answers"] == expected_answers


def test_ext06_missing_prism_height_refuses_missing_dimension():
    text = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác cân tại C, AB = a. "
        "Góc tạo bởi đường thẳng BC' với mặt phẳng (ABB'A') bằng 60°. "
        "Tính thể tích khối lăng trụ ABC.A'B'C' theo a."
    )
    out = route_text_input(text, allow_live_ai=False)
    assert out.status == "REFUSED"
    assert out.response["route_d"]["refusal"]["code"] == "MISSING_DIMENSION"
