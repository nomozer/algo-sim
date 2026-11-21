"""Mathematical Scene3D invariants, checked from the SERVED ENVELOPE ONLY with exact arithmetic written here.

Independent of the construction code: no kernel, no metric module, no quantity_annotations import. Inputs are the
scene's exact coordinates, plane covectors and `chart_metric` G. Checked for every scene served on the input set:
  - angle_construction: vertex / foot / helper / rays relations of its relation type, and cos² of the drawn angle equals
    the quantity's exact value;
  - distance witnesses: foot on the target, (from − foot) ⟂ target in G, |from − foot|²_G = value²;
  - certified altitudes (`perpendicular_witness` on segments): line direction ⟂ both plane directions in G.
Oracle class: AGENT_VERIFIED_DIAGNOSTIC (written by the agent, independent code path, not an independent human oracle).
Run from backend/:  python <tools>/scene_invariants.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from scene_capability_audit import PROBES  # noqa: E402

F = Fraction


def v(x):
    return [F(c) for c in x]


def sub(a, b):
    return [x - y for x, y in zip(a, b)]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


def eu(a, b):
    return sum(x * y for x, y in zip(a, b))


class Frame:
    def __init__(self, g):
        self.g = [[F(x) for x in row] for row in g]

    def dot(self, a, b):
        return sum(a[i] * self.g[i][j] * b[j] for i in range(3) for j in range(3))

    def cos2(self, a, b):
        return self.dot(a, b) ** 2 / (self.dot(a, a) * self.dot(b, b))


def plane_dirs(n):
    ds = [cross(n, e) for e in ([1, 0, 0], [0, 1, 0], [0, 0, 1])]
    ds = [d for d in ds if any(d)]
    for i, a in enumerate(ds):
        for b in ds[i + 1:]:
            if any(cross(a, b)):
                return a, b
    raise ValueError("degenerate plane")


def exact_sq(e):
    """Square of a quantity's exact value: rational, or coefficient·√radicand."""
    if e["kind"] == "rational":
        return F(e["value"]) ** 2
    if e["kind"] == "radical":
        return F(e["coefficient"]) ** 2 * F(e["radicand"])
    raise ValueError(e["kind"])


def check_scene(name: str, sc: dict) -> list[dict]:
    fr = Frame(sc["chart_metric"])
    by = {o["id"]: o for o in sc["objects"]}
    out = []

    def rec(kind, obj, ok, detail=""):
        out.append({"case": name, "object": obj, "check": kind, "ok": bool(ok), **({"detail": detail} if detail else {})})

    for o in sc["objects"]:
        ac = o.get("angle_construction")
        if ac:
            vx, a1, a2 = v(ac["vertex"]), v(ac["arms"][0]["to"]), v(ac["arms"][1]["to"])
            r1, r2 = sub(a1, vx), sub(a2, vx)
            rec("angle_cos_sq_equals_measure", o["id"], fr.cos2(r1, r2) == F(o["exact"]["value"]) if o.get("exact", {}).get("kind") == "rational" else False)
            if ac["relation"] == "line_plane":
                pl = by[ac["perpendicular"]["on"]]
                n, p0 = v(pl["normal"]), v(pl["point"])
                h, p = v(ac["perpendicular"]["foot"]), v(ac["perpendicular"]["from"])
                d1, d2 = plane_dirs(n)
                rec("projection_foot_on_plane", o["id"], eu(n, sub(h, p0)) == 0)
                rec("vertex_on_plane", o["id"], eu(n, sub(vx, p0)) == 0)
                rec("perpendicular_to_plane_in_G", o["id"], fr.dot(sub(p, h), d1) == 0 and fr.dot(sub(p, h), d2) == 0)
                rec("foot_is_second_arm", o["id"], h == a2)
                rec("first_arm_through_from", o["id"], not any(cross(sub(p, vx), r1)))
            elif ac["relation"] == "plane_plane":
                e = v(ac["edge"]["direction"])
                rec("rays_perpendicular_to_common_line_in_G", o["id"], fr.dot(r1, e) == 0 and fr.dot(r2, e) == 0)
            elif ac["relation"] == "line_line_skew":
                rec("helper_is_second_arm", o["id"], v(ac["parallel"]["to"]) == a2 and v(ac["parallel"]["through"]) == vx)
                ln = by.get(ac["parallel"]["of"]) or {}
                if ln.get("direction"):
                    rec("helper_parallel_to_second_line", o["id"], not any(cross(r2, v(ln["direction"]))))
        ann = o.get("annotation") or {}
        w = ann.get("witness")
        if ann.get("kind") == "distance" and w and o.get("exact"):
            tgt = by.get(w["on"]) or {}
            frm = v(w["from_point"]) if w.get("from_point") else v(by[w["from"]]["xyz"])
            foot, leg = v(w["foot"]), sub(frm, v(w["foot"]))
            if tgt.get("type") == "plane3":
                n, p0 = v(tgt["normal"]), v(tgt["point"])
                d1, d2 = plane_dirs(n)
                rec("distance_foot_on_plane", o["id"], eu(n, sub(foot, p0)) == 0)
                rec("distance_leg_perpendicular_in_G", o["id"], fr.dot(leg, d1) == 0 and fr.dot(leg, d2) == 0)
            elif tgt.get("type") in ("line3", "segment3") and (tgt.get("direction") or tgt.get("point_a")):
                d = v(tgt["direction"]) if tgt.get("direction") else sub(v(tgt["point_b"]), v(tgt["point_a"]))
                p0 = v(tgt["point"]) if tgt.get("point") else v(tgt["point_a"])
                rec("distance_foot_on_line", o["id"], not any(cross(sub(foot, p0), d)))
                rec("distance_leg_perpendicular_in_G", o["id"], fr.dot(leg, d) == 0)
            rec("distance_length_equals_value", o["id"], fr.dot(leg, leg) == exact_sq(o["exact"]))
        pw = o.get("perpendicular_witness")
        if pw and pw.get("from") in by and by[pw["from"]].get("xyz"):
            leg = sub(v(by[pw["from"]]["xyz"]), v(pw["foot"]))
            if pw.get("plane_directions"):
                rec("altitude_perpendicular_to_base_in_G", o["id"], all(fr.dot(leg, v(d)) == 0 for d in pw["plane_directions"]))
            tgt = by.get(pw.get("on")) or {}
            if tgt.get("type") == "plane3":
                d1, d2 = plane_dirs(v(tgt["normal"]))
                rec("projection_foot_on_plane", o["id"], eu(v(tgt["normal"]), sub(v(pw["foot"]), v(tgt["point"]))) == 0)
                rec("projection_leg_perpendicular_in_G", o["id"], fr.dot(leg, d1) == 0 and fr.dot(leg, d2) == 0)
            elif tgt.get("type") == "line3":
                d = v(tgt["direction"])
                rec("projection_foot_on_line", o["id"], not any(cross(sub(v(pw["foot"]), v(tgt["point"])), d)))
                rec("projection_leg_perpendicular_in_G", o["id"], fr.dot(leg, d) == 0)
    return out


def corpus() -> dict[str, str]:
    texts = {f"probe:{k}": t for k, (_, t) in PROBES.items()}
    prior = json.loads((RUN.parent / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))
    texts.update({f"controlled_vision:{i['case_id']}": i["statement"] for i in prior["items"]})
    return texts


def self_test() -> dict:
    """Witness window: the checker must FAIL on tampered copies of a known-good scene (else its PASS means nothing)."""
    import copy
    t = PROBES["angle_line_plane"][1]
    sc = route_text_input(t, allow_live_ai=False).response["envelope"]["scene3d"]
    good = check_scene("good", sc)
    caught = {}
    for label, mutate in {
        "foot_moved_off_plane": lambda q: q["angle_construction"]["perpendicular"].update(foot=["0", "0", "1/2"]),
        "arm_moved": lambda q: q["angle_construction"]["arms"][1].update(to=["1", "0", "0"]),
        "value_changed": lambda q: q["exact"].update(value="1/2"),
    }.items():
        bad = copy.deepcopy(sc)
        mutate(next(o for o in bad["objects"] if o.get("angle_construction")))
        caught[label] = any(not x["ok"] for x in check_scene(label, bad))
    return {"good_scene_all_ok": all(x["ok"] for x in good), "tampered_scenes_caught": caught}


def main() -> int:
    witness = self_test()
    assert witness["good_scene_all_ok"] and all(witness["tampered_scenes_caught"].values()), witness
    rows, served = [], []
    for name, text in corpus().items():
        r = route_text_input(text, allow_live_ai=False).response
        if (r.get("route_d") or {}).get("status") != "SERVED":
            continue
        served.append(name)
        rows += check_scene(name, r["envelope"]["scene3d"])
    fails = [x for x in rows if not x["ok"]]
    from collections import Counter
    (RUN / "scene3d_mathematical_invariants.json").write_text(json.dumps({
        "run_id": RUN.name, "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        "oracle": "AGENT_VERIFIED_DIAGNOSTIC: exact Fractions and the envelope's own chart_metric G, written independently of the construction code",
        "inputs": "synthetic goal probes + controlled-vision agent transcriptions (development/exposed); only SERVED scenes are checked",
        "witness_window": witness, "served_scenes": len(served), "served": served,
        "checks_total": len(rows), "checks_failed": len(fails), "checks_by_kind": dict(Counter(x["check"] for x in rows)),
        "failures": fails, "checks": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("served", len(served), "checks", len(rows), "failed", len(fails))
    for x in fails:
        print("  FAIL", x)
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(main())
