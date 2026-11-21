"""Independent exact checks of constraint-defined planes, their sections and intersection lines (AGENT_DIAGNOSTIC:
Fractions + the envelope's Gram metric, written here, never calling the construction code), run on the development
probes for a given backend tree (before = archive of the start product, after = the worktree).

  python verify_plane_constraints.py [--backend DIR]        # prints one line per probe
  python verify_plane_constraints.py --probe                # child: reads probes on stdin (internal)
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from fractions import Fraction as F
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plane_constraint_probes import PROBES  # noqa: E402

_prev = importlib.util.spec_from_file_location(
    "prev_vc", RUN.parent / "verified-section-intersection-dihedral-local/tools/verify_constructions.py")
VC = importlib.util.module_from_spec(_prev)
_prev.loader.exec_module(VC)
v, sub, cross, eu, gdot, collinear, plane_of = VC.v, VC.sub, VC.cross, VC.eu, VC.gdot, VC.collinear, VC.plane_of


def probe() -> None:
    os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
    from app.ai.adaptive_input_router import route_text_input
    out = {}
    for k, t in json.loads(sys.stdin.read()).items():
        r = route_text_input(t, allow_live_ai=False).response
        rd = r.get("route_d") or {}
        out[k] = {"status": rd.get("status"), "answers": rd.get("answers"),
                  "reason": r.get("reason_code") or (r.get("envelope") or {}).get("reason_code") or (rd.get("refusal") or {}).get("code"),
                  "scene": (r.get("envelope") or {}).get("scene3d"), "sections": rd.get("sections")}
    print(json.dumps(out, ensure_ascii=False))


def run(backend: Path, texts: dict[str, str]) -> dict:
    env = {**os.environ, "PYTHONPATH": str(backend), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1", "ALLOW_LIVE_AI": "0", "GEMINI_API_KEY": ""}
    res = subprocess.run([sys.executable, __file__, "--probe"], input=json.dumps(texts, ensure_ascii=False), capture_output=True,
                         text=True, cwd=backend, env=env, encoding="utf-8", check=True)
    return json.loads(res.stdout.strip().splitlines()[-1])


def nm(i: str) -> str:
    return i.replace("_prime", "'")


def boundary(sc: dict) -> list[tuple] | None:
    """Canonical boundary descriptors of the drawn section (VERTEX label | EDGE sorted labels + t from the first label),
    in polygon order — from coordinates only."""
    obj = {o["id"]: o for o in sc["objects"]}
    sec = next((o for o in sc["objects"] if o["type"] == "section"), None)
    if sec is None:
        return None
    solid = obj.get((sec.get("depends") or [None])[0]) or {}
    vids, faces = solid.get("vertex_ids") or [], solid.get("faces") or []
    lab = {i: nm(i) for i in vids}                                      # point ids are the vertex labels
    pts = {i: v(obj[i]["xyz"]) for i in vids if obj.get(i, {}).get("xyz")}
    edges = {tuple(sorted((vids[f[a]], vids[f[(a + 1) % len(f)]]))) for f in faces for a in range(len(f))}  # faces index vertex_ids
    out = []
    for q in (v(p) for p in sec.get("polygon") or []):
        hit = next((("VERTEX", lab[i]) for i in vids if pts.get(i) == q), None)
        if hit is None:
            for i, j in edges:
                a, b = pts[i], pts[j]
                d = sub(b, a)
                if collinear(a, b, q) and 0 < eu(sub(q, a), d) < eu(d, d):
                    t = eu(sub(q, a), d) / eu(d, d)
                    x, y = lab[i], lab[j]
                    hit = ("EDGE", *sorted((x, y)), t if x <= y else 1 - t)
                    break
        out.append(hit or ("OFF_BOUNDARY",))
    return out


def area_sq(sc: dict) -> F | None:
    """Exact area² of the drawn section: shoelace in the plane basis (e1, e2) times the Gram determinant of (e1, e2)."""
    sec = next((o for o in sc["objects"] if o["type"] == "section"), None)
    if sec is None:
        return None
    g = [[F(x) for x in row] for row in sc["chart_metric"]]
    poly = [v(p) for p in sec["polygon"]]
    o = poly[0]
    e1 = sub(poly[1], o)
    e2 = next((sub(q, o) for q in poly[2:] if any(cross(e1, sub(q, o)))), None)
    if e2 is None:
        return None
    n = cross(e1, e2)
    k = max(range(3), key=lambda i: abs(n[i]))                     # solve q - o = s e1 + t e2 on the two other axes
    i, j = [x for x in range(3) if x != k]
    det = e1[i] * e2[j] - e1[j] * e2[i]
    st = [((q[i] - o[i]) * e2[j] - (q[j] - o[j]) * e2[i]) / det for q in poly], \
         [(e1[i] * (q[j] - o[j]) - e1[j] * (q[i] - o[i])) / det for q in poly]
    s, t = st
    shoelace = sum(s[a] * t[(a + 1) % len(poly)] - s[(a + 1) % len(poly)] * t[a] for a in range(len(poly))) / 2
    gram = gdot(g, e1, e1) * gdot(g, e2, e2) - gdot(g, e1, e2) ** 2
    return shoelace ** 2 * gram


def plane_checks(text: str, sc: dict) -> list[dict]:
    """Relation of the drawn cutting plane to what the text states — parsed here from the text with a deliberately tiny,
    independent reading (labels only), never from the product's facts."""
    import re
    out = []
    obj = {o["id"]: o for o in sc["objects"]}
    lab = {nm(o["id"]): v(o["xyz"]) for o in sc["objects"] if o["type"] == "point3" and o.get("xyz")}
    text = text.replace("′", "'")
    g = [[F(x) for x in row] for row in sc["chart_metric"]]
    sec = next((o for o in sc["objects"] if o["type"] == "section"), None)
    if sec is None:
        return out
    pl = obj.get((sec.get("depends") or [None, None])[1]) or {}
    n, p0 = (v(pl["normal"]), v(pl["point"])) if pl.get("normal") else plane_of([v(x) for x in sec["polygon"]])
    on = lambda q: eu(n, sub(q, p0)) == 0                                      # noqa: E731
    span = [sub(v(x), p0) for x in sec["polygon"]]
    P = r"[A-Z]'?"
    m = re.search(rf"(?:đi qua|qua|chứa)\s+({P})\s+(?:và\s+)?song song với (?:mặt phẳng |mp )?\(((?:{P}){{3,}})\)", text) or \
        re.search(rf"Qua ({P}) dựng mặt phẳng \(\S+\) song song với \(((?:{P}){{3,}})\)", text)
    if m and m.group(1) in lab:
        q = [lab[x] for x in re.findall(P, m.group(2))]
        nq, _ = plane_of(q)
        out.append({"check": "cut_plane_through_stated_point", "ok": on(lab[m.group(1)])})
        out.append({"check": "cut_plane_parallel_to_stated_plane", "ok": not any(cross(n, nq)) and not on(q[0])})
    m = re.search(rf"(?:đi qua|qua)\s+({P})\s+(?:và\s+)?song song với (?:mặt phẳng |mặt )?đáy", text)
    if m and m.group(1) in lab:                                        # "∥ (mặt phẳng) đáy": the solid's base face
        solid = next((o for o in sc["objects"] if o["type"] == "solid"), {})
        base = [lab[x] for x in [nm(i) for i in solid.get("vertex_ids") or []] if x in lab][1:] if solid else []
        nq, _ = plane_of(base) if len(base) >= 3 else (None, None)
        out.append({"check": "cut_plane_through_stated_point", "ok": on(lab[m.group(1)])})
        out.append({"check": "cut_plane_parallel_to_base", "ok": nq is not None and not any(cross(n, nq))})
    m = re.search(rf"(?:đi qua|qua)\s+({P})\s+(?:và\s+)?vuông góc với (?:đường thẳng )?({P})({P})(?![\w'(])", text)
    if m and all(x in lab for x in m.groups()):
        d = sub(lab[m.group(3)], lab[m.group(2)])
        out.append({"check": "cut_plane_through_stated_point", "ok": on(lab[m.group(1)])})
        out.append({"check": "stated_line_perpendicular_to_cut_plane_in_G", "ok": all(gdot(g, d, w) == 0 for w in span)})
    m = re.search(rf"chứa\s+(?:đường thẳng\s+)?({P})({P})\s+và\s+(?:đi qua|qua)\s+({P})|(?:đi qua|qua)\s+({P})\s+và\s+chứa\s+(?:đường thẳng\s+)?({P})({P})", text)
    if m:
        labs = [x for x in m.groups() if x]
        if all(x in lab for x in labs):
            out.append({"check": "cut_plane_contains_stated_line_and_point", "ok": all(on(lab[x]) for x in labs)})
    m = re.search(rf"chứa hai đường thẳng (?:cắt nhau |song song )?({P})({P}) và ({P})({P})", text)
    if m and all(x in lab for x in m.groups()):
        out.append({"check": "cut_plane_contains_both_stated_lines", "ok": all(on(lab[x]) for x in m.groups())})
    m = re.search(rf"chứa ({P})({P}) và song song với ({P})({P})", text)
    if m and all(x in lab for x in m.groups()):
        d = sub(lab[m.group(4)], lab[m.group(3)])
        out.append({"check": "cut_plane_contains_line_parallel_to_stated_line",
                    "ok": on(lab[m.group(1)]) and on(lab[m.group(2)]) and eu(n, d) == 0 and not on(lab[m.group(3)])})
    m = re.search(rf"chứa ({P})({P}) và vuông góc với mặt phẳng \(({P})({P})({P})\)", text)
    if m and all(x in lab for x in m.groups()):
        a, b, c = (lab[x] for x in m.groups()[2:])
        e1, e2 = sub(b, a), sub(c, a)
        # (P) ⊥ (Q) in G: the G-normal of (Q) lies in (P) — u in P with u ⟂_G e1, e2 exists among span combos
        nq_dual = None
        for w1 in span:
            for w2 in span:
                cand = [x * gdot(g, w2, e1) - y * gdot(g, w1, e1) for x, y in zip(w1, w2)]
                if any(cand) and gdot(g, cand, e2) == 0:
                    nq_dual = cand
        out.append({"check": "cut_plane_contains_stated_line_and_perpendicular_to_stated_plane_in_G",
                    "ok": on(lab[m.group(1)]) and on(lab[m.group(2)]) and nq_dual is not None})
    m = re.search(rf"(?:đi qua|qua)\s+({P})\s+(?:và\s+)?song song với hai đường thẳng ({P})({P}) và ({P})({P})", text)
    if m and all(x in lab for x in m.groups()):
        d1, d2 = sub(lab[m.group(3)], lab[m.group(2)]), sub(lab[m.group(5)], lab[m.group(4)])
        out.append({"check": "cut_plane_through_stated_point", "ok": on(lab[m.group(1)])})
        out.append({"check": "cut_plane_parallel_to_both_stated_lines",
                    "ok": eu(n, d1) == 0 and eu(n, d2) == 0 and not on(lab[m.group(2)]) and not on(lab[m.group(4)])})
    m = re.search(rf"mặt phẳng trung trực của đoạn(?: thẳng)? ({P})({P})", text)
    if m and all(x in lab for x in m.groups()):
        a, b = lab[m.group(1)], lab[m.group(2)]
        mid = [(x + y) / 2 for x, y in zip(a, b)]
        out.append({"check": "cut_plane_through_midpoint", "ok": on(mid)})
        out.append({"check": "segment_perpendicular_to_cut_plane_in_G", "ok": all(gdot(g, sub(b, a), w) == 0 for w in span)})
    return out


def evaluate(backend: Path) -> dict:
    got = run(backend, {k: t for k, (_c, _e, t) in PROBES.items()})
    rows = {}
    for k, (cat, (exp, n), text) in PROBES.items():
        r = got[k]
        sc = r["scene"] if r["status"] == "SERVED" else None
        row = {"category": cat, "expected": exp, "expected_vertices": n, "status": r["status"] or "REFUSED", "reason": r["reason"]}
        if sc:
            checks = VC.check("probe", sc) + plane_checks(text, sc)
            secs = [o for o in sc["objects"] if o["type"] == "section"]
            lines = [o for o in sc["objects"] if o.get("producer") == "intersect_plane_plane"]
            row.update(sections=[len(o.get("polygon") or []) for o in secs], intersection_lines=len(lines),
                       boundary=[list(map(str, b)) for b in (boundary(sc) or [])], area_sq=str(area_sq(sc)) if secs else None,
                       checks=checks, failed_checks=[c["check"] for c in checks if not c["ok"]])
            hit = (len(lines) >= 1) if n == "line" else (row["sections"] == [n])
            row["outcome"] = ("AS_EXPECTED" if exp == "SERVED" and hit and not row["failed_checks"] else
                              "WRONG_SERVED" if exp == "REFUSED" or not hit or row["failed_checks"] else "?")
        else:
            row["outcome"] = "AS_EXPECTED" if exp == "REFUSED" else "NOT_SERVED"
        rows[k] = row
    return rows


if __name__ == "__main__":
    if "--probe" in sys.argv:
        probe()
        raise SystemExit(0)
    backend = Path(sys.argv[sys.argv.index("--backend") + 1]) if "--backend" in sys.argv else ROOT / "backend"
    rows = evaluate(backend)
    for k, r in rows.items():
        print(f"{r['outcome']:12} {k:42} {r['status']:8} {str(r['reason'])[:28]:28} {r.get('sections')} {r.get('failed_checks') or ''}")
