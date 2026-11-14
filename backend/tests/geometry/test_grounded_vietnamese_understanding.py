# -*- coding: utf-8 -*-
"""Run `grounded-vietnamese-geometry-understanding`: Vietnamese source grounding without loosening the Source Gate.

Agent-written development texts (no dataset case id or exact problem text is used by the product):
- an unnamed base ("có đáy là hình vuông cạnh a") binds to the declared solid when no subject change precedes it;
- a face clause may close with a figure reference; a cuboid's notation span quotes its unnamed base;
- "góc giữa cạnh bên và mặt đáy" is one angle only in a regular pyramid;
- a prism notation written without its dot splits only when the top is the base primed in order;
- "tam giác XYZ cân" without its apex reads as the legs at a right angle another validated call proves;
- the area of the unnamed base is read; a premise value no item quotes is never silently dropped.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions import registry as R

SQ0 = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, "
FACE = "mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy"
DIST = "Tính khoảng cách từ A đến mặt phẳng (SBD)."


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _rd(text):
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def _served(text):
    rd = _rd(text)
    assert rd.get("status") == "SERVED", (text, rd.get("refusal"), rd.get("local_diagnostics"))
    return rd


# ── unnamed base, clause order ─────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text", [
    SQ0 + FACE + ". " + DIST,
    SQ0 + FACE + " (minh họa như hình vẽ bên). " + DIST,
])
def test_an_unnamed_base_before_a_face_clause_binds_its_side(text):
    assert _served(text)["answers"]["q1"] == "a√21/7"          # SAB equilateral ⊥ base: d(A,(SBD)) = a√21/7


def test_a_subject_change_before_the_unnamed_base_still_binds_nothing():
    assert _rd("Cho hình chóp S.ABCD, mặt bên SAB là tam giác đều có đáy là hình vuông cạnh a. " + DIST)["status"] != "SERVED"


def test_the_gate_reads_the_order_of_the_sentence():
    calls = R.doc_ke_hoach({"calls": [
        {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quotes": ["Cho hình chóp S.ABCD"]}},
        {"id": "p1", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "a"},
         "source": {"quotes": ["S.ABCD có đáy là hình vuông cạnh a"]}}]})
    before = "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, mặt bên SAB là tam giác đều"
    after = "Cho hình chóp S.ABCD, mặt bên SAB là tam giác đều, có đáy là hình vuông cạnh a"
    assert any(b[0] == "side" for b in R._lien_ket_cau(before, 0, len(before), calls).values())
    assert not any(b[0] == "side" for b in R._lien_ket_cau(after, 0, len(after), calls).values())


def test_a_cuboid_quotes_its_unnamed_square_base_from_its_notation():
    lp = parse_geometry_problem_locally("Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông, AB = 1, AA' = √6. "
                                        "Tính góc giữa đường thẳng CA' và mặt phẳng (ABCD).", use_cache=False)
    sq = [p for p in lp.payload["premises"] if p["kind"] == "regular_polygon"]
    assert [p["quote"] for p in sq] == ["ABCD.A'B'C'D' có đáy là hình vuông"]


# ── lateral edge goal ──────────────────────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("text, cos2", [
    ("Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng a, cạnh bên bằng 2a/3. Tính góc giữa cạnh bên và mặt đáy.", "3/4"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2 và cạnh bên bằng 2. Tính góc giữa cạnh bên và mặt phẳng đáy.", "1/2"),
    ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a và cạnh bên bằng 2a. Góc giữa cạnh bên và mặt đáy bằng", "1/8"),
])
def test_a_lateral_edge_angle_of_a_regular_pyramid_is_served(text, cos2):
    assert _served(text)["answer_exact"]["q1"]["coef"] == cos2


def test_a_lateral_edge_angle_of_a_pyramid_that_is_not_regular_is_ambiguous():
    rd = _rd("Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với đáy và SA = a. "
             "Tính góc giữa cạnh bên và mặt đáy.")
    assert rd["status"] != "SERVED" and (rd.get("refusal") or {}).get("code") == "AMBIGUOUS_FACT"


def test_the_gate_refuses_a_lateral_edge_angle_without_a_regular_pyramid():
    calls = R.doc_ke_hoach({"calls": [
        {"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
        {"id": "q1", "fn": "ask_angle_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
         "source": {"quotes": ["góc giữa cạnh bên và mặt đáy"]}}]})
    with pytest.raises(R.TuChoi) as e:
        R._kiem_canh_ben_dai_dien(next(c for c in calls if c.id == "q1"), "Tính góc giữa cạnh bên và mặt đáy.", calls)
    assert e.value.code == "SOURCE_OBJECT_MISMATCH"


# ── prism notation without its dot ─────────────────────────────────────────────────────────────────────────────────
def test_an_undotted_prism_notation_splits_only_into_base_and_primed_top():
    assert R._tach_lang_tru_lien([["A", "B", "C", "A'", "B'", "C'"]]) == [["A", "B", "C"], ["A'", "B'", "C'"]]
    assert R._tach_lang_tru_lien([["A", "B", "C", "B'", "A'", "C'"]]) == [["A", "B", "C", "B'", "A'", "C'"]]
    assert R._tach_lang_tru_lien([["A", "B", "C", "D"]]) == [["A", "B", "C", "D"]]
    assert R._tach_lang_tru_lien([["A", "B"], ["C", "D"]]) == [["A", "B"], ["C", "D"]]


@pytest.mark.parametrize("notation", ["ABCA'B'C'", "ABC.A'B'C'"])
def test_dotted_and_undotted_prisms_give_the_same_volume(notation):
    rd = _served(f"Cho lăng trụ đứng {notation} có đáy ABC là tam giác đều cạnh 2 và AA' = 3. Tính thể tích khối lăng trụ đã cho.")
    assert rd["answers"]["q1"] == "3√3"


def test_a_scrambled_undotted_notation_is_not_a_prism():
    assert _rd("Cho lăng trụ đứng ABCB'A'C' có đáy ABC là tam giác đều cạnh 2 và AA' = 3. "
               "Tính thể tích khối lăng trụ đã cho.")["status"] != "SERVED"


# ── isosceles triangle without its apex ────────────────────────────────────────────────────────────────────────────
RB = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân ở B, AB = a, SA vuông góc với mặt đáy (ABC) và "


def test_an_isosceles_triangle_right_at_a_proven_vertex_reads_its_legs():
    assert _served(RB + "tam giác SAB cân. Tính thể tích khối chóp S.ABC.")["answers"]["q1"] == "a³/6"
    lp = parse_geometry_problem_locally(RB + "tam giác SAB cân. Tính thể tích khối chóp S.ABC.", use_cache=False)
    eq = [p for p in lp.payload["premises"] if p["kind"] == "equal_length" and p["quote"] == "tam giác SAB cân"]
    assert len(eq) == 1 and {frozenset(eq[0]["args"]["segment_a"]), frozenset(eq[0]["args"]["segment_b"])} == {
        frozenset("AS"), frozenset("AB")}


def test_an_isosceles_triangle_without_a_proven_right_angle_stays_unread():
    rd = _rd(RB + "tam giác SBC cân. Tính thể tích khối chóp S.ABC.")
    assert rd["status"] != "SERVED"


def test_the_gate_grounds_the_legs_only_with_the_right_angle_call():
    base = [{"id": "s1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]}, "source": {"quotes": ["Cho hình chóp S.ABC"]}},
            {"id": "e1", "fn": "equal_length", "args": {"segment_a": ["A", "S"], "segment_b": ["A", "B"]},
             "source": {"quotes": ["tam giác SAB cân"]}}]
    perp = {"id": "p1", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
            "source": {"quotes": ["SA vuông góc với mặt đáy (ABC)"]}}
    calls = R.doc_ke_hoach({"calls": base + [perp]})
    eq = next(c for c in calls if c.id == "e1")
    assert R._can_co_goc_vuong(eq, calls) is True
    assert R._can_co_goc_vuong(eq, R.doc_ke_hoach({"calls": base})) is False
    wrong = R.doc_ke_hoach({"calls": [base[0], {**base[1], "args": {"segment_a": ["S", "A"], "segment_b": ["S", "B"]}}, perp]})
    assert R._can_co_goc_vuong(next(c for c in wrong if c.id == "e1"), wrong) is False   # legs at S: not the right angle


# ── base area and completeness ─────────────────────────────────────────────────────────────────────────────────────
def test_the_area_of_the_unnamed_base_is_read():
    assert _served("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3 và diện tích đáy bằng 4. "
                   "Tính thể tích khối chóp S.ABCD.")["answers"]["q1"] == "4√7/3"


@pytest.mark.parametrize("text", [
    "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3 và chu vi đáy bằng 8. Tính thể tích khối chóp S.ABCD.",
    "Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng a và diện tích đáy bằng a². Tính khoảng cách từ A đến mặt phẳng (SBC).",
])
def test_a_premise_value_no_item_reads_is_never_silently_dropped(text):
    lp = parse_geometry_problem_locally(text, use_cache=False)
    assert lp.status != "LOCAL_PARSE_COMPLETE" and lp.payload is None
    assert any(str(n).startswith("UNREAD_VALUE@") for c in lp.source_coverage.clauses for n in c.get("notes") or ())
    assert (_rd(text).get("local_diagnostics") or {}).get("root_cause") == "INCOMPLETE_FACT_EXTRACTION"


@pytest.mark.parametrize("text", [
    "Câu 12. Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
    "Tính thể tích khối chóp S.ABCD.",
    "Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy là hình vuông, AB = 1, AA' = √6 (tham khảo hình vẽ). "
    "Tính góc giữa đường thẳng CA' và mặt phẳng (ABCD).",
])
def test_exam_headers_and_figure_references_carry_no_premise_value(text):
    assert parse_geometry_problem_locally(text, use_cache=False).status == "LOCAL_PARSE_COMPLETE"
