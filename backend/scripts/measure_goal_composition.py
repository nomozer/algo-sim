"""Comparative and ablation replay for run `contract-driven-goal-composition` — 0 model calls, never overwrites output.

Usage:
    python backend/scripts/measure_goal_composition.py run-all --out-dir docs/evaluation/geometry/runs/contract-driven-goal-composition
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from fractions import Fraction
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time
import tracemalloc

import measure_function_discovery as fd
import measure_goal_entry as ge

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/evaluation/geometry/runs/contract-driven-goal-composition"
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def apply_variant(variant: str) -> None:
    from app.simulation.geometry_functions import planner, registry

    R = registry.REGISTRY
    if variant == "production":
        return
    if variant == "no-area":
        R["ask_area"] = replace(R["ask_area"], planning=None)
        return
    if variant == "lying-area-verifier":
        R["ask_area"] = replace(R["ask_area"], planning=replace(R["ask_area"].planning, verifier="length"))
        return
    ge.variant(variant)
    assert planner.REGISTRY is registry.REGISTRY


def build_bundle(out: Path) -> None:
    with TemporaryDirectory() as td:
        p = Path(td) / "ge_bundle.json"
        ge.bundle(p)
        data = json.loads(p.read_text(encoding="utf-8"))
    corpus = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))
    for split in ("positive", "discovery", "held_out", "angle_line_plane_slice_b", "negative"):
        for c in corpus[split]:
            expect = {
                k: c[k]
                for k in ("expected_squared", "expected_cos_sq", "expected_codes", "expected_code", "expected_answer")
                if k in c
            }
            data["rows"].append({
                "corpus": f"goal_composition/{split}",
                "id": c["id"],
                "slice": c.get("slice"),
                "text": c["text"],
                "facts": c["payload"]["facts"],
                "expect": expect,
            })
    data["schema"] = "goal_composition_bundle/1"
    fd._write(out, data)


def run_arm_in_memory(rows: list[dict], label: str, variant: str) -> dict:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions import planner, registry
    from app.simulation.geometry_functions.registry import TuChoi

    saved_registry = dict(registry.REGISTRY)
    try:
        apply_variant(variant)
        res = []
        for row in rows:
            payload = {"facts": row["facts"]}
            t0 = time.perf_counter()
            r = run_fact_route(row["text"], json.loads(json.dumps(payload)))
            route_s = time.perf_counter() - t0
            squares = {}
            cos2s = {}
            if r.status == "SERVED":
                fm = r.exec_result.final_memory
                for q, ans_str in (r.answers or {}).items():
                    val = fm.get(f"kq_{q}")
                    squares[q] = fd._square(val)
                    if isinstance(val, (int, Fraction)) and str(ans_str).startswith("cos²="):
                        cos2s[q] = str(Fraction(val))
            tracemalloc.start()
            t0 = time.perf_counter()
            try:
                k = planner.lap_ke_hoach(json.loads(json.dumps(payload)), row["text"])
                plan_err = None
            except TuChoi as e:
                k, plan_err = None, e.code
            plan_s = time.perf_counter() - t0
            peak = tracemalloc.get_traced_memory()[1]
            tracemalloc.stop()
            stats = None
            if k is not None:
                rv = getattr(k, "resolver", None)
                fresh = [x for d in k.auxiliary for x in (d.get("labels") or ([d["label"]] if d.get("label") else []))]
                stats = {
                    "calls": len(k.calls),
                    "functions": sorted({c["fn"] for c in k.calls}),
                    "auxiliary": len(k.auxiliary),
                    "fresh_labels": fresh,
                    "needs": getattr(rv, "needs", None),
                    "candidates": getattr(rv, "candidates", None),
                    "depth_max": getattr(rv, "depth_max", None),
                    "resolver_used": getattr(rv, "used", None),
                }
            res.append({
                "corpus": row["corpus"],
                "id": row["id"],
                "status": r.status,
                "code": r.code,
                "answers": r.answers or {},
                "squares": squares,
                "cos2s": cos2s,
                "plan_error": plan_err,
                "plan": stats,
                "route_seconds": round(route_s, 4),
                "plan_seconds": round(plan_s, 5),
                "plan_peak_bytes": peak,
            })
        return {
            "schema": "goal_composition_arm/1",
            "label": label,
            "registry_variant": variant,
            "planner_version": planner.PLANNER_VERSION,
            "registry_version": registry.REGISTRY_VERSION,
            "model_calls": 0,
            "rows": res,
        }
    finally:
        registry.REGISTRY.clear()
        registry.REGISTRY.update(saved_registry)


def classify_row(row: dict, got: dict) -> str:
    e = row["expect"]
    served = got["status"] == "SERVED"
    if "expected_cos_sq" in e:
        want = e["expected_cos_sq"]
        ok = served and (all(got.get("cos2s", {}).get(q) == v for q, v in want.items()) if isinstance(want, dict)
                         else bool(got.get("cos2s")) and all(v == want for v in got["cos2s"].values()))
        return "correct_served" if ok else "wrong_served" if served else "false_refusal"
    return fd.classify(row, got)


#: Capability-disabled negatives: valid, source-grounded mathematical problems placed in a `negative` split solely to
#: verify fail-closed refusal (`UNSUPPORTED_CAPABILITY`) when a producer contract is absent from the production catalog.
#: Paired with their exact discovery twin and independent oracle squared value when the capability arm is enabled.
CAPABILITY_DISABLED_NEGATIVES = {
    "new/negative::centroid-without-contract": {
        "enabled_in_arms": ("NEW[centroid]",),
        "discovery_twin": "new/discovery::centroid-to-plane",
        "oracle_expected_squared": {"q": "16/9"},
        "oracle_expected_answer": {"q": "4/3"},
        "disabled_expected_codes": ["UNSUPPORTED_CAPABILITY"],
    }
}


def reconcile_ablation(ablation_path: Path, out_path: Path) -> None:
    """Reconcile raw ablation classifications by separating true safety negatives from capability-disabled negatives,
    without modifying raw ablation.json or any gold expectations."""
    ablation = json.loads(ablation_path.read_text(encoding="utf-8"))
    cases = ablation["cases"]
    reconciled_counts: dict[str, dict[str, dict[str, int]]] = {}
    safety_summary: dict[str, dict[str, int]] = {}
    capability_disabled_audit: dict[str, dict] = {}

    with TemporaryDirectory() as td:
        bpath = Path(td) / "bundle_all.json"
        build_bundle(bpath)
        bundle_rows = {f"{r['corpus']}::{r['id']}": r for r in json.loads(bpath.read_text(encoding="utf-8"))["rows"]}

    taxonomy = {
        "total_evaluated_cases": len(bundle_rows),
        "production_positive_cases": 0,
        "experimental_discovery_positive_cases": 0,
        "total_negative_cases": 0,
        "true_safety_negative_cases": 0,
        "true_safety_negative_explicit_splits": 0,
        "true_safety_negative_benchmark_and_two_line": 0,
        "capability_disabled_negative_cases": 0,
    }
    for cid, row in bundle_rows.items():
        c = row["corpus"]
        e = row["expect"]
        if cid in CAPABILITY_DISABLED_NEGATIVES:
            taxonomy["total_negative_cases"] += 1
            taxonomy["capability_disabled_negative_cases"] += 1
        elif c.endswith("/discovery"):
            taxonomy["experimental_discovery_positive_cases"] += 1
        elif "expected_codes" in e or "expected_code" in e:
            taxonomy["total_negative_cases"] += 1
            taxonomy["true_safety_negative_cases"] += 1
            taxonomy["true_safety_negative_explicit_splits"] += 1
        elif (c == "benchmark30" or c.startswith("two_line/")) and e.get("status") != "SERVED":
            taxonomy["total_negative_cases"] += 1
            taxonomy["true_safety_negative_cases"] += 1
            taxonomy["true_safety_negative_benchmark_and_two_line"] += 1
        else:
            taxonomy["production_positive_cases"] += 1

    for arm in ablation["counts"]:
        reconciled_counts[arm] = {}
        safety_summary[arm] = {
            "safety_wrong_served": 0,
            "true_safety_negatives_refused": 0,
            "true_safety_negatives_total": taxonomy["true_safety_negative_cases"],
            "capability_disabled_raw_wrong_served": 0,
            "capability_enabled_oracle_verified_served": 0,
        }

    for cid, by_arm in sorted(cases.items()):
        corpus = cid.split("::", 1)[0]
        row = bundle_rows[cid]
        e = row["expect"]
        is_true_safety_neg = (
            cid not in CAPABILITY_DISABLED_NEGATIVES
            and not corpus.endswith("/discovery")
            and (
                "expected_codes" in e
                or "expected_code" in e
                or ((corpus == "benchmark30" or corpus.startswith("two_line/")) and e.get("status") != "SERVED")
            )
        )
        cap_spec = CAPABILITY_DISABLED_NEGATIVES.get(cid)
        if cap_spec is not None:
            twin_by_arm = cases.get(cap_spec["discovery_twin"], {})
            capability_disabled_audit[cid] = {
                "negative_kind": "capability_disabled_negative",
                "discovery_twin": cap_spec["discovery_twin"],
                "oracle_expected_squared": cap_spec["oracle_expected_squared"],
                "oracle_expected_answer": cap_spec["oracle_expected_answer"],
                "arms": {},
            }
        for arm, res in by_arm.items():
            raw_outcome = res["outcome"]
            if cap_spec is not None:
                if arm in cap_spec["enabled_in_arms"]:
                    twin_res = twin_by_arm.get(arm, {})
                    oracle_match = (
                        res["status"] == "SERVED"
                        and res.get("squares") == cap_spec["oracle_expected_squared"]
                        and res.get("answers") == cap_spec["oracle_expected_answer"]
                        and twin_res.get("status") == "SERVED"
                        and twin_res.get("squares") == res.get("squares")
                    )
                    reconciled = "correct_served_enabled_capability" if oracle_match else "safety_wrong_served"
                    if raw_outcome == "wrong_served":
                        safety_summary[arm]["capability_disabled_raw_wrong_served"] += 1
                    if oracle_match:
                        safety_summary[arm]["capability_enabled_oracle_verified_served"] += 1
                    else:
                        safety_summary[arm]["safety_wrong_served"] += 1
                else:
                    reconciled = (
                        "correct_refusal_disabled_capability"
                        if res["status"] == "REFUSED" and res["code"] in cap_spec["disabled_expected_codes"]
                        else "correct_refusal_lying_contract_caught"
                        if res["status"] == "REFUSED" and res["code"] == "ENGINE_SELF_CHECK_FAILED"
                        else raw_outcome
                    )
                    if res["status"] == "SERVED":
                        safety_summary[arm]["safety_wrong_served"] += 1
                capability_disabled_audit[cid]["arms"][arm] = {
                    "raw_outcome": raw_outcome,
                    "reconciled_outcome": reconciled,
                    "status": res["status"],
                    "code": res["code"],
                    "answers": res["answers"],
                    "squares": res["squares"],
                }
            else:
                reconciled = raw_outcome
                if is_true_safety_neg and res["status"] == "REFUSED":
                    safety_summary[arm]["true_safety_negatives_refused"] += 1
                if raw_outcome == "wrong_served":
                    safety_summary[arm]["safety_wrong_served"] += 1
            reconciled_counts[arm].setdefault(corpus, Counter())[reconciled] += 1

    for arm in reconciled_counts:
        reconciled_counts[arm] = {c: dict(cnt) for c, cnt in sorted(reconciled_counts[arm].items())}

    out_data = {
        "schema": "goal_composition_ablation_reconciled/1",
        "source_ablation": str(ablation_path.relative_to(ROOT)).replace("\\", "/"),
        "model_calls": 0,
        "corpus_taxonomy_breakdown": taxonomy,
        "safety_summary_by_arm": safety_summary,
        "capability_disabled_negative_audit": capability_disabled_audit,
        "raw_counts": ablation["counts"],
        "reconciled_counts": reconciled_counts,
    }
    fd._write(out_path, out_data)
    print(json.dumps({
        "corpus_taxonomy_breakdown": taxonomy,
        "safety_summary_by_arm": safety_summary,
        "capability_disabled_negative_audit": capability_disabled_audit,
    }, ensure_ascii=False, indent=2))


def run_all(out_dir: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    baseline_reg_path = out_dir / "baseline/regression-174.json"
    baseline_reg = json.loads(baseline_reg_path.read_text(encoding="utf-8"))
    baseline_rows_by_key = {(r["corpus"], r["id"]): r for r in baseline_reg["rows"]}

    with TemporaryDirectory() as td:
        bpath = Path(td) / "bundle_all.json"
        build_bundle(bpath)
        bundle_all = json.loads(bpath.read_text(encoding="utf-8"))
    all_rows = bundle_all["rows"]
    rows_by_key = {(r["corpus"], r["id"]): r for r in all_rows}

    variants = ("production", "centroid", "no-area", "no-midpoint", "reversed", "lying", "lying-area-verifier")
    arms = {v: run_arm_in_memory(all_rows, "NEW", v) for v in variants}

    # 1. Verify 174 prior rows regression against baseline
    prod_prior = [r for r in arms["production"]["rows"] if not r["corpus"].startswith("goal_composition/")]
    rev_prior = [r for r in arms["reversed"]["rows"] if not r["corpus"].startswith("goal_composition/")]
    diffs_vs_baseline = []
    diffs_vs_reversed = []
    for r_prod, r_rev in zip(prod_prior, rev_prior):
        key = (r_prod["corpus"], r_prod["id"])
        r_base = baseline_rows_by_key[key]
        if (r_prod["status"], r_prod["code"], r_prod["answers"], r_prod["squares"], r_prod["plan"]) != (
            r_base["status"], r_base["code"], r_base["answers"], r_base["squares"], r_base["plan"]
        ):
            diffs_vs_baseline.append({"corpus": key[0], "id": key[1], "baseline": r_base, "new": r_prod})
        if (r_prod["status"], r_prod["code"], r_prod["answers"], r_prod["squares"]) != (
            r_rev["status"], r_rev["code"], r_rev["answers"], r_rev["squares"]
        ):
            diffs_vs_reversed.append({"corpus": key[0], "id": key[1], "production": r_prod, "reversed": r_rev})

    reg_out = {
        "schema": "goal_composition_regression_174/1",
        "model_calls": 0,
        "total_prior_rows": len(prod_prior),
        "n_differing_from_baseline": len(diffs_vs_baseline),
        "differing_from_baseline": diffs_vs_baseline,
        "n_differing_reversed_registry": len(diffs_vs_reversed),
        "differing_reversed_registry": diffs_vs_reversed,
        "rows": prod_prior,
    }
    fd._write(out_dir / "regression-174.json", reg_out)

    # 2. Summarize ablation across all arms
    summary_counts = {}
    per_case = {}
    for v, arm_data in arms.items():
        key = f"NEW[{v}]"
        counts: dict[str, Counter] = {}
        for got in arm_data["rows"]:
            row = rows_by_key[(got["corpus"], got["id"])]
            outcome = classify_row(row, got)
            counts.setdefault(got["corpus"], Counter())[outcome] += 1
            per_case.setdefault(f"{got['corpus']}::{got['id']}", {})[key] = {
                "outcome": outcome,
                "status": got["status"],
                "code": got["code"],
                "answers": got["answers"],
                "squares": got["squares"],
                "cos2s": got["cos2s"],
                "plan": got["plan"],
                "plan_seconds": got["plan_seconds"],
                "route_seconds": got["route_seconds"],
                "plan_peak_bytes": peak if "peak" in locals() else got["plan_peak_bytes"],
            }
        summary_counts[key] = {c: dict(cnt) for c, cnt in sorted(counts.items())}

    # Check production vs reversed across ALL 214 rows (174 prior + 40 new)
    prod_vs_rev_all = [
        cid for cid, by in per_case.items()
        if (
            by["NEW[production]"]["status"],
            by["NEW[production]"]["code"],
            by["NEW[production]"]["answers"],
            by["NEW[production]"]["squares"],
            by["NEW[production]"]["cos2s"],
        ) != (
            by["NEW[reversed]"]["status"],
            by["NEW[reversed]"]["code"],
            by["NEW[reversed]"]["answers"],
            by["NEW[reversed]"]["squares"],
            by["NEW[reversed]"]["cos2s"],
        )
    ]

    ablation_out = {
        "schema": "goal_composition_ablation/1",
        "model_calls": 0,
        "total_rows": len(all_rows),
        "prior_rows": len(prod_prior),
        "new_rows": len(all_rows) - len(prod_prior),
        "production_vs_reversed_differing_cases": prod_vs_rev_all,
        "counts": summary_counts,
        "cases": per_case,
    }
    fd._write(out_dir / "ablation.json", ablation_out)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run-all")
    r.add_argument("--out-dir", type=Path, default=RUN)
    rec = sub.add_parser("reconcile")
    rec.add_argument("--ablation", type=Path, default=RUN / "ablation.json")
    rec.add_argument("--out", type=Path, default=RUN / "ablation-reconciled.json")
    args = ap.parse_args()
    if args.cmd == "run-all":
        run_all(args.out_dir.resolve())
    elif args.cmd == "reconcile":
        reconcile_ablation(args.ablation.resolve(), args.out.resolve())


if __name__ == "__main__":
    main()
