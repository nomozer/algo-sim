"""A quadrilateral base "vuông tại A" states a right ANGLE at A, not a right-triangle shape claim.

Regression (main 9e059eb7, found by the Axo pre-merge audit): `registry._phan_loai_hinh_2d` classified any "vuông" base
wording as `right_triangle`, so the standard right-trapezoid wording "Đáy ABCD vuông tại A … vuông tại B" was certified
as a triangle on four vertices and refused as INCONSISTENT_FACTS — a false contradiction verdict on consistent data.

Hand oracle: A(0,0,0) B(3,0,0) C(3,2,0) D(0,4,0), S(0,0,6); base = right trapezoid AD ∥ BC, area (4+2)/2·3 = 9; the
plane through M = mid SA parallel to (ABCD) cuts a similar section at ratio 1/2 ⇒ area 9/4.
"""
from __future__ import annotations

from app.ai.function_route import run_fact_route
from tests.geometry import hybrid_compiler_benchmark as HB


def _trapezoid(right_at_b_quote: str = "Đáy ABCD vuông tại B.") -> list[dict]:
    return [
        HB._f("tp1", "solid", "Cho hình chóp S.ABCD.", solid="S.ABCD", solid_type="pyramid"),
        HB._f("tp2", "right_angle", "Đáy ABCD vuông tại A.", at="A", points=["B", "D"]),
        HB._f("tp3", "right_angle", right_at_b_quote, at="B", points=["A", "C"]),
        HB._f("tp4", "length", "AD = 4.", points=["A", "D"], measure="segment", value="4"),
        HB._f("tp5", "length", "AB = 3.", points=["A", "B"], measure="segment", value="3"),
        HB._f("tp6", "length", "BC = 2.", points=["B", "C"], measure="segment", value="2"),
        HB._f("tp7", "perpendicular", "SA vuông góc với (ABCD).", points_a=["S", "A"], points_b=["A", "B", "C", "D"]),
        HB._f("tp8", "length", "SA = 6.", points=["S", "A"], measure="segment", value="6"),
        HB._mid("tp9", "M", "S", "A"),
        HB._ask("tp10", "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng qua M song song với (ABCD).",
                "area", solid="S.ABCD", plane_relation="parallel", point="M", points_b=["A", "B", "C", "D"]),
    ]


def _run(facts):
    return run_fact_route(" ".join(f["quotes"][0] for f in facts), {"facts": facts})


def test_right_trapezoid_base_right_at_a_and_b_is_served_exactly() -> None:
    r = _run(_trapezoid())
    assert (r.status, r.code) == ("SERVED", None), r.reason
    assert r.answers == {"tp10": "9/4"}


def test_triangle_base_right_at_a_is_still_certified_as_a_right_triangle() -> None:
    """The fix is scoped to ≥ 4 vertices: on a triangle the wording keeps certifying, and a false claim is refused."""
    base = [
        HB._f("t1", "solid", "Cho hình chóp S.ABC.", solid="S.ABC", solid_type="pyramid"),
        HB._f("t3", "length", "AB = 3.", points=["A", "B"], measure="segment", value="3"),
        HB._f("t4", "length", "AC = 4.", points=["A", "C"], measure="segment", value="4"),
        HB._f("t5", "length", "BC = 6.", points=["B", "C"], measure="segment", value="6"),
        HB._f("t6", "perpendicular", "SA vuông góc với (ABC).", points_a=["S", "A"], points_b=["A", "B", "C"]),
        HB._f("t7", "length", "SA = 2.", points=["S", "A"], measure="segment", value="2"),
        HB._ask("t8", "Tính thể tích khối chóp S.ABC.", "volume", solid="S.ABC"),
    ]
    claim = HB._f("t2", "polygon_shape", "Đáy ABC là tam giác vuông tại A.", points=["A", "B", "C"], shape="right_triangle")
    r = _run([base[0], claim, *base[1:]])
    assert r.status == "REFUSED", "3-4-6 is not right at A; the right-triangle claim must still be checked"
