"""Independent exact validator for served Scene3D payloads (does not import product code).

Coordinates are exact rationals in an affine chart; every inner product goes through the scene's Gram matrix G
(`chart_metric`), plane normals are covectors u×v measured with G⁻¹. Nothing is read from the screen.
usage: python scene_oracle.py <manifest.json> <responses.jsonl> <out.json>      (self-check: python scene_oracle.py --selfcheck)
"""

from fractions import Fraction as F
import json
import os
import re
import sys

TOKEN = re.compile(r"[A-Z][0-9]*'?")


def pid(tok: str) -> str:
    return tok.replace("'", "_prime")


def pts(s: str) -> list[str]:
    return [pid(t) for t in TOKEN.findall(s)]


def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def iszero(v): return all(x == 0 for x in v)


def inv3(m):
    (a, b, c), (d, e, f), (g, h, i) = m
    det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)
    if det == 0:
        raise ValueError("singular metric")
    adj = ((e * i - f * h, c * h - b * i, b * f - c * e), (f * g - d * i, a * i - c * g, c * d - a * f),
           (d * h - e * g, b * g - a * h, a * e - b * d))
    return tuple(tuple(x / det for x in row) for row in adj)


class Scene:
    def __init__(self, scene: dict):
        self.G = tuple(tuple(F(x) for x in row) for row in scene["chart_metric"])
        self.Gi = inv3(self.G)
        self.objs = {o["id"]: o for o in scene["objects"]}
        self.P = {o["id"]: tuple(F(x) for x in o["xyz"]) for o in scene["objects"] if o["type"] == "point3"}

    def dot(self, u, v, M=None):
        M = M or self.G
        return sum(u[i] * M[i][j] * v[j] for i in range(3) for j in range(3))

    def vec(self, seg):
        a, b = pts(seg)[:2]
        return sub(self.P[b], self.P[a])

    def normal(self, plane):
        a, b, c = pts(plane)[:3]
        return cross(sub(self.P[b], self.P[a]), sub(self.P[c], self.P[a]))


def check_relation(sc: Scene, rel: list) -> bool:
    k, *args = rel
    if k == "len2":
        v = sc.vec(args[0]); return sc.dot(v, v) == F(args[1])
    if k == "eq":
        u, v = sc.vec(args[0]), sc.vec(args[1]); return sc.dot(u, u) == sc.dot(v, v)
    if k == "ratio2":  # /11: |XY|^2 / |ZT|^2 = r — unit-free (problems stated in cm)
        u, v = sc.vec(args[0]), sc.vec(args[1]); return sc.dot(u, u) == F(args[2]) * sc.dot(v, v)
    if k == "dot":
        return sc.dot(sc.vec(args[0]), sc.vec(args[1])) == F(args[2])
    if k == "perp_ll":
        return sc.dot(sc.vec(args[0]), sc.vec(args[1])) == 0
    if k == "par_ll":
        return iszero(cross(sc.vec(args[0]), sc.vec(args[1])))
    if k == "perp_lp":
        d = sc.vec(args[0]); a, b, c = pts(args[1])[:3]
        return sc.dot(d, sub(sc.P[b], sc.P[a])) == 0 and sc.dot(d, sub(sc.P[c], sc.P[a])) == 0
    if k == "perp_pp":
        return sc.dot(sc.normal(args[0]), sc.normal(args[1]), sc.Gi) == 0
    if k == "dist2":
        p = sc.P[pid(args[0])]; a = pts(args[1])[0]; n = sc.normal(args[1])
        num = sum(n[i] * (p[i] - sc.P[a][i]) for i in range(3))
        return num * num / sc.dot(n, n, sc.Gi) == F(args[2])
    if k == "mid":
        m = sc.P[pid(args[0])]; a, b = pts(args[1]); return all(2 * m[i] == sc.P[a][i] + sc.P[b][i] for i in range(3))
    if k == "ratio":
        m, x, y = (sc.P[pid(t)] for t in args[:3]); t = F(args[3])
        return all(m[i] == x[i] + t * (y[i] - x[i]) for i in range(3))
    if k == "centroid":
        g = sc.P[pid(args[0])]; a, b, c = pts(args[1])
        return all(3 * g[i] == sc.P[a][i] + sc.P[b][i] + sc.P[c][i] for i in range(3))
    if k == "foot_line":
        h, a = sc.P[pid(args[0])], sc.P[pid(args[1])]; x, y = pts(args[2])
        d = sub(sc.P[y], sc.P[x])
        return iszero(cross(sub(h, sc.P[x]), d)) and sc.dot(sub(a, h), d) == 0
    raise KeyError(k)


def structural(sc: Scene, case: dict) -> tuple[dict, list[str]]:
    """Solid topology / planarity / references / fabricated points."""
    issues = []
    solids = [o for o in sc.objs.values() if o["type"] == "solid"]
    gold_v = [pid(v) for v in case["gold_entities"]["solid_vertices"]]
    solid = next((s for s in solids if set(s.get("vertex_ids", [])) == set(gold_v)), None)
    if solid is None:
        issues.append(f"NO_SOLID_WITH_GOLD_VERTICES {sorted(gold_v)} got {[s.get('vertex_ids') for s in solids]}")
        return {"solid_found": False}, issues
    vids, faces = solid["vertex_ids"], solid["faces"]
    exp = case["expected_counts"]
    if len(vids) != exp["vertices"]: issues.append(f"VERTEX_COUNT {len(vids)}!={exp['vertices']}")
    if len(faces) != exp["faces"]: issues.append(f"FACE_COUNT {len(faces)}!={exp['faces']}")
    V = [tuple(F(x) for x in v) for v in solid["vertices"]]
    for vid, v in zip(vids, V):
        if sc.P.get(vid) != v: issues.append(f"SOLID_VERTEX_MISMATCH {vid}")
    edges = {tuple(sorted((f[i], f[(i + 1) % len(f)]))) for f in faces for i in range(len(f))}
    if len(V) - len(edges) + len(faces) != 2: issues.append("EULER_CHARACTERISTIC_NOT_2")
    for f in faces:
        n = cross(sub(V[f[1]], V[f[0]]), sub(V[f[2]], V[f[0]]))
        if iszero(n): issues.append(f"DEGENERATE_FACE {f}")
        elif any(sum(n[i] * (V[q][i] - V[f[0]][i]) for i in range(3)) != 0 for q in f[3:]):
            issues.append(f"NON_PLANAR_FACE {f}")
    # volume ≠ 0: some vertex off the first face plane
    n0 = cross(sub(V[faces[0][1]], V[faces[0][0]]), sub(V[faces[0][2]], V[faces[0][0]]))
    if all(sum(n0[i] * (v[i] - V[faces[0][0]][i]) for i in range(3)) == 0 for v in V): issues.append("FLAT_SOLID")
    dangling = sorted({d for o in sc.objs.values() for d in o.get("depends", []) if d not in sc.objs})
    if dangling: issues.append(f"DANGLING_REFERENCES {dangling}")
    gold_all = set(gold_v) | {pid(a) for a in case["gold_entities"]["auxiliary_points"]}
    missing = sorted(gold_all - set(sc.P))
    if missing: issues.append(f"MISSING_GOLD_POINTS {missing}")
    free_extra = sorted(p for p, o in sc.objs.items() if o["type"] == "point3" and o.get("origin") == "free" and p not in gold_all)
    # v2 (A2): a free point that IS the centroid of a solid face is the layout centre (foot of a regular solid's
    # height), geometrically justified — recorded as a finding, not as fabrication. Anything else stays fabricated.
    face_centres = {tuple(sum(V[q][i] for q in f) / len(f) for i in range(3)) for f in faces}
    layout = [p for p in free_extra if sc.P[p] in face_centres]
    free_extra = [p for p in free_extra if p not in layout]
    if free_extra: issues.append(f"FABRICATED_FREE_POINTS {free_extra}")
    findings = [f"UNDECLARED_LAYOUT_CENTRE {p}" + (" LABELED_GIVEN" if "given" in (sc.objs[p].get("display_group") or []) else "")
                for p in layout]
    derived_extra = sorted(p for p, o in sc.objs.items() if o["type"] == "point3" and o.get("origin") != "free" and p not in gold_all)
    types = sorted({o["type"] for o in sc.objs.values()})
    # v2 (A3): edges/faces may be drawn from the solid's own edge ownership (tetrahedra do), so only solid + points
    # are required object types; segment3/polygon3 are recorded, not demanded.
    lacking = [t for t in ("solid", "point3") if t not in types]
    if lacking: issues.append(f"MISSING_OBJECT_TYPES {lacking}")
    return {"solid_found": True, "solid_id": solid["id"], "vertices": len(vids), "faces": len(faces), "edges": len(edges),
            "derived_auxiliary_points": derived_extra, "object_types": types, "findings": findings,
            "metric_is_identity": sc.G == ((1, 0, 0), (0, 1, 0), (0, 0, 1))}, issues


def numeric(answers: dict, exact: dict, gold: list[float]) -> dict:
    """Served answers vs gold floats (display strings like 'a√3/2', '45°', 'arctan(√2)' parsed best-effort)."""
    import math

    def num(t: str) -> float:
        t = t.replace("°", "").replace("π", "*math.pi").replace("a³", "").replace("a²", "").replace("a", "")
        t = re.sub(r"(\d)√", r"\1*√", t)
        t = re.sub(r"√\(([^)]*)\)", r"math.sqrt(\1)", t)
        t = re.sub(r"√(\d+)", r"math.sqrt(\1)", t)
        return float(eval(t, {"math": math, "__builtins__": {}}))

    vals = []
    for k, s in (answers or {}).items():
        try:
            trig = re.match(r"\s*(cos|sin|tan)(²?)\s*=\s*(.+)$", str(s))   # v2 (A1): angles served as cos²=1/2 etc.
            if trig:
                fn, sq, rhs = trig.groups()
                x = num(rhs) ** (0.5 if sq else 1)
                vals.append(math.degrees({"cos": math.acos, "sin": math.asin, "tan": math.atan}[fn](x)))
            elif str(s).startswith("arctan"):
                vals.append(math.degrees(math.atan(num(str(s)[6:]))))
            else:
                vals.append(num(str((exact or {}).get(k, {}).get("coef") or s)))
        except Exception:
            vals.append(None)
    matched = sum(any(v is not None and abs(v - g) < 1e-9 * max(1, abs(g)) for v in vals) for g in gold)
    return {"served": answers, "parsed": vals, "gold": gold, "matched": matched, "of": len(gold),
            "status": "CORRECT" if matched == len(gold) else ("UNPARSED" if None in vals else "MISMATCH")}


def validate(case: dict, body: dict) -> dict:
    rd = body.get("route_d") or {}
    scene = (body.get("envelope") or {}).get("scene3d")
    out = {"case_id": case["case_id"], "route_status": rd.get("status")}
    if rd.get("status") != "SERVED" or not scene:
        out["scene_validation"] = "NOT_SERVED"
        return out
    try:
        sc = Scene(scene)
        info, issues = structural(sc, case)
        rels = []
        if info.get("solid_found"):
            for r in case["gold_relations"]:
                try:
                    ok = check_relation(sc, r)
                except KeyError as e:
                    ok = None; issues.append(f"MISSING_POINT_FOR_RELATION {r} {e}")
                rels.append({"relation": r, "holds": ok})
                if ok is False: issues.append(f"RELATION_VIOLATED {r}")
        out.update(info, relations=rels, issues=issues,
                   scene_validation="MATHEMATICALLY_VALID" if not issues else "MATHEMATICALLY_INVALID")
    except Exception as e:  # unparseable scene is never a pass
        out.update(scene_validation="VALIDATION_ERROR", issues=[f"{type(e).__name__}: {e}"])
    if case.get("metric_oracle"):
        out["numeric"] = numeric(rd.get("answers"), rd.get("answer_exact"), case["metric_oracle"])
    return out


def selfcheck():
    sq = {"chart_metric": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]], "objects": [
        *({"id": i, "type": "point3", "origin": "free", "xyz": x, "depends": []} for i, x in
          [("A", ["0", "0", "0"]), ("B", ["1", "0", "0"]), ("C", ["1", "1", "0"]), ("D", ["0", "1", "0"]), ("S", ["0", "0", "1"])]),
        {"id": "k", "type": "solid", "depends": ["A", "B", "C", "D", "S"], "vertex_ids": ["S", "A", "B", "C", "D"],
         "vertices": [["0", "0", "1"], ["0", "0", "0"], ["1", "0", "0"], ["1", "1", "0"], ["0", "1", "0"]],
         "faces": [[1, 2, 3, 4], [0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 1]]},
        {"id": "p", "type": "polygon3", "depends": ["A"]}, {"id": "s", "type": "segment3", "depends": ["A"]}]}
    case = {"case_id": "self", "gold_entities": {"solid_vertices": ["S", "A", "B", "C", "D"], "auxiliary_points": []},
            "expected_counts": {"vertices": 5, "faces": 5}, "expected_scene_object_types": ["solid", "point3"],
            "gold_relations": [["perp_lp", "SA", "ABC"], ["len2", "AB", "1"], ["eq", "AB", "BC"], ["dist2", "S", "ABC", "1"],
                               ["perp_pp", "SAB", "ABC"], ["perp_ll", "AB", "AD"]], "metric_oracle": None}
    body = lambda s: {"route_d": {"status": "SERVED"}, "envelope": {"scene3d": s}}
    assert validate(case, body(sq))["scene_validation"] == "MATHEMATICALLY_VALID"
    bad = json.loads(json.dumps(sq)); bad["objects"][4]["xyz"] = ["1/2", "0", "1"]; bad["objects"][5]["vertices"][0] = ["1/2", "0", "1"]
    r = validate(case, body(bad)); assert r["scene_validation"] == "MATHEMATICALLY_INVALID", r      # tilted apex caught
    skew = json.loads(json.dumps(sq)); skew["chart_metric"] = [["1", "1/2", "0"], ["1/2", "1", "0"], ["0", "0", "1"]]
    r = validate(case, body(skew)); assert any("perp_ll" in i for i in r["issues"]), r               # metric honoured: rhombus ≠ square
    fab = json.loads(json.dumps(sq)); fab["objects"].append({"id": "X", "type": "point3", "origin": "free", "xyz": ["2", "2", "2"], "depends": []})
    assert any("FABRICATED" in i for i in validate(case, body(fab))["issues"])
    assert numeric({"q1": "a√3/2"}, {"q1": {"coef": "√3/2"}}, [0.8660254037844386])["status"] == "CORRECT"
    assert numeric({"q1": "45°"}, {}, [45.0])["status"] == "CORRECT"
    assert numeric({"q1": "a/3"}, {"q1": {"coef": "1/3"}}, [0.5])["status"] == "MISMATCH"
    assert check_relation(Scene(sq), ["ratio2", "SB", "AB", "2"]) and not check_relation(Scene(sq), ["ratio2", "SB", "AB", "3"])
    assert numeric({"q1": "cos²=1/2"}, {}, [45.0])["status"] == "CORRECT"                          # v2 A1
    assert numeric({"q1": "cos²=1/3"}, {}, [54.735610317245346])["status"] == "CORRECT"
    assert numeric({"q1": "cos²=1/3"}, {}, [45.0])["status"] == "MISMATCH"
    reg = json.loads(json.dumps(sq)); reg["objects"].append({"id": "O", "type": "point3", "origin": "free", "xyz": ["1/2", "1/2", "0"],
                                                           "depends": [], "display_group": ["given"]})
    r = validate(case, body(reg)); assert r["scene_validation"] == "MATHEMATICALLY_VALID" and r["findings"], r  # v2 A2
    off = json.loads(json.dumps(sq)); off["objects"].append({"id": "O", "type": "point3", "origin": "free", "xyz": ["1/3", "1/2", "0"], "depends": []})
    assert any("FABRICATED" in i for i in validate(case, body(off))["issues"])                     # off-centre stays fabricated
    print("scene_oracle selfcheck OK")


if __name__ == "__main__":
    if sys.argv[1] == "--selfcheck":
        selfcheck(); sys.exit(0)
    if os.path.exists(sys.argv[3]):
        sys.exit(f"refusing to overwrite {sys.argv[3]}: evidence is never overwritten")
    man = json.load(open(sys.argv[1], encoding="utf-8"))
    cases = {c["case_id"]: c for c in man["valid_cases"] + man["negative_cases"]}
    rows = [json.loads(l) for l in open(sys.argv[2], encoding="utf-8") if l.strip()]
    res = [validate(cases[r["case_id"]], r["body"]) for r in rows if r["case_id"] in cases and r.get("body")]
    json.dump({"schema": "axo-scene3d-mathematical-validation/1", "validator": "tools/scene_oracle.py v2 (independent; exact Fraction, Gram metric; amendments A1-A3 after pass 1)",
               "results": res}, open(sys.argv[3], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print({k: sum(r.get("scene_validation") == k for r in res) for k in
           ("MATHEMATICALLY_VALID", "MATHEMATICALLY_INVALID", "VALIDATION_ERROR", "NOT_SERVED")})
