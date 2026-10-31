# -*- coding: utf-8 -*-
"""Route D (/4) Source Gate role-phrase parity tests without 'của' before explicit solid nouns."""
from __future__ import annotations

from app.ai.adapter4_route import run_typed_fact_next_v2_route


def _pyramid_height_payload(hq: str) -> dict:
    text = f"Cho hình chóp tứ giác đều S.ABCD có đáy ABCD là hình vuông cạnh 3, {hq}. Tính thể tích khối chóp S.ABCD."
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "regular_pyramid",
                "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
                "solid_id": "s1",
            },
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "3"},
                "quote": "có đáy ABCD là hình vuông cạnh 3",
                "solid_id": "s1",
            },
            {
                "kind": "height",
                "args": {"value": "4", "solid": "s1"},
                "quote": hq,
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp tứ giác đều S.ABCD"}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": "Tính thể tích khối chóp S.ABCD",
            }
        ],
    }


def test_role_phrase_height_without_cua_serves_matching_pyramid() -> None:
    for phrase in (
        "chiều cao hình chóp bằng 4",
        "chiều cao khối chóp bằng 4",
        "chiều cao hình chóp S.ABCD bằng 4",
        "đường cao hình chóp bằng 4",
    ):
        res = run_typed_fact_next_v2_route(_pyramid_height_payload(phrase))
        assert res.status == "SERVED", (phrase, res.code, res.reason)
        assert list(res.answers.values()) == ["12"], phrase


def test_role_phrase_without_cua_refuses_mismatched_solid_kind_or_label() -> None:
    r_kind = run_typed_fact_next_v2_route(_pyramid_height_payload("chiều cao khối lăng trụ bằng 4"))
    assert r_kind.status == "REFUSED" and r_kind.code == "UNGROUNDED_VALUE"

    r_label = run_typed_fact_next_v2_route(_pyramid_height_payload("chiều cao hình chóp T.ABCD bằng 4"))
    assert r_label.status == "REFUSED" and r_label.code in ("UNGROUNDED_VALUE", "UNKNOWN_LABEL")


def test_role_phrase_lateral_edge_without_cua_serves_prism() -> None:
    text = (
        "Cho hình lăng trụ tam giác đều ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, "
        "cạnh bên hình lăng trụ bằng 3. Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho hình lăng trụ tam giác đều ABC.A'B'C'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                "quote": "Cho hình lăng trụ tam giác đều ABC.A'B'C'",
                "solid_id": "s1",
            },
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C"], "side": "2"},
                "quote": "có đáy ABC là tam giác đều cạnh 2",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "A'"], "value": "3"},
                "quote": "cạnh bên hình lăng trụ bằng 3",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ tam giác đều ABC.A'B'C'"}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": "Tính thể tích khối lăng trụ ABC.A'B'C'",
            }
        ],
    }
    res = run_typed_fact_next_v2_route(payload)
    assert res.status == "SERVED", (res.code, res.reason)
    assert list(res.answers.values()) == ["3√3"]


def test_role_phrase_without_cua_refuses_incompatible_prism_subclasses() -> None:
    """Round 1 MAJOR-1: cube/box role phrases without 'của' must not bind onto a triangular or non-matching prism."""
    for bad_phrase in (
        "chiều cao hình lập phương bằng 4",
        "chiều cao hình hộp chữ nhật bằng 4",
        "chiều cao hình hộp bằng 4",
    ):
        text = (
            f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, "
            f"{bad_phrase}. Tính thể tích khối lăng trụ ABC.A'B'C'."
        )
        payload = {
            "schema_version": "typed-fact-next/2",
            "problem_text": text,
            "length_unit": "1",
            "solids": [
                {
                    "solid_id": "s1",
                    "solid_type": "prism",
                    "notation": "ABC.A'B'C'",
                    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                }
            ],
            "premises": [
                {
                    "kind": "right_prism",
                    "solid_id": "s1",
                    "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                },
                {
                    "kind": "regular_polygon",
                    "solid_id": "s1",
                    "args": {"vertices": ["A", "B", "C"], "side": "2"},
                    "quote": "có đáy ABC là tam giác đều cạnh 2",
                },
                {
                    "kind": "height",
                    "solid_id": "s1",
                    "args": {"value": "4"},
                    "quote": bad_phrase,
                },
            ],
            "relations": [],
            "simulation_goals": [
                {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}
            ],
            "math_goals": [
                {
                    "goal_id": "mg1",
                    "kind": "measurement",
                    "goal_type": "volume",
                    "solid_id": "s1",
                    "target": {"solid_id": "s1"},
                    "quote": "Tính thể tích khối lăng trụ ABC.A'B'C'.",
                }
            ],
        }
        res = run_typed_fact_next_v2_route(payload)
        assert res.status == "REFUSED" and res.code == "UNGROUNDED_VALUE", (bad_phrase, res.status, res.code)

    # Also a 4-gon rectangular box must refuse 'chiều cao hình lập phương bằng 4':
    box_text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, "
        "chiều cao hình lập phương bằng 4. Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    box_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": box_text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABCD.A'B'C'D'",
                "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "solid_id": "s1",
                "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]},
                "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
            },
            {
                "kind": "rectangle",
                "solid_id": "s1",
                "args": {"vertices": ["A", "B", "C", "D"]},
                "quote": "có đáy ABCD là hình chữ nhật",
            },
            {"kind": "segment_length", "solid_id": "s1", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2"},
            {"kind": "segment_length", "solid_id": "s1", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3"},
            {"kind": "height", "solid_id": "s1", "args": {"value": "4"}, "quote": "chiều cao hình lập phương bằng 4"},
        ],
        "relations": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'"}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'.",
            }
        ],
    }
    r_box = run_typed_fact_next_v2_route(box_payload)
    assert r_box.status == "REFUSED" and r_box.code == "UNGROUNDED_VALUE"
