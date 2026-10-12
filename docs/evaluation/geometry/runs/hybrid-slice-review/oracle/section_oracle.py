"""Independent exact oracle (no product import in the oracle part) + comparison with product sections."""
from fractions import Fraction as Fr
from itertools import combinations


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def mid(a, b): return mul(add(a, b), Fr(1, 2))
def V(*x): return tuple(Fr(t) for t in x)


def plane(p, q, r):
    n = cross(sub(q, p), sub(r, p))
    if n == (0, 0, 0):
        return None                                   # collinear => refuse
    return n, dot(n, p)


def clip(verts, edges, pl):
    """verts: name->point, edges: list of (u,v). Returns {point: (kind, info)} of plane ∩ solid edges."""
    n, d = pl
    s = {k: dot(n, p) - d for k, p in verts.items()}
    out = {}
    for k, p in verts.items():
        if s[k] == 0:
            out[p] = ("V", k)
    for u, v in edges:
        if s[u] * s[v] < 0:
            t = s[u] / (s[u] - s[v])                  # param from u
            out.setdefault(add(verts[u], mul(sub(verts[v], verts[u]), t)), ("E", (u, v, t)))
    return out, s


def area2(pts, n):
    """Convex polygon area² from unordered coplanar pts: order by angle via exact half-plane comparison."""
    c = mul(sum_(pts), Fr(1, len(pts)))
    u = sub(pts[0], c)
    w = cross(n, u)
    def key(p):
        x, y = dot(sub(p, c), u), dot(sub(p, c), w)
        half = 0 if (y > 0 or (y == 0 and x > 0)) else 1
        return half, p
    import functools
    def cmp(a, b):
        ka, kb = key(a)[0], key(b)[0]
        if ka != kb: return ka - kb
        cr = dot(cross(sub(a, c), sub(b, c)), n)
        return -1 if cr > 0 else (1 if cr < 0 else 0)
    ordp = sorted(pts, key=functools.cmp_to_key(cmp))
    tot = (Fr(0),) * 3
    for i in range(len(ordp)):
        tot = add(tot, cross(ordp[i], ordp[(i + 1) % len(ordp)]))
    return dot(tot, tot) / 4


def sum_(ps):
    t = (Fr(0),) * 3
    for p in ps: t = add(t, p)
    return t


A, B, C, D, S = V(0,0,0), V(2,0,0), V(2,2,0), V(0,2,0), V(0,0,3)
PYR = ({"S": S, "A": A, "B": B, "C": C, "D": D},
       [("S","A"),("S","B"),("S","C"),("S","D"),("A","B"),("B","C"),("C","D"),("D","A")])
cb = {"A": V(0,0,0), "B": V(2,0,0), "C": V(2,2,0), "D": V(0,2,0)}
cb.update({k + "'": add(v, V(0,0,2)) for k, v in list(cb.items())})
CUBE = (cb, [(a, b) for a, b in combinations(cb, 2) if sum(1 for x, y in zip(cb[a], cb[b]) if x != y) == 1])
# regular tetrahedron edge √2 (area² ×4 for edge 2)
tv = {"A": V(0,0,0), "B": V(1,1,0), "C": V(1,0,1), "D": V(0,1,1)}
TET = (tv, list(combinations(tv, 2)))


def section(solid, p, q, r, scale=1):
    pl = plane(p, q, r)
    if pl is None:
        return "REFUSE collinear", None
    pts, _ = clip(*solid, pl)
    if len(pts) < 3:
        return f"REFUSE degenerate ({len(pts)} pts)", pts
    return area2(list(pts), pl[0]) * scale, pts


M_SC, M_SA, M_SB, M_SD = mid(S, C), mid(S, A), mid(S, B), mid(S, D)
I_, K_ = V(0,4,0), V(2,4,0)
cases = {
    "pyr (MAB) M=mid SC": section(PYR, M_SC, A, B),
    "pyr (SAC)": section(PYR, S, A, C),
    "pyr (mid SA,SB,SC)": section(PYR, M_SA, M_SB, M_SC),
    "pyr (C, mid SA, mid SB)": section(PYR, C, M_SA, M_SB),
    "pyr (M=mid SC, I, K)": section(PYR, M_SC, I_, K_),
    "pyr (S,I,K) touches vertex": section(PYR, S, I_, K_),
    "pyr (S,C,I) touches edge": section(PYR, S, C, I_),
    "pyr (SAB) face": section(PYR, S, A, B),
    "pyr (ABC) base": section(PYR, A, B, C),
    "pyr plane through M=midSC parallel to base": section(PYR, M_SC, add(M_SC, V(1,0,0)), add(M_SC, V(0,1,0))),
    "pyr collinear (mid AB, A, B)": section(PYR, mid(A, B), A, B),
    "cube (A'BD)": section(CUBE, cb["A'"], cb["B"], cb["D"]),
    "cube hexagon (mid AB, mid BC, mid CC')": section(CUBE, mid(cb["A"], cb["B"]), mid(cb["B"], cb["C"]), mid(cb["C"], cb["C'"])),
    "tet (mid DA,DB,DC) edge2": section(TET, mid(tv["D"], tv["A"]), mid(tv["D"], tv["B"]), mid(tv["D"], tv["C"]), 4),
    "tet (mid AB,AC,DB) edge2": section(TET, mid(tv["A"], tv["B"]), mid(tv["A"], tv["C"]), mid(tv["D"], tv["B"]), 4),
}
for k, (a, pts) in cases.items():
    info = sorted(str(v) for v in pts.values()) if pts else ""
    print(f"{k:45s} area²={a}  {info}")

# intersection lines
def line_pp(p1, p2):
    (n1, d1), (n2, d2) = p1, p2
    return cross(n1, n2)
dSAB_SCD = line_pp(plane(S, A, B), plane(S, C, D))
print("(SAB)∩(SCD) dir", dSAB_SCD, "∥AB:", cross(dSAB_SCD, sub(B, A)) == (0,0,0),
      "S on both:", dot(plane(S,A,B)[0], S) == plane(S,A,B)[1] and dot(plane(S,C,D)[0], S) == plane(S,C,D)[1])
O = mid(A, C)
dSAC_SBD = line_pp(plane(S, A, C), plane(S, B, D))
print("(SAC)∩(SBD) dir", dSAC_SBD, "∥SO:", cross(dSAC_SBD, sub(O, S)) == (0,0,0))
print("(MNP mid SA,SB,SC) vs (ABC) parallel:", line_pp(plane(M_SA, M_SB, M_SC), plane(A, B, C)) == (0,0,0))
print("(SAB) vs (SCD) via đáy: (SAB)∩(ABCD) dir", line_pp(plane(S,A,B), plane(A,B,C)), "vs (SAB)∩(SCD)", dSAB_SCD)
print("tri MAB area²", dot(cross(sub(A, M_SC), sub(B, M_SC)), cross(sub(A, M_SC), sub(B, M_SC))) / 4)
