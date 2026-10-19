"""Baseline comparison of run `source-gate-hardening` — 0 model calls, never overwrites output.

    python scripts/measure_source_gate_hardening.py run-all --out <NEW dir> --base-root <checkout of main before>
    python scripts/measure_source_gate_hardening.py arm --arm <hardened|baseline-main> --out <dir> [--code-root]
    python scripts/measure_source_gate_hardening.py compare --out <dir>

Both arms read the SAME typed facts (the run's `corpus.json`, groups A/B/C) and are scored against the run's independent
`oracle.py`: exact value (coefficient² at a = 1) and, for symbolic cases, the power of a in the served answer. Also per
case: refusal code, goal coverage, provenance (every call quote of a served plan is verbatim in the text), effect chains.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess
import sys
from collections import Counter
from copy import deepcopy
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import measure_goal_directed_composition as base  # noqa: E402  (shared value / chain / timeline readers)

ROOT = HERE.parents[1]
RUN = ROOT / "docs/evaluation/geometry/runs/source-gate-hardening"
ARMS = ("hardened", "baseline-main")
os.environ.setdefault("ALLOW_LIVE_AI", "0")
_POW = {"": 0, "a": 1, "a²": 2, "a³": 3}


def _oracle():
    spec = importlib.util.spec_from_file_location("source_gate_oracle", RUN / "oracle.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _power(answer: str) -> int | None:
    m = re.search(r"a[²³]?", answer)
    return _POW.get(m.group() if m else "")


def _verbatim(text: str, quote: str) -> bool:
    squash = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    return squash(quote) in squash(text)


def arm(name: str, out: Path, code_root: Path) -> None:
    sys.path.insert(0, str(code_root / "backend"))
    os.chdir(code_root / "backend")
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import REGISTRY_VERSION

    oracle, rows = _oracle(), []
    for c in json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))["cases"]:
        r = run_fact_route(c["text"], deepcopy(c["payload"]))
        want = oracle.expected(c) if c["kind"] == "positive" else {}
        got = {q: str(base._value(r, q)) for q in r.answers} if r.status == "SERVED" else {}
        powers_ok = all(_power(r.answers[g]) == (oracle.power(c["goals"][g]) if c.get("symbolic") else 0)
                        for g in want if g in r.answers)
        calls = r.planner.get("calls", []) if r.planner else []
        if c["kind"] == "positive":
            ok = r.status == "SERVED" and got == want and powers_ok
            verdict = "VERIFIED" if ok else "WRONG_SERVE" if r.status == "SERVED" else "REFUSED"
        else:
            verdict = ("FALSE_SERVE" if r.status == "SERVED" else
                       "CORRECT_REFUSAL" if r.code in c["expected_codes"] else "REFUSED_OTHER_CODE")
        rows.append({"id": c["id"], "group": c["group"], "sg": c["sg"], "kind": c["kind"], "status": r.status, "code": r.code,
                     "verdict": verdict, "values": got, "expected": want, "powers_ok": powers_ok if want else None,
                     "expected_codes": c.get("expected_codes"), "goals": len(want),
                     "goals_verified": sum(got.get(g) == v for g, v in want.items()),
                     "provenance_verbatim": (all(_verbatim(c["text"], x) for k in calls
                                                 for x in (k.get("source") or {}).get("quotes", []))
                                             if r.status == "SERVED" else None),
                     "effect_chains": (sum(d.get("rule") == "effect-chain" for d in r.planner.get("auxiliary", []))
                                       if r.status == "SERVED" else None),
                     "signature": base._signature(r),
                     "scene_timeline_ok": base._timeline_ok(r.scene3d) if r.status == "SERVED" else None})
    out.mkdir(parents=True, exist_ok=True)
    (out / f"arm-{name}.json").write_text(json.dumps({
        "schema": "source-gate-arm/1", "arm": name, "code_root_head": base._head(code_root),
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
            "positive_served": frac(sum(r["status"] == "SERVED" for r in pos), len(pos)),
            "exact_answer_match": frac(sum(r["verdict"] == "VERIFIED" for r in pos), len(pos)),
            "goal_coverage": frac(sum(r["goals_verified"] for r in pos), sum(r["goals"] for r in pos)),
            "correct_refusals": frac(sum(r["verdict"] == "CORRECT_REFUSAL" for r in neg), len(neg)),
            "refused_other_code": frac(sum(r["verdict"] == "REFUSED_OTHER_CODE" for r in neg), len(neg)),
            "wrong_serves": frac(sum(r["verdict"] in ("WRONG_SERVE", "FALSE_SERVE") for r in rows), len(rows)),
            "false_refusals_remaining": sorted(r["id"] for r in pos if r["status"] != "SERVED"),
            "provenance_verbatim": frac(sum(bool(r["provenance_verbatim"]) for r in rows if r["status"] == "SERVED"),
                                        sum(r["status"] == "SERVED" for r in rows)),
            "served_with_effect_chain": sum(bool(r["effect_chains"]) for r in rows if r["status"] == "SERVED"),
            "scene_timeline_ok": frac(sum(bool(r["scene_timeline_ok"]) for r in rows if r["status"] == "SERVED"),
                                      sum(r["status"] == "SERVED" for r in rows)),
            "by_group": {g: {"positive_verified": frac(sum(r["verdict"] == "VERIFIED" for r in pos if r["group"] == g),
                                                       sum(r["group"] == g for r in pos)),
                             "negative_correct": frac(sum(r["verdict"] == "CORRECT_REFUSAL" for r in neg if r["group"] == g),
                                                      sum(r["group"] == g for r in neg))}
                         for g in sorted({r["group"] for r in rows})},
            "by_sg": {s: frac(sum(r["verdict"] == "VERIFIED" for r in pos if r["sg"] == s), sum(r["sg"] == s for r in pos))
                      for s in sorted({r["sg"] for r in pos})},
            "refusal_codes": dict(Counter(r["code"] for r in rows if r["status"] != "SERVED")),
        }
    before = {r["id"]: r for r in arms["baseline-main"]}
    changed = [{"id": r["id"], "kind": r["kind"], "before": [before[r["id"]]["status"], before[r["id"]]["code"]],
                "after": [r["status"], r["code"]],
                # a negative that moved to another refusal code is CLASSIFIED, never counted as an unchanged pass
                "class": ("newly_served" if r["status"] == "SERVED" != before[r["id"]]["status"] else
                          "refusal_code_changed" if r["status"] == before[r["id"]]["status"] == "REFUSED" else "other")}
               for r in arms["hardened"] if [r["status"], r["code"]] != [before[r["id"]]["status"], before[r["id"]]["code"]]]
    (out / "metrics.json").write_text(json.dumps({
        "schema": "source-gate-metrics/1", "model_calls": 0, "arms": summary, "changed_vs_baseline_main": changed},
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
        if (out / f"arm-{a.arm}.json").exists():
            print(f"refusing to overwrite {out / f'arm-{a.arm}.json'}")
            return 2
        arm(a.arm, out, a.code_root.resolve())
        return 0
    if a.cmd == "compare":
        compare(out)
        return 0
    if out.exists():
        print(f"refusing to overwrite {out}")
        return 2
    env = {**os.environ, "ALLOW_LIVE_AI": "0", "PYTHONIOENCODING": "utf-8"}
    for name, root in (("hardened", ROOT), ("baseline-main", a.base_root.resolve())):
        subprocess.run([sys.executable, __file__, "arm", "--arm", name, "--out", str(out), "--code-root", str(root)],
                       check=True, env=env)
    compare(out)
    print(json.dumps(json.loads((out / "metrics.json").read_text(encoding="utf-8")), ensure_ascii=False, indent=1)[:5000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
