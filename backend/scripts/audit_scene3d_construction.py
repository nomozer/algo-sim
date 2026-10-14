"""Construction audit of served Hybrid two-line scenes: every point, every trace step, metamorphic variants.

Harness, not product. Reads `scenes.json` exported by `export_hybrid_section_scenes.py --scenes two-line`, checks
each object against its producer with exact fractions in the CHART frame, and the section against the independent
research oracle `tests/geometry/two_line_plane_oracle.py` (facet halfspaces, Gram area). Incidence uses covectors only;
no Euclidean dot product is applied to chart coordinates. Metamorphic variants re-run the real Hybrid route (fake
facts, 0 model calls) and go through the same point, section and step checks. `--browser <browser-check.json>` (from
`frontend/scripts/hybrid-section-visual-check.mjs --playback`) adds world-space metric checks and the per-step visual
verdicts to the step table.

  cd backend && PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe scripts/audit_scene3d_construction.py \
      --scenes <scenes.json> --out <new dir> [--browser <browser-check.json>]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tests.geometry.two_line_plane_oracle import cross, dot, fixture_model, section, sub  # noqa: E402

PRIME = "′"


def vec(v):
    return tuple(F(x) for x in v)


def notation_points(notation: str) -> list[str]:
    """`BB′` → ['B', 'B_prime'] (scene ids)."""
    return [m[0] + ("_prime" if m[1] else "") for m in re.findall(r"([A-Z])(" + PRIME + "?)", notation)]


def side(halfspaces, p):
    vals = [dot(f, p) - z for f, z in halfspaces]
    return "OUTSIDE" if any(v > 0 for v in vals) else "BOUNDARY" if any(v == 0 for v in vals) else "INSIDE"


def on_segment(p, a, b):
    d, e = sub(b, a), sub(p, a)
    if any(cross(d, e)):
        return False
    t = dot(e, d) / dot(d, d)  # collinear: affine parameter, metric-free
    return 0 <= t <= 1


def solid_halfspaces(pts, faces):
    verts = {k for f in faces for k in f}
    out = []
    for face in faces:
        a, b, c = (pts[k] for k in face[:3])
        f = cross(sub(b, a), sub(c, a))
        z = dot(f, a)
        if any(dot(f, pts[k]) - z > 0 for k in verts):
            f, z = tuple(-x for x in f), -z
        out.append((f, z))
    return out


def audit_scene(scene, case):
    """All point/plane/section checks of one served scene."""
    fx_pts, faces, gram = fixture_model(case["family"])
    sid = lambda k: k.replace("'", "_prime")  # fixture name → scene id
    objs = {o["id"]: o for o in scene["objects"]}
    P = {o["id"]: vec(o["xyz"]) for o in scene["objects"] if o["type"] in ("point3", "vector3")}
    fails, points = [], []
    if tuple(tuple(map(F, r)) for r in scene["chart_metric"]) != tuple(tuple(map(F, r)) for r in gram):
        fails.append("chart_metric differs from the fixture Gram matrix")
    halfspaces = solid_halfspaces(fx_pts, faces)
    for k, xyz in fx_pts.items():
        if P.get(sid(k)) != vec(xyz):
            fails.append(f"given point {sid(k)} {P.get(sid(k))} != fixture {xyz}")
    mids = [o for o in scene["objects"] if o.get("producer") == "construct_point.midpoint"]
    trans = [o for o in scene["objects"] if o.get("producer") == "construct_point.translate"]
    vecs = {o["id"]: o for o in scene["objects"] if o.get("producer") == "vector_from_points"}
    plane = next(o for o in scene["objects"] if o["type"] == "plane3")
    sec = next(o for o in scene["objects"] if o["type"] == "section")
    if len(mids) != 1 or len(trans) != 2:
        fails.append(f"expected 1 midpoint + 2 translates, got {len(mids)} + {len(trans)}")
    m = mids[0]
    want_mid = {sid(x) for x in case["mid"]}
    anchor = tuple((vec(fx_pts[case["mid"][0]])[i] + vec(fx_pts[case["mid"][1]])[i]) / 2 for i in range(3))
    lines = [tuple(sid(x) for x in ln) for ln in case["lines"]]
    for o in scene["objects"]:
        if o["type"] != "point3":
            continue
        row = {"id": o["id"], "label": o["label"], "producer": o.get("producer"), "depends": o["depends"],
               "binding": o.get("source", {}).get("binding"), "chart_xyz": o["xyz"], "checks": {}}
        c = row["checks"]
        if o.get("producer") is None:
            row["definition"] = "given vertex (fixture chart)"
            fixture_name = next((k for k in fx_pts if sid(k) == o["id"]), None)
            c["fixture"] = fixture_name is not None and P[o["id"]] == vec(fx_pts[fixture_name])
        elif o["producer"] == "construct_point.midpoint":
            a, b = o["depends"]
            row["definition"] = f"midpoint of {a}{b}"
            c["midpoint"] = P[o["id"]] == tuple((P[a][i] + P[b][i]) / 2 for i in range(3))
            c["source_pair_is_declared"] = set(o["depends"]) == want_mid
            c["equals_oracle_anchor"] = P[o["id"]] == anchor
        elif o["producer"] == "construct_point.translate":
            base = next(d for d in o["depends"] if d not in vecs)
            v = next(d for d in o["depends"] if d in vecs)
            vo = vecs[v]
            p, q = notation_points(vo["notation"])
            row["definition"] = f"{base} + vector {vo['notation']}"
            c["vector_is_endpoint_difference"] = P[v] == sub(P[q], P[p])
            c["vector_line_is_declared"] = any({p, q} == set(ln) for ln in lines)
            c["translate"] = P[o["id"]] == tuple(P[base][i] + P[v][i] for i in range(3))
            c["base_is_midpoint"] = base == m["id"]
            c["auxiliary_role"] = o.get("source", {}).get("binding") == "AUXILIARY" and o["role"] == "Điểm dựng phụ"
            row["line"] = frozenset((p, q))
        else:
            c["producer_has_a_check"] = False  # review: an unknown producer must not pass with no check
        row["solid"] = side(halfspaces, P[o["id"]])
        if not all(c.values()):
            fails.append(f"point {o['id']}: {[k for k, v in c.items() if not v]}")
        points.append(row)
    # the two auxiliary points use the two DIFFERENT declared lines, and M, H, H1 are not collinear
    aux = [r for r in points if "line" in r]
    if len({r.pop("line") for r in aux}) != 2:
        fails.append("auxiliary points do not use two different declared lines")
    if len(aux) == 2 and not any(cross(sub(P[aux[0]["id"]], P[m["id"]]), sub(P[aux[1]["id"]], P[m["id"]]))):
        fails.append("M and the auxiliary points are collinear")
    # plane: covector through the three defining points, strict parallel to both declared lines
    n, pt = vec(plane["normal"]), vec(plane["point"])
    d = dot(n, pt)
    pc = {"defining_points_on_plane": all(dot(n, P[k]) == d for k in plane["depends"]),
          "normal_nonzero": any(n),
          "strict_parallel": [{"line": "".join(ln), "direction_in_plane": dot(n, sub(P[ln[1]], P[ln[0]])) == 0,
                               "not_contained": dot(n, P[ln[0]]) != d} for ln in lines],
          "named": plane["label"] == "(P)" and "(P)" in sec["label"]}
    if not (pc["defining_points_on_plane"] and pc["normal_nonzero"] and pc["named"]
            and all(x["direction_in_plane"] and x["not_contained"] for x in pc["strict_parallel"])):
        fails.append(f"plane checks {pc}")
    # section vs independent oracle
    oracle = section(fx_pts, faces, anchor, case["lines"], gram)
    ring = [vec(p) for p in sec["polygon"]]
    edges = lambda ps: {frozenset((a, b)) for a, b in zip(ps, ps[1:] + ps[:1])}
    ent = sec["endpoint_entities"]
    solid_obj = objs[sec["depends"][0]]
    sverts = [vec(v) for v in solid_obj["vertices"]]
    on_edges = []
    for e in ent:
        a, b = re.search(r"::edge:(.+)-(.+)$", e["entity_id"]).groups()
        p = ring[e["section_vertex_ordinal"]]
        on_edges.append({"entity": e["entity_id"], "on_edge": on_segment(p, P[a], P[b]), "on_plane": dot(n, p) == d})
    answer = F(scene_answer(scene))
    sc = {"oracle_status": oracle["status"],
          "vertex_set_equals_oracle": oracle["status"] == "SERVED" and set(ring) == set(oracle["vertices"]),
          "edge_set_equals_oracle": oracle["status"] == "SERVED" and edges(ring) == edges(list(oracle["vertices"])),
          "vertices_on_named_solid_edges": all(x["on_edge"] and x["on_plane"] for x in on_edges),
          "area_squared_equals_oracle": oracle["status"] == "SERVED" and answer_sq(scene) == oracle["area_sq"],
          "area_readout": answer, "oracle_area_sq": str(oracle.get("area_sq"))}
    if not all(v for k, v in sc.items() if k not in ("area_readout", "oracle_status", "oracle_area_sq")):
        fails.append(f"section checks {sc}")
    # progressive section segments: each lies in the named face and joins the named edges
    seg = []
    for k, s in enumerate(sec["steps"]):
        face = [sverts[i] for i in solid_obj["faces"][s["face_index"]]]
        f = cross(sub(face[1], face[0]), sub(face[2], face[0]))
        seg.append({"k": k, "face": "".join(solid_obj["vertex_ids"][i].replace("_prime", PRIME)
                                           for i in solid_obj["faces"][s["face_index"]]),
                    "in_face": all(dot(f, vec(x)) == dot(f, face[0]) for x in (s["a"], s["b"])),
                    "a": s["a"], "b": s["b"]})
    if not all(x["in_face"] for x in seg):
        fails.append("section segment not in its face")
    # review: the progressive segments are exactly the ring edges, each once (a segment past an edge would pass in_face)
    if sorted(map(sorted, ({vec(s["a"]), vec(s["b"])} for s in sec["steps"]))) != sorted(map(sorted, edges(ring))):
        fails.append("progressive section segments are not exactly the ring edges")
    # coincident coordinates with distinct identity (point3 objects and section vertex entities)
    by = {}
    for o in scene["objects"]:
        if o["type"] == "point3":
            by.setdefault(P[o["id"]], []).append(o["id"])
    for e in ent:
        by.setdefault(ring[e["section_vertex_ordinal"]], []).append(e["entity_id"])
    coincident = [{"chart_xyz": [str(x) for x in k], "ids": v} for k, v in by.items() if len(v) > 1]
    return {"fails": fails, "points": points, "plane": pc, "section": sc, "section_vertices": on_edges,
            "section_segments": seg, "coincident": coincident}


def scene_answer(scene):
    return next(o["value"] for o in scene["objects"] if o["type"] == "quantity")


def answer_sq(scene):
    from tests.geometry import hybrid_compiler_benchmark as HB
    return HB.answer_square(scene_answer(scene))


def audit_steps(scene, seg):
    """Raw trace steps: what appears, from which inputs, whether its dependencies already exist."""
    objs = {o["id"]: o for o in scene["objects"]}
    steps, fails, prev = [], [], set()
    if len(scene["formation"]["steps"]) != len(scene["events"]):
        fails.append("formation steps and events differ in count")
    for st, ev in zip(scene["formation"]["steps"], scene["events"]):
        k = st["step_index"]
        vis = set(st["visible_ids"])
        new, gone = sorted(vis - prev), sorted(prev - vis)
        late = {i: [d for d in objs[i]["depends"] if d not in prev] for i in new if k > 0}
        late = {i: v for i, v in late.items() if v}
        prog = (st.get("geometry_progress") or [{}])[0]
        row = {"step": k, "event": ev["action"], "semantic_kind": st["semantic_kind"], "object": ev["object"],
               "inputs": ev["depends"], "new_outputs": new, "removed": gone, "focus": st["focus_ids"],
               "learner_text": st["learner_text"], "section_edges": len(prog.get("visible_edge_ids", [])),
               "closed": prog.get("closed"), "fill": prog.get("fill_visible")}
        geometry_change = bool([i for i in new if objs[i]["render"] not in ("non_visual", "readout")]) or \
            (k and row["section_edges"] != steps[-1]["section_edges"]) or (k and row["fill"] != steps[-1]["fill"])
        row["geometry_change"] = bool(geometry_change)
        row["kind"] = ("INIT_GIVEN" if ev["action"] == "INIT" and "DECLARE_ENTITIES" in st["formation_roles"] else
                       "CONSTRUCTION" if st["semantic_kind"] == "GEOMETRY_CONSTRUCTION" else
                       "INTERPRETIVE" if st["semantic_kind"] in ("MEASUREMENT", "FINAL_RESULT", "EXPLANATION") else "?")
        issues = []
        if gone:
            issues.append(f"objects disappear {gone}")
        if late:
            issues.append(f"appears before its dependencies {late}")
        if row["kind"] == "INIT_GIVEN" and set(new) != set(scene["free_objects"]):
            issues.append(f"INIT shows {new}, not exactly the given points")
        if row["kind"] == "?":
            issues.append(f"unknown step kind {st['semantic_kind']}")
        if row["kind"] == "CONSTRUCTION" and not geometry_change:
            issues.append("construction step without a constructed object")
        if row["kind"] == "INTERPRETIVE" and [i for i in new if objs[i]["render"] not in ("non_visual", "readout")]:
            issues.append("interpretive step adds drawn geometry")
        if ev["action"] == "EXTEND":
            j = row["section_edges"] - 1
            s = seg[j]
            named_face = re.search(r"mặt (\S+),", ev["learner_text"])
            row["section_segment"] = s
            if not s["in_face"] or not named_face or named_face[1] != s["face"]:
                issues.append(f"narrated face {named_face and named_face[1]} != segment face {s['face']}")
        sec_dep = [i for i in new if objs[i]["type"] == "section"]
        for i in sec_dep:
            if any(d not in prev for d in objs[i]["depends"]):
                issues.append("section before its plane/solid")
        row["math_verdict"] = "PASS" if not issues else "FAIL"
        row["issues"] = issues
        fails += [f"step {k}: {x}" for x in issues]
        steps.append(row)
        prev = vis
    return steps, fails


def metamorphic(case_index):
    from app.ai.function_route import run_fact_route
    from tests.geometry.test_two_line_plane_section import CASES, problem

    case = CASES[case_index]
    out = []
    variants = {"swap_lines": dict(lines=case["lines"][::-1]),
                "reverse_first": dict(lines=[case["lines"][0][::-1], case["lines"][1]]),
                "reverse_second": dict(lines=[case["lines"][0], case["lines"][1][::-1]]),
                "reverse_midpoint": dict(mid=case["mid"][::-1])}
    for name, kw in variants.items():
        c = {**case, "lines": [list(x) for x in kw.get("lines", case["lines"])], "mid": list(kw.get("mid", case["mid"]))}
        text, payload = problem(c["family"], tuple(c["mid"]), tuple(tuple(x) for x in c["lines"]))
        r = run_fact_route(text, payload)
        a = audit_scene(r.scene3d, c) if r.status == "SERVED" else {"fails": [f"refused {r.code}"]}
        if r.status == "SERVED":
            a["fails"] += audit_steps(r.scene3d, a["section_segments"])[1]
        out.append({"variant": name, "status": r.status, "answer": r.answers.get("q"), "fails": a["fails"],
                    "aux_ids": [o["id"] for o in (r.scene3d or {}).get("objects", [])
                                if o.get("source", {}).get("binding") == "AUXILIARY"]})
    # name collision: the midpoint is called H, the name of the auxiliary point
    text, payload = problem(case["family"], tuple(case["mid"]), tuple(tuple(x) for x in case["lines"]))
    text = text.replace("Gọi M", "Gọi H").replace("qua M", "qua H")
    payload = json.loads(json.dumps(payload, ensure_ascii=False).replace('"M"', '"H"')
                         .replace("Gọi M", "Gọi H").replace("qua M", "qua H"))
    r = run_fact_route(text, payload)
    a = audit_scene(r.scene3d, case) if r.status == "SERVED" else {"fails": [f"refused {r.code}"], "coincident": []}
    if r.status == "SERVED":
        a["fails"] += audit_steps(r.scene3d, a["section_segments"])[1]
    ids = [o["id"] for o in (r.scene3d or {}).get("objects", []) if o["type"] == "point3"]
    out.append({"variant": "midpoint_named_H", "status": r.status, "answer": r.answers.get("q"), "fails": a["fails"]
                + ([] if len(ids) == len(set(ids)) else ["duplicate point id"]),
                "aux_ids": [o["id"] for o in (r.scene3d or {}).get("objects", [])
                            if o.get("source", {}).get("binding") == "AUXILIARY"], "point_ids": ids})
    return out


def world_checks(scene, world, gram):
    """Renderer world coordinates preserve the chart metric: |w(p)-w(q)|² = (p-q)ᵀ G (p-q)."""
    pts = {o["id"]: vec(o["xyz"]) for o in scene["objects"] if o["type"] == "point3"}
    worst, n = 0.0, 0
    ids = sorted(set(pts) & set(world))
    G = [[F(x) for x in r] for r in gram]
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            d = sub(pts[a], pts[b])
            exact = float(sum(d[r] * G[r][c] * d[c] for r in range(3) for c in range(3)))
            w = sum((world[a][j] - world[b][j]) ** 2 for j in range(3))
            worst, n = max(worst, abs(w - exact)), n + 1
    return {"pairs": n, "max_abs_error": worst, "passed": n > 0 and worst < 1e-6}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--browser")
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    from tests.geometry.test_two_line_plane_section import CASES

    rows = json.loads(Path(args.scenes).read_text(encoding="utf-8"))
    browser = {r["id"]: r for r in json.loads(Path(args.browser).read_text(encoding="utf-8"))["playback"]} \
        if args.browser else {}
    report, fails = [], []
    for row in rows:
        case = CASES[row["corpus_index"]]
        if not row["served"]:
            ok = row["scene"] is None and row["code"] == case["expected"] and not row["answers"]
            report.append({"id": row["id"], "served": False, "code": row["code"], "passed": ok})
            fails += [] if ok else [f"{row['id']}: refusal mismatch"]
            continue
        a = audit_scene(row["scene"], case)
        steps, sf = audit_steps(row["scene"], a["section_segments"])
        b = browser.get(row["id"])
        if b:
            for s in steps:
                g = next((x for x in b["steps"] if x["start"] <= s["step"] <= x["end"]), None)
                s["learner_step"] = g and g["index"]
                s["screenshot"] = g and g["screenshot"]
                s["visual_verdict"] = g and ("PASS" if not g["failures"] else "FAIL")
                if s["visual_verdict"] == "FAIL":  # review: visual FAILs count as audit failures
                    sf.append(f"step {s['step']} visual: {g['failures']}")
            a["world"] = world_checks(row["scene"], b["world_points"], row["scene"]["chart_metric"])
            if not a["world"]["passed"]:
                a["fails"].append("world-space metric mismatch")
        meta = metamorphic(row["corpus_index"])
        mf = [f"{m['variant']}: {m['fails']}" for m in meta if m["fails"] or m["answer"] != row["answers"]["q"]]
        all_f = [f"{row['id']}: {x}" for x in a["fails"] + sf + mf]
        fails += all_f
        report.append({"id": row["id"], "served": True, "answer": row["answers"]["q"], "raw_steps": len(steps),
                       "points_checked": len(a["points"]), "audit": a, "steps": steps, "metamorphic": meta,
                       "passed": not all_f})
        print(json.dumps({"id": row["id"], "points": len(a["points"]), "steps": len(steps), "fails": all_f},
                         ensure_ascii=False))
    out.mkdir(parents=True)
    (out / "construction-audit.json").write_text(json.dumps(
        {"scenes": args.scenes, "browser": args.browser, "oracle": "tests/geometry/two_line_plane_oracle.py",
         "model_calls": 0, "failures": fails, "report": report}, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    print(json.dumps({"failures": fails}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
