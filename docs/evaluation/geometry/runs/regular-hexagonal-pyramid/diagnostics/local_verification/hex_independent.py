"""LOCAL independent check (no product import): for every labelled hexagonal row, build the Gram metric from the TEXT's
lengths at S, A, B, C, apply it to the corpus program's AFFINE chart, and compute exactly:
  - V² from chart volume × det(G) (or SA² for the lateral question),
  - base regularity under the metric (all six sides² = b², opposite vertices through O),
  - apex on the normal through O, and |SO|² = h².
Compare with the textbook formula V = (√3/2)·b²·h, l² = h² + b² written independently here."""
import json, re, sys
from fractions import Fraction as F
from pathlib import Path

RUN = Path(sys.argv[1])
ROWS = json.loads((RUN / "labels.json").read_text(encoding="utf-8"))["rows"]
CORR = json.loads((RUN / "label_corrections.json").read_text(encoding="utf-8"))["rows"]
HEX = [(2, 1, 0), (1, 2, 0), (0, 2, 0), (0, 1, 0), (1, 0, 0), (2, 0, 0)]
LAYOUT = {"regular": (1, 1, 1), "apex_over_vertex": (2, 1, 1)}


def sq(v):
    m = re.fullmatch(r"(\d+(?:/\d+)?)?(?:√(\d+))?", v)
    q = F(m.group(1) or 1)
    return q * q * int(m.group(2) or 1)


def sub(p, q): return tuple(F(a) - F(b) for a, b in zip(p, q))
def det3(m): return (m[0][0]*(m[1][1]*m[2][2]-m[1][2]*m[2][1]) - m[0][1]*(m[1][0]*m[2][2]-m[1][2]*m[2][0])
                     + m[0][2]*(m[1][0]*m[2][1]-m[1][1]*m[2][0]))
def inv3(m):
    d = det3(m)
    c = [[(m[(j+1)%3][(i+1)%3]*m[(j+2)%3][(i+2)%3] - m[(j+1)%3][(i+2)%3]*m[(j+2)%3][(i+1)%3]) / d for j in range(3)] for i in range(3)]
    return c


def metric(b2, h2, A, B, C, S):
    """Chart metric G with vᵀGv = length², from the text's lengths at A, B, C, S."""
    e = [sub(B, A), sub(C, A), sub(S, A)]
    L = {(0, 0): b2, (1, 1): 3 * b2, (2, 2): b2 + h2}
    d2 = {(0, 1): b2, (0, 2): b2 + h2, (1, 2): b2 + h2}           # |e_i − e_j|²: BC², SB², SC²
    Ge = [[None]*3 for _ in range(3)]
    for i in range(3):
        Ge[i][i] = L[(i, i)]
    for (i, j), v in d2.items():
        Ge[i][j] = Ge[j][i] = (L[(i, i)] + L[(j, j)] - v) / 2
    M = [[e[c][r] for c in range(3)] for r in range(3)]          # columns = e_i
    Mi = inv3(M)
    return [[sum(Mi[a][r] * Ge[a][b] * Mi[b][c] for a in range(3) for b in range(3)) for c in range(3)] for r in range(3)]


def dot(G, u, v): return sum(u[r] * G[r][c] * v[c] for r in range(3) for c in range(3))


ok = True
for rid, r in ROWS.items():
    expect = CORR.get(rid, {}).get("now", r["expect"])
    if not expect.startswith("served"):
        continue
    d = r["dims"]
    b2 = sq(d["base"])
    h2 = sq(d["height"]) if "height" in d else sq(d["lateral"]) - b2
    S = LAYOUT[r["program"]]
    A, B, C = HEX[0], HEX[1], HEX[2]
    G = metric(b2, h2, A, B, C, S)
    O = (1, 1, 0)
    sides = {dot(G, sub(HEX[(i+1) % 6], HEX[i]), sub(HEX[(i+1) % 6], HEX[i])) for i in range(6)}
    centre_ok = all(sub(HEX[i], O) == tuple(-x for x in sub(HEX[i+3], O)) for i in range(3))
    so = sub(S, O)
    perp = all(dot(G, so, sub(HEX[i], O)) == 0 for i in range(6))
    hh = dot(G, so, so)
    # chart volume of the pyramid (apex height 1 above z = 0, hexagon area by shoelace) × sqrt(det G)
    area = abs(sum(F(HEX[i][0]) * HEX[(i+1) % 6][1] - F(HEX[(i+1) % 6][0]) * HEX[i][1] for i in range(6))) / 2
    v2 = (area / 3) ** 2 * det3(G)
    want = F(3, 4) * b2 * b2 * h2 if r["ask"] == "volume" else h2 + b2
    got = v2 if r["ask"] == "volume" else dot(G, sub(S, A), sub(S, A))
    row_ok = sides == {b2} and centre_ok and perp and hh == h2 and got == want
    ok &= row_ok
    print(f"{rid}: program={r['program']} sides²={sorted(sides)} perp={perp} |SO|²={hh} (h²={h2}) "
          f"{'V²' if r['ask']=='volume' else 'SA²'}={got} formula={want} label={expect} {'OK' if row_ok else 'MISMATCH'}")
print("ALL_OK" if ok else "FAILED")
