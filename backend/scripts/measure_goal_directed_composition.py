"""Comparative / ablation measurement of run `goal-directed-function-composition` — 0 model calls, never overwrites output.

    python scripts/measure_goal_directed_composition.py run-all --out <NEW dir> [--base-root <checkout of the base commit>]
    python scripts/measure_goal_directed_composition.py arm --arm <name> --out <dir> [--code-root <checkout>]

Every arm reads the SAME typed facts (corpus-dev / corpus-holdout of the run), the SAME Registry snapshot of its code root
and the SAME exact engine; expected values come from the run's independent `oracle.py` (no `app.*` import). Arms differ
only in what the planner may compose:

    goal-directed        production planner (bounded backward search, MAX_EFFECT_DEPTH = 3)
    single-step          same, MAX_EFFECT_DEPTH = 2 (one producer level under a goal)
    no-composition       same, MAX_EFFECT_DEPTH = 1 (a goal on objects the source names; no producer)
    rule-based           no rule constructs an object the source does not name (described points refused); the Registry is
                         NOT reduced — named facts, named-line feet and declared intersections keep their rules
    pre-composition-main the production planner of `--base-root` (the commit before this run), same inputs
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import time
from copy import deepcopy
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/evaluation/geometry/runs/goal-directed-function-composition"
CORPORA = ("corpus-dev.json", "corpus-holdout.json")
ARMS = ("goal-directed", "single-step", "no-composition", "rule-based", "pre-composition-main")
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def _oracle():
    spec = importlib.util.spec_from_file_location("composition_oracle", RUN / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _apply(arm: str) -> None:
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import TuChoi

    if arm in ("goal-directed", "pre-composition-main"):
        return
    if arm in ("single-step", "no-composition"):
        planner.MAX_EFFECT_DEPTH = 2 if arm == "single-step" else 1
        return
    if arm == "rule-based":
        resolve = planner._EffectResolver._resolve

        def no_unnamed(self, kind, operands, depth=0):
            if kind == "Point" and isinstance(operands[0], tuple) and operands[0][:1] == ("desc",):
                raise TuChoi("UNSUPPORTED_CAPABILITY", "rule-based: no rule constructs a point the source does not name")
            return resolve(self, kind, operands, depth)

        planner._EffectResolver._resolve = no_unnamed
        return
    raise SystemExit(f"unknown arm {arm}")


def _value(r, q):
    v = r.exec_result.final_memory.get(f"kq_{q}")
    if str(r.answers.get(q, "")).startswith("cos²="):
        return Fraction(v)
    if hasattr(v, "can"):
        return None if getattr(v, "mu", 0) else Fraction(v.he) ** 2 * v.can
    return Fraction(v) ** 2


def _signature(r) -> str | None:
    """Functions the plan composed for each asked goal: chain producers → ask, or the ask alone when nothing was built."""
    if r.status != "SERVED":
        return None
    chains = {d["ask"]: [e["fn"] for e in d["chain"]] for d in r.planner.get("auxiliary", []) if d.get("rule") == "effect-chain"}
    feet = {d["ask"]: d for d in r.planner.get("auxiliary", []) if d.get("rule") == "distance(point,line)"}
    parts = []
    for c in r.planner["calls"]:
        if not c["fn"].startswith("ask_"):
            continue
        fns = chains.get(c["id"]) or ([next(x["fn"] for x in r.planner["calls"] if x["id"] == feet[c["id"]]["construct"]), c["fn"]]
                                       if c["id"] in feet else [c["fn"]])
        parts.append("->".join(dict.fromkeys(fns)))
    return " | ".join(parts)


def _timeline_ok(scene: dict) -> bool:
    born: dict[str, int] = {}
    for st in scene["formation"]["steps"]:
        for vid in st["visible_ids"]:
            born.setdefault(vid, st["step_index"])
    return all(born[d] <= born[o["id"]] for o in scene["objects"] if o["id"] in born
               for d in o.get("depends") or () if d in born)


def arm(name: str, out: Path, code_root: Path, corpora: tuple[str, ...] = CORPORA) -> None:
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import REGISTRY_VERSION, TuChoi

    _apply(name)
    oracle = _oracle()
    rows = []
    for corpus in corpora:
        for c in json.loads((RUN / corpus).read_text(encoding="utf-8"))["cases"]:
            payload = {"facts": c["payload"]["facts"]}
            t0 = time.perf_counter()
            try:
                k = planner.lap_ke_hoach(deepcopy(payload), c["text"])
                rv, plan_err = k.resolver, None
            except TuChoi as e:
                k, rv, plan_err = None, None, e.code
            plan_ms = (time.perf_counter() - t0) * 1000
            t0 = time.perf_counter()
            r = run_fact_route(c["text"], deepcopy(payload))
            route_ms = (time.perf_counter() - t0) * 1000
            want = oracle.expected(c) if c["kind"] == "positive" else {}
            got = {q: str(_value(r, q)) for q in r.answers} if r.status == "SERVED" else {}
            if c["kind"] == "positive":
                verdict = ("VERIFIED" if r.status == "SERVED" and got == want else
                           "WRONG_SERVE" if r.status == "SERVED" else "REFUSED")
            else:
                verdict = ("FALSE_SERVE" if r.status == "SERVED" else
                           "CORRECT_REFUSAL" if r.code in c["expected_codes"] else "REFUSED_OTHER_CODE")
            fresh = [x for d in (k.auxiliary if k else []) for x in (d.get("labels") or ([d["label"]] if d.get("label") else []))]
            rows.append({
                "corpus": corpus, "id": c["id"], "split": c["split"], "kind": c["kind"], "source": c.get("source"),
                "novelty": c.get("novelty"), "composition_declared": c.get("composition"),
                "status": r.status, "code": r.code, "verdict": verdict, "values": got, "expected": want,
                "expected_codes": c.get("expected_codes"), "signature": _signature(r),
                "goals": len(want) if c["kind"] == "positive" else 0,
                "goals_verified": sum(got.get(q) == v for q, v in want.items()) if r.status == "SERVED" else 0,
                "calls": len(r.planner.get("calls", [])) if r.planner else None, "fresh_constructions": len(fresh),
                "search": {"needs": getattr(rv, "needs", None), "candidates": getattr(rv, "candidates", None),
                           "depth_max": getattr(rv, "depth_max", None)},
                "plan_error": plan_err, "plan_ms": round(plan_ms, 3), "route_ms": round(route_ms, 3),
                "scene_timeline_ok": _timeline_ok(r.scene3d) if r.status == "SERVED" else None,
            })
    out.mkdir(parents=True, exist_ok=True)
    (out / f"arm-{name}.json").write_text(json.dumps({
        "schema": "goal-directed-composition-arm/1", "arm": name, "code_root_head": _head(code_root),
        "registry_version": REGISTRY_VERSION, "planner_version": planner.PLANNER_VERSION,
        "max_effect_depth": planner.MAX_EFFECT_DEPTH, "model_calls": 0, "rows": rows}, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8")


BUNDLE = ROOT / "docs/evaluation/geometry/runs/contract-driven-goal-composition/baseline/bundle-174.json"


def bundle_arm(name: str, out: Path, code_root: Path) -> None:
    """Supplementary split: the preregistered 174-row bundle (expectations from its SOURCE corpora, not product output).
    Added after the main evaluation to separate depth 2 from depth 3 — the run's corpora hold no depth-2 composition."""
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route

    _apply(name)
    rows = []
    for row in json.loads(BUNDLE.read_text(encoding="utf-8"))["rows"]:
        e = row["expect"]
        want = e.get("expected_squared") or e.get("answer_sq") or e.get("area_sq")
        r = run_fact_route(row["text"], {"facts": deepcopy(row["facts"])})
        got = {q: _value(r, q) for q in r.answers} if r.status == "SERVED" else {}
        if want is not None and e.get("status", "SERVED") == "SERVED":
            want = {"_": want} if isinstance(want, str) else want
            ok = r.status == "SERVED" and all(
                v == Fraction(want["_"] if "_" in want else want[q]) for q, v in got.items()) and bool(got)
            verdict = "VERIFIED" if ok else "WRONG_SERVE" if r.status == "SERVED" else "REFUSED"
        elif e.get("expected_codes"):
            verdict = ("FALSE_SERVE" if r.status == "SERVED" else
                       "CORRECT_REFUSAL" if r.code in e["expected_codes"] else "REFUSED_OTHER_CODE")
        else:
            verdict = "NO_INDEPENDENT_EXPECTATION"
        rows.append({"corpus": row["corpus"], "id": row["id"], "status": r.status, "code": r.code, "verdict": verdict,
                     "signature": _signature(r)})
    out.mkdir(parents=True, exist_ok=True)
    (out / f"bundle-{name}.json").write_text(json.dumps({"schema": "goal-directed-composition-bundle-arm/1", "arm": name,
                                                         "code_root_head": _head(code_root), "rows": rows},
                                                        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _head(code_root: Path) -> str:
    return subprocess.run(["git", "-C", str(code_root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def _metrics(rows: list[dict], novel_before: set[str]) -> dict:
    pos = [r for r in rows if r["kind"] == "positive"]
    neg = [r for r in rows if r["kind"] == "negative"]
    served = [r for r in rows if r["status"] == "SERVED"]
    novel_rows = [r for r in pos if r["novelty"] == "novel_function_combination"]
    solved_novel = {r["signature"] for r in novel_rows if r["verdict"] == "VERIFIED"} - novel_before
    stats = [r["search"] for r in pos if r["verdict"] == "VERIFIED" and r["search"]["needs"] is not None]

    def frac(n, d):
        return {"n": n, "d": d}

    return {
        "verified_problem_coverage": frac(sum(r["verdict"] == "VERIFIED" for r in pos), len(pos)),
        "novel_combination_problems_verified": frac(sum(r["verdict"] == "VERIFIED" for r in novel_rows), len(novel_rows)),
        "novel_function_combinations_solved": {"count": len(solved_novel), "signatures": sorted(solved_novel)},
        "goals_solved": frac(sum(r["goals_verified"] for r in pos), sum(r["goals"] for r in pos)),
        "correct_refusal_rate": frac(sum(r["verdict"] == "CORRECT_REFUSAL" for r in neg), len(neg)),
        "refused_with_other_code": frac(sum(r["verdict"] == "REFUSED_OTHER_CODE" for r in neg), len(neg)),
        "false_positive_rate": frac(sum(r["verdict"] in ("WRONG_SERVE", "FALSE_SERVE") for r in rows), len(rows)),
        "intermediate_constructions_on_verified": sum(r["fresh_constructions"] for r in pos if r["verdict"] == "VERIFIED"),
        "search_max": {k: max((s[k] for s in stats), default=None) for k in ("needs", "candidates", "depth_max")},
        "plan_ms_median_verified": sorted(r["plan_ms"] for r in pos if r["verdict"] == "VERIFIED")[
            len([r for r in pos if r["verdict"] == "VERIFIED"]) // 2] if any(r["verdict"] == "VERIFIED" for r in pos) else None,
        "scene_timeline_ok": frac(sum(bool(r["scene_timeline_ok"]) for r in served), len(served)),
    }


def compare(out: Path) -> None:
    arms = {a: json.loads((out / f"arm-{a}.json").read_text(encoding="utf-8")) for a in ARMS if (out / f"arm-{a}.json").exists()}
    base = arms.get("pre-composition-main")
    before = {r["signature"] for r in (base or {"rows": []})["rows"] if r["verdict"] == "VERIFIED" and r["signature"]}
    summary = {}
    for a, data in arms.items():
        summary[a] = {split: _metrics([r for r in data["rows"] if r["split"] == split], before) for split in ("dev", "holdout")}
    (out / "metrics.json").write_text(json.dumps({
        "schema": "goal-directed-composition-metrics/1", "model_calls": 0,
        "novelty_reference": "signatures VERIFIED by `pre-composition-main` on the same inputs are not counted as novel",
        "inputs": {name: _sha(RUN / name) for name in (*CORPORA, "oracle.py")},
        "arms": summary}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("run-all", "arm", "compare", "bundle-arm"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--code-root", type=Path, default=ROOT)
    ap.add_argument("--base-root", type=Path)
    ap.add_argument("--dev-only", action="store_true", help="arm: development corpus only (never reads the holdout)")
    a = ap.parse_args()
    out = a.out.resolve()
    if a.cmd == "arm":
        arm(a.arm, out, a.code_root.resolve(), CORPORA[:1] if a.dev_only else CORPORA)
        return 0
    if a.cmd == "compare":
        compare(out)
        return 0
    if a.cmd == "bundle-arm":
        bundle_arm(a.arm, out, a.code_root.resolve())
        return 0
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    lock = json.loads((RUN / "holdout-lock.json").read_text(encoding="utf-8"))
    if _sha(RUN / "corpus-holdout.json") != lock["corpus_holdout_sha256"] or _sha(RUN / "oracle.py") != lock["oracle_sha256"]:
        print("holdout corpus or oracle differs from its lock")
        return 3
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "PYTHONIOENCODING": "utf-8"}
    for name in ARMS:
        root = (a.base_root.resolve() if a.base_root else None) if name == "pre-composition-main" else ROOT
        if root is None:
            continue
        subprocess.run([sys.executable, __file__, "arm", "--arm", name, "--out", str(out), "--code-root", str(root)],
                       check=True, env=env)
    compare(out)
    print(json.dumps(json.loads((out / "metrics.json").read_text(encoding="utf-8"))["arms"], ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
