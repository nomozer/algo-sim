"""Independent mathematical oracle: similarity and median/base-ratio volume identities.

No product imports or chart coordinates. For an equilateral base of side b and height h,
area²=3b⁴/16, volume²=b⁴h²/48. Homothety scales area by t² and volume by t³.
For a point dividing BC at BM/BC=t, the two triangles have base-area fractions t and 1-t.
"""
from fractions import Fraction as F


def expected(case):
    p = case["oracle"]
    b, h, t = F(p["side"]), F(p["height"]), F(p["t"])
    root_v2 = b**4 * h**2 / 48
    if p["slice"] == "section":
        values = {"volume0": root_v2 * t**6, "area": 3*b**4*t**4/16, "length": b*b*t*t}
    else:
        values = {"volume0": root_v2*t*t, "volume1": root_v2*(1-t)**2}
    return {q: str(values[q]) for q in p["goals"]}


def self_check():
    # Independent Euclidean tetrahedron: A(0,0,0), B(4,0,0), C(2,2√3,0), S(0,0,6).
    # Scalar triple product / 6 = 8√3. Half-scale child √3, each median half 4√3.
    assert expected({"oracle": dict(side="4", height="6", t="1/2", slice="section", goals=["volume0"])}) == {"volume0": "3"}
    assert expected({"oracle": dict(side="4", height="6", t="1/2", slice="shared", goals=["volume0", "volume1"])}) == {"volume0": "48", "volume1": "48"}


self_check()
