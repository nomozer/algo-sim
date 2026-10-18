"""Derive the ONE synthetic fixture this run needs: insufficient_specification + refusal_cause SOURCE.

No producer emits that pair (Route D preview: group MISSING_DATA -> UNKNOWN, `hybrid_preview._NHOM`; LLM_ONLY:
GIVEN_VALUE_NOT_IN_SOURCE reaches the client as geometry_generation_failed + SOURCE). The frontend branch for it
(HFOI-F6) still has to be exercised, so it is derived from a frozen fixture by changing exactly one field.
usage: python make_synthetic.py <fixtures-adapter-2 dir> <out json>
"""
import hashlib, json, sys
from pathlib import Path

src_dir, out = Path(sys.argv[1]), Path(sys.argv[2])
canon = lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
src = json.loads((src_dir / "refusal-missing-dimension.json").read_text(encoding="utf-8"))
manifest = json.loads((src_dir / "manifest.json").read_text(encoding="utf-8"))
row = next(r for r in manifest["fixtures"] if r["id"] == "refusal-missing-dimension")
assert hashlib.sha256(canon(src["response"]).encode()).hexdigest() == row["response_sha256"]
env = dict(src["response"]["envelope"])
assert env["failure_category"] == "insufficient_specification" and env["refusal_cause"] == "UNKNOWN"
env["refusal_cause"] = "SOURCE"
fx = {
    "schema": "hybrid-offline-synthetic-fixture/1",
    "id": "synthetic-insufficient-specification-source",
    "SYNTHETIC": True,
    "provenance": {
        "derived_from": "docs/evaluation/geometry/runs/hybrid-preview-contract-hardening/fixtures-adapter-2/refusal-missing-dimension.json",
        "derived_from_response_sha256": row["response_sha256"],
        "only_change": "response.envelope.refusal_cause: UNKNOWN -> SOURCE",
        "why_synthetic": "no producer emits insufficient_specification + SOURCE (preview MISSING_DATA -> UNKNOWN; LLM_ONLY input_not_grounded -> geometry_generation_failed)",
        "learner_reason": "copied unchanged from the source fixture (UNKNOWN wording); not regenerated, no backend text exists for this pair",
        "not_a_backend_response": True,
    },
    "response": {"schema_version": src["response"]["schema_version"], "envelope": env},
}
out.write_text(json.dumps(fx, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
print("written", out, hashlib.sha256(canon(fx["response"]).encode()).hexdigest())
