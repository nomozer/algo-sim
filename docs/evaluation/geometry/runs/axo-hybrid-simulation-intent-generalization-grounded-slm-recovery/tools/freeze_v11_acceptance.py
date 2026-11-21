"""Freeze the /11 blind live acceptance BEFORE any live call: identities + the SLM_REQUIRED stratum.

Stratum (pre-registered, V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json §slm_recovery): an in-scope case is SLM_REQUIRED when
the deterministic parser on the frozen candidate returns no LOCAL_PARSE_COMPLETE, neither on the raw text nor on the
`slm-verified-normalizer/3` text (the two texts the product fast path parses). 0 model calls, 0 network.
The router's own escalation decision is recorded beside it (not used for the stratum).
usage (from backend/, clean tree at the commit under test): python <this> <out.json>
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, ".")
RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
OUT = Path(sys.argv[1])
if OUT.exists():
    raise SystemExit(f"refusing to overwrite {OUT}")

from app.ai.local_geometry_parser import LOCAL_GEOMETRY_PARSER_VERSION, LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import LOCAL_SLM_EXTRACTOR_V9_VERSION, SLM_GROUNDING_VALIDATOR_V9_VERSION  # noqa: E402
from app.ai.local_slm_runtime import LLAMA_CPP_RUNTIME_SPEC, resolve_local_slm_model_spec  # noqa: E402
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


assert git("status", "--porcelain", "--untracked-files=no") == "", "freeze needs a clean tracked tree"
man_p, crit_p = RUN / "V11_LIVE_ACCEPTANCE_MANIFEST.json", RUN / "V11_ACCEPTANCE_CRITERIA_PREREGISTERED.json"
crit = json.loads(crit_p.read_text(encoding="utf-8"))
assert sha(man_p) == crit["manifest"]["sha256"], "manifest changed after pre-registration"
man = json.loads(man_p.read_text(encoding="utf-8"))
cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
spec = resolve_local_slm_model_spec("v9")
SPEC_ANTICIPATED = {"S09", "S10", "S11"}   # phrasings listed verbatim in the /11 campaign spec (seen before fixes)

rows = []
for c in man["valid_cases"]:
    text = c["original_input"]
    raw = parse_geometry_problem_locally(text, use_cache=False)
    v3 = normalize_for_slm_grounding(text, normalizer_version="v3")
    nrm = parse_geometry_problem_locally(v3.canonical_text, use_cache=False) if v3.changed else None
    complete = raw.status == LOCAL_PARSE_COMPLETE or (nrm is not None and nrm.status == LOCAL_PARSE_COMPLETE)
    in_scope = c["expected_behavior"] == "SERVE"
    rows.append({"case_id": c["case_id"], "intent": c["simulation_intent"], "in_scope": in_scope,
                 "parse_raw": raw.status, "parse_v3": nrm.status if nrm else None, "v3_changed": v3.changed,
                 "stratum": ("PARSER_COMPLETE" if complete else "SLM_REQUIRED") if in_scope else "SEPARATE",
                 "spec_anticipated": c["case_id"] in SPEC_ANTICIPATED})

ins = [r for r in rows if r["in_scope"]]
out = {
    "schema": "axo-v11-live-acceptance-freeze/1",
    "frozen_before_live_calls": True,
    "code": {"head": git("rev-parse", "HEAD"), "tracked_tree_clean": True,
             "candidate_commit": cand.get("commit"), "measured_system_tree_hash": cand["measured_system"]["tree_hash"], "measured_system_files": cand["measured_system"]["so_file"],
             "cache_version": CACHE_VERSION, "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
             "parser_version": LOCAL_GEOMETRY_PARSER_VERSION, "slm_extractor_version": LOCAL_SLM_EXTRACTOR_V9_VERSION,
             "slm_validator_version": SLM_GROUNDING_VALIDATOR_V9_VERSION},
    "model": {"key": spec.model_key, "sha256": spec.sha256, "llama_cpp_release": LLAMA_CPP_RUNTIME_SPEC.release_tag},
    "browser": {"driver": "playwright", "playwright_version": json.loads((ROOT / "frontend/node_modules/playwright/package.json").read_text())["version"],
                "engine": "chromium (bundled with playwright)"},
    "inputs": {"manifest_sha256": sha(man_p), "criteria_sha256": sha(crit_p)},
    "stratum_rule": crit["slm_recovery"]["stratum"],
    "counts": {"in_scope": len(ins), "slm_required": sum(r["stratum"] == "SLM_REQUIRED" for r in ins),
               "parser_complete": sum(r["stratum"] == "PARSER_COMPLETE" for r in ins),
               "spec_anticipated": sorted(SPEC_ANTICIPATED)},
    "rows": rows,
}
OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(out["counts"]), out["code"]["head"][:10], out["code"]["measured_system_tree_hash"])
