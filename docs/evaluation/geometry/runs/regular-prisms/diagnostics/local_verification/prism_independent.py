"""LOCAL independent check (no product import). For every served regular-prism row:
  1. build the TRUE Euclidean regular prism of side b, height h (b, h from the text's dimensions, hand-encoded labels)
     and pull its basis dot products back onto the corpus program's AFFINE chart (e1 = B − A, e2 = C − A, e3 = A′ − A)
     — a different construction from the product's six-lengths Gram (`do_luong_cua`);
  2. under that metric, on the chart coordinates of cases.py: every base and top side² = b², top = translation of the
     base, lateral edge ⊥ every base edge, |lateral|² = h², V² = (chart area · chart height)² · det G;
  3. compare V² with the textbook formula written here: V = (3√3/2)b²h (hexagon), (√3/4)b²h (triangle);
  4. compare G exactly with the scene's chart_metric (dumped by prism_scene_dump.py) and the label value.
Run: python prism_independent.py <run dir> <scene dump dir>"""
import json, re, sys
from fractions import Fraction as F
from pathlib import Path

RUN, SCENES = Path(sys.argv[1]), Path(sys.argv[2])
ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
CHART = {6: [(2, 1), (1, 2), (0, 2), (0, 1), (1, 0), (2, 0)], 3: [(0, 0), (1, 0), (0, 1)]}   # cases.py, top z = 1


def sq(v):
    m = re.fullmatch(r"(\d+(?:/\d+)?)?(?:√(\d+))?", v)
    q = F(m.group(1) or 1)
    return q * q * int(m.group(2) or 1)


def sub(p, q): return tuple(F(a) - F(b) for a, b in zip(p, q))
def det3(m): return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
                     + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
def inv3(m):
    d = det3(m)
    return [[(m[(j+1)%3][(i+1)%3]*m[(j+2)%3][(i+2)%3] - m[(j+1)%3][(i+2)%3]*m[(j+2)%3][(i+1)%3]) / d
             for j in range(3)] for i in range(3)]
def dot(G, u, v): return sum(u[r] * G[r][c] * v[c] for r in range(3) for c in range(3))


def true_basis_gram(k, b2, h2):
    """e_i · e_j of the real prism. Real hexagon A, B, C = (b, 0), (b/2, b√3/2), (−b/2, b√3/2):
    e1 = (−b/2, b√3/2), e2 = (−3b/2, b√3/2) ⇒ e1² = b², e2² = 3b², e1·e2 = 3b²/2.
    Real triangle A, B, C = (0, 0), (b, 0), (b/2, b√3/2): e1² = e2² = b², e1·e2 = b²/2. e3 = (0, 0, h) ⊥ both."""
    e11, e22, e12 = (b2, 3 * b2, F(3, 2) * b2) if k == 6 else (b2, b2, b2 / 2)
    return [[e11, e12, 0], [e12, e22, 0], [0, 0, h2]]


ok = True
for rid, r in ROWS.items():
    if not r["expect"].startswith("served"):
        continue
    k, d = r["k"], r["dims"]
    b2 = sq(d["base"])
    h2 = sq(d["height"] if "height" in d else d["lateral"])
    base = [(*xy, 0) for xy in CHART[k]]
    top = [(x, y, 1) for x, y, _ in base]
    A, B, C, A1 = base[0], base[1], base[2], top[0]
    M = [[e[i] for e in (sub(B, A), sub(C, A), sub(A1, A))] for i in range(3)]       # columns e1, e2, e3
    Mi, Ge = inv3(M), true_basis_gram(k, b2, h2)
    G = [[sum(Mi[a][r_] * Ge[a][b_] * Mi[b_][c] for a in range(3) for b_ in range(3)) for c in range(3)] for r_ in range(3)]
    sides = {dot(G, sub(w[(i+1) % k], w[i]), sub(w[(i+1) % k], w[i])) for w in (base, top) for i in range(k)}
    lat = sub(A1, A)
    translation = all(sub(top[i], base[i]) == lat for i in range(k))
    perp = all(dot(G, lat, sub(base[(i+1) % k], base[i])) == 0 for i in range(k))
    area = abs(sum(F(base[i][0]) * base[(i+1) % k][1] - F(base[(i+1) % k][0]) * base[i][1] for i in range(k))) / 2
    v2 = (area * 1) ** 2 * det3(G)
    formula = (F(27, 4) if k == 6 else F(3, 16)) * b2 * b2 * h2                     # ((3√3/2)b²h)², ((√3/4)b²h)²
    label = r["expect"].split(":")[1]
    m = re.fullmatch(r"(\d+)?(?:√(\d+))?(?:/(\d+))?", label)
    label2 = F(int(m.group(1) or 1) ** 2 * int(m.group(2) or 1), int(m.group(3) or 1) ** 2)
    scene = json.loads((SCENES / f"{rid}.json").read_text(encoding="utf-8"))
    product_G = [[F(x) for x in row] for row in scene["chart_metric"]]
    row_ok = (sides == {b2} and translation and perp and dot(G, lat, lat) == h2 and v2 == formula == label2
              and product_G == G)
    ok &= row_ok
    print(f"{rid}: k={k} b²={b2} h²={h2} sides²={sorted(sides)} translation={translation} lateral⊥base={perp} "
          f"|AA′|²={dot(G, lat, lat)} V²={v2} formula={formula} label={label} G==chart_metric={product_G == G} "
          f"{'OK' if row_ok else 'MISMATCH'}")
print("ALL_OK" if ok else "FAILED")
