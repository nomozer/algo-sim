"""Freeze a preregistered acceptance set: manifest + criteria hashes, code/model identity and the deterministic-parser
dry-run stratum of every case (axo-live-acceptance-harness/1; generalised from the /12 `freeze_v12_acceptance.py`).

  --mode baseline        before any product change of the run: refuses unless backend/ and frontend/ are identical to
                         --baseline-ref (the commit the holdout is frozen against)
  --mode candidate_bind  after the candidate freeze, on a clean tracked tree: re-derives the stratum on the evaluated code

usage: python freeze_acceptance.py --manifest M --criteria C --mode baseline --baseline-ref <sha> --out <new file>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "backend"))
HARNESS_VERSION = "axo-live-acceptance-harness/1"


def _sha(p: Path) -> str:
    """LF-normalised: core.autocrlf may rewrite a frozen file's line endings on checkout, never its content."""
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True, type=Path)
    ap.add_argument("--criteria", required=True, type=Path)
    ap.add_argument("--mode", required=True, choices=("baseline", "candidate_bind"))
    ap.add_argument("--baseline-ref")
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        raise SystemExit(f"refusing to overwrite {a.out}")
    if a.mode == "baseline":
        if not a.baseline_ref:
            raise SystemExit("--baseline-ref is required in baseline mode")
        diff = _git("diff", "--stat", a.baseline_ref, "--", "backend/", "frontend/")
        if diff:
            raise SystemExit(f"baseline freeze requires 0 backend/frontend change vs {a.baseline_ref}:\n{diff}")
    elif _git("status", "--porcelain", "--untracked-files=no"):
        raise SystemExit("candidate_bind requires a clean tracked tree")

    from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION, LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally
    from app.ai.local_slm_extractor import LOCAL_SLM_EXTRACTOR_V9_VERSION, SLM_GROUNDING_VALIDATOR_V9_VERSION
    from app.ai.local_slm_runtime import LLAMA_CPP_RUNTIME_SPEC, resolve_local_slm_model_spec
    from app.ai.slm_verified_normalizer import normalize_for_slm_grounding
    from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY

    man = json.loads(a.manifest.read_text(encoding="utf-8"))
    crit = json.loads(a.criteria.read_text(encoding="utf-8"))
    if crit["manifest"]["sha256"] != _sha(a.manifest):
        raise SystemExit("manifest sha256 differs from the one the criteria registered")
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "backend/cache_identity.lock.json").read_text(encoding="utf-8"))
    spec = resolve_local_slm_model_spec("v9")

    rows = []
    for c in man["valid_cases"]:
        text = c["original_input"]
        raw = parse_geometry_problem_locally(text, use_cache=False)
        v3 = normalize_for_slm_grounding(text, normalizer_version="v3")
        nrm = parse_geometry_problem_locally(v3.canonical_text, use_cache=False) if v3.changed else None
        complete = raw.status == LOCAL_PARSE_COMPLETE or (nrm is not None and nrm.status == LOCAL_PARSE_COMPLETE)
        in_scope = c["expected_behavior"] == "SERVE"
        rows.append({"case_id": c["case_id"], "intent": c["simulation_intent"], "in_scope": in_scope,
                     "preregistered_slm_target": bool(c.get("preregistered_slm_target")), "parse_raw": raw.status,
                     "parse_v3": nrm.status if nrm else None, "v3_changed": v3.changed,
                     "stratum": ("PARSER_COMPLETE" if complete else "SLM_REQUIRED") if in_scope else "SEPARATE"})
    ins = [r for r in rows if r["in_scope"]]
    tgt = [r for r in ins if r["preregistered_slm_target"]]
    out = {
        "schema": "axo-evaluation-freeze/1",
        "harness_version": HARNESS_VERSION,
        "phase_mode": a.mode,
        "baseline_ref": a.baseline_ref,
        "frozen_before_any_product_change": a.mode == "baseline",
        "code": {"head": _git("rev-parse", "HEAD"), "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
                 "candidate_commit": cand.get("commit"), "product_commit_sha": cand.get("product_commit_sha"),
                 "measured_system_tree_hash": cand["measured_system"]["tree_hash"], "cache_version": CACHE_VERSION,
                 "route_d_cache_policy": ROUTE_D_CACHE_POLICY, "semantic_environment_hash": lock.get("semantic_environment_hash"),
                 "parser_version": LOCAL_GEOMETRY_PARSER_VERSION, "slm_extractor_version": LOCAL_SLM_EXTRACTOR_V9_VERSION,
                 "slm_validator_version": SLM_GROUNDING_VALIDATOR_V9_VERSION},
        "model": {"key": spec.model_key, "sha256": spec.sha256, "llama_cpp_release": LLAMA_CPP_RUNTIME_SPEC.release_tag},
        "inputs": {"manifest_sha256": _sha(a.manifest), "criteria_sha256": _sha(a.criteria)},
        "counts": {"valid_total": len(rows), "in_scope": len(ins),
                   "parser_complete": sum(r["stratum"] == "PARSER_COMPLETE" for r in ins),
                   "slm_required": sum(r["stratum"] == "SLM_REQUIRED" for r in ins),
                   "preregistered_slm_targets": len(tgt),
                   "preregistered_slm_targets_in_slm_required": sum(r["stratum"] == "SLM_REQUIRED" for r in tgt),
                   "separate": sum(not r["in_scope"] for r in rows), "negative": len(man["negative_cases"])},
        "rows": rows,
    }
    a.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"]), "head=", out["code"]["head"][:10])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
