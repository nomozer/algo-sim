# -*- coding: utf-8 -*-
"""Build locked W2-M4 verification corpus and evaluate RED / GREEN outcomes."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ["ALLOW_LIVE_AI"] = "0"
sys.dont_write_bytecode = True

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

SG_RUN = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-wave2-source-gate-language-generalization"
HISTORY_W2 = "ecdc26b012c8ce80d53524a98dc75cdcb020079d"
HIST_W2_PATH = "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"


def git_blob(commit: str, rel: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{rel}"], cwd=ROOT)


def build_corpus() -> dict:
    sg_dev = json.loads((SG_RUN / "inputs/development.json").read_text(encoding="utf-8"))["cases"]
    dev_1_3 = next(c for c in sg_dev if c["id"] == "DEV-1-3")

    w2_cases = json.loads(git_blob(HISTORY_W2, f"{HIST_W2_PATH}/inputs/holdout-wave2.json"))["cases"]
    w2_oracles = json.loads(git_blob(HISTORY_W2, f"{HIST_W2_PATH}/oracle/expected.json"))
    w2_a04 = next(c for c in w2_cases if c["id"] == "W2-A04")
    w2_a04_oracle = w2_oracles["W2-A04"]

    # Independent exact verification of the two target oracles using pure integer arithmetic
    assert 6175 * 6175 == 38130625 and 242 * 242 == 58564
    assert 11250 * 11250 * 2 == 253125000 and 697 * 697 == 485809

    corpus = {
        "schema": "w2-m4-exact-radical-verification-corpus/1",
        "task": "HYBRID_V2_W2_M4_EXACT_RADICAL_NORMALIZATION",
        "max_radicand": 10**12,
        "end_to_end_cases": [
            {
                "id": "DEV-1-3",
                "source_corpus": "hybrid-v2-wave2-source-gate-language-generalization/inputs/development.json",
                "family": dev_1_3["family"],
                "plane_relation": dev_1_3["plane_relation"],
                "expected_status": "SERVED",
                "payload": dev_1_3["payload"],
                "oracle": dev_1_3["oracle"],
                "expected_exact_area": {
                    "kind": "rational",
                    "value": "6175/242",
                    "display": "6175/242",
                    "area_squared": "38130625/58564",
                },
            },
            {
                "id": "W2-A04",
                "source_corpus": "hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json",
                "family": w2_a04["family"],
                "plane_relation": w2_a04["plane_relation"],
                "expected_status": "SERVED",
                "payload": w2_a04["payload"],
                "oracle": w2_a04_oracle,
                "expected_exact_area": {
                    "kind": "radical",
                    "coefficient": "11250/697",
                    "radicand": 2,
                    "display": "11250√2/697",
                    "area_squared": "253125000/485809",
                },
            },
        ],
        "kernel_cases": [
            {
                "id": "K-01-zero-rational",
                "op": "sqrt_rational",
                "arg": "0",
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "0"},
                "expected_display": "0",
                "expected_square": "0",
            },
            {
                "id": "K-02-integer-square",
                "op": "sqrt_rational",
                "arg": "144",
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "12"},
                "expected_display": "12",
                "expected_square": "144",
            },
            {
                "id": "K-03-fraction-square",
                "op": "sqrt_rational",
                "arg": "49/121",
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "7/11"},
                "expected_display": "7/11",
                "expected_square": "49/121",
            },
            {
                "id": "K-04-dev-1-3-sqrt-rational",
                "op": "sqrt_rational",
                "arg": "38130625/58564",
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "6175/242"},
                "expected_display": "6175/242",
                "expected_square": "38130625/58564",
            },
            {
                "id": "K-05-w2-a04-sqrt-rational",
                "op": "sqrt_rational",
                "arg": "253125000/485809",
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "11250/697", "radicand": 2},
                "expected_display": "11250√2/697",
                "expected_square": "253125000/485809",
            },
            {
                "id": "K-06-large-coprime-prime-squares",
                "op": "sqrt_rational",
                "arg": f"{787867**2}/{468449**2}",
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "787867/468449"},
                "expected_display": "787867/468449",
                "expected_square": f"{787867**2}/{468449**2}",
            },
            {
                "id": "K-07-large-prime-squares-with-squarefree-3",
                "op": "sqrt_rational",
                "arg": f"{3 * (787867**2)}/{468449**2}",
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "787867/468449", "radicand": 3},
                "expected_display": "787867√3/468449",
                "expected_square": f"{3 * (787867**2)}/{468449**2}",
            },
            {
                "id": "K-08-dev-1-3-direct-radical",
                "op": "radical",
                "he": "1/58564",
                "can": 2233081922500,
                "mu": 0,
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "6175/242"},
                "expected_display": "6175/242",
                "expected_square": "38130625/58564",
            },
            {
                "id": "K-09-w2-a04-direct-radical",
                "op": "radical",
                "he": "1/485809",
                "can": 122970403125000,
                "mu": 0,
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "11250/697", "radicand": 2},
                "expected_display": "11250√2/697",
                "expected_square": "253125000/485809",
            },
            {
                "id": "K-10-negative-sign-radical",
                "op": "radical",
                "he": "-5/7",
                "can": 72,
                "mu": 0,
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "-30/7", "radicand": 2},
                "expected_display": "-30√2/7",
                "expected_square": "1800/49",
            },
            {
                "id": "K-11-zero-he-with-reducible-radicand-above-ceiling",
                "op": "radical",
                "he": "0",
                "can": 2233081922500,
                "mu": 0,
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "0"},
                "expected_display": "0",
                "expected_square": "0",
            },
            {
                "id": "K-12-pi-exponent-1",
                "op": "radical",
                "he": "3/4",
                "can": 12,
                "mu": 1,
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "3/2", "radicand": 3, "pi": 1},
                "expected_display": "3π√3/2",
                "expected_square": None,
            },
            {
                "id": "K-13-boundary-max-radicand-minus-1",
                "op": "radical",
                "he": "1",
                "can": 10**12 - 1,
                "mu": 0,
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "3", "radicand": 111111111111},
                "expected_display": "3√111111111111",
                "expected_square": str(10**12 - 1),
            },
            {
                "id": "K-14-boundary-exact-max-radicand",
                "op": "radical",
                "he": "1",
                "can": 10**12,
                "mu": 0,
                "expected_type": "Fraction",
                "expected_json": {"kind": "rational", "value": "1000000"},
                "expected_display": "1000000",
                "expected_square": str(10**12),
            },
            {
                "id": "K-15-boundary-large-prime-square-times-6",
                "op": "radical",
                "he": "1",
                "can": 6 * (1026601**2),
                "mu": 0,
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "1026601", "radicand": 6},
                "expected_display": "1026601√6",
                "expected_square": str(6 * (1026601**2)),
            },
            {
                "id": "K-16-multiply-shared-large-prime-factor",
                "op": "multiply",
                "a": {"he": "3/5", "can": 2 * 999983, "mu": 0},
                "b": {"he": "10/9", "can": 3 * 999983, "mu": 0},
                "expected_type": "Radical",
                "expected_json": {"kind": "radical", "coefficient": "1999966/3", "radicand": 6},
                "expected_display": "1999966√6/3",
                "expected_square": str(Fraction(1999966, 3) ** 2 * 6),
            },
        ],
        "metamorphic_groups": [
            {
                "id": "M-01-dev-1-3-equivalent-paths",
                "description": "Four distinct algebraic paths to DEV-1-3 section area must yield identical Fraction(6175, 242)",
                "expected_json": {"kind": "rational", "value": "6175/242"},
                "expected_display": "6175/242",
            },
            {
                "id": "M-02-w2-a04-equivalent-paths",
                "description": "Four distinct algebraic paths to W2-A04 section area must yield identical Radical(11250/697, 2)",
                "expected_json": {"kind": "radical", "coefficient": "11250/697", "radicand": 2},
                "expected_display": "11250√2/697",
            },
            {
                "id": "M-03-shared-prime-product-paths",
                "description": "sqrt(2k)*sqrt(3k), radical(1, 6k^2), and k*sqrt(6) for k=1026601=9973*103 must yield identical Radical(1026601, 6)",
                "expected_json": {"kind": "radical", "coefficient": "1026601", "radicand": 6},
                "expected_display": "1026601√6",
            },
            {
                "id": "M-04-cancellation-to-exact-zero",
                "description": "sqrt(50/49)*sqrt(98/25) - 2 must canonicalize to Fraction(0), not a Radical",
                "expected_json": {"kind": "rational", "value": "0"},
                "expected_display": "0",
            },
            {
                "id": "M-05-serialization-and-parse-roundtrip",
                "description": "to_json/from_json and display/parse_exact roundtrip on DEV-1-3 and W2-A04 areas",
                "expected_json": {"kind": "radical", "coefficient": "11250/697", "radicand": 2},
                "expected_display": "11250√2/697",
            },
            {
                "id": "M-06-square-is-exact-inverse-of-sqrt-rational",
                "description": "square(sqrt_rational(x)) == x for large-denominator rationals",
                "expected_json": {"kind": "rational", "value": "1"},
                "expected_display": "1",
            },
        ],
        "negative_cases": [
            {
                "id": "N-01-max-radicand-plus-1-squarefree",
                "op": "radical",
                "he": "1",
                "can": 10**12 + 1,
                "mu": 0,
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-02-prime-above-max-radicand",
                "op": "radical",
                "he": "1",
                "can": 10**12 + 39,
                "mu": 0,
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-03-sqrt-rational-coprime-product-above-max-radicand",
                "op": "sqrt_rational",
                "arg": "1000003/1000033",
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-04-multiply-squarefree-product-above-max-radicand",
                "op": "multiply",
                "a": {"he": "1", "can": 1000003, "mu": 0},
                "b": {"he": "1", "can": 1000033, "mu": 0},
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-05-reducible-by-4-but-squarefree-core-above-max-radicand",
                "op": "radical",
                "he": "1",
                "can": 4 * (10**12 + 39),
                "mu": 0,
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-06-above-hard-input-ceiling-max-squared",
                "op": "radical",
                "he": "1",
                "can": 10**24 + 7,
                "mu": 0,
                "expected_error": "RadicalDomainError",
                "max_ms": 50.0,
            },
            {
                "id": "N-07-zero-he-still-rejects-overflowing-radicand",
                "op": "radical",
                "he": "0",
                "can": 10**12 + 1,
                "mu": 0,
                "expected_error": "RadicalDomainError",
                "max_ms": 200.0,
            },
            {
                "id": "N-08-negative-rational-sqrt",
                "op": "sqrt_rational",
                "arg": "-4/9",
                "expected_error": "RadicalDomainError",
                "max_ms": 50.0,
            },
            {
                "id": "N-09-incommensurable-sum",
                "op": "add_incommensurable",
                "expected_error": "RadicalDomainError",
                "max_ms": 50.0,
            },
            {
                "id": "N-10-pi-squared-outside-domain",
                "op": "multiply",
                "a": {"he": "1", "can": 2, "mu": 1},
                "b": {"he": "1", "can": 3, "mu": 1},
                "expected_error": "RadicalDomainError",
                "max_ms": 50.0,
            },
            {
                "id": "N-11-decimal-approximation-large-prime-square-above-ceiling",
                "op": "sqrt_rational",
                "arg": "300000000/300017041",
                "expected_error": "RadicalDomainError",
                "max_ms": 50.0,
            },
        ],
    }
    return corpus


def evaluate_corpus(corpus: dict) -> dict:
    import importlib.util
    from types import ModuleType
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.simulation.geometry import radical as R

    # Load audited historical scorer from commit ecdc26b0
    scorer_src = git_blob(HISTORY_W2, f"{HIST_W2_PATH}/tools/evaluate_holdout_wave2.py")
    assert hashlib.sha256(scorer_src).hexdigest() == "e9c36a177c2f43cb8af59f361a78421b6f253a5c642e980ad98939793ae51e12"
    scorer = ModuleType("historical_section_scorer")
    scorer.__file__ = str(RUN / "tools/historical_scorer_read_only.py")
    exec(compile(scorer_src, scorer.__file__, "exec"), scorer.__dict__)
    scorer.ROOT = ROOT
    tax = json.loads(git_blob(HISTORY_W2, f"{HIST_W2_PATH}/tools/refusal_taxonomy.json"))

    e2e_rows = []
    for c in corpus["end_to_end_cases"]:
        r = run_typed_fact_next_v2_route(deepcopy(c["payload"]))
        resp = build_adapter4_response(r, c["payload"]["problem_text"])
        case_meta = dict(
            c,
            stratum="development",
            question_type="section_and_area",
            expected_disposition="SERVE",
            acceptable_categories=[],
        )
        rec = scorer.score_observed_response(case_meta, c["oracle"], tax, r, resp)
        rec["matches_expected"] = rec["outcome"] == "SERVED_CORRECT" and not rec.get("oracle_mismatches")
        e2e_rows.append(rec)

    kernel_rows = []
    for kc in corpus["kernel_cases"]:
        t0 = time.perf_counter()
        try:
            if kc["op"] == "sqrt_rational":
                val = R.sqrt_rational(Fraction(kc["arg"]))
            elif kc["op"] == "radical":
                val = R.radical(Fraction(kc["he"]), int(kc["can"]), int(kc.get("mu", 0)))
            elif kc["op"] == "multiply":
                a = R.radical(Fraction(kc["a"]["he"]), int(kc["a"]["can"]), int(kc["a"].get("mu", 0)))
                b = R.radical(Fraction(kc["b"]["he"]), int(kc["b"]["can"]), int(kc["b"].get("mu", 0)))
                val = R.multiply(a, b)
            else:
                raise RuntimeError(f"Unknown op: {kc['op']}")
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            actual_type = type(val).__name__
            actual_json = R.to_json(val)
            actual_display = R.display(val)
            sq_ok = True
            if kc["expected_square"] is not None:
                sq_val = R.square(val)
                sq_ok = isinstance(sq_val, Fraction) and sq_val == Fraction(kc["expected_square"])
            passed = (
                actual_type == kc["expected_type"]
                and actual_json == kc["expected_json"]
                and actual_display == kc["expected_display"]
                and sq_ok
            )
            kernel_rows.append({
                "id": kc["id"],
                "passed": passed,
                "actual_type": actual_type,
                "actual_json": actual_json,
                "actual_display": actual_display,
                "square_ok": sq_ok,
                "elapsed_ms": round(elapsed_ms, 3),
            })
        except R.RadicalDomainError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            kernel_rows.append({
                "id": kc["id"],
                "passed": False,
                "error": "RadicalDomainError",
                "detail": str(exc),
                "elapsed_ms": round(elapsed_ms, 3),
            })

    meta_rows = []
    for mg in corpus["metamorphic_groups"]:
        mid = mg["id"]
        try:
            if mid == "M-01-dev-1-3-equivalent-paths":
                vals = [
                    R.sqrt_rational(Fraction(38130625, 58564)),
                    R.radical(Fraction(1, 58564), 2233081922500),
                    R.divided_by_rational(R.sqrt_rational(38130625), 242),
                    R.multiply(Fraction(25, 121), Fraction(247, 2)),
                ]
            elif mid == "M-02-w2-a04-equivalent-paths":
                vals = [
                    R.sqrt_rational(Fraction(253125000, 485809)),
                    R.radical(Fraction(1, 485809), 122970403125000),
                    R.divided_by_rational(R.sqrt_rational(253125000), 697),
                    R.multiply(Fraction(2250, 697), R.sqrt_rational(50)),
                ]
            elif mid == "M-03-shared-prime-product-paths":
                p = 1026601
                vals = [
                    R.multiply(R.sqrt_rational(2 * p), R.sqrt_rational(3 * p)),
                    R.radical(1, 6 * p * p),
                    R.times_rational(R.sqrt_rational(6), p),
                ]
            elif mid == "M-04-cancellation-to-exact-zero":
                vals = [
                    R.add(
                        R.multiply(R.sqrt_rational(Fraction(50, 49)), R.sqrt_rational(Fraction(98, 25))),
                        R.negate(Fraction(2)),
                    ),
                    Fraction(0),
                ]
            elif mid == "M-05-serialization-and-parse-roundtrip":
                w = R.sqrt_rational(Fraction(253125000, 485809))
                vals = [
                    w,
                    R.from_json(R.to_json(w)),
                    R.parse_exact(R.display(w)),
                ]
            elif mid == "M-06-square-is-exact-inverse-of-sqrt-rational":
                xs = [
                    Fraction(38130625, 58564),
                    Fraction(253125000, 485809),
                    Fraction(3 * (787867**2), 468449**2),
                ]
                ok_inv = all(R.square(R.sqrt_rational(x)) == x for x in xs)
                vals = [Fraction(1) if ok_inv else Fraction(0), Fraction(1)]
            else:
                raise RuntimeError(f"Unknown metamorphic group: {mid}")

            all_eq = all(v == vals[0] and type(v) is type(vals[0]) and hash(v) == hash(vals[0]) for v in vals[1:])
            json_ok = R.to_json(vals[0]) == mg["expected_json"]
            disp_ok = R.display(vals[0]) == mg["expected_display"]
            meta_rows.append({
                "id": mid,
                "passed": bool(all_eq and json_ok and disp_ok),
                "all_equal_and_same_hash": all_eq,
                "actual_json": R.to_json(vals[0]),
                "actual_display": R.display(vals[0]),
            })
        except R.RadicalDomainError as exc:
            meta_rows.append({
                "id": mid,
                "passed": False,
                "error": "RadicalDomainError",
                "detail": str(exc),
            })

    neg_rows = []
    for nc in corpus["negative_cases"]:
        t0 = time.perf_counter()
        try:
            if nc["op"] == "sqrt_rational":
                R.sqrt_rational(Fraction(nc["arg"]))
            elif nc["op"] == "radical":
                R.radical(Fraction(nc["he"]), int(nc["can"]), int(nc.get("mu", 0)))
            elif nc["op"] == "multiply":
                a = R.radical(Fraction(nc["a"]["he"]), int(nc["a"]["can"]), int(nc["a"].get("mu", 0)))
                b = R.radical(Fraction(nc["b"]["he"]), int(nc["b"]["can"]), int(nc["b"].get("mu", 0)))
                R.multiply(a, b)
            elif nc["op"] == "add_incommensurable":
                R.add(R.sqrt_rational(2), R.sqrt_rational(3))
            else:
                raise RuntimeError(f"Unknown negative op: {nc['op']}")
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            neg_rows.append({
                "id": nc["id"],
                "passed": False,
                "error": None,
                "elapsed_ms": round(elapsed_ms, 3),
            })
        except R.RadicalDomainError as exc:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            neg_rows.append({
                "id": nc["id"],
                "passed": elapsed_ms <= nc["max_ms"],
                "error": "RadicalDomainError",
                "detail": str(exc),
                "elapsed_ms": round(elapsed_ms, 3),
            })

    summary = {
        "end_to_end_passed": f"{sum(r['matches_expected'] for r in e2e_rows)}/{len(e2e_rows)}",
        "kernel_passed": f"{sum(r['passed'] for r in kernel_rows)}/{len(kernel_rows)}",
        "metamorphic_passed": f"{sum(r['passed'] for r in meta_rows)}/{len(meta_rows)}",
        "negative_passed": f"{sum(r['passed'] for r in neg_rows)}/{len(neg_rows)}",
        "all_passed": (
            all(r["matches_expected"] for r in e2e_rows)
            and all(r["passed"] for r in kernel_rows)
            and all(r["passed"] for r in meta_rows)
            and all(r["passed"] for r in neg_rows)
        ),
    }
    return {
        "schema": "w2-m4-exact-radical-evaluation-result/1",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "product_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "--", "backend/app"], cwd=ROOT)
        ).hexdigest(),
        "live_provider_calls": 0,
        "summary": summary,
        "end_to_end_cases": e2e_rows,
        "kernel_cases": kernel_rows,
        "metamorphic_groups": meta_rows,
        "negative_cases": neg_rows,
    }


def main() -> None:
    mode = sys.argv[1]
    inp_path = RUN / "inputs/development.json"
    if mode == "build-and-red":
        if inp_path.exists():
            raise FileExistsError(inp_path)
        corpus = build_corpus()
        inp_path.parent.mkdir(parents=True, exist_ok=True)
        inp_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        res = evaluate_corpus(corpus)
        res["corpus_sha256"] = hashlib.sha256(inp_path.read_bytes()).hexdigest()
        out_path = RUN / "results/red-before.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("x", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
    elif mode == "green":
        corpus = json.loads(inp_path.read_text(encoding="utf-8"))
        res = evaluate_corpus(corpus)
        res["corpus_sha256"] = hashlib.sha256(inp_path.read_bytes()).hexdigest()
        out_path = RUN / "results/green-after.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("x", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(res["summary"], ensure_ascii=False, indent=2))
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
