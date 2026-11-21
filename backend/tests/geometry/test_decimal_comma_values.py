# -*- coding: utf-8 -*-
"""Run `certified-scale-cache-safety`: a Vietnamese decimal ("3,5") is one number.

The local parser's value grammar `_VAL` had no decimal form at all and deliberately refused to read "3" out of "3,5",
so "SA = 3,5" left an unbacked "=" and the sentence unparsed. The contract (`NUMBER_PATTERN`) and the Source Gate
(`_SO`, `doc_so`) already read decimals with either separator; only the parser lacked them.
"""
from __future__ import annotations

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import _subclause_spans

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {a}, SA vuông góc với mặt phẳng đáy và SA = {h}. Tính khoảng cách từ A đến mặt phẳng (SBC)."


@pytest.fixture(autouse=True)
def _offline(monkeypatch):
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "")


def _answers(text):
    rd = (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}
    return rd.get("status"), rd.get("answer_exact")


def test_decimal_comma_decimal_point_and_fraction_are_the_same_number():
    got = {h: _answers(P.format(a="2", h=h)) for h in ("3,5", "3.5", "7/2")}
    assert {s for s, _ in got.values()} == {"SERVED"}
    assert len({str(e) for _s, e in got.values()}) == 1          # 7/(√65/2) = 14√65/65 in every spelling


def test_a_decimal_side_is_read():
    assert _answers(P.format(a="1,5", h="2")) == _answers(P.format(a="3/2", h="2"))


def test_a_list_separated_by_comma_and_space_is_not_a_decimal():
    text = ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, SA vuông góc với mặt phẳng (ABC) "
            "và SA = 2. Tính khoảng cách từ A đến mặt phẳng (SBC).")
    status, exact = _answers(text)
    assert status == "SERVED" and exact["q1"]["coef"] == "12√61/61"     # AB = 3 and AC = 4, not 3,4
    parts = [text[a:b].strip() for a, b in _subclause_spans(text, 0, text.index(". Tính"))]
    assert "AB = 3" in parts and "AC = 4" in parts


@pytest.mark.parametrize("h", ["3,5,6", "≈ 3,5", "3,"])
def test_malformed_or_approximate_decimals_are_refused(h):
    text = P.format(a="2", h=h).replace("SA = ≈", "SA ≈")
    assert _answers(text)[0] != "SERVED"


def test_renaming_keeps_the_decimal_reading():
    renamed = P.format(a="2", h="3,5").replace("S.ABCD", "T.EFGH").replace("ABCD", "EFGH").replace("SA", "TE") \
        .replace("từ A", "từ E").replace("(SBC)", "(TFG)")
    assert _answers(renamed) == _answers(P.format(a="2", h="3,5"))


def test_a_decimal_leg_of_a_right_prism_base_is_read_not_called_corrupt():
    """Formerly a 'numeric corruption' case of test_correctness_ocr_performance; V = ½ · 3,5 · 4 · 5 = 35."""
    status, exact = _answers("Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3,5, AC = 4, "
                             "AA' = 5. Tính thể tích khối lăng trụ ABC.A'B'C'.")
    assert status == "SERVED" and exact["q1"]["coef"] == "35"
