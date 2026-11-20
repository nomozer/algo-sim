"""Freeze /12 preregistered manifest, criteria, baseline identity, and deterministic parser dry-run stratum.

Usage:
  python freeze_v12_acceptance.py <out.json> --mode p2_baseline   (requires empty backend/ + frontend/ diff vs /11 HEAD)
  python freeze_v12_acceptance.py <out.json> --mode candidate_bind (runs after P7/P9 candidate freeze on clean tree)
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

from app.ai.local_geometry_parser import (  # noqa: E402
    LOCAL_GEOMETRY_PARSER_VERSION,
    LOCAL_PARSE_COMPLETE,
    parse_geometry_problem_locally,
)
from app.ai.local_slm_extractor import (  # noqa: E402
    LOCAL_SLM_EXTRACTOR_V9_VERSION,
    SLM_GROUNDING_VALIDATOR_V9_VERSION,
)
from app.ai.local_slm_runtime import LLAMA_CPP_RUNTIME_SPEC, resolve_local_slm_model_spec  # noqa: E402
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY  # noqa: E402


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", type=Path)
    ap.add_argument("--mode", choices=("p2_baseline", "candidate_bind"), required=True)
    args = ap.parse_args()

    if args.out.exists():
        raise SystemExit(f"refusing to overwrite {args.out}")

    if args.mode == "p2_baseline":
        code_diff = _git("diff", "--stat", "ef1075e7df4727e895a913ef4e6fdd8382b8d671", "HEAD", "--", "backend/", "frontend/")
        assert code_diff == "", f"P2 freeze requires 0 backend/frontend edits! Got:\n{code_diff}"
    else:
        assert _git("status", "--porcelain", "--untracked-files=no") == "", "candidate_bind requires clean tracked tree"

    man_p = RUN / "V12_ACCEPTANCE_MANIFEST.json"
    crit_p = RUN / "V12_ACCEPTANCE_CRITERIA.json"
    man = json.loads(man_p.read_text(encoding="utf-8"))
    crit = json.loads(crit_p.read_text(encoding="utf-8"))
    assert _sha(man_p) == crit["manifest"]["sha256"], "manifest sha256 mismatch vs criteria"

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
        rows.append({
            "case_id": c["case_id"],
            "intent": c["simulation_intent"],
            "in_scope": in_scope,
            "preregistered_slm_target": bool(c.get("preregistered_slm_target")),
            "parse_raw": raw.status,
            "parse_v3": nrm.status if nrm else None,
            "v3_changed": v3.changed,
            "stratum": ("PARSER_COMPLETE" if complete else "SLM_REQUIRED") if in_scope else "SEPARATE",
        })

    in_scope_rows = [r for r in rows if r["in_scope"]]
    slm_req = [r for r in in_scope_rows if r["stratum"] == "SLM_REQUIRED"]
    targets = [r for r in in_scope_rows if r["preregistered_slm_target"]]
    out = {
        "schema": "axo-v12-evaluation-freeze/1",
        "phase_mode": args.mode,
        "frozen_before_any_v12_code_change": args.mode == "p2_baseline",
        "zero_backend_frontend_diff_vs_v11": args.mode == "p2_baseline",
        "code": {
            "head": _git("rev-parse", "HEAD"),
            "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
            "candidate_commit": cand.get("commit"),
            "product_commit_sha": cand.get("product_commit_sha"),
            "measured_system_tree_hash": cand["measured_system"]["tree_hash"],
            "cache_version": CACHE_VERSION,
            "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
            "semantic_environment_hash": lock.get("semantic_environment_hash"),
            "parser_version": LOCAL_GEOMETRY_PARSER_VERSION,
            "slm_extractor_version": LOCAL_SLM_EXTRACTOR_V9_VERSION,
            "slm_validator_version": SLM_GROUNDING_VALIDATOR_V9_VERSION,
        },
        "model": {
            "key": spec.model_key,
            "sha256": spec.sha256,
            "llama_cpp_release": LLAMA_CPP_RUNTIME_SPEC.release_tag,
        },
        "inputs": {
            "manifest_sha256": _sha(man_p),
            "criteria_sha256": _sha(crit_p),
        },
        "counts": {
            "valid_total": len(rows),
            "in_scope": len(in_scope_rows),
            "parser_complete": sum(r["stratum"] == "PARSER_COMPLETE" for r in in_scope_rows),
            "slm_required": len(slm_req),
            "preregistered_slm_targets": len(targets),
            "preregistered_slm_targets_in_slm_required": sum(r["stratum"] == "SLM_REQUIRED" for r in targets),
            "underdetermined_diagnostic": sum(not r["in_scope"] for r in rows),
            "negative": len(man["negative_cases"]),
        },
        "rows": rows,
    }
    args.out.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out["counts"], ensure_ascii=False), "head=", out["code"]["head"][:10])


if __name__ == "__main__":
    main()
