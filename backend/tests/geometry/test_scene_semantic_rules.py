# -*- coding: utf-8 -*-
"""semantic-to-scene3d-verified-simulation — three general local-parser rules that let existing constructions run.

R1  projection image named in place by a descriptor ("… trùng với trọng tâm G của tam giác ABC", "… là trung điểm H của
    cạnh AB") → centroid / midpoint + orthogonal_projection, each with its own quote;
R2  a lateral face perpendicular to the base ("tam giác SAB đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy",
    "(SAB) ⊥ (ABCD)") → face_perpendicular_base, plus an equilateral LATERAL face;
R3  a regular base polygon without a side whose side or diagonal is given later by a length of its own vertices.
Answers are hand-derived (comments); counterexamples must stay unserved. No AI call.
"""
from __future__ import annotations

import os

import pytest

from app.ai.adaptive_input_router import route_text_input

os.environ.setdefault("ALLOW_LIVE_AI", "0")


def _run(text: str) -> tuple[str | None, dict | None, dict]:
    r = route_text_input(text, allow_live_ai=False).response
    rd = r.get("route_d") or {}
    return rd.get("status"), rd.get("answers"), r


@pytest.mark.parametrize("text,answer", [
    # SG² = SA² − GA² = 4a² − a²/3 = 11a²/3; V = ⅓·(√3/4)a²·a√(11/3) = a³√11/12
    ("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với "
     "trọng tâm G của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC.", "a³√11/12"),
    # foot H = midpoint of AB, SH = a, base 4a² ⇒ V = 4a³/3 (facts in separate sentences)
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2a. Hình chiếu vuông góc của S lên mặt phẳng đáy là trung "
     "điểm H của cạnh AB, SH = a. Tính thể tích khối chóp S.ABCD.", "4a³/3"),
])
def test_r1_projection_onto_a_named_descriptor_point(text, answer):
    status, answers, r = _run(text)
    assert status == "SERVED" and answers == {"q1": answer}
    objs = r["envelope"]["scene3d"]["objects"]
    assert any(o["type"] == "point3" and o.get("origin") != "free" for o in objs)          # the foot is constructed
    assert any(o.get("perpendicular_witness") for o in objs)                                 # the height is certified


def test_r1_unnamed_descriptor_is_not_given_an_invented_label():
    from app.ai.local_geometry_parser import parse_geometry_problem_locally

    text = ("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên mặt phẳng "
            "(ABC) trùng với trọng tâm của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC.")
    parsed = parse_geometry_problem_locally(text)
    assert any(
        p.get("kind") == "orthogonal_projection" and str((p.get("args") or {}).get("image") or "").startswith("@")
        for p in (parsed.payload.get("premises") or [])
    )
    status, answers, r = _run(text)
    assert status == "SERVED" and answers == {"q1": "a³√11/12"}
    assert r["route_d"]["planner"]["auxiliary"][0]["chain"][0]["fresh"] is True

    unsupported = ("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên mặt phẳng "
                   "(ABC) trùng với tâm đường tròn nội tiếp của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC.")
    u_status, _, _ = _run(unsupported)
    assert u_status != "SERVED"


@pytest.mark.parametrize("text,answer", [
    # H midpoint of AB, SH = a√3/2 ⟂ base ⇒ V = ⅓·a²·a√3/2 = a³√3/6
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng vuông góc với "
     "mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.", "a³√3/6"),
    # AB ∥ (SCD) ⇒ d(A,(SCD)) = d(H,(SCD)) = SH·HM/√(SH²+HM²) = (a√3/2·a)/(a√7/2) = a√21/7
    ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Mặt bên SAB là tam giác đều và (SAB) ⊥ (ABCD). "
     "Tính khoảng cách từ A đến mặt phẳng (SCD).", "a√21/7"),
])
def test_r2_lateral_face_perpendicular_to_the_base(text, answer):
    status, answers, _ = _run(text)
    assert status == "SERVED" and answers == {"q1": answer}


@pytest.mark.parametrize("text", [
    # the plane named is not the base: the old guard still holds
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, mặt bên SAB nằm trong mặt phẳng vuông góc với mặt phẳng (SCD). "
    "Tính thể tích khối chóp S.ABCD.",
    # negation is never read as perpendicularity
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và (SAB) không vuông góc với (ABCD). "
    "Tính thể tích khối chóp S.ABCD.",
    # a face that is not a face of the declared solid
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, (SXY) ⊥ (ABCD), SA = a. Tính thể tích khối chóp S.ABCD.",
])
def test_r2_counterexamples_are_not_served(text):
    status, _, _ = _run(text)
    assert status != "SERVED"


@pytest.mark.parametrize("ab,answer", [("1", "2/3"), ("2", "2√3/3")])
def test_r3_square_side_given_by_a_later_length(ab, answer):
    # 1/d² = 1/SA² + 1/AB² + 1/AD² ; d(C,(SBD)) = d(A,(SBD)) by symmetry in BD. AB=1: 1+1+¼ ⇒ ⅔; AB=2: ¾ ⇒ 2/√3
    status, answers, _ = _run(f"Cho hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD là hình vuông, biết AB = {ab}, SA = 2. "
                              "Tính khoảng cách từ điểm C đến mặt phẳng (SBD).")
    assert status == "SERVED" and answers == {"q1": answer}


def test_r3_without_a_length_of_the_polygon_still_asks():
    status, _, r = _run("Cho hình chóp S.ABCD có SA ⊥ (ABCD), đáy ABCD là hình vuông, biết SA = 2. "
                        "Tính khoảng cách từ điểm C đến mặt phẳng (SBD).")
    assert status != "SERVED"
