"""Independent verification of the constructions this run serves on the LOCAL route, BEFORE vs AFTER, with mutations.

Everything is recomputed from the SERVED ENVELOPE with exact Fractions and the envelope's own Gram matrix G, written here
(no kernel, no metric module, no quantity_annotations import). Probes are SYNTHETIC statements written by the agent
(development probes, AGENT_DIAGNOSTIC — not an independent human oracle). BEFORE = backend/app at ffc62f6fe (git archive,
child process); AFTER = this checkout.  Run from backend/:  python <tools>/verify_constructions.py <before_backend_dir>
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
REN = "Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
PROBES = {
    # angles (convention: non-oriented, [0°, 90°])
    "angle_planes_SBC_SCD_60_not_120": ("angle", P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD)."),
    "angle_planes_SCD_SBC_swapped": ("angle", P + "Tính góc giữa mặt phẳng (SCD) và mặt phẳng (SBC)."),
    "angle_planes_renamed": ("angle", REN + "Tính góc giữa mặt phẳng (TNP) và mặt phẳng (TPQ)."),
    "angle_planes_SAB_SCD": ("angle", P + "Tính góc giữa mặt phẳng (SAB) và mặt phẳng (SCD)."),
    "angle_planes_SBD_SCD": ("angle", P + "Tính góc giữa mặt phẳng (SBD) và mặt phẳng (SCD)."),
    "angle_planes_SBC_ABCD": ("angle", P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD)."),
    "angle_planes_cube_A'BD_C'BD": ("angle", CUBE + "Tính góc giữa mặt phẳng (A'BD) và mặt phẳng (C'BD)."),
    "angle_lines_SB_SD": ("angle", P + "Tính góc giữa hai đường thẳng SB và SD."),
    "angle_lines_skew_SB_CD": ("angle", P + "Tính góc giữa hai đường thẳng SB và CD."),
    "angle_lines_skew_cube": ("angle", CUBE + "Tính góc giữa hai đường thẳng AC và DA'."),
    "angle_line_plane_SC_ABCD": ("angle", P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD)."),
    "angle_tetra": ("angle", "Cho tứ diện đều ABCD có cạnh bằng a. Tính góc giữa đường thẳng AB và mặt phẳng (BCD)."),
    # sections
    "section_cube_MNC'": ("section", CUBE + "Gọi M, N lần lượt là trung điểm của AB và AD. Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (MNC')."),
    "section_pyramid_ABM": ("section", P + "Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM)."),
    "section_pyramid_area": ("section", P + "Gọi M là trung điểm của SC. Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (ABM)."),
    "section_cube_triangle": ("section", CUBE + "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD)."),
    "section_cube_hexagon": ("section", CUBE + "Gọi M, N, P lần lượt là trung điểm của AB, BC và CC'. Tìm thiết diện của hình lập phương cắt bởi mặt phẳng (MNP)."),
    "section_contains_edge": ("section", CUBE + "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (ABC')."),
    "section_plane_is_face": ("section", P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (ABC)."),
    "section_through_vertex_and_edge_midpoints": ("section", P + "Gọi M, N lần lượt là trung điểm của SB và SD. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (AMN)."),
    "section_renamed": ("section", REN + "Gọi K là trung điểm của TP. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (MNK)."),
    "section_collinear_refused": ("section", P + "Gọi M là trung điểm của AC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (AMC)."),
    "section_unknown_point_refused": ("section", P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (XYZ)."),
    "section_question_form_unparsed": ("section", P + "Gọi M là trung điểm của SC. Mặt phẳng (ABM) cắt hình chóp theo thiết diện là hình gì?"),
    # intersection lines
    "iline_SAB_SCD": ("intersection", P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD)."),
    "iline_SAC_SBD": ("intersection", P + "Tìm giao tuyến của hai mặt phẳng (SAC) và (SBD)."),
    "iline_named_d": ("intersection", P + "Gọi d là giao tuyến của (SAB) và (SCD)."),
    "iline_SAD_SBC": ("intersection", P + "Dựng giao tuyến của mặt phẳng (SAD) và mặt phẳng (SBC)."),
    "iline_cube_A'BD_C'BD": ("intersection", CUBE + "Tìm giao tuyến của hai mặt phẳng (A'BD) và (C'BD)."),
    "iline_parallel_refused": ("intersection", CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (A'B'C')."),
    "iline_same_plane_refused": ("intersection", CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (ACD)."),
    # altitudes
    "altitude_face_perp_equilateral": ("altitude", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD."),
    "altitude_face_perp_symbol": ("altitude", "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a. Mặt bên SAB là tam giác đều và (SAB) ⊥ (ABCD). Tính thể tích khối chóp S.ABCD."),
    "altitude_face_perp_triangle_base": ("altitude", "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, tam giác SBC đều và nằm trong mặt phẳng vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABC."),
    "altitude_regular_pyramid": ("altitude", "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a, cạnh bên bằng 2a. Tính thể tích khối chóp S.ABCD."),
    "altitude_already_drawn_SA": ("altitude", P + "Tính thể tích khối chóp S.ABCD."),
}


def probe() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for k, (_g, t) in json.loads(sys.stdin.read()).items():
        r = route_text_input(t, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        out[k] = {"status": rd.get("status"), "answers": rd.get("answers"),
                  "reason": r.get("reason_code") or (r.get("envelope") or {}).get("reason_code") or (rd.get("refusal") or {}).get("code"),
                  "scene": (r.get("envelope") or {}).get("scene3d")}
    print(json.dumps(out, ensure_ascii=False))


def side(backend: Path) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--probe"], input=json.dumps(PROBES, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


# ── exact algebra, written here ───────────────────────────────────────────────────────────────────────────────────────
def v(x): return [F(c) for c in x]
def sub(a, b): return [x - y for x, y in zip(a, b)]
def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]
def eu(a, b): return sum(x * y for x, y in zip(a, b))
def gdot(g, a, b): return sum(a[i] * g[i][j] * b[j] for i in range(3) for j in range(3))
def collinear(a, b, c): return not any(cross(sub(b, a), sub(c, a)))


def plane_of(pts):
    """Normal (Euclidean cross product, affine incidence only) of the plane through the first three non-collinear points."""
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            for k in range(j + 1, len(pts)):
                n = cross(sub(pts[j], pts[i]), sub(pts[k], pts[i]))
                if any(n):
                    return n, pts[i]
    return None, None


def check(kind: str, sc: dict) -> list[dict]:
    g = [[F(x) for x in row] for row in sc["chart_metric"]]
    obj = {o["id"]: o for o in sc["objects"]}
    pts = {o["id"]: v(o["xyz"]) for o in sc["objects"] if o["type"] == "point3" and o.get("xyz")}
    out = []

    def rec(c, ok): out.append({"check": c, "ok": bool(ok)})

    for o in sc["objects"]:
        ac = o.get("angle_construction")
        if ac:
            vx = v(ac["vertex"]); a, b = (sub(v(arm["to"]), vx) for arm in ac["arms"])
            c2 = gdot(g, a, b) ** 2 / (gdot(g, a, a) * gdot(g, b, b))
            rec("angle_signed_cos_nonnegative", gdot(g, a, b) >= 0)
            rec("angle_cos_sq_equals_measure", o.get("exact", {}).get("kind") == "rational" and c2 == F(o["exact"]["value"]))
            if ac["relation"] == "plane_plane":
                e = v(ac["edge"]["direction"])
                rec("plane_angle_rays_perpendicular_to_common_line", gdot(g, a, e) == 0 and gdot(g, b, e) == 0)
        if o["type"] == "section":
            poly = [v(p) for p in o.get("polygon") or []]
            solid = obj.get((o.get("depends") or [None])[0]) or {}
            plane = obj.get((o.get("depends") or [None, None])[1]) or {}
            n, p0 = (v(plane["normal"]), v(plane["point"])) if plane.get("normal") else plane_of(poly)
            rec("section_vertices_on_cutting_plane", all(eu(n, sub(q, p0)) == 0 for q in poly))
            vids, faces = solid.get("vertex_ids") or [], solid.get("faces") or []
            edges = {tuple(sorted((f[i], f[(i + 1) % len(f)]))) for f in faces for i in range(len(f))}
            on_edge = lambda q: any(collinear(pts[vids[i]], pts[vids[j]], q) and  # noqa: E731
                                    0 <= eu(sub(q, pts[vids[i]]), sub(pts[vids[j]], pts[vids[i]])) <= eu(sub(pts[vids[j]], pts[vids[i]]), sub(pts[vids[j]], pts[vids[i]]))
                                    for i, j in edges)
            rec("section_vertices_on_solid_edges", bool(vids) and all(on_edge(q) for q in poly))
            rec("section_vertices_distinct", len({tuple(q) for q in poly}) == len(poly) >= 3)
            # simple convex cyclic order: consecutive cross products all point the same way (n), no three collinear
            turns = [eu(n, cross(sub(poly[(i + 1) % len(poly)], poly[i]), sub(poly[(i + 2) % len(poly)], poly[(i + 1) % len(poly)])))
                     for i in range(len(poly))]
            rec("section_polygon_convex_cyclic_order", all(t > 0 for t in turns) or all(t < 0 for t in turns))
            # each section edge lies in one face of the solid (edge–face consistency)
            face_planes = [plane_of([pts[vids[i]] for i in f]) for f in faces]
            def in_face(a, b):
                return any(fn is not None and eu(fn, sub(a, fp)) == 0 and eu(fn, sub(b, fp)) == 0 for fn, fp in face_planes)
            rec("section_edges_lie_in_solid_faces", all(in_face(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))))
        if o.get("producer") == "intersect_plane_plane" and o["type"] == "line3":
            p0, d = v(o["point"]), v(o["direction"])
            planes = [obj[x] for x in o.get("depends") or [] if obj.get(x, {}).get("type") == "plane3"]
            rec("intersection_line_has_two_source_planes", len(planes) == 2)
            for pl in planes:
                n, q = v(pl["normal"]), v(pl["point"])
                rec("intersection_point_on_plane", eu(n, sub(p0, q)) == 0)
                rec("intersection_direction_in_plane", eu(n, d) == 0)
            rec("intersection_direction_nonzero", any(d))
        al = o.get("altitude_construction")
        if al:
            s, h = v(al["from"]), v(al["foot"])
            base = obj[al["on"]]
            bpts = [pts[x] for x in base["vertex_ids"]]
            n, p0 = plane_of(bpts)
            rec("altitude_foot_on_base_plane", eu(n, sub(h, p0)) == 0)
            rec("altitude_perpendicular_to_base_in_G", all(gdot(g, sub(s, h), sub(q, bpts[0])) == 0 for q in bpts[1:]))
            rec("altitude_apex_is_the_solid_apex", s == pts[al["apex_id"]])
            if al.get("base_edge"):
                x, y = (pts[k] for k in al["base_edge"])
                rec("altitude_foot_on_face_base_intersection_line", collinear(x, y, h))
                fpts = [pts[k] for k in al["face"]]
                fn, _ = plane_of(fpts)
                # face ⟂ base in G: G^-1 n_face · n_base = 0 ⇔ some vector of the face orthogonal to the edge is ⟂ base
                e = sub(y, x)
                w = sub(s, x); k_ = gdot(g, w, e) / gdot(g, e, e); perp = [wi - k_ * ei for wi, ei in zip(w, e)]
                rec("altitude_face_perpendicular_to_base_in_G", all(gdot(g, perp, sub(q, bpts[0])) == 0 for q in bpts[1:]))
    return out


MUTATIONS = {
    "flip_angle_ray": lambda sc: _mut(sc, "angle_construction", lambda a: a["arms"][1].update(
        to=[str(2 * F(x) - F(y)) for x, y in zip(a["vertex"], a["arms"][1]["to"])])),
    "section_vertex_off_plane": lambda sc: _mut_section(sc, lambda poly: poly[0].__setitem__(2, str(F(poly[0][2]) + F(1, 7)))),
    "section_vertex_order_swapped": lambda sc: _mut_section(sc, lambda poly: poly.__setitem__(slice(0, 2), [poly[1], poly[0]])),
    "section_vertex_replaced_by_wrong_edge_point": lambda sc: _mut_section(sc, lambda poly: poly.__setitem__(0, poly[1])),
    "intersection_direction_tilted": lambda sc: _mut_line(sc, lambda o: o.__setitem__("direction", [str(F(x) + (1 if i == 2 else 0)) for i, x in enumerate(o["direction"])])),
    "intersection_point_moved": lambda sc: _mut_line(sc, lambda o: o.__setitem__("point", [str(F(x) + F(1, 3)) for x in o["point"]])),
    "altitude_wrong_foot": lambda sc: _mut(sc, "altitude_construction", lambda a: a.__setitem__("foot", ["0", "0", "0"]) if a["foot"] != ["0", "0", "0"] else a.__setitem__("foot", ["1", "0", "0"])),
}


def _mut(sc, key, fn):
    o = next((o for o in sc["objects"] if o.get(key)), None)
    if o is None:
        return False
    fn(o[key]); return True


def _mut_section(sc, fn):
    o = next((o for o in sc["objects"] if o["type"] == "section"), None)
    if o is None:
        return False
    fn(o["polygon"]); return True


def _mut_line(sc, fn):
    o = next((o for o in sc["objects"] if o.get("producer") == "intersect_plane_plane"), None)
    if o is None:
        return False
    fn(o); return True


def write(name, data):
    (RUN / name).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                                        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
                                        "oracle": "AGENT_DIAGNOSTIC: exact Fractions + envelope Gram G written here, independent of the construction code",
                                        "probe_class": "SYNTHETIC_DEVELOPMENT_PROBES (agent-written)", **data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    before, after = side(Path(sys.argv[1])), side(ROOT / "backend")
    rows = []
    for k, (goal, text) in PROBES.items():
        row = {"probe": k, "goal": goal, "text": text}
        for name, res in (("before", before[k]), ("after", after[k])):
            sc = res.pop("scene")
            row[name] = {**res, "checks": check(goal, sc) if sc else []}
            row[name]["failed_checks"] = [c["check"] for c in row[name]["checks"] if not c["ok"]]
            if name == "after" and sc:
                row["after"]["objects"] = {"sections": [len(o.get("polygon") or []) for o in sc["objects"] if o["type"] == "section"],
                                           "intersection_lines": sum(o.get("producer") == "intersect_plane_plane" for o in sc["objects"]),
                                           "altitude": next((o["altitude_construction"] for o in sc["objects"] if o.get("altitude_construction")), None) is not None,
                                           "angle_relation": next((o["angle_construction"]["relation"] for o in sc["objects"] if o.get("angle_construction")), None)}
                muts = {}
                for m, fn in MUTATIONS.items():
                    bad = copy.deepcopy(sc)
                    if fn(bad):
                        muts[m] = any(not c["ok"] for c in check(goal, bad))
                row["after"]["mutations_caught"] = muts
        rows.append(row)
        print(f"{k:45s} before {row['before']['status']} fails={row['before']['failed_checks']} | after {row['after']['status']} fails={row['after']['failed_checks']}", flush=True)
    by = lambda g: [r for r in rows if r["goal"] == g]  # noqa: E731
    muts = Counter(); caught = Counter()
    for r in rows:
        for m, ok in (r["after"].get("mutations_caught") or {}).items():
            muts[m] += 1; caught[m] += bool(ok)
    common = {"before_ref": "ffc62f6fe (run start)", "mutation_summary": {m: {"applied": muts[m], "caught": caught[m]} for m in muts}}
    write("angle_construction_before_after.json", {**common, "convention": "every supported angle ask is the non-oriented angle in [0°, 90°]",
          "rows": by("angle"), "before_obtuse_drawn": [r["probe"] for r in by("angle") if "angle_signed_cos_nonnegative" in r["before"]["failed_checks"]],
          "after_obtuse_drawn": [r["probe"] for r in by("angle") if "angle_signed_cos_nonnegative" in r["after"]["failed_checks"]]})
    write("polyhedron_section_correctness.json", {**common, "rows": by("section"),
          "served_after": sum(r["after"]["status"] == "SERVED" for r in by("section")), "served_before": sum(r["before"]["status"] == "SERVED" for r in by("section")),
          "check_failures_after": sum(len(r["after"]["failed_checks"]) for r in by("section"))})
    write("plane_intersection_correctness.json", {**common, "rows": by("intersection"),
          "served_after": sum(r["after"]["status"] == "SERVED" for r in by("intersection")), "served_before": sum(r["before"]["status"] == "SERVED" for r in by("intersection")),
          "check_failures_after": sum(len(r["after"]["failed_checks"]) for r in by("intersection"))})
    write("altitude_face_perpendicular_verification.json", {**common, "rows": by("altitude"),
          "with_altitude_after": [r["probe"] for r in by("altitude") if (r["after"].get("objects") or {}).get("altitude")],
          "check_failures_after": sum(len(r["after"]["failed_checks"]) for r in by("altitude"))})
    allc = [c for r in rows for c in r["after"]["checks"]]
    write("scene3d_mathematical_invariants.json", {**common, "served_scenes_after": sum(r["after"]["status"] == "SERVED" for r in rows),
          "checks_total": len(allc), "checks_failed": sum(not c["ok"] for c in allc), "checks_by_kind": dict(Counter(c["check"] for c in allc)),
          "before_failed_checks": {r["probe"]: r["before"]["failed_checks"] for r in rows if r["before"]["failed_checks"]}})
    print(json.dumps(common["mutation_summary"]))
    return 0


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
    else:
        raise SystemExit(main())
