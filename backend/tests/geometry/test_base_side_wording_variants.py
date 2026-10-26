"""Source Gate wording of a square base's side (run `hybrid-v2-nl-certificates-e2e`, audit finding NL-1).

"Đáy ABCD là hình vuông, cạnh 4" / "… với cạnh 4" / "… và có cạnh 4" / "… có độ dài cạnh bằng 4" were refused
`UNGROUNDED_VALUE` although they say what "… có cạnh 4" already said. The clause grammar `_C_DAY` now takes the same
connectors as the already-accepted `_CANH_SAU_DAY`. Positive cases are checked against the closed-form distance
d²(S, BD) = h² + s²/2 (SA ⊥ base, SA = h, side s) — never against engine output; the negative metamorphic cases prove the
wider connector does not let a side value be bound to a different, qualified or ambiguous number.

Authored DEV cases by the implementing agent — not a holdout, no provider call."""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _square


def _payload(base: str, side: str = "4", labels: str = "SABCD", h: int = 3) -> dict:
    S, A, B, C, D = labels
    solid, perp, ln = f"Cho hình chóp {S}.{A}{B}{C}{D}.", f"{S}{A} vuông góc với mặt phẳng ({A}{B}{C}{D}).", f"{S}{A} = {h}."
    goal = f"Tính khoảng cách từ {S} đến {B}{D}."
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join((solid, base, perp, ln, goal)), "length_unit": "1",
            "solids": [{"solid_id": "py", "solid_type": "pyramid", "notation": f"{S}.{A}{B}{C}{D}", "quote": solid}],
            "premises": [{"kind": "base_is_square", "args": {"vertices": [A, B, C, D], "side": side}, "quote": base},
                         {"kind": "perpendicular_line_plane", "args": {"line": [S, A], "plane": [A, B, C, D]}, "quote": perp},
                         {"kind": "segment_length", "args": {"segment": [S, A], "value": str(h)}, "quote": ln}],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "py", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": "distance",
                            "target": {"point": S, "line": [B, D]}, "quote": goal}]}


SIDE_CLAUSES = ["Đáy {A}{B}{C}{D} là hình vuông, cạnh {s}.", "Đáy {A}{B}{C}{D} là hình vuông, cạnh bằng {s}.",
                "Đáy {A}{B}{C}{D} là hình vuông với cạnh {s}.", "Đáy {A}{B}{C}{D} là hình vuông và có cạnh {s}.",
                "Đáy {A}{B}{C}{D} là hình vuông có độ dài cạnh bằng {s}.", "Đáy là hình vuông {A}{B}{C}{D}, cạnh {s}.",
                "Đáy {A}{B}{C}{D} là hình vuông cạnh {s}.", "Đáy {A}{B}{C}{D} là hình vuông có cạnh {s}."]


@pytest.mark.parametrize("clause", SIDE_CLAUSES)
@pytest.mark.parametrize("labels,s,h", [("SABCD", 4, 3), ("PKLMN", 2, 5), ("OPQRT", 6, 1)])
def test_side_wording_variants_are_served_with_the_formula_value(clause, labels, s, h):
    S, A, B, C, D = labels
    r = run_typed_fact_next_v2_route(_payload(clause.format(A=A, B=B, C=C, D=D, s=s), str(s), labels, h))
    assert r.status == "SERVED", (r.code, r.reason)
    assert _square(r) == F(h * h) + F(s * s, 2)


@pytest.mark.parametrize("clause,side", [
    ("Đáy ABCD là hình vuông, cạnh bên SA = 3.", "3"),             # a different edge's length is not the base side
    ("Đáy ABCD là hình vuông, cạnh 4 hoặc 5.", "4"),               # disjunction: no single bound value
    ("Đáy ABCD là hình vuông, cạnh 4 hoặc 5.", "5"),
    ("Đáy ABCD là hình vuông, cạnh không bằng 4.", "4"),           # negation / inequality / approximation / multiple
    ("Đáy ABCD là hình vuông, cạnh lớn hơn 4.", "4"),
    ("Đáy ABCD là hình vuông và có cạnh nhỏ hơn 4.", "4"),
    ("Đáy ABCD là hình vuông, cạnh khoảng 4.", "4"),
    ("Đáy ABCD là hình vuông, cạnh gấp đôi 4.", "4"),
    ("Đáy ABCD là hình vuông, cạnh a.", "4"),                      # a symbol the text does not equate to 4
    ("Đáy ABCD là hình vuông, cạnh 4, cạnh bên 5.", "4"),          # a second role number in the same sentence
    ("Đáy ABCD là hình vuông với cạnh tam giác kia bằng 4.", "4"),  # another object's side
])
def test_wider_connectors_never_bind_a_wrong_or_qualified_value(clause, side):
    r = run_typed_fact_next_v2_route(_payload(clause, side))
    assert r.status == "REFUSED", (clause, r.answers)


def test_side_value_must_still_equal_the_quoted_number():
    r = run_typed_fact_next_v2_route(_payload("Đáy ABCD là hình vuông, cạnh 4.", side="5"))
    assert r.status == "REFUSED" and r.code == "UNGROUNDED_VALUE"


def test_known_unsupported_side_wordings_stay_refused():
    """Parenthesised or split-sentence sides are NOT read (recorded gap NL-2); they must refuse, not guess."""
    for clause in ("Đáy ABCD là hình vuông (cạnh 4).", "Hình vuông ABCD cạnh 4 là đáy."):
        assert run_typed_fact_next_v2_route(_payload(clause)).status == "REFUSED"
