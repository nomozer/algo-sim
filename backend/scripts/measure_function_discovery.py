"""Comparative replay for run `goal-directed-function-discovery` — 0 model calls, never writes over an output.

    bundle  --out B.json                      text + verified Typed Facts of every corpus, built from THIS checkout
    scenes  --out DIR                         real-route Scene3D fixtures for the browser harness (src=function-discovery)
    arm     --code-root R --bundle B.json --label L --out O.json [--registry VARIANT]
            run the bundle on the code under R/backend (a detached worktree of another commit, or this checkout)
    compare --bundle B.json --arms O1.json O2.json … --out C.json

Registry variants (arm NEW only; they need the planning-contract call templates of geometry-fact-planner/6):
production · no-midpoint · no-plane-ask · centroid (experimental contract for the existing `centroid` function) ·
reversed (catalog order reversed) · lying (descriptor `centroid` claimed by the `midpoint` function).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import tracemalloc
from collections import Counter
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "docs/evaluation/geometry/runs/goal-directed-function-discovery"
os.environ.setdefault("ALLOW_LIVE_AI", "0")


def _write(path: Path, data) -> None:
    if path.exists():
        raise SystemExit(f"refusing to overwrite {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# ── bundle (this checkout) ────────────────────────────────────────────────────────────────────────────────────────
def bundle(out: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from tests.geometry import hybrid_compiler_benchmark as HB
    from tests.geometry.test_two_line_plane_section import problem

    rows = []
    new = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))
    for split in ("positive", "negative", "discovery"):
        for c in new[split]:
            rows.append({"corpus": f"new/{split}", "id": c["id"], "text": c["text"], "facts": c["payload"]["facts"],
                         "expect": {k: c[k] for k in ("expected_squared", "expected_codes") if k in c}})
    for c in HB.cases():
        e = dict(c["expect"])
        if "answer_sq" in e:
            e["answer_sq"] = str(e["answer_sq"])
        rows.append({"corpus": "benchmark30", "id": c["id"], "text": c["text"], "facts": c["facts"], "expect": e})
    rb = json.loads((ROOT / "docs/evaluation/geometry/runs/goal-directed-planner-generalization-audit/"
                            "next-slice-corpus.json").read_text(encoding="utf-8"))
    for split in ("positive", "negative"):
        for c in rb[split]:
            e = ({"expected_squared": str(c["expected_squared"])} if split == "positive"
                 else {"expected_code": c["expected_code"]})
            rows.append({"corpus": f"result_binding/{split}", "id": c["id"], "text": c["text"],
                         "facts": c["payload"]["facts"], "expect": e})
    two = ROOT / "docs/evaluation/geometry/runs/two-line-plane-section/inputs"
    for split, name in (("development", "math-corpus.json"), ("heldout", "heldout.json")):
        for i, row in enumerate(json.loads((two / name).read_text(encoding="utf-8"))["cases"]):
            text, payload = problem(row["family"], row["mid"], row["lines"])
            rows.append({"corpus": f"two_line/{split}", "id": f"{split}-{i}", "text": text, "facts": payload["facts"],
                         "expect": {"status": row["expected"], **({"area_sq": row["area_sq"]} if "area_sq" in row else {})}})
    _write(out, {"schema": "function_discovery_bundle/1", "rows": rows})
    print(json.dumps(Counter(r["corpus"] for r in rows)))


# ── registry variants (arm NEW) ───────────────────────────────────────────────────────────────────────────────────
def experimental_centroid_contract(registry):
    """ONE planning contract for the existing `centroid` function: data only, no planner/gate/engine code."""
    from dataclasses import replace

    P, T = registry.PlanningContract, registry.PlanningTerm
    contract = P(inputs=(T("Point", ("A",)), T("Point", ("B",)), T("Point", ("C",))), effect=T("Point", ("G",)),
                 source_policy="derived_point", verifier="centroid", call=(("point", "G"), ("polygon", ("A", "B", "C"))),
                 fresh="G", descriptor="centroid",
                 phrase=r"trọng tâm\s+(?:của\s+)?(?:(?:tam giác|Δ)\s*)?(?P<ops>{P}{P}{P})(?![\w'])")
    return replace(registry.REGISTRY["centroid"], planning=contract)


def apply_variant(variant: str):
    from dataclasses import replace

    from app.simulation.geometry_functions import planner, registry

    R = registry.REGISTRY
    if variant == "production":
        return
    if not hasattr(registry.PlanningContract, "__dataclass_fields__") or "call" not in registry.PlanningContract.__dataclass_fields__:
        raise SystemExit(f"registry variant {variant!r} needs planning-contract call templates (not in this arm)")
    if variant == "no-midpoint":
        R["midpoint"] = replace(R["midpoint"], planning=None)
    elif variant == "no-plane-ask":
        R["ask_distance_point_plane"] = replace(R["ask_distance_point_plane"], planning=None)
    elif variant == "centroid":
        R["centroid"] = experimental_centroid_contract(registry)
    elif variant == "lying":
        lie = replace(experimental_centroid_contract(registry).planning, call=(("point", "G"), ("segment", ("A", "B"))))
        R["midpoint"] = replace(R["midpoint"], planning=lie)
    elif variant == "reversed":
        rev = dict(reversed(list(R.items())))
        R.clear()
        R.update(rev)
    else:
        raise SystemExit(f"unknown variant {variant}")
    assert planner.REGISTRY is registry.REGISTRY


# ── one arm ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _square(v) -> str | None:
    try:
        from app.simulation.geometry.radical import Radical
    except ImportError:                                     # pragma: no cover — every arm has it
        Radical = ()
    if isinstance(v, Radical):
        return str(Fraction(v.he) ** 2 * v.can)
    if isinstance(v, (int, Fraction)):
        return str(Fraction(v) ** 2)
    return None


def arm(code_root: Path, bundle_path: Path, label: str, out: Path, variant: str) -> None:
    backend = code_root / "backend"
    sys.path.insert(0, str(backend))
    os.chdir(backend)
    from app.ai.function_route import run_fact_route
    from app.simulation.geometry_functions import planner
    from app.simulation.geometry_functions.registry import TuChoi

    apply_variant(variant)
    rows = json.loads(bundle_path.read_text(encoding="utf-8"))["rows"]
    res = []
    for row in rows:
        payload = {"facts": row["facts"]}
        t0 = time.perf_counter()
        r = run_fact_route(row["text"], json.loads(json.dumps(payload)))
        route_s = time.perf_counter() - t0
        squares = {}
        if r.status == "SERVED":
            fm = r.exec_result.final_memory
            squares = {q: _square(fm.get(f"kq_{q}")) for q in (r.answers or {})}
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
            stats = {"calls": len(k.calls), "functions": sorted({c["fn"] for c in k.calls}), "auxiliary": len(k.auxiliary),
                     "fresh_labels": fresh,
                     "needs": getattr(rv, "needs", None), "candidates": getattr(rv, "candidates", None),
                     "depth_max": getattr(rv, "depth_max", None), "resolver_used": getattr(rv, "used", None)}
        res.append({"corpus": row["corpus"], "id": row["id"], "status": r.status, "code": r.code,
                    "answers": r.answers or {}, "squares": squares, "plan_error": plan_err, "plan": stats,
                    "route_seconds": round(route_s, 4), "plan_seconds": round(plan_s, 5), "plan_peak_bytes": peak})
    _write(out, {"schema": "function_discovery_arm/1", "label": label, "registry_variant": variant,
                 "planner_version": planner.PLANNER_VERSION, "code_root": str(code_root), "model_calls": 0,
                 "rows": res})
    print(label, variant, Counter((x["corpus"], x["status"]) for x in res))


# ── compare ───────────────────────────────────────────────────────────────────────────────────────────────────────
def classify(row, got) -> str:
    e, served = row["expect"], got["status"] == "SERVED"
    corpus = row["corpus"]
    if "expected_squared" in e:                              # new positive/discovery, result-binding positive
        want = e["expected_squared"]
        ok = served and (all(got["squares"].get(q) == v for q, v in want.items()) if isinstance(want, dict)
                         else bool(got["squares"]) and all(v == want for v in got["squares"].values()))
        return "correct_served" if ok else "wrong_served" if served else "false_refusal"
    if "expected_codes" in e or "expected_code" in e:
        if served:
            return "wrong_served"
        codes = e.get("expected_codes") or [e["expected_code"]]
        if codes == ["closed source refusal"]:
            codes = ["SOURCE_PREMISE_UNREAD", "SOURCE_OBJECT_MISMATCH", "LOCAL_SOURCE_BINDING_UNVERIFIED"]
        if codes == ["dependency cycle refusal"]:
            codes = ["DEPENDENCY_CYCLE"]
        return "correct_refusal" if got["code"] in codes else "wrong_code_refusal"
    if corpus == "benchmark30":
        from tests.geometry import hybrid_compiler_benchmark as HB
        from types import SimpleNamespace
        r = SimpleNamespace(status=got["status"], code=got["code"], answers=got["answers"])
        return HB.classify({"expect": {**e, **({"answer_sq": Fraction(e["answer_sq"])} if "answer_sq" in e else {})},
                            "gap": ""}, r)["outcome"]
    # two-line: SERVED rows carry the oracle area²; refusals are positional (their codes vary by row)
    if e["status"] == "SERVED":
        from tests.geometry import hybrid_compiler_benchmark as HB
        ok = served and HB.answer_square(got["answers"].get("q", "")) == Fraction(e["area_sq"])
        return "correct_served" if ok else "wrong_served" if served else "false_refusal"
    return "wrong_served" if served else "correct_refusal"


def compare(bundle_path: Path, arm_paths: list[Path], out: Path) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    rows = {(r["corpus"], r["id"]): r for r in json.loads(bundle_path.read_text(encoding="utf-8"))["rows"]}
    arms = [json.loads(p.read_text(encoding="utf-8")) for p in arm_paths]
    table, per_case = {}, {}
    for a in arms:
        key = f'{a["label"]}[{a["registry_variant"]}]'
        counts: dict[str, Counter] = {}
        for got in a["rows"]:
            row = rows[(got["corpus"], got["id"])]
            outcome = classify(row, got)
            counts.setdefault(got["corpus"], Counter())[outcome] += 1
            per_case.setdefault(f'{got["corpus"]}::{got["id"]}', {})[key] = {
                "outcome": outcome, "status": got["status"], "code": got["code"], "answers": got["answers"],
                "plan": got["plan"], "plan_seconds": got["plan_seconds"], "route_seconds": got["route_seconds"],
                "plan_peak_bytes": got["plan_peak_bytes"]}
        table[key] = {c: dict(v) for c, v in sorted(counts.items())}
    keys = list(table)
    identical = {}
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            diff = sorted(cid for cid, by in per_case.items() if a in by and b in by and
                          (by[a]["status"], by[a]["code"], by[a]["answers"]) != (by[b]["status"], by[b]["code"], by[b]["answers"]))
            identical[f"{a} vs {b}"] = {"differing_cases": diff, "n_differing": len(diff)}
    _write(out, {"schema": "function_discovery_comparison/1", "model_calls": 0, "counts": table,
                 "pairwise_identity": identical, "cases": per_case})
    print(json.dumps(table, indent=1))


# ── browser fixtures (this checkout) ─────────────────────────────────────────────────────────────────────────────
#: (case, object born first, object born after it): the harness checks order, rendering under aux=0, selection,
#: backward playback, orbit/zoom/reset and the first object's own pixels.
SCENES = (("pyr-midpoint-to-plane", "khoi_S_ABCD", "M"), ("pyr-midpoint-to-named-line", "M", "H"),
          ("pyr-midpoint-to-result-line", "gt_g", "H"), ("cube-midpoint-to-plane", "khoi_ABCD_A_primeB_primeC_primeD_prime", "M"),
          ("prism-midpoint-to-plane", "khoi_ABC_A_primeB_primeC_prime", "M"), ("descriptor-operands-mismatch", None, None))


#: `--integration` (run `scene3d-visual-correctness`): the browser set re-exported from the integrated backend — the
#: plane-target scenes check the target plane itself (CONTRACT-BE-1), plus derived-line and length-goal fixtures.
INTEGRATION_SCENES = (("pyr-midpoint-to-plane", "khoi_S_ABCD", "mp_q"), ("cube-midpoint-to-plane", "khoi_ABCD_A_primeB_primeC_primeD_prime", "mp_q"),
                      ("prism-midpoint-to-plane", "khoi_ABC_A_primeB_primeC_prime", "mp_q"), ("pyr-midpoint-to-named-line", "M", "H"),
                      ("pyr-midpoint-to-result-line", "gt_g", "H"), ("cuboid-midpoint-to-result-line", "gt_g", "H"),
                      ("rb:derived-line-pyramid", "gt_g", "H"), ("rb:derived-line-cuboid", "gt_g", "H"),
                      ("rb:derived-line-prism", "gt_g", "H"), ("ge:pyramid-midpoint-A", "khoi_S_ABCD", "M"),
                      ("descriptor-operands-mismatch", None, None))


def scenes(out: Path, integration: bool = False) -> None:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.ai.function_route import run_fact_route

    corpus = json.loads((RUN / "corpus.json").read_text(encoding="utf-8"))
    cases = {c["id"]: c for split in ("positive", "negative") for c in corpus[split]}
    if integration:
        runs = ROOT / "docs/evaluation/geometry/runs"
        rb = json.loads((runs / "goal-directed-planner-generalization-audit/next-slice-corpus.json").read_text(encoding="utf-8"))
        ge = json.loads((runs / "generalized-goal-entry/corpus.json").read_text(encoding="utf-8"))
        cases |= {f"rb:{c['id']}": c for c in rb["positive"]} | {f"ge:{c['id']}": c for c in ge["positive"]}
    rows = []
    for cid, first, after in (INTEGRATION_SCENES if integration else SCENES):
        c = cases[cid]
        r = run_fact_route(c["text"], json.loads(json.dumps(c["payload"])))
        ids = {o["id"] for o in (r.scene3d or {}).get("objects", [])}
        if r.status == "SERVED" and not {first, after} <= ids:
            raise SystemExit(f"{cid}: scene lacks {first}/{after}: {sorted(ids)}")
        rows.append({"id": cid, "served": r.status == "SERVED", "code": r.code, "reason": r.reason, "kind": "descriptor",
                     "target": first, "foot": after, "scene": r.scene3d, "answers": r.answers, "text": c["text"]})
    _write(out / "scenes.json", rows)
    print(f"exported {len(rows)} fixtures; live calls 0")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("bundle"); b.add_argument("--out", type=Path, required=True)
    s = sub.add_parser("scenes"); s.add_argument("--out", type=Path, required=True); s.add_argument("--integration", action="store_true")
    a = sub.add_parser("arm")
    a.add_argument("--code-root", type=Path, required=True); a.add_argument("--bundle", type=Path, required=True)
    a.add_argument("--label", required=True); a.add_argument("--out", type=Path, required=True)
    a.add_argument("--registry", default="production")
    c = sub.add_parser("compare")
    c.add_argument("--bundle", type=Path, required=True); c.add_argument("--arms", type=Path, nargs="+", required=True)
    c.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    if args.cmd == "bundle":
        bundle(args.out.resolve())
    elif args.cmd == "scenes":
        scenes(args.out.resolve(), args.integration)
    elif args.cmd == "arm":
        arm(args.code_root.resolve(), args.bundle.resolve(), args.label, args.out.resolve(), args.registry)
    else:
        compare(args.bundle.resolve(), [p.resolve() for p in args.arms], args.out.resolve())


if __name__ == "__main__":
    main()
