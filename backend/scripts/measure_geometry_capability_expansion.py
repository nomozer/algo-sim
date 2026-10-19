"""Baseline comparison of run `geometry-capability-expansion` — 0 model calls, never overwrites output.

    python scripts/measure_geometry_capability_expansion.py run-all --out <NEW dir> --base-root <checkout of main before>
    python scripts/measure_geometry_capability_expansion.py arm --arm <expansion|pre-expansion-main> --out <dir> [--code-root]

Both arms read the SAME typed facts (the run's `corpus-dev.json`) and are scored against the run's independent
`oracle.py`. `expansion` runs this checkout; `pre-expansion-main` runs `--base-root` (main before the run). Per case: status,
refusal code, exact values vs oracle, composed chain, search cost, Scene3D timeline order, and the case's
`success_source` label (new primitive / new composition / new configuration / semantic representation).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_goal_directed_composition as base  # noqa: E402  (shared value / chain / timeline readers)

ROOT = HERE.parents[1]
RUN = ROOT / "docs/evaluation/geometry/runs/geometry-capability-expansion"
ARMS = ("expansion", "pre-expansion-main")
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def _oracle():
    spec = importlib.util.spec_from_file_location("capability_oracle", RUN / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def arm(name: str, out: Path, code_root: Path) -> None:
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import REGISTRY, REGISTRY_VERSION, TuChoi

    oracle, rows = _oracle(), []
    for c in json.loads((RUN / "corpus-dev.json").read_text(encoding="utf-8"))["cases"]:
        payload = {"facts": c["payload"]["facts"]}
        try:
            k = planner.lap_ke_hoach(deepcopy(payload), c["text"])
            rv = k.resolver
        except (TuChoi, Exception):                       # a base checkout may not even parse a new fact form
            k = rv = None
        t0 = time.perf_counter()
        r = run_fact_route(c["text"], deepcopy(payload))
        ms = (time.perf_counter() - t0) * 1000
        want = oracle.expected(c) if c["kind"] == "positive" else {}
        got = {q: str(base._value(r, q)) for q in r.answers} if r.status == "SERVED" else {}
        if c["kind"] == "positive":
            verdict = "VERIFIED" if r.status == "SERVED" and got == want else "WRONG_SERVE" if r.status == "SERVED" else "REFUSED"
        else:
            verdict = ("FALSE_SERVE" if r.status == "SERVED" else
                       "CORRECT_REFUSAL" if r.code in c["expected_codes"] else "REFUSED_OTHER_CODE")
        rows.append({"id": c["id"], "kind": c["kind"], "source": c["source"], "success_source": c.get("success_source"),
                     "composition_declared": c.get("composition"), "status": r.status, "code": r.code, "verdict": verdict,
                     "values": got, "expected": want, "expected_codes": c.get("expected_codes"),
                     "goals": len(want), "goals_verified": sum(got.get(g) == v for g, v in want.items()),
                     "signature": base._signature(r), "calls": len(r.planner.get("calls", [])) if r.planner else None,
                     # every construct function the executed plan used (named producers, decomposition auxiliaries)
                     "constructs": dict(Counter(x["fn"] for x in (r.planner.get("calls", []) if r.planner else [])
                                                if REGISTRY.get(x["fn"]) and REGISTRY[x["fn"]].kind == "construct")),
                     "auxiliary_points": sum(len(d.get("labels") or []) + len(d.get("feet") or [])
                                             for d in (k.auxiliary if k else []) if isinstance(d, dict)),
                     "search": {"needs": getattr(rv, "needs", None), "candidates": getattr(rv, "candidates", None),
                                "depth_max": getattr(rv, "depth_max", None)},
                     "route_ms": round(ms, 3),
                     "scene_timeline_ok": base._timeline_ok(r.scene3d) if r.status == "SERVED" else None,
                     "has_section": (any(o["type"] == "section" for o in r.scene3d["objects"])
                                     if r.status == "SERVED" else None)})
    out.mkdir(parents=True, exist_ok=True)
    (out / f"arm-{name}.json").write_text(json.dumps({
        "schema": "geometry-capability-arm/1", "arm": name, "code_root_head": base._head(code_root),
        "registry_version": REGISTRY_VERSION, "planner_version": planner.PLANNER_VERSION, "model_calls": 0, "rows": rows},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def compare(out: Path) -> None:
    arms = {a: json.loads((out / f"arm-{a}.json").read_text(encoding="utf-8"))["rows"] for a in ARMS}

    def frac(n, d):
        return {"n": n, "d": d}

    summary = {}
    for a, rows in arms.items():
        pos, neg = [r for r in rows if r["kind"] == "positive"], [r for r in rows if r["kind"] == "negative"]
        summary[a] = {
            "verified_coverage": frac(sum(r["verdict"] == "VERIFIED" for r in pos), len(pos)),
            "goals_solved": frac(sum(r["goals_verified"] for r in pos), sum(r["goals"] for r in pos)),
            "correct_refusals": frac(sum(r["verdict"] == "CORRECT_REFUSAL" for r in neg), len(neg)),
            "refused_other_code": frac(sum(r["verdict"] == "REFUSED_OTHER_CODE" for r in neg), len(neg)),
            "false_serves": frac(sum(r["verdict"] in ("WRONG_SERVE", "FALSE_SERVE") for r in rows), len(rows)),
            "by_success_source": {s: frac(sum(r["verdict"] == "VERIFIED" for r in pos if r["success_source"] == s),
                                          sum(r["success_source"] == s for r in pos))
                                  for s in sorted({r["success_source"] for r in pos})},
            "scene_timeline_ok": frac(sum(bool(r["scene_timeline_ok"]) for r in rows if r["status"] == "SERVED"),
                                      sum(r["status"] == "SERVED" for r in rows)),
            "refusal_codes": dict(Counter(r["code"] for r in rows if r["status"] != "SERVED")),
            "distinct_chains_verified": sorted({r["signature"] for r in pos if r["verdict"] == "VERIFIED"}),
        }
    before = {r["id"]: r for r in arms["pre-expansion-main"]}
    changed = [{"id": r["id"], "before": [before[r["id"]]["status"], before[r["id"]]["code"]], "after": [r["status"], r["code"]]}
               for r in arms["expansion"] if [r["status"], r["code"]] != [before[r["id"]]["status"], before[r["id"]]["code"]]]
    (out / "metrics.json").write_text(json.dumps({
        "schema": "geometry-capability-metrics/1", "model_calls": 0, "arms": summary, "changed_vs_pre_expansion_main": changed},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run-all", "arm", "compare"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--code-root", type=Path, default=ROOT)
    ap.add_argument("--base-root", type=Path)
    a = ap.parse_args()
    out = a.out.resolve()
    if a.cmd == "arm":
        arm(a.arm, out, a.code_root.resolve())
        return 0
    if a.cmd == "compare":
        compare(out)
        return 0
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "PYTHONIOENCODING": "utf-8"}
    for name, root in (("expansion", ROOT), ("pre-expansion-main", a.base_root.resolve())):
        subprocess.run([sys.executable, __file__, "arm", "--arm", name, "--out", str(out), "--code-root", str(root)],
                       check=True, env=env)
    compare(out)
    print(json.dumps(json.loads((out / "metrics.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
