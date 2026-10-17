"""Independent exact oracle for the fresh held-out corpus (stdlib only).

Every figure is an explicit coordinate model in an affine frame with a Gram
matrix G (identity unless irrational lengths are folded into the metric, e.g.
y scaled by sqrt 3 for an equilateral base). All measures are computed from
Gram determinants, so they stay in Q:
  dist^2(P, plane XYZ) = Gram(u, v, P-X) / Gram(u, v)
  dist^2(P, line AB)   = Gram(u, P-A) / Gram(u)
  dist^2(skew AB, CD)  = Gram(u, v, C-A) / Gram(u, v)   (Gram triple = |(u x v).w|^2)
  area^2(triangle)     = Gram(u, v) / 4,   volume^2(tetra) = Gram(u, v, w) / 36
  cos^2 line-plane     = 1 - Gram(p, q, u) / (Gram(p, q) |u|^2)
  cos^2 plane-plane    = <a^b, c^d>^2 / (Gram(a, b) Gram(c, d))
Values with the symbol a use a = 1.
"""
import json
import os
import sys
from fractions import Fraction as F

I3 = ((1, 0, 0), (0, 1, 0), (0, 0, 1))


def diag(a, b, c):
    return ((F(a), 0, 0), (0, F(b), 0), (0, 0, F(c)))


def det(m):
    if len(m) == 1:
        return m[0][0]
    return sum((-1) ** j * m[0][j] * det([r[:j] + r[j + 1:] for r in m[1:]]) for j in range(len(m)))


class Fig:
    def __init__(self, pts, G=I3):
        self.P = {k: tuple(F(x) for x in p) for k, p in pts.items()}
        self.G = G

    def v(self, a, b):
        return tuple(y - x for x, y in zip(self.P[a], self.P[b]))

    def dot(self, u, w):
        return sum(u[i] * self.G[i][j] * w[j] for i in range(3) for j in range(3))

    def gram(self, *vs):
        return det([[self.dot(a, b) for b in vs] for a in vs])

    def coplanar(self, plane):
        x = plane[0]
        for r in plane[3:]:
            assert self.gram(self.v(x, plane[1]), self.v(x, plane[2]), self.v(x, r)) == 0, plane

    def seg(self, a, b):
        u = self.v(a, b)
        return self.dot(u, u)

    def pt_plane(self, p, plane):
        self.coplanar(plane)
        x, y, z = plane[:3]
        u, w = self.v(x, y), self.v(x, z)
        assert self.gram(u, w) != 0
        return self.gram(u, w, self.v(x, p)) / self.gram(u, w)

    def pt_line(self, p, a, b):
        u = self.v(a, b)
        return self.gram(u, self.v(a, p)) / self.gram(u)

    def line_line(self, a, b, c, d):
        u, w = self.v(a, b), self.v(c, d)
        assert self.gram(u, w) != 0, "parallel lines"
        g = self.gram(u, w, self.v(a, c))
        assert g != 0, "lines intersect"
        return g / self.gram(u, w)

    def ang_line_plane(self, a, b, plane):
        self.coplanar(plane)
        x, y, z = plane[:3]
        p, q, u = self.v(x, y), self.v(x, z), self.v(a, b)
        return 1 - self.gram(p, q, u) / (self.gram(p, q) * self.dot(u, u))

    def ang_plane_plane(self, pl1, pl2):
        self.coplanar(pl1)
        self.coplanar(pl2)
        a, b = self.v(pl1[0], pl1[1]), self.v(pl1[0], pl1[2])
        c, d = self.v(pl2[0], pl2[1]), self.v(pl2[0], pl2[2])
        inner = self.dot(a, c) * self.dot(b, d) - self.dot(a, d) * self.dot(b, c)
        return inner ** 2 / (self.gram(a, b) * self.gram(c, d))

    def tri_area(self, a, b, c):
        return self.gram(self.v(a, b), self.v(a, c)) / 4

    def is_par(self, a, b, c, d):
        return all(p + r == q + s for p, q, r, s in zip(self.P[a], self.P[b], self.P[c], self.P[d]))

    def par_area(self, a, b, c, d):
        assert self.is_par(a, b, c, d)
        return self.gram(self.v(a, b), self.v(a, d))

    def tet_vol(self, a, b, c, d):
        return self.gram(self.v(a, b), self.v(a, c), self.v(a, d)) / 36

    def pyr_par_vol(self, s, a, b, c, d):  # pyramid over a parallelogram = 2 tetrahedra
        assert self.is_par(a, b, c, d)
        return 4 * self.tet_vol(s, a, b, d)

    def tri_prism_vol(self, a, b, c, a1):  # triangular prism = 3 tetrahedra
        return 9 * self.tet_vol(a, b, c, a1)

    def box_vol(self, a, b, d, a1):
        return self.gram(self.v(a, b), self.v(a, d), self.v(a, a1))


def box(names, x, y, z, G=I3, extra=None):
    A, B, C, D, A1, B1, C1, D1 = names
    pts = {A: (0, 0, 0), B: (x, 0, 0), C: (x, y, 0), D: (0, y, 0),
           A1: (0, 0, z), B1: (x, 0, z), C1: (x, y, z), D1: (0, y, z)}
    pts.update(extra or {})
    return Fig(pts, G)


def reg_pyr(half, h, G=I3):
    return Fig({"A": (-half, -half, 0), "B": (half, -half, 0), "C": (half, half, 0),
                "D": (-half, half, 0), "S": (0, 0, h), "O": (0, 0, 0)}, G)


AP = ["A", "B", "C", "D", "A'", "B'", "C'", "D'"]
UP = ["A", "B", "C", "D", "A′", "B′", "C′", "D′"]
SQ = ["A", "B", "C", "D"]
EQ3 = diag(1, 3, 1)  # y scaled by sqrt 3: C=(1,1,0) is (1, sqrt3, 0)

checks = []  # sanity checks on the stated data
expected = {}

# h01 cube edge 2
f = box(AP, 2, 2, 2)
expected[("h01", "r1")] = f.seg("A", "C'")
expected[("h01", "r2")] = f.pt_plane("A", ["A'", "B", "D"])
# h02 cube edge a = 1, Unicode primes
f = box(UP, 1, 1, 1)
expected[("h02", "r1")] = f.pt_plane("C", ["B′", "D′", "D"])
# h03 cube edge 3
f = box(AP, 3, 3, 3)
expected[("h03", "r1")] = f.pt_line("A'", "B", "D")
# h04 box 3 x 4 x 12
f = box(AP, 3, 4, 12)
expected[("h04", "r1")] = f.seg("A", "C'")
expected[("h04", "r2")] = f.box_vol("A", "B", "D", "A'")
# h05 missing height: both answers change with AA'
g1, g2 = box(AP, 3, 4, 1), box(AP, 3, 4, 2)
checks.append(("h05 diagonal depends on AA'", g1.seg("A", "C'") != g2.seg("A", "C'")))
checks.append(("h05 volume depends on AA'", g1.box_vol("A", "B", "D", "A'") != g2.box_vol("A", "B", "D", "A'")))
# h06 box 2 x 1 x 2
f = box(AP, 2, 1, 2)
expected[("h06", "r1")] = f.ang_line_plane("A'", "C", SQ)
expected[("h06", "r2")] = f.par_area("A", "C", "C'", "A'")
# h07 regular pyramid, base edge 2, height 3
f = reg_pyr(1, 3)
expected[("h07", "r1")] = f.pyr_par_vol("S", *SQ)
expected[("h07", "r2")] = f.ang_line_plane("S", "A", SQ)
# h08 regular pyramid, base edge 2, lateral edge 3 -> height sqrt 7 folded into z metric
f = reg_pyr(1, 1, diag(1, 1, 7))
checks.append(("h08 lateral edge 3", f.seg("S", "A") == 9 and f.seg("S", "C") == 9))
checks.append(("h08 base edge 2", f.seg("A", "B") == 4))
expected[("h08", "r1")] = f.pt_plane("O", ["S", "C", "D"])
expected[("h08", "r2")] = f.pyr_par_vol("S", *SQ)
# h09 regular pyramid, base edge 4, height 2
f = reg_pyr(2, 2)
expected[("h09", "r1")] = f.ang_plane_plane(["S", "B", "C"], SQ)
expected[("h09", "r2")] = f.tri_area("S", "B", "C")
# h10 square base a = 1, SA = 1 perpendicular
f = Fig({"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "D": (0, 1, 0), "S": (0, 0, 1)})
expected[("h10", "r1")] = f.line_line("S", "C", "B", "D")
expected[("h10", "r2")] = f.pt_plane("A", ["S", "B", "D"])
# h11 right at B, AB 3, BC 4, SA 4
f = Fig({"B": (0, 0, 0), "A": (3, 0, 0), "C": (0, 4, 0), "S": (3, 0, 4)})
checks.append(("h11 right angle at B", f.dot(f.v("B", "A"), f.v("B", "C")) == 0))
expected[("h11", "r1")] = f.tet_vol("S", "A", "B", "C")
expected[("h11", "r2")] = f.pt_plane("A", ["S", "B", "C"])
# h12 rectangle 2 x 3, SA unknown: r1 independent of SA, r2 dependent
hs = [Fig({"A": (0, 0, 0), "B": (2, 0, 0), "C": (2, 3, 0), "D": (0, 3, 0), "S": (0, 0, h)}) for h in (1, 5)]
r1 = [g.pt_plane("D", ["S", "A", "B"]) for g in hs]
checks.append(("h12 r1 independent of SA", r1[0] == r1[1]))
checks.append(("h12 r2 depends on SA", hs[0].ang_line_plane("S", "C", SQ) != hs[1].ang_line_plane("S", "C", SQ)))
expected[("h12", "r1")] = r1[0]
# h13 right prism, right at A, AB 3, AC 4, AA' 6
f = Fig({"A": (0, 0, 0), "B": (3, 0, 0), "C": (0, 4, 0), "A'": (0, 0, 6), "B'": (3, 0, 6), "C'": (0, 4, 6)})
expected[("h13", "r1")] = f.tri_prism_vol("A", "B", "C", "A'")
expected[("h13", "r2")] = f.seg("B'", "C")
# h14 right prism, equilateral base 2, lateral edge 3
f = Fig({"A": (0, 0, 0), "B": (2, 0, 0), "C": (1, 1, 0), "A′": (0, 0, 3), "B′": (2, 0, 3), "C′": (1, 1, 3)}, EQ3)
checks.append(("h14 equilateral base", f.seg("A", "B") == f.seg("B", "C") == f.seg("C", "A") == 4))
checks.append(("h14 lateral edge 3", f.seg("A", "A′") == 9))
expected[("h14", "r1")] = f.ang_plane_plane(["A′", "B", "C"], ["A", "B", "C"])
expected[("h14", "r2")] = f.tri_area("A′", "B", "C")
# h15 right prism, isosceles right at B, BA = BC = 2, AA' = 3
f = Fig({"B": (0, 0, 0), "A": (2, 0, 0), "C": (0, 2, 0), "B'": (0, 0, 3), "A'": (2, 0, 3), "C'": (0, 2, 3)})
expected[("h15", "r1")] = f.tri_prism_vol("A", "B", "C", "A'")
expected[("h15", "r2")] = f.pyr_par_vol("A'", "B", "C", "C'", "B'")
# h16 trirectangular tetrahedron
f = Fig({"O": (0, 0, 0), "A": (1, 0, 0), "B": (0, 2, 0), "C": (0, 0, 2)})
expected[("h16", "r1")] = f.pt_plane("O", ["A", "B", "C"])
expected[("h16", "r2")] = f.tet_vol("O", "A", "B", "C")
# h17 regular tetrahedron on alternate cube vertices, metric 1/2 -> edge 1
f = Fig({"A": (0, 0, 0), "B": (1, 1, 0), "C": (1, 0, 1), "D": (0, 1, 1)}, diag(F(1, 2), F(1, 2), F(1, 2)))
checks.append(("h17 all edges 1", all(f.seg(p, q) == 1 for p, q in ["AB", "AC", "AD", "BC", "BD", "CD"])))
expected[("h17", "r1")] = f.line_line("A", "B", "C", "D")
expected[("h17", "r2")] = f.ang_line_plane("A", "B", ["B", "C", "D"])
# h18 DA perpendicular (ABC), right at B, AB 1, BC 2, DA 2
f = Fig({"B": (0, 0, 0), "A": (1, 0, 0), "C": (0, 2, 0), "D": (1, 0, 2)})
checks.append(("h18 BCD right at B", f.dot(f.v("B", "C"), f.v("B", "D")) == 0))
expected[("h18", "r1")] = f.tri_area("B", "C", "D")
# h19 / h20 regular quadrilateral prism, base 2, height 4
f = box(AP, 2, 2, 4)
expected[("h19", "r1")] = f.ang_plane_plane(["A'", "B", "D"], SQ)
expected[("h19", "r2")] = f.pt_line("A", "B'", "D'")
f = box(UP, 2, 2, 4)
expected[("h20", "r1")] = f.ang_plane_plane(["A′", "B", "D"], SQ)
expected[("h20", "r2")] = f.tet_vol("A′", "A", "B", "D")
# h21 cube ABCD.EFGH edge 2, S centre of EFGH
f = box(list("ABCDEFGH"), 2, 2, 2, extra={"S": (1, 1, 2)})
checks.append(("h21 S centre of EFGH", f.is_par("E", "F", "G", "H") and f.seg("S", "E") == f.seg("S", "G") == 2))
expected[("h21", "r1")] = f.pyr_par_vol("S", *SQ)
expected[("h21", "r2")] = f.ang_line_plane("S", "A", SQ)
cube_face = f.pt_plane("S", ["A", "B", "F", "E"])
pyr_face = f.pt_plane("S", ["S", "A", "B"])
checks.append(("h21 'mặt bên' readings differ", cube_face == 1 and pyr_face == 0))
# h22-h24 SA perpendicular, equilateral base 2, SA 2
f = Fig({"A": (0, 0, 0), "B": (2, 0, 0), "C": (1, 1, 0), "S": (0, 0, 2)}, EQ3)
checks.append(("h22 equilateral base", f.seg("A", "B") == f.seg("B", "C") == f.seg("C", "A") == 4))
expected[("h22", "r1")] = f.pt_line("S", "B", "C")
expected[("h22", "r2")] = f.seg("S", "B")
expected[("h23", "r2")] = f.tet_vol("S", "A", "B", "C")
expected[("h24", "r1")] = f.ang_line_plane("S", "B", ["A", "B", "C"])


def labels_in(target):
    out = []
    for k, v in target.items():
        if isinstance(v, list):
            out += v
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "corpus.json"), encoding="utf-8") as fh:
        corpus = json.load(fh)
    assert corpus["schema"] == "fresh-heldout/1"
    cases = corpus["cases"]
    assert [c["id"] for c in cases] == ["h%02d" % i for i in range(1, 25)]
    fams = [c["structure_id"] for c in cases]
    assert len(set(fams)) == 8
    for i in range(0, 24, 3):  # 8 families x 3, contiguous
        assert len(set(fams[i:i + 3])) == 1 and fams.count(fams[i]) == 3, fams[i]

    seen = set()
    disp = {}
    numeric = multi = 0
    for c in cases:
        assert c["split"] == "heldout"
        reqs = c["requests"]
        assert c["n_source_requests"] == len(reqs), c["id"]
        multi += len(reqs) >= 2
        rids = [r["rid"] for r in reqs]
        assert len(rids) == len(set(rids)), c["id"]
        ents = set(c["entities"])
        assert len(ents) == len(c["entities"]), c["id"]
        for e in ents:
            assert e in c["source_text"], (c["id"], e)
        for r in reqs:
            key = (c["id"], r["rid"])
            assert r["source_quote"] in c["source_text"], key
            assert set(labels_in(r["target"])) <= ents, key
            assert r["intent"] in {"calculate", "construct", "prove", "explain", "simulate"}, key
            assert r["disposition"] in {"answer", "unsupported", "ambiguous", "missing_source", "capability_gap"}, key
            disp[r["disposition"]] = disp.get(r["disposition"], 0) + 1
            if r["quantity"] == "angle":
                assert r["response_form"] in {"angle", "cos_squared"}, key
            else:
                assert "response_form" not in r, key
            if r["disposition"] == "answer":
                o = r["oracle"]
                assert o is not None and key in expected, key
                field = "cos_squared" if r["quantity"] == "angle" else "value_squared"
                assert list(o) == [field], key
                got = expected[key]
                assert F(o[field]) == got, (key, o[field], str(got))
                if field == "cos_squared":
                    assert 0 <= got <= 1, key
                numeric += 1
                seen.add(key)
            else:
                assert r["oracle"] is None and key not in expected, key
    assert seen == set(expected), set(expected) - seen
    failed = [name for name, ok in checks if not ok]
    assert not failed, failed

    nreq = sum(len(c["requests"]) for c in cases)
    non_numeric = nreq - numeric
    assert multi >= 9 and non_numeric >= 5
    print(json.dumps({"status": "PASS", "cases": len(cases), "families": len(set(fams)),
                      "requests": nreq, "numeric_oracles": numeric, "non_numeric": non_numeric,
                      "multi_request_cases": multi, "dispositions": disp,
                      "data_checks": len(checks)}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
