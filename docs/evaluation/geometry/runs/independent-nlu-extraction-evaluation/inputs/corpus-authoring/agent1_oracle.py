# Independent exact oracle (stdlib fractions only). Places every figure in coordinates
# chosen here, recomputes every expected value, and asserts corpus.json agrees.
# Symbolic edge "a" is evaluated at a = 1 (corpus marks those values with "unit").
import sys; sys.stdout.reconfigure(encoding="utf-8")
import json, os, re
from fractions import Fraction as F

HERE = os.path.dirname(os.path.abspath(__file__))


def v(*xs): return tuple(F(x) for x in xs)
def sub(p, q): return tuple(a - b for a, b in zip(p, q))
def add(p, q): return tuple(a + b for a, b in zip(p, q))
def mul(p, k): return tuple(a * k for a in p)
def dot(p, q): return sum(a * b for a, b in zip(p, q))
def cross(p, q): return (p[1]*q[2]-p[2]*q[1], p[2]*q[0]-p[0]*q[2], p[0]*q[1]-p[1]*q[0])
def n2(p): return dot(p, p)
def mid(p, q): return mul(add(p, q), F(1, 2))
def centroid(*ps): return mul(tuple(sum(c) for c in zip(*ps)), F(1, len(ps)))
def triple(a, b, c): return dot(a, cross(b, c))
def normal(p, q, r): return cross(sub(q, p), sub(r, p))

def d2_pp(p, q): return n2(sub(p, q))
def d2_pl(p, a, b):  # point to line ab
    return n2(cross(sub(p, a), sub(b, a))) / n2(sub(b, a))
def d2_pseg(p, a, b):
    t = dot(sub(p, a), sub(b, a)) / n2(sub(b, a))
    t = min(max(t, F(0)), F(1))
    return n2(sub(p, add(a, mul(sub(b, a), t))))
def d2_pplane(p, a, b, c):
    n = normal(a, b, c)
    return dot(sub(p, a), n) ** 2 / n2(n)
def d2_ll(a, b, c, d):
    n = cross(sub(b, a), sub(d, c))
    return dot(sub(c, a), n) ** 2 / n2(n)
def cos2_ll(a, b, c, d):
    u, w = sub(b, a), sub(d, c)
    return dot(u, w) ** 2 / (n2(u) * n2(w))
def cos2_lplane(a, b, p, q, r):  # angle between line ab and plane pqr
    u, n = sub(b, a), normal(p, q, r)
    return 1 - dot(u, n) ** 2 / (n2(u) * n2(n))
def cos2_planes(p1, p2):
    n, m = normal(*p1), normal(*p2)
    return dot(n, m) ** 2 / (n2(n) * n2(m))
def area2(a, b, c): return n2(normal(a, b, c)) / 4
def vol_tet(a, b, c, d): return abs(triple(sub(b, a), sub(c, a), sub(d, a))) / 6
def coplanar(*ps): return triple(sub(ps[1], ps[0]), sub(ps[2], ps[0]), sub(ps[3], ps[0])) == 0


# ---------- figures ----------
def pyr(ab, ad, sa):  # S.ABCD, rectangle base, SA ⊥ base
    return dict(A=v(0, 0, 0), B=v(ab, 0, 0), C=v(ab, ad, 0), D=v(0, ad, 0), S=v(0, 0, sa))
def pyr_vol(P): return vol_tet(P["S"], P["A"], P["B"], P["C"]) + vol_tet(P["S"], P["A"], P["C"], P["D"])
def box(ab, ad, h):
    P = dict(A=v(0, 0, 0), B=v(ab, 0, 0), C=v(ab, ad, 0), D=v(0, ad, 0))
    for k in "ABCD":
        P[k + "'"] = add(P[k], v(0, 0, h))
    return P
def box_vol(P): return abs(triple(sub(P["B"], P["A"]), sub(P["D"], P["A"]), sub(P["A'"], P["A"])))
def tet(oa, ob, oc): return dict(O=v(0, 0, 0), A=v(oa, 0, 0), B=v(0, ob, 0), C=v(0, 0, oc))
def prism(ab, ac, h):  # right prism, base right angle at A
    P = dict(A=v(0, 0, 0), B=v(ab, 0, 0), C=v(0, ac, 0))
    for k in "ABC":
        P[k + "'"] = add(P[k], v(0, 0, h))
    return P
def prism_vol(P): return abs(triple(sub(P["B"], P["A"]), sub(P["C"], P["A"]), sub(P["A'"], P["A"]))) / 2
def chop_rB(ab, bc, sa): return dict(A=v(0, 0, 0), B=v(ab, 0, 0), C=v(ab, bc, 0), S=v(0, 0, sa))
def chop_rA(ab, ac, sa): return dict(A=v(0, 0, 0), B=v(ab, 0, 0), C=v(0, ac, 0), S=v(0, 0, sa))
def foot_line(p, a, b):
    t = dot(sub(p, a), sub(b, a)) / n2(sub(b, a))
    return add(a, mul(sub(b, a), t)), t

# Premise sanity of non-trivial bases
TRAP = dict(A=v(0, 0, 0), B=v(2, 0, 0), C=v(4, 2, 0), D=v(0, 2, 0), S=v(0, 0, 2))
assert cross(sub(TRAP["B"], TRAP["A"]), sub(TRAP["C"], TRAP["D"])) == v(0, 0, 0)  # AB ∥ CD
assert dot(sub(TRAP["B"], TRAP["A"]), sub(TRAP["D"], TRAP["A"])) == 0             # right at A (and D)
assert d2_pp(TRAP["C"], TRAP["D"]) == 16 and d2_pp(TRAP["A"], TRAP["B"]) == 4 == d2_pp(TRAP["A"], TRAP["D"])
PAR = dict(A=v(0, 0, 0), B=v(2, 0, 0), C=v(1, 1, 0), D=v(-1, 1, 0), S=v(0, 0, 1))
assert add(PAR["A"], PAR["C"]) == add(PAR["B"], PAR["D"])                          # parallelogram
ab, ad = sub(PAR["B"], PAR["A"]), sub(PAR["D"], PAR["A"])
assert n2(ab) == 4 and n2(ad) == 2 and dot(ab, ad) < 0 and dot(ab, ad) ** 2 / (n2(ab) * n2(ad)) == F(1, 2)  # 135°

STD = {F(1): "0", F(3, 4): "30", F(1, 2): "45", F(1, 4): "60", F(0): "90"}
O = {}  # case id -> rid -> (kind, Fraction)
CHECKS = []  # non-numeric facts asserted for refusal / construction cases

# ---------- DEV ----------
P1 = pyr(2, 2, 2)
for cid in ("D01", "D02", "D03"):
    O[cid] = {"r1": ("d2", d2_pplane(P1["A"], P1["S"], P1["B"], P1["C"]))}
f, t = foot_line(TRAP["S"], TRAP["B"], TRAP["C"])
assert t < 0  # foot outside segment BC, beyond B
O["D04"] = {"r1": ("d2", d2_pl(TRAP["S"], TRAP["B"], TRAP["C"]))}
O["D05"] = {"r1": ("d2", d2_pseg(TRAP["S"], TRAP["B"], TRAP["C"]))}
O["D06"] = {"r1": ("cos2", cos2_lplane(P1["S"], P1["C"], P1["A"], P1["B"], P1["C"]))}
O["D07"] = {"r1": ("d2", d2_pplane(mid(P1["S"], P1["C"]), P1["A"], P1["B"], P1["C"]))}
T = tet(2, 3, 6)
O["D08"] = {"r1": ("d2", d2_pplane(T["O"], T["A"], T["B"], T["C"]))}
K = box(2, 2, 2)
O["D09"] = {"r1": ("d2", d2_pp(centroid(K["A'"], K["B"], K["D"]), K["C'"]))}
Q = chop_rB(3, 4, 4)
assert dot(sub(Q["A"], Q["B"]), sub(Q["C"], Q["B"])) == 0
O["D10"] = {"r1": ("vol", vol_tet(Q["S"], Q["A"], Q["B"], Q["C"])),
            "r2": ("d2", d2_pplane(Q["A"], Q["S"], Q["B"], Q["C"]))}
Pr = prism(3, 4, 6)
H, _ = foot_line(Pr["A"], Pr["B"], Pr["C"])
assert d2_pp(Pr["B"], H) == F(81, 25)  # BH = 9/5
O["D11"] = {"r2": ("d2", d2_pp(Pr["A'"], H))}
K1 = box(1, 1, 1)
O["D12"] = {"r1": ("d2", d2_pp(K1["A"], K1["C'"])),
            "r2": ("cos2", cos2_ll(K1["A"], K1["B'"], K1["B"], K1["C'"])),
            "r3": ("d2", d2_ll(K1["A"], K1["B'"], K1["B"], K1["C'"]))}
H, _ = foot_line(P1["A"], P1["S"], P1["B"])
O["D13"] = {"r1": ("d2", d2_pp(P1["A"], H))}
B = chop_rA(3, 4, 0)
CHECKS.append(("D15", "AB²+AC² != BC²", n2(sub(B["B"], B["A"])) + n2(sub(B["C"], B["A"])) != 36))
CHECKS.append(("D16", "volume depends on SA", pyr_vol(pyr(3, 3, 1)) != pyr_vol(pyr(3, 3, 2))))

# ---------- LOCKED ----------
Bx = box(3, 4, 12)
for cid in ("L01", "L02", "L03"):
    O[cid] = {"r1": ("d2", d2_pp(Bx["A"], Bx["C'"]))}
K2 = box(2, 2, 2)
for cid in ("L04", "L05"):
    O[cid] = {"r1": ("d2", d2_pplane(K2["A"], K2["A'"], K2["B"], K2["D"]))}
P5 = pyr(3, 4, 5)
for cid in ("L06", "L07"):
    O[cid] = {"r1": ("cos2", cos2_lplane(P5["S"], P5["C"], P5["A"], P5["B"], P5["C"]))}
O["L09"] = {"r1": ("d2", d2_pp(P5["S"], P5["C"]))}
O["L10"] = {"r1": ("sq", d2_pp(P5["S"], P5["C"]))}
f, t = foot_line(PAR["B"], PAR["S"], PAR["D"])
assert t == F(-1, 3)  # foot beyond S
O["L11"] = {"r1": ("d2", d2_pl(PAR["B"], PAR["S"], PAR["D"]))}
O["L12"] = {"r1": ("d2", d2_pseg(PAR["B"], PAR["S"], PAR["D"]))}
O["L13"] = {"r1": ("cos2", cos2_lplane(Bx["A"], Bx["C'"], Bx["A"], Bx["B"], Bx["C"]))}
O["L14"] = {"r1": ("cos2", cos2_lplane(Bx["A"], Bx["C'"], Bx["A"], Bx["B"], Bx["C"]))}
CHECKS.append(("L15", "A,B,C',D' coplanar", coplanar(K2["A"], K2["B"], K2["C'"], K2["D'"])))
O["L15"] = {"r1": ("d2", d2_pplane(K2["A'"], K2["A"], K2["B"], K2["D'"]))}
CHECKS.append(("L16", "A,B,C',D not coplanar", not coplanar(K2["A"], K2["B"], K2["C'"], K2["D"])))
n1, n2_ = normal(P5["S"], P5["A"], P5["B"]), normal(P5["S"], P5["C"], P5["D"])
CHECKS.append(("L17", "S∈both planes, AB ⟂ both normals",
               dot(sub(P5["B"], P5["A"]), n1) == 0 == dot(sub(P5["B"], P5["A"]), n2_) and cross(n1, n2_) != v(0, 0, 0)))
Og = mid(PAR["A"], PAR["C"])  # any parallelogram works; reuse PAR base
CHECKS.append(("L18", "S and AC∩BD lie in (SAC) and (SBD)",
               Og == mid(PAR["B"], PAR["D"]) and coplanar(PAR["S"], PAR["A"], PAR["C"], Og) and coplanar(PAR["S"], PAR["B"], PAR["D"], Og)))
T3 = tet(3, 3, 3)
O["L19"] = {"r1": ("d2", d2_pp(T3["O"], centroid(T3["A"], T3["B"], T3["C"])))}
O["L20"] = {"r1": ("d2", d2_pp(K1["A"], mid(K1["C"], K1["C'"])))}
Pr2 = prism(2, 2, 4)
O["L21"] = {"r1": ("d2", d2_pp(Pr2["C"], mid(Pr2["A'"], Pr2["B"])))}
Q2 = chop_rB(2, 2, 2)
O["L22"] = {"r1": ("d2", d2_pplane(Q2["A"], Q2["S"], Q2["B"], Q2["C"]))}
T4 = tet(1, 2, 2)
O["L23"] = {"r1": ("vol", vol_tet(T4["O"], T4["A"], T4["B"], T4["C"])),
            "r2": ("area2", area2(T4["A"], T4["B"], T4["C"])),
            "r3": ("d2", d2_pplane(T4["O"], T4["A"], T4["B"], T4["C"]))}
Pr3 = prism(1, 2, 2)
O["L24"] = {"r1": ("vol", prism_vol(Pr3)),
            "r2": ("cos2", cos2_planes((Pr3["A'"], Pr3["B"], Pr3["C"]), (Pr3["A"], Pr3["B"], Pr3["C"])))}
H, _ = foot_line(P5["A"], P5["S"], P5["B"])
assert d2_pp(P5["A"], H) == d2_pplane(P5["A"], P5["S"], P5["B"], P5["C"])  # H is the foot on (SBC)
O["L25"] = {"r2": ("d2", d2_pp(P5["A"], H))}
Pa = pyr(1, 1, 1)
O["L26"] = {"r1": ("vol", pyr_vol(Pa)), "r2": ("cos2", cos2_lplane(Pa["S"], Pa["B"], Pa["A"], Pa["B"], Pa["C"]))}
Bx2 = box(1, 2, 2)
O["L27"] = {"r1": ("d2", d2_pp(Bx2["B"], Bx2["D'"])), "r2": ("vol", box_vol(Bx2)),
            "r3": ("d2", d2_ll(Bx2["A"], Bx2["A'"], Bx2["B"], Bx2["D'"]))}
Q3 = chop_rA(2, 2, 2)
M = mid(Q3["B"], Q3["C"])
O["L28"] = {"r1": ("d2", d2_pp(Q3["S"], M)), "r2": ("area2", area2(Q3["S"], Q3["B"], Q3["C"]))}
O["L29"] = {"r1": ("d2", d2_ll(K1["B"], K1["D"], K1["B'"], K1["C"])),
            "r2": ("cos2", cos2_ll(K1["B"], K1["D"], K1["B'"], K1["C"]))}
P4 = pyr(4, 4, 3)
O["L30"] = {"r1": ("d2", d2_pp(P4["S"], P4["C"])),
            "r2": ("cos2", cos2_lplane(P4["S"], P4["C"], P4["A"], P4["B"], P4["C"])),
            "r3": ("vol", pyr_vol(P4))}
I = mid(K2["A"], K2["C'"])
assert I == mid(K2["B"], K2["D'"])
O["L31"] = {"r1": ("d2", d2_pplane(I, K2["A"], K2["B"], K2["C"]))}
Q4 = chop_rA(3, 4, 3)
O["L36"] = {"r2": ("d2", d2_pp(Q4["S"], mid(Q4["B"], Q4["C"])))}
CHECKS.append(("L37", "volume depends on the unknown height",
               pyr_vol(pyr(2, 5, 4)) != pyr_vol(dict(pyr(2, 5, 0), S=v(0, F(12, 5), F(16, 5))))))
K3 = box(3, 3, 3)
O["L38"] = {"r1": ("d2", d2_pp(K3["A"], K3["C'"]))}
CHECKS.append(("L39", "(ABCD) ∥ (A'B'C'D') and distinct",
               cross(normal(Bx["A"], Bx["B"], Bx["C"]), normal(Bx["A'"], Bx["B'"], Bx["C'"])) == v(0, 0, 0)
               and d2_pplane(Bx["A'"], Bx["A"], Bx["B"], Bx["C"]) > 0))
# L40: equilateral ABC side 2 has an irrational vertex; check underdetermination in the plane x = 1
# (perpendicular bisector of AB) using squared heights only: S = (1, y, z) with SA² = 1 + y² + z² = 9,
# height above (ABC) is z. Two admissible S: y = 0, z² = 8 and y = 2, z² = 4 -> different volumes.
CHECKS.append(("L40", "SA=SB=3 admits different heights", 1 + 0 + 8 == 9 == 1 + 4 + 4 and F(8) != F(4)))
Q5 = chop_rA(2, 2, 2)
CHECKS.append(("L41", "BC ⟂ AM and BC ⟂ SA", dot(sub(Q5["C"], Q5["B"]), sub(mid(Q5["B"], Q5["C"]), Q5["A"])) == 0
               and dot(sub(Q5["C"], Q5["B"]), sub(Q5["S"], Q5["A"])) == 0))
O["L41"] = {"r2": ("d2", d2_pplane(Q5["A"], Q5["S"], Q5["B"], Q5["C"]))}
P6 = pyr(2, 3, 4)
CHECKS.append(("L43", "the two M differ and give different AM",
               d2_pp(P6["A"], mid(P6["S"], P6["B"])) != d2_pp(P6["A"], mid(P6["S"], P6["D"]))))
CHECKS.append(("L44", "edge 2 -> AC'² = 12 != 16", d2_pp(K2["A"], K2["C'"]) == 12))


# ---------- compare with corpus ----------
def exact_sq(s):
    s = s.replace("a³", "").replace("a", "")
    m = re.fullmatch(r"(\d*)(?:√(\d+))?(?:/(\d+))?", s)
    assert m, s
    k = F(int(m.group(1) or 1)); r = F(int(m.group(2) or 1)); d = F(int(m.group(3) or 1))
    return k * k * r / (d * d)


corpus = json.load(open(os.path.join(HERE, "corpus.json"), encoding="utf-8"))
by_id = {c["id"]: c for c in corpus["cases"]}
n_vals = 0
for c in corpus["cases"]:
    assert set(c["expected_values"]) == set(O.get(c["id"], {})), (c["id"], "expected rid set != oracle rid set")
for cid, rids in O.items():
    ev = by_id[cid]["expected_values"]
    for rid, (kind, x) in rids.items():
        e = ev[rid]
        if kind == "d2":
            assert F(e["value_squared"]) == x and exact_sq(e["exact"]) == x, (cid, rid, x)
        elif kind in ("sq", "vol"):  # value itself is x (rational here)
            assert F(e["value_squared"]) == x * x and exact_sq(e["exact"]) == x * x, (cid, rid, x)
            assert exact_sq(e["value"]) == x * x, (cid, rid, "value")
        elif kind == "area2":
            assert F(e["value_squared"]) == x and exact_sq(e["exact"]) == x, (cid, rid, x)
        elif kind == "cos2":
            assert F(e["cos_squared"]) == x, (cid, rid, x)
            if "value" in e:
                assert F(e["value"]) == x
            if "degrees" in e:
                assert e["degrees"] == STD.get(x), (cid, rid, "degrees", STD.get(x))
        n_vals += 1
        print(f"{cid} {rid} {kind:5s} {x}")
for cid, what, ok in CHECKS:
    assert ok, (cid, what)
    print(f"{cid} check  {what}: OK")
print(f"ORACLE PASS: {n_vals} numeric values in {len(O)} cases, {len(CHECKS)} structural checks")
