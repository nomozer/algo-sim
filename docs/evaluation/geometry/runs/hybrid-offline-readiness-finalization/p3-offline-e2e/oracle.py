"""Independent mathematical oracle for the 12 served Hybrid preview fixtures (HFOI P3).

Expected values come from MY OWN coordinates placed from each problem statement (Euclidean, hand derivation below),
never from backend code. Backend answers are parsed from `route_d.answers` and compared at a = 1 and a = 2 (so the
power of a is checked, not only the a = 1 number). The two answer-less scenes are checked on affine invariants
(parallelism, incidence, midpoints) in the scene's own chart coordinates — those hold under any chart metric.
usage: python oracle.py <fixtures-adapter-2 dir> <out.json>
"""
import json, math, re, sys
from fractions import Fraction
from pathlib import Path

R3 = math.sqrt


def sub(p, q): return tuple(a - b for a, b in zip(p, q))
def add(p, q): return tuple(a + b for a, b in zip(p, q))
def mul(p, k): return tuple(a * k for a in p)
def dot(p, q): return sum(a * b for a, b in zip(p, q))
def cross(p, q): return (p[1]*q[2]-p[2]*q[1], p[2]*q[0]-p[0]*q[2], p[0]*q[1]-p[1]*q[0])
def norm(p): return math.sqrt(dot(p, p))
def mid(p, q): return mul(add(p, q), 0.5)
def tri_area(a, b, c): return norm(cross(sub(b, a), sub(c, a))) / 2
def foot_on_line(p, a, b):
    d = sub(b, a); t = dot(sub(p, a), d) / dot(d, d); return add(a, mul(d, t))
def dist_point_plane(p, a, b, c):
    n = cross(sub(b, a), sub(c, a)); return abs(dot(sub(p, a), n)) / norm(n)
def dist_skew(a1, a2, b1, b2):
    n = cross(sub(a2, a1), sub(b2, b1)); return abs(dot(sub(b1, a1), n)) / norm(n)
def cos2_line_plane(p, q, a, b, c):
    d = sub(q, p); n = cross(sub(b, a), sub(c, a))
    sin = abs(dot(d, n)) / (norm(d) * norm(n)); return 1 - sin * sin


def expected(case: str, a: float) -> dict:
    """Hand coordinates from the statement; keys are the quantity the problem asks."""
    if case == "H01_CUBE":
        A, C1 = (0, 0, 0), (a, a, a)
        return {"V": a ** 3, "AC'": norm(sub(C1, A))}
    if case == "H02_CUBOID_DISTANCE":           # AB = a (x), AD = 2a (y), AA' = 3a (z)
        A, B, D, A1 = (0, 0, 0), (a, 0, 0), (0, 2 * a, 0), (0, 0, 3 * a)
        return {"V": a * 2 * a * 3 * a, "d": dist_point_plane(A, A1, B, D)}
    if case == "H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS":   # base a, lateral a√2, apex over centre
        A, B, C = (0, 0, 0), (a, 0, 0), (a, a, 0)
        O = (a / 2, a / 2, 0); h = R3(2 * a * a - dot(sub(A, O), sub(A, O))); S = (a / 2, a / 2, h)
        return {"V": a * a * h / 3, "cos2": cos2_line_plane(S, A, A, B, C)}
    if case == "H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED":    # right angle at B, AB = a, BC = a√3, SA ⊥ base, SA = 2a
        B, A, C = (0, 0, 0), (a, 0, 0), (0, a * R3(3), 0); S = (a, 0, 2 * a)
        bc_perp_sab = abs(dot(sub(C, B), sub(A, B))) < 1e-9 and abs(dot(sub(C, B), sub(S, B))) < 1e-9
        return {"V": tri_area(A, B, C) * 2 * a / 3, "BC_perp_SAB": bc_perp_sab}
    if case == "H11_SKEW_DISTANCE_COMPOSITION":   # right prism, right at A, AB = a, AC = 2a, AA' = 2a; M mid BC
        A, B, C = (0, 0, 0), (a, 0, 0), (0, 2 * a, 0); B1 = (a, 0, 2 * a); M = mid(B, C)
        return {"d": dist_skew(A, M, B1, C)}
    if case == "H12_PROJECTION_MIDPOINT_ANGLE":   # equilateral a, H mid AB, SH ⊥ base, SH = a√3/2
        A, B = (0, 0, 0), (a, 0, 0); C = (a / 2, a * R3(3) / 2, 0); H = mid(A, B); S = (H[0], H[1], a * R3(3) / 2)
        return {"V": tri_area(A, B, C) * S[2] / 3, "cos2": cos2_line_plane(S, C, A, B, C)}
    if case == "H14_REGULAR_TETRAHEDRON":
        return {"V": a ** 3 / (6 * R3(2))}
    # square base side 2, SA = 3 vertical at A (numbers: a has no role)
    A, B, C, D, S = (0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0), (0, 0, 3)
    M = mid(S, C)
    if case == "pyramid-midpoint-area-AB":
        return {"S": tri_area(M, A, B)}
    if case == "pyramid-projection-and-unnamed-midpoint-area":
        H = foot_on_line(A, S, B); return {"S": tri_area(M, H, D)}
    if case == "pyramid-shared-midpoint-area-and-distance":
        return {"S": tri_area(M, A, B), "d": dist_point_plane(M, S, A, B)}
    raise KeyError(case)


def parse_answer(text: str, a: float) -> float:
    """Backend answer string → number at a (`a³√6/6`, `6a/7`, `cos²=1/4`, `√1018/26`)."""
    s = text.split("=")[-1].strip()
    s = s.replace("³", "**3").replace("²", "**2")
    s = re.sub(r"(\d)a", r"\1*a", s); s = re.sub(r"a(\*\*\d)?√", lambda m: f"a{m.group(1) or ''}*√", s)
    s = re.sub(r"(\d|a)√", r"\1*√", s)
    s = re.sub(r"√(\d+)", r"math.sqrt(\1)", s)
    return float(eval(s, {"math": math, "a": a}))          # strings are the frozen fixture's, not user input


# fixture call id → quantity key of `expected`, by reading the problem (order of the questions)
ANSWER_KEY = {
    "H01_CUBE": {"f3": "V", "f4": "AC'"}, "H02_CUBOID_DISTANCE": {"f5": "V", "f6": "d"},
    "H03_REGULAR_SQUARE_PYRAMID_ROLE_LENGTHS": {"f4": "V", "f5": "cos2"},
    "H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED": {"f8": "V"}, "H11_SKEW_DISTANCE_COMPOSITION": {"f7": "d"},
    "H12_PROJECTION_MIDPOINT_ANGLE": {"f6": "V", "f7": "cos2"}, "H14_REGULAR_TETRAHEDRON": {"f3": "V"},
    "pyramid-midpoint-area-AB": {"q": "S"}, "pyramid-projection-and-unnamed-midpoint-area": {"q": "S"},
    "pyramid-shared-midpoint-area-and-distance": {"q1": "S", "q2": "d"},
}


def chart_points(scene) -> dict:
    return {o["id"]: tuple(float(Fraction(x)) for x in o["xyz"]) for o in scene["objects"] if o.get("xyz")}


def check_affine(case: str, scene) -> dict:
    P = chart_points(scene)
    if case == "intersection-SAB-SCD":       # (SAB) ∩ (SCD) is the line through S parallel to AB (AB ∥ CD)
        lines = [o for o in scene["objects"] if o.get("type") == "line3"]
        ok = [o["id"] for o in lines
              if norm(cross(tuple(float(Fraction(x)) for x in o["direction"]), sub(P["B"], P["A"]))) < 1e-9
              and norm(cross(sub(tuple(float(Fraction(x)) for x in o["point"]), P["S"]),
                             tuple(float(Fraction(x)) for x in o["direction"]))) < 1e-9]
        return {"line_through_S_parallel_AB": ok, "pass": bool(ok)}
    if case == "section-MAB-trapezoid":      # (MAB) cuts SD at its midpoint N (MN ∥ CD ∥ AB): trapezoid A B M N
        M, N = mid(P["S"], P["C"]), mid(P["S"], P["D"])
        # The cut is a `section` object carrying its `polygon` (not a `polygon3` face of the solid).
        polys = [o for o in scene["objects"] if o.get("type") == "section" and o.get("polygon")]
        found = []
        for o in polys:
            vs = [tuple(float(Fraction(x)) for x in v) for v in o["polygon"]]
            want = [P["A"], P["B"], M, N]
            if len(vs) == 4 and all(any(norm(sub(v, w)) < 1e-9 for v in vs) for w in want):
                found.append(o["id"])
        return {"trapezoid_ABMN": found, "pass": bool(found)}
    raise KeyError(case)


def main(src: Path, out: Path):
    rows = []
    for p in sorted(src.glob("served-*.json")):
        case = p.stem.removeprefix("served-")
        resp = json.loads(p.read_text(encoding="utf-8"))["response"]
        rd, scene = resp["route_d"], resp["envelope"]["scene3d"]
        if case in ANSWER_KEY:
            checks = []
            for call, key in ANSWER_KEY[case].items():
                for a in (1.0, 2.0):
                    got, want = parse_answer(rd["answers"][call], a), expected(case, a)[key]
                    checks.append({"call": call, "quantity": key, "a": a, "backend": got, "oracle": want,
                                   "pass": math.isclose(got, want, rel_tol=1e-9, abs_tol=1e-12)})
            extra = {}
            if case == "H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED":
                obs = rd["planner"]["goal_checks"]["f7"]["evidence_state"]
                extra = {"goal_BC_perp_SAB_oracle": expected(case, 1.0)["BC_perp_SAB"], "backend_observation": obs,
                         "pass_observation": (obs == "TRUE_ON_CONFIGURATION") == expected(case, 1.0)["BC_perp_SAB"]}
            rows.append({"case": case, "checks": checks, **extra,
                         "pass": all(c["pass"] for c in checks) and extra.get("pass_observation", True)})
        else:
            rows.append({"case": case, **check_affine(case, scene)})
    # Witness window: known-wrong answers must FAIL (the a = 1 value with the wrong power of a, a wrong coefficient).
    witness = [
        ("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "V", "a²√3/3"), ("H07_PROOF_GOAL_NOT_PREMISE_BUT_CHECKED", "V", "a³√3/2"),
        ("H02_CUBOID_DISTANCE", "d", "6a/5"), ("pyramid-midpoint-area-AB", "S", "√13"),
    ]
    caught = [not all(math.isclose(parse_answer(w, a), expected(c, a)[k], rel_tol=1e-9) for a in (1.0, 2.0))
              for c, k, w in witness]
    res = {"schema": "HFOI_ORACLE/1", "independence": "hand coordinates from the statement; no backend import",
           "cases": len(rows), "pass": sum(r["pass"] for r in rows),
           "witness_wrong_answers_caught": f"{sum(caught)}/{len(caught)}", "rows": rows}
    assert all(caught), "oracle failed its witness window"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"oracle {res['pass']}/{res['cases']}")
    for r in rows:
        if not r["pass"]:
            print("FAIL", json.dumps(r, ensure_ascii=False)[:600])


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
