"""Scene3D mathematical invariants of run `certified-scale-cache-safety` (tool copied from compositional-semantics-simulation-goals) (read-only for earlier runs).

  python scene_invariants_run.py      # from the worktree root, backend interpreter
1. the earlier development probes re-served and re-checked by their independent exact checkers;
2. every newly served item of this run's corpus checked by the same sign-aware checker;
3. equivalence pairs: one-sentence ↔ split definitions, plane-after-question ↔ before, trig question ↔ plain angle
   question must give the SAME certified geometry (section vertex coordinates / exact angle);
4. scene mutations (a moved section vertex, a moved angle foot, a swapped angle ray) must be caught by the checker.
"""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent),
                str(RUN.parent / "independent-geometry-plane-constraints/tools")]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
import verify_plane_constraints as V  # noqa: E402

VC = V.VC


def serve(text):
    from app.ai.adaptive_input_router import route_text_input
    r = route_text_input(text, allow_live_ai=False).response or {}
    return (r.get("route_d") or {}), ((r.get("envelope") or {}).get("scene3d"))


def sections(scene):
    pts = {o["id"]: tuple(o["xyz"]) for o in scene["objects"] if o["type"] == "point3"}
    def xyz(v):                          # a polygon vertex is a point id or its coordinates
        return tuple(str(Fraction(c)) for c in v) if isinstance(v, list) else (pts.get(v) or (v,))
    return sorted(sorted(xyz(v) for v in (o.get("polygon") or [])) for o in scene["objects"] if o["type"] == "section")


def mutate(scene, kind):
    s = copy.deepcopy(scene)
    objs = s["objects"]
    if kind == "section_vertex_moved":
        sec = next((o for o in objs if o["type"] == "section"), None)
        if not sec:
            return None
        v0 = sec["polygon"][0]
        if isinstance(v0, list):         # coordinates carried by the section itself
            sec["polygon"][0] = [str(Fraction(v0[0]) + Fraction(1, 7)), *v0[1:]]
            return s
        p = next(o for o in objs if o["type"] == "point3" and o["id"] == v0)
        p["xyz"] = [str(Fraction(p["xyz"][0]) + Fraction(1, 7)), *p["xyz"][1:]]
        return s
    q = next((o for o in objs if o.get("type") == "quantity" and o.get("angle_construction")), None)
    if not q:
        return None
    ac = q["angle_construction"]                    # angle-construction/1: vertex, arms[].to, perpendicular.foot (coordinates)
    if kind == "angle_ray_swapped":
        if len(ac.get("arms") or []) != 2 or ac["arms"][0]["to"] == ac["vertex"]:
            return None
        ac["arms"][0]["to"] = [str(2 * Fraction(v) - Fraction(t)) for v, t in zip(ac["vertex"], ac["arms"][0]["to"])]   # reflected arm
        return s
    perp = ac.get("perpendicular") or {}
    if "foot" not in perp:
        return None
    perp["foot"] = [str(Fraction(perp["foot"][0]) + Fraction(1, 7)), *perp["foot"][1:]]
    return s


def main() -> int:
    from compositional_dev_corpus import CORPUS
    plane_rows = V.evaluate(ROOT / "backend")
    raw = V.run(ROOT / "backend", {k: t for k, (_g, t) in VC.PROBES.items()})
    prev = {k: {"status": r["status"] or "REFUSED", "checks": len(VC.check("x", r["scene"])) if r["status"] == "SERVED" else 0,
                "failed": [c["check"] for c in VC.check("x", r["scene"]) if not c["ok"]] if r["status"] == "SERVED" else []}
            for k, r in raw.items()}
    served, new_rows = {}, {}
    for k, item in CORPUS.items():
        rd, sc = serve(item["text"])
        if rd.get("status") == "SERVED" and sc:
            served[k] = (rd, sc)
            checks = VC.check("x", sc)
            new_rows[k] = {"group": item["group"], "checks": len(checks), "failed": [c["check"] for c in checks if not c["ok"]],
                           "source_goal_completion": bool(rd.get("source_goal_completion"))}
    pairs = []
    for k, item in CORPUS.items():
        ref = item.get("same_as") or (item.get("pair") if item.get("numeric") else None)
        if k in served and ref in served:
            (rd1, s1), (rd2, s2) = served[k], served[ref]
            renamed = item["group"] == "metamorphic"
            same = (rd1.get("answer_exact") == rd2.get("answer_exact")
                    and (renamed or sections(s1) == sections(s2)))
            pairs.append({"item": k, "reference": ref, "same_certified_geometry": same,
                          "compared": "answer_exact" + ("" if renamed else " + section vertex coordinates")})
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    muts = []
    for k, (rd, sc) in served.items():
        r = run_typed_fact_next_v2_route(parse_geometry_problem_locally(CORPUS[k]["text"], use_cache=False).payload)
        for kind in ("section_vertex_moved", "angle_foot_moved", "angle_ray_swapped"):
            m = mutate(sc, kind)
            if m is None:
                continue
            by_checker = not all(c["ok"] for c in VC.check("x", m))
            rm = copy.deepcopy(r)
            rm.scene3d = m
            by_product = build_adapter4_response(rm, CORPUS[k]["text"])["route_d"]["status"] != "SERVED"
            muts.append({"item": k, "mutation": kind, "caught_by_independent_checker": by_checker,
                         "caught_by_product_boundary": by_product, "caught": by_checker or by_product})
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
           "environment": {"ALLOW_LIVE_AI": "0"},
           "command": "python docs/evaluation/geometry/runs/compositional-semantics-simulation-goals/tools/scene_invariants_run.py",
           "dataset_partition": "DEVELOPMENT (agent corpus of this run; exposed probes of earlier runs)",
           "oracle_status": "AGENT_DIAGNOSTIC exact checks (Fractions + envelope Gram G), independent of the construction code",
           "plane_constraint_probes": {"as_expected": sum(r["outcome"] == "AS_EXPECTED" for r in plane_rows.values()), "probes": len(plane_rows),
                                       "wrong_served": sum(r["outcome"] == "WRONG_SERVED" for r in plane_rows.values())},
           "section_intersection_dihedral_probes": {"served": sum(r["status"] == "SERVED" for r in prev.values()), "probes": len(prev),
                                                    "checks": sum(r["checks"] for r in prev.values()), "failed": sum(len(r["failed"]) for r in prev.values())},
           "new_served_items": new_rows,
           "new_served_checks": sum(r["checks"] for r in new_rows.values()), "new_served_failed": sum(len(r["failed"]) for r in new_rows.values()),
           "equivalence_pairs": pairs, "mutations": muts,
           "mutations_caught": f"{sum(m['caught'] for m in muts)}/{len(muts)}"}
    (RUN / "scene3d_mathematical_invariants.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print({k: v for k, v in out.items() if k in ("plane_constraint_probes", "section_intersection_dihedral_probes", "new_served_checks",
                                                 "new_served_failed", "mutations_caught")},
          [p for p in pairs if not p["same_certified_geometry"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
