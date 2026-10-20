"""Offline development evaluation of one code snapshot on the Wave 2C locked development corpus.

Run each arm in a fresh process: --code-root <snapshot> --out <new JSON>. No provider calls.
The oracle uses similarity/area-ratio identities independently of product Gram and boundary-volume algorithms.
"""
import argparse
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/evaluation/geometry/runs/composite-geometry"


def measure(code_root):
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions.planner import lap_ke_hoach
    from app.simulation.geometry_functions.registry import TuChoi, doc_ke_hoach, kiem_nguon
    spec = importlib.util.spec_from_file_location("composite_oracle", RUN / "oracle.py")
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    rows = []
    for c in json.loads((RUN / "corpus-dev.json").read_text(encoding="utf-8"))["cases"]:
        k, source, plan_code, source_code = None, False, None, None
        t0 = time.perf_counter()
        try:
            k = lap_ke_hoach(deepcopy(c["payload"]), c["text"])
        except TuChoi as e:
            plan_code = e.code
        if k is not None:
            try:
                kiem_nguon(doc_ke_hoach({"calls": k.calls}), c["text"], tuple(k.auxiliary))
                source = True
            except TuChoi as e:
                source_code = e.code
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        got = {}
        for q in r.answers:
            v = r.exec_result.final_memory["kq_" + q]
            got[q] = str(Fraction(v.he)**2*v.can if hasattr(v, "can") else Fraction(v)**2)
        want = oracle.expected(c) if c["kind"] == "positive" else {}
        born, valid, topology = {}, None, None
        if r.status == "SERVED":
            for st in r.scene3d["formation"]["steps"]:
                for vid in st["visible_ids"]:
                    born.setdefault(vid, st["step_index"])
            objs = r.scene3d["objects"]
            valid = all(born[d] <= born[o["id"]] for o in objs if o["id"] in born for d in o.get("depends", []) if d in born)
            solids = [o for o in objs if o["type"] == "solid"]
            topology = (len({o["id"] for o in objs}) == len(objs)
                        and all(o.get("shape_class") == "PYRAMID_LIKE" and len(set(o["vertex_ids"])) == len(o["vertex_ids"])
                                and all(0 <= i < len(o["vertex_ids"]) for face in o["faces"] for i in face) for o in solids))
        rv = k.resolver if k else None
        rows.append(dict(id=c["id"], kind=c["kind"], slice=c.get("oracle", {}).get("slice"), status=r.status, code=r.code,
                         planner_resolved=k is not None, planner_code=plan_code, source_gate_success=source, source_code=source_code,
                         expected=want, got=got, exact_served=r.status == "SERVED" and got == want and c["kind"] == "positive",
                         correct_refusal=r.status == "REFUSED" and c["kind"] == "negative" and r.code in c["expected_codes"],
                         false_serve=r.status == "SERVED" and (c["kind"] == "negative" or got != want),
                         goals=len(want), goals_exact=sum(got.get(q) == v for q, v in want.items()),
                         calls=len(k.calls) if k else None, search=dict(needs=getattr(rv, "needs", None),
                         candidates=getattr(rv, "candidates", None), depth=getattr(rv, "depth_max", None)),
                         scene_timeline_valid=valid, scene_topology_valid=topology,
                         functions=[c["fn"] for c in k.calls] if k else [],
                         volume_certificates=[s for s in r.trace if s["step"] == "verify_solid"],
                         duration_ms=round((time.perf_counter()-t0)*1000, 3)))
    pos = [r for r in rows if r["kind"] == "positive"]
    neg = [r for r in rows if r["kind"] == "negative"]
    count = lambda key, xs: sum(bool(r[key]) for r in xs)
    return dict(measurement_class="DEVELOPMENT_EVALUATION_NOT_BLIND", code_root=str(code_root),
                full_sha=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=code_root, text=True).strip(),
                product_dirty=bool(subprocess.check_output(["git", "diff", "--name-only", "HEAD", "--", "backend/app", "frontend/src"], cwd=code_root, text=True).strip()),
                live_provider_calls=0, rows=rows, metrics=dict(positive_exact_served=[count("exact_served", pos), len(pos)],
                planner_resolved=[count("planner_resolved", pos), len(pos)], source_gate_success=[count("source_gate_success", pos), len(pos)],
                goal_coverage=[sum(r["goals_exact"] for r in pos), sum(r["goals"] for r in pos)],
                correct_refusal=[count("correct_refusal", neg), len(neg)], false_serves=count("false_serve", rows),
                scene_valid=[sum(r["scene_timeline_valid"] is True and r["scene_topology_valid"] is True for r in rows),
                             sum(r["status"] == "SERVED" for r in rows)],
                max_calls=max((r["calls"] or 0 for r in rows), default=0)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--code-root", type=Path, default=ROOT)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    out = a.out.resolve()
    if out.exists():
        raise SystemExit("refusing to overwrite evaluation evidence")
    os.environ["ALLOW_LIVE_AI"] = "0"
    result = measure(a.code_root.resolve())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()
